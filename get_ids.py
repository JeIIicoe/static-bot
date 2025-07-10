import os
from fflogsapi import FFLogsClient
from dotenv import load_dotenv

load_dotenv()

def get_all_encounters():
    client_id = os.getenv("FFLOGS_CLIENT_ID")
    client_secret = os.getenv("FFLOGS_CLIENT_SECRET")

    client = FFLogsClient(client_id, client_secret)

    all_encounters = []

    for expansion in client.all_expansions():
        print(f"\n=== {expansion.name()} ===")
        for zone in client.all_zones(expansion.id):
            for encounter in zone.encounters():
                all_encounters.append({"id": encounter.id, "name": encounter.name()})
                print(f"{encounter.id}: {encounter.name()}")

    client.close()
    return all_encounters

if __name__ == "__main__":
    get_all_encounters()
