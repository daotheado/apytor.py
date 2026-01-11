#!/usr/bin/env python3
import os
import sys
import subprocess
import time
from pathlib import Path
from tqdm import tqdm  # pip install tqdm

# -----------------------------
# Config
# -----------------------------
if getattr(sys, 'frozen', False):
    # Running from PyInstaller bundle
    bundle_dir = sys._MEIPASS
    ARIA2_PATH = os.path.join(bundle_dir, "aria2c.exe")
else:
    # Normal Python run
    ARIA2_PATH = r"C:\Users\Usersname\FilepathTo\aria2-1.37.0-win-64bit-build1\aria2c.exe"

DEFAULT_CONF_DIR = Path.home() / ".aria2"
DEFAULT_CONF_FILE = DEFAULT_CONF_DIR / "aria2.conf"
DEFAULT_DOWNLOAD_DIR = Path.home() / "Downloads"

# Pacing and behavior
MAX_OVERALL_DOWNLOAD_LIMIT = "4M"
MAX_OVERALL_UPLOAD_LIMIT = "200K"
MAX_CONNECTIONS_PER_SERVER = "4"
RETRY_COUNT = 3
RETRY_DELAY_BASE = 5  # seconds

# BitTorrent/DHT settings
LISTEN_PORT = "6881"
ENABLE_DHT = True
ENABLE_PEX = True

EXTRA_TRACKERS = [
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://open.stealth.si:80/announce",
    "udp://tracker.torrent.eu.org:451/announce",
    "udp://opentracker.i2p.rocks:6969/announce"
]

# -----------------------------
# Utility functions
# -----------------------------
def print_info(msg): print(f"[INFO] {msg}")
def print_warn(msg): print(f"[WARN] {msg}")
def print_error(msg): print(f"[ERROR] {msg}")

def ensure_dirs():
    DEFAULT_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_CONF_DIR.mkdir(parents=True, exist_ok=True)

def ensure_config():
    if DEFAULT_CONF_FILE.exists():
        return
    lines = [
        f"dir={DEFAULT_DOWNLOAD_DIR.as_posix()}",
        "continue=true",
        "check-integrity=true",
        f"max-overall-download-limit={MAX_OVERALL_DOWNLOAD_LIMIT}",
        f"max-overall-upload-limit={MAX_OVERALL_UPLOAD_LIMIT}",
        f"max-connection-per-server={MAX_CONNECTIONS_PER_SERVER}",
        "min-split-size=10M",
        "split=8",
        "enable-rpc=false",
        "summary-interval=1",  # frequent updates
        "console-log-level=notice",
        "file-allocation=prealloc",
        f"listen-port={LISTEN_PORT}",
        f"enable-dht={'true' if ENABLE_DHT else 'false'}",
        f"enable-peer-exchange={'true' if ENABLE_PEX else 'false'}",
        "bt-enable-lpd=true",
        "bt-tracker-connect-timeout=10",
        "bt-tracker-timeout=15",
        "bt-timeout=60",
        "bt-request-peer-speed-limit=512K",
        "bt-max-peers=55",
    ]
    if EXTRA_TRACKERS:
        lines.append("bt-tracker=" + ",".join(EXTRA_TRACKERS))
    DEFAULT_CONF_FILE.write_text("\n".join(lines), encoding="utf-8")
    print_info(f"Created default config at {DEFAULT_CONF_FILE}")

def build_aria2_args(input_link):
    base_args = [
        "--enable-dht=true" if ENABLE_DHT else "--enable-dht=false",
        "--enable-peer-exchange=true" if ENABLE_PEX else "--enable-peer-exchange=false",
        f"--max-overall-download-limit={MAX_OVERALL_DOWNLOAD_LIMIT}",
        f"--max-overall-upload-limit={MAX_OVERALL_UPLOAD_LIMIT}",
        f"--max-connection-per-server={MAX_CONNECTIONS_PER_SERVER}",
        "--continue=true",
        "--auto-file-renaming=true",
        "--summary-interval=1",
        f"--dir={DEFAULT_DOWNLOAD_DIR.as_posix()}",
        f"--listen-port={LISTEN_PORT}",
    ]
    if EXTRA_TRACKERS:
        base_args.append("--bt-tracker=" + ",".join(EXTRA_TRACKERS))

    if input_link.startswith("magnet:"):
        return base_args + [input_link]
    elif input_link.startswith("http://") or input_link.startswith("https://"):
        return base_args + [input_link]
    elif Path(input_link).is_file():
        return base_args + ["-T", str(Path(input_link))]
    else:
        return None

def run_with_progress(args):
    cmd = [ARIA2_PATH] + args
    print_info(f"Starting aria2c: {' '.join(cmd)}")

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    pbar = tqdm(total=100, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]")

    for line in process.stdout:
        line = line.strip()
        if "%" in line:
            try:
                percent_str = line.split("%")[0].split()[-1]
                percent = int(percent_str)
                pbar.n = percent
                pbar.refresh()
            except Exception:
                pass
        # still print aria2 output for details
        print(line)

    process.wait()
    pbar.close()

    if process.returncode != 0:
        raise RuntimeError(f"aria2c exited with status {process.returncode}")
    else:
        print_info("Download completed successfully.")

def download_with_retries(input_link):
    args = build_aria2_args(input_link)
    if args is None:
        raise ValueError("Invalid input. Must be magnet link, torrent URL, or local .torrent file path.")

    last_error = None
    for attempt in range(1, RETRY_COUNT + 1):
        print_info(f"Attempt {attempt}/{RETRY_COUNT}")
        try:
            run_with_progress(args)
            return
        except RuntimeError as e:
            last_error = str(e)
            print_warn(last_error)
            if attempt < RETRY_COUNT:
                delay = RETRY_DELAY_BASE * attempt
                print_info(f"Retrying in {delay} seconds...")
                time.sleep(delay)

    print_warn("Applying fallback options...")
    fallback_args = args + [
        "--bt-enable-lpd=true",
        "--bt-detach-seed-only=true",
        "--timeout=30",
        "--connect-timeout=20",
        "--retry-wait=10",
    ]
    run_with_progress(fallback_args)

def main():
    print("Welcome to your Torrent Manager (aria2)")
    user_input = input("Paste magnet link, torrent URL, or local .torrent file path:\n> ").strip()
    if not user_input:
        print_error("No input provided.")
        sys.exit(1)

    ensure_dirs()
    ensure_config()

    if not Path(ARIA2_PATH).exists():
        print_error(f"aria2c not found at {ARIA2_PATH}. Please check the path.")
        sys.exit(1)

    print_info(f"Using aria2c at: {ARIA2_PATH}")

    if not (user_input.startswith("magnet:") or user_input.startswith("http://") or user_input.startswith("https://")) and not Path(user_input).exists():
        print_error("The file path you entered does not exist.")
        sys.exit(1)

    try:
        download_with_retries(user_input)
    except Exception as e:
        print_error(str(e))
        sys.exit(2)

if __name__ == "__main__":
    main()

