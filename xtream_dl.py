#!/usr/bin/env python3
"""
xtream_dl.py — Search and download series episodes from an Xtream Codes provider.

Usage:
    source .venv/bin/activate
    python xtream_dl.py --host http://HOST:PORT --user USER --pass PASS
    python xtream_dl.py --host http://HOST:PORT --user USER --pass PASS --search "Breaking Bad"

Requirements:
    pip install requests yt-dlp
"""

import argparse
import json
import os
import sys
import requests

try:
    import yt_dlp
except ImportError:
    print("ERROR: yt-dlp is not installed. Run: pip install yt-dlp")
    sys.exit(1)


# ─── API helpers ──────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

def api_get(host, user, password, action, **params):
    url = f"{host}/player_api.php"
    p = {"username": user, "password": password, "action": action, **params}
    try:
        r = requests.get(url, params=p, timeout=30, headers=HEADERS)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"  [!] Request failed: {e}")
        return None
    except json.JSONDecodeError:
        print("  [!] Could not parse server response as JSON.")
        return None


def check_auth(host, user, password):
    data = api_get(host, user, password, "")
    if data and data.get("user_info", {}).get("auth") == 1:
        info = data["user_info"]
        print(f"  Logged in as: {info.get('username')}")
        print(f"  Status:       {info.get('status')}")
        print(f"  Expires:      {info.get('exp_date', 'N/A')}")
        return True
    print("  [!] Authentication failed. Check your host/user/pass.")
    return False


def get_all_series(host, user, password):
    print("  Fetching series list (this may take a moment)...")
    data = api_get(host, user, password, "get_series")
    return data if isinstance(data, list) else []


def search_series(series_list, query):
    q = query.lower()
    return [s for s in series_list if q in s.get("name", "").lower()]


def get_series_info(host, user, password, series_id):
    return api_get(host, user, password, "get_series_info", series_id=series_id)


# ─── Display helpers ──────────────────────────────────────────────────────────

def pick(prompt, options, display_fn=None, allow_all=False):
    """Generic numbered picker. Returns list of chosen items."""
    if not options:
        print("  No items available.")
        return []

    print()
    for i, opt in enumerate(options, 1):
        label = display_fn(opt) if display_fn else str(opt)
        print(f"  {i:>3}. {label}")

    all_hint = ", 'all'" if allow_all else ""
    raw = input(f"\n{prompt} (numbers separated by space{all_hint}, or 'q' to quit): ").strip()

    if raw.lower() == "q":
        return None  # signal quit
    if allow_all and raw.lower() == "all":
        return options

    chosen = []
    for token in raw.split():
        try:
            idx = int(token) - 1
            if 0 <= idx < len(options):
                chosen.append(options[idx])
            else:
                print(f"  [!] {token} out of range, skipping.")
        except ValueError:
            print(f"  [!] '{token}' is not a number, skipping.")
    return chosen


# ─── Download ─────────────────────────────────────────────────────────────────

def sanitise(name):
    """Remove characters that are problematic in file/folder names."""
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, "_")
    return name.strip()


def download_episode(host, user, password, series_name, season_num, ep, output_dir, dry_run=False):
    ep_id  = ep.get("id")
    ep_num = ep.get("episode_num", "?")
    title  = ep.get("title") or f"Episode {ep_num}"
    ext    = ep.get("container_extension", "mkv")

    season_str = f"S{int(season_num):02d}"
    ep_str     = f"E{int(ep_num):02d}" if str(ep_num).isdigit() else f"E{ep_num}"
    filename   = sanitise(f"{series_name} {season_str}{ep_str} - {title}.{ext}")
    filepath   = os.path.join(output_dir, filename)

    url = f"{host}/series/{user}/{password}/{ep_id}.{ext}"

    if os.path.exists(filepath):
        print(f"  [skip] Already exists: {filename}")
        return

    if dry_run:
        print(f"  [dry-run] Would download: {filename}")
        print(f"            URL: {url}")
        return

    print(f"  Downloading: {filename}")
    ydl_opts = {
        "outtmpl":        filepath,
        "quiet":          False,
        "no_warnings":    False,
        "continuedl":     True,       # resume partial downloads
        "noprogress":     False,
        "http_headers":   HEADERS,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"  [!] yt-dlp error: {e}")


# ─── Main flow ────────────────────────────────────────────────────────────────

def interactive(host, user, password, initial_search=None, output_dir=".", dry_run=False):

    # 1. Auth check
    print("\n── Checking credentials ──")
    if not check_auth(host, user, password):
        return

    # 2. Load series list
    print("\n── Loading series ──")
    all_series = get_all_series(host, user, password)
    if not all_series:
        print("  No series found on this provider.")
        return
    print(f"  Found {len(all_series)} series total.")

    while True:
        # 3. Search
        query = initial_search or input("\nSearch series (or 'q' to quit): ").strip()
        initial_search = None  # only use CLI arg on first iteration

        if query.lower() == "q":
            break

        results = search_series(all_series, query)
        if not results:
            print(f"  No series found matching '{query}'.")
            continue

        print(f"\n  Found {len(results)} match(es).")

        # 4. Pick a series
        chosen_series = pick("Select series", results,
                             display_fn=lambda s: s.get("name", "Unknown"))
        if chosen_series is None:
            break
        if not chosen_series:
            continue
        series = chosen_series[0]  # single select

        series_name = series.get("name", "Unknown")
        series_id   = series.get("series_id")

        # 5. Fetch series info (seasons + episodes)
        print(f"\n── Fetching info for: {series_name} ──")
        info = get_series_info(host, user, password, series_id)
        if not info:
            print("  Could not retrieve series info.")
            continue

        episodes_by_season = info.get("episodes", {})
        if not episodes_by_season:
            print("  No episodes found for this series.")
            continue

        seasons = sorted(episodes_by_season.keys(), key=lambda x: int(x) if x.isdigit() else 0)
        print(f"  Seasons available: {', '.join(seasons)}")

        # 6. Pick seasons
        chosen_seasons = pick("Select season(s)", seasons,
                              display_fn=lambda s: f"Season {s} ({len(episodes_by_season[s])} episodes)",
                              allow_all=True)
        if chosen_seasons is None:
            break
        if not chosen_seasons:
            continue

        # 7. For each season, pick episodes
        for season in chosen_seasons:
            eps = episodes_by_season[season]
            print(f"\n  Season {season} — {len(eps)} episode(s):")

            chosen_eps = pick(f"Select episodes for Season {season}",
                              eps,
                              display_fn=lambda e: (
                                  f"E{int(e.get('episode_num','?')):02d} — "
                                  f"{e.get('title') or 'Untitled'}"
                              ),
                              allow_all=True)
            if chosen_eps is None:
                break
            if not chosen_eps:
                continue

            # 8. Download
            series_dir = os.path.join(output_dir, sanitise(series_name))
            os.makedirs(series_dir, exist_ok=True)
            print(f"\n  Saving to: {series_dir}")

            for ep in chosen_eps:
                download_episode(host, user, password,
                                 series_name, season, ep,
                                 series_dir, dry_run=dry_run)

        print("\n  Done with this series.")
        another = input("Search for another series? (y/n): ").strip().lower()
        if another != "y":
            break

    print("\nGoodbye!")


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Search and download series from an Xtream Codes provider."
    )
    parser.add_argument("--host",   required=True, help="Provider URL, e.g. http://host:port")
    parser.add_argument("--user",   required=True, help="Xtream username")
    parser.add_argument("--pass",   dest="password", required=True, help="Xtream password")
    parser.add_argument("--search", default=None,  help="Pre-fill initial series search query")
    parser.add_argument("--output", default=".",   help="Output directory (default: current dir)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be downloaded without actually downloading")
    args = parser.parse_args()

    # Normalise host: strip trailing slash
    host = args.host.rstrip("/")

    interactive(host, args.user, args.password,
                initial_search=args.search,
                output_dir=args.output,
                dry_run=args.dry_run)


if __name__ == "__main__":
    main()
