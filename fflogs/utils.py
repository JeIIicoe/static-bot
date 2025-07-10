import os
import requests
import json
from typing import Dict, List, Union
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from dotenv import load_dotenv

load_dotenv()

# Comprehensive map of all relevant zones + encounters
ENCOUNTER_IDS_BY_ZONE: Dict[int, List[int]] = {
    None: [97, 98, 99, 100],             # Dawntrail current savage
    62: [93, 94, 95, 96],                # DT previous savage
    65: [1079],                          # FRU
    59: [1073, 1074, 1075, 1076, 1077],  # Legacy ultimates (Dawntrail)
    45: [1065],                          # DSR (Endwalker)
    53: [1068],                          # TOP (Endwalker)
    43: [1060, 1061, 1062],              # Legacy ultimates (Endwalker)
}

def get_access_token() -> str:
    response = requests.post("https://www.fflogs.com/oauth/token", data={
        "grant_type": "client_credentials",
        "client_id": os.getenv("FFLOGS_CLIENT_ID"),
        "client_secret": os.getenv("FFLOGS_CLIENT_SECRET")
    })
    response.raise_for_status()
    return response.json()["access_token"]

def get_graphql_client(token: str) -> Client:
    transport = RequestsHTTPTransport(
        url="https://www.fflogs.com/api/v2/client",
        headers={"Authorization": f"Bearer {token}"},
        use_json=True
    )
    return Client(transport=transport, fetch_schema_from_transport=True)

def fetch_rankings_by_zone(client: Client, character_id: int, zone_id: Union[int, None]) -> Dict[int, Dict[str, Union[str, float, int]]]:
    if zone_id is not None:
        query = gql("""
        query ($id: Int!, $zone: Int!) {
          characterData {
            character(id: $id) {
              zoneRankings(zoneID: $zone)
            }
          }
        }
        """)
        variables = {"id": character_id, "zone": zone_id}
    else:
        query = gql("""
        query ($id: Int!) {
          characterData {
            character(id: $id) {
              zoneRankings
            }
          }
        }
        """)
        variables = {"id": character_id}

    result = client.execute(query, variable_values=variables)
    raw = result["characterData"]["character"]["zoneRankings"]

    if not isinstance(raw, dict):
        raise TypeError("zoneRankings response is not a dict")
    if "error" in raw:
        raise ValueError(f"Zone {zone_id or 'latest'} not supported: {raw['error']}")

    encounter_data = {}
    for entry in raw.get("rankings", []):
        encounter = entry.get("encounter", {})
        if not encounter:
            continue
        eid = encounter.get("id")
        if eid is None:
            continue
        encounter_data[eid] = {
            "encounter_name": encounter.get("name"),
            "percentile": entry.get("rankPercent"),
            "spec": entry.get("spec"),
            "kills": entry.get("totalKills"),
        }

    return encounter_data

def get_parses_for_fights(client: Client, character_id: int) -> Dict[int, Dict[str, Union[str, float, int]]]:
    final_data: Dict[int, Dict[str, Union[str, float, int]]] = {}

    for zone_id in ENCOUNTER_IDS_BY_ZONE:
        try:
            zone_data = fetch_rankings_by_zone(client, character_id, zone_id)
            for eid, data in zone_data.items():
                # Update if no data exists or this one has more kills or is lockedIn/better
                if eid not in final_data:
                    final_data[eid] = data
                else:
                    existing = final_data[eid]
                    new_kills = data.get("kills", 0) or 0
                    old_kills = existing.get("kills", 0) or 0
                    new_pct = data.get("percentile", 0) or 0
                    old_pct = existing.get("percentile", 0) or 0

                    if new_kills > old_kills or new_pct > old_pct:
                        final_data[eid] = data
        except Exception as e:
            print(f"[ERROR] Failed to fetch parses for zone {zone_id}: {e}")

    return final_data
