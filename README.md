# 🗺️ FlagMap Bot

**FlagMap Bot** is a Discord utility bot designed to **copy and re-upload images** from one server channel to another — perfect for backing up media, transferring projects, or sharing image archives between servers.

---

## 🚀 Features

- `/copy` → Copies up to **20 most recent images** from a channel.
- `/paste` → Reuploads the copied images in another channel.
- `/status` → Shows how many images are stored.
- `/cancel` → Cancels an ongoing upload.
- 📦 Stores image data in a local **SQLite database**.
- 💾 Keeps images after upload (no auto-delete).
- ⚡ Fast and asynchronous image upload with a progress bar.
- 🧠 Uses **strong database logic** to prevent data loss.

---

## 🧰 Requirements

- Python **3.9+** (recommended: **3.11+**)
- Discord bot token from [Discord Developer Portal](https://discord.com/developers/applications)
- The following Python packages:
  ```bash
  pip install -r requirements.txt
