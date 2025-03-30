# MediaMarauder 🎬

**MediaMarauder** is a Python script that automates the downloading and organizing of multimedia content — including movies, TV series, anime, documentaries, and docu-series — into structured directories suitable for media servers like Plex, Jellyfin, or Emby. It uses the powerful [TDL Telegram Downloader](https://github.com/iyear/tdl-telegram) to download content directly from Telegram messages.

![Example Gif](https://github.com/Ukly0/MediaMarauder/blob/main/example.gif)

## 🧠 Features

- Telegram bot integration for easy interaction
- Accepts both direct media links and attached files from Telegram
- Automatically sorts content into:
  - Movies
  - TV Series
  - Anime
  - Docu-Series
  - Documentaries
- Handles multi-season folder creation
- Detects and downloads full episode groups by just sending the **first episode link**
- Automatically extracts `.rar` archives for:
  - Series
  - Docu-Series
  - Anime
- Compatible with Plex, Jellyfin, Emby, and other media servers

## 📁 Directory Structure

By default, MediaMarauder organizes files under:

```
/media/disk/
├── Movies/
├── Series/<Series Name>/Season XX/
├── Anime/<Anime Name>/Season XX/
├── DocuSeries/<Title>/Season XX/
└── Documentaries/
```

## ⚙️ Requirements

- Python 3.8+
- [TDL](https://github.com/iyear/tdl-telegram) installed and working in terminal
- `unrar` installed on your system
- Python dependencies:
  - `python-telegram-bot`
  - `nest_asyncio`

## 📦 Installation

1. Clone this repository:

```bash
git clone https://github.com/Ukly0/MediaMarauder.git
cd mediamarauder
```

2. Install required packages:

```bash
pip install -r requirements.txt
```

3. Set your `BOT_TOKEN` and `ADMIN_CHAT_ID` in the script.

4. Ensure `tdl` is functional in your command line.

## 🚀 Usage

1. **Run the bot:**

```bash
python mediamarauder.py
```

2. **Telegram Setup:**

- Add your bot to a Telegram **group**.
- Set the group to **public**. This is essential for `tdl` to generate links from attached files.
- Make sure your bot has permission to read messages and media.

3. **Interact via Commands:**

Use these Telegram commands to set the media category:

- `/peliculas` 🎬 — Save to the Movies folder
- `/serie` 📺 — Start a prompt to name the series and specify the season
- `/anime` ✨ — Start setup for anime series
- `/docuseries` 📼 — Organize as docu-series
- `/documentales` — Save to Documentaries folder

4. **Send Content:**

You can send either:

- A **Telegram link** to a message (e.g., from a channel or group)
- **Media content directly** (video, document, audio, etc.)

MediaMarauder will:

- Use `tdl` to download the content
- Organize it in the correct directory
- If part of a **grouped message (like episodes)**, it will automatically download the **entire group**, even if only the first link is provided
- Automatically **extract `.rar` files** for series, anime, and docu-series

## 🙌 Credits

MediaMarauder uses:

- [TDL Telegram Downloader](https://github.com/iyear/tdl-telegram) by [@iyear](https://github.com/iyear)
- [`python-telegram-bot`](https://github.com/python-telegram-bot/python-telegram-bot)

## 📄 License

MIT License
