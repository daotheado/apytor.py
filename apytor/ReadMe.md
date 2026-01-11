# Torrent Manager (aria2 Wrapper)

A simple Python-based torrent manager that leverages [aria2](https://aria2.github.io/) for downloading torrents, magnet links, and direct URLs.  
It provides:
- Automatic configuration setup
- Retry logic with exponential backoff
- Progress bar visualization using `tqdm`
- Support for magnet links, torrent files, and HTTP/HTTPS URLs
- Extra BitTorrent trackers for better peer discovery

---

## 🚀 Features
- **Cross-platform support**: Works with Windows, Linux, and macOS (requires aria2 installed).
- **Automatic config generation**: Creates a default `aria2.conf` if none exists.
- **Progress tracking**: Displays download progress with a clean progress bar.
- **Retry mechanism**: Retries failed downloads with increasing delay.
- **Fallback options**: Applies extra settings if retries fail.

---

## 📦 Requirements
- Python 3.7+
- [aria2](https://aria2.github.io/) installed (binary `aria2c` must be accessible)
- Dependencies listed in `requirements.txt`

---

## 🔧 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/torrent-manager.git
   cd torrent-manager
