## The Static CEO

A personalised static organisation bot for Discord, written in Python using [`discord.py`](https://discordpy.readthedocs.io/en/stable/). Currently supports slash commands like `/ping` and `/hello`.

---

### Setup Instructions

#### 1. **Clone the Repository**

```bash
git clone https://github.com/yourusername/static-bot.git
cd static-bot
```

---

#### 2. **Create a Virtual Environment**

##### On Windows:

```bash
py -3.12 -m venv venv
venv\Scripts\activate
```

##### On macOS / Linux:

```bash
python3.12 -m venv venv
source venv/bin/activate
```

---

#### 3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

---

#### 4. **Create a `.env` File**

In the root directory, create a `.env` file with the following format:

```
DISCORD_TOKEN=your_discord_bot_token_here
GUILD_ID=your_discord_server_id_here
```

* `DISCORD_TOKEN`: Found in the [Discord Developer Portal](https://discord.com/developers/applications)
* `GUILD_ID`: Right-click your server icon in Discord → **Copy Server ID** (you must enable Developer Mode)

---

#### 5. **Run the Bot**

```bash
python main.py
```

You should see a message like:

```
READY | StaticBot#1234 is online.
```

You can now use `/hello` in your Discord server.

---

### For Developers

Once the virtual environment is set up:

* **Activate it before coding sessions**:

  ```bash
  # Windows
  venv\Scripts\activate

  # macOS/Linux
  source venv/bin/activate
  ```

* Then you can rerun the bot with:

  ```bash
  python main.py
  ```

---

### Current Slash Commands

* `/hello` – Responds with a random greeting

---