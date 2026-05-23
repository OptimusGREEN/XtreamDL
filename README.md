# Xtream Codes Series Downloader (`xtream_dl.py`)

A user-friendly, interactive command-line interface (CLI) tool to search and download series episodes from any Xtream Codes provider using `yt-dlp`.

---

## Features

- **Interactive Selection**: Search for series, pick a series, choose multiple seasons, and select specific episodes to download (or download everything at once).
- **Resumable Downloads**: Automatically resumes interrupted downloads using `yt-dlp`.
- **Clean Filenames**: Sanitizes folder and file names, creating clean structures like:
  `[Series Name]/S[Season]E[Episode] - [Episode Title].[Extension]` (e.g., `Breaking Bad/S01E01 - Pilot.mkv`).
- **User-Agent Spoofing**: Incorporates simulated browser headers for both API calls and video streams to bypass potential provider restrictions or blocks.
- **Dry-run Mode**: Preview what files would be created and which URLs would be requested before downloading anything.

---

## Requirements & Setup

A virtual environment (`.venv`) is recommended.

### 1. Setup Virtual Environment & Dependencies

If you haven't set up the virtual environment yet, run the following:

```bash
# Create the virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt  # Or manually: pip install requests yt-dlp
```

### 2. Activate the Virtual Environment

Always ensure your virtual environment is active before running the script:

```bash
source .venv/bin/activate
```

---

## Usage

Run the downloader by specifying your Xtream host URL, username, and password:

```bash
python xtream_dl.py --host http://HOST:PORT --user USER --pass PASS
```

### Command Line Options

| Argument | Short / Long Option | Required | Description |
| :--- | :--- | :---: | :--- |
| **Host** | `--host` | Yes | The base URL of your Xtream provider (e.g., `http://myprovider.xyz:8080`). |
| **Username** | `--user` | Yes | Your Xtream Codes username. |
| **Password** | `--pass` | Yes | Your Xtream Codes password. |
| **Search Query** | `--search` | No | Pre-fills the initial series search term (e.g., `--search "Breaking Yerda"`). |
| **Output Directory** | `--output` | No | Base folder to save files (defaults to current directory `.`). |
| **Dry Run** | `--dry-run` | No | Outputs what would be downloaded without requesting the actual media streams. |

### Example Commands

- **Normal Interactive Mode**:
  ```bash
  python xtream_dl.py --host http://example.com:8080 --user test_user --pass test_pass
  ```

- **Pre-filled Search and Custom Output Directory**:
  ```bash
  python xtream_dl.py --host http://example.com:8080 --user test_user --pass test_pass --search "The Flires" --output ~/Downloads/Series
  ```

- **Dry-Run Check**:
  ```bash
  python xtream_dl.py --host http://example.com:8080 --user test_user --pass test_pass --search "Shernobil" --dry-run
  ```

---

## Interactive Flow Walkthrough

1. **Authentication**: The script verifies credentials with your provider.
2. **Search**: Enter a keyword to search for series.
3. **Select Series**: Pick from a list of matching results by entering its index.
4. **Select Seasons**: Enter specific season numbers (separated by space) or type `all`.
5. **Select Episodes**: Choose specific episodes to download or choose `all`.
6. **Download**: The script creates appropriate subdirectories and handles downloads with progress bars.
7. **Repeat or Quit**: You will be prompted to search again or exit cleanly.
