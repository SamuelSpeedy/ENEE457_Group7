#!/usr/bin/env python3
"""
Download malware samples from MalwareBazaar and benign samples from legitimate sources.
For educational/research purposes only.
"""

import requests
import zipfile
import io
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
MALWARE_DIR = BASE_DIR / "malware_samples"
BENIGN_DIR = BASE_DIR / "benign_samples"

MALWARE_DIR.mkdir(exist_ok=True)
BENIGN_DIR.mkdir(exist_ok=True)

def download_malware_samples(count=10):
    """Download recent PE malware samples from MalwareBazaar."""
    print(f"Fetching {count} malware samples from MalwareBazaar...")

    # Query for recent exe samples
    response = requests.post(
        "https://mb-api.abuse.ch/api/v1/",
        data={"query": "get_file_type", "file_type": "exe", "limit": count}
    )

    if response.status_code != 200:
        print(f"API error: {response.status_code}")
        return

    data = response.json()
    if data.get("query_status") != "ok":
        print(f"Query failed: {data.get('query_status')}")
        return

    samples = data.get("data", [])
    print(f"Found {len(samples)} samples")

    downloaded = 0
    for sample in samples:
        sha256 = sample.get("sha256_hash")
        if not sha256:
            continue

        filename = f"{sha256[:16]}.exe"
        filepath = MALWARE_DIR / filename

        if filepath.exists():
            print(f"  Skipping {filename} (exists)")
            continue

        print(f"  Downloading {filename}...")
        try:
            # Download the sample (comes as password-protected zip, password: "infected")
            dl_response = requests.post(
                "https://mb-api.abuse.ch/api/v1/",
                data={"query": "get_file", "sha256_hash": sha256},
                timeout=30
            )

            if dl_response.status_code == 200 and len(dl_response.content) > 100:
                # Extract from zip with password "infected"
                try:
                    with zipfile.ZipFile(io.BytesIO(dl_response.content)) as zf:
                        zf.extractall(path=MALWARE_DIR, pwd=b"infected")
                        # Rename extracted file
                        for name in zf.namelist():
                            extracted = MALWARE_DIR / name
                            if extracted.exists():
                                extracted.rename(filepath)
                                downloaded += 1
                                print(f"    Saved {filename}")
                                break
                except zipfile.BadZipFile:
                    print(f"    Bad zip for {sha256[:16]}")
                except Exception as e:
                    print(f"    Extract error: {e}")
            else:
                print(f"    Download failed for {sha256[:16]}")
        except Exception as e:
            print(f"    Error: {e}")

    print(f"Downloaded {downloaded} malware samples")


def download_benign_samples():
    """Download legitimate Windows executables from trusted sources."""
    print("Downloading benign samples...")

    benign_urls = [
        # Sysinternals tools (Microsoft)
        ("https://live.sysinternals.com/procexp.exe", "procexp.exe"),
        ("https://live.sysinternals.com/procmon.exe", "procmon.exe"),
        ("https://live.sysinternals.com/autoruns.exe", "autoruns.exe"),
        ("https://live.sysinternals.com/tcpview.exe", "tcpview.exe"),
        ("https://live.sysinternals.com/pslist.exe", "pslist.exe"),
        ("https://live.sysinternals.com/listdlls.exe", "listdlls.exe"),
        ("https://live.sysinternals.com/handle.exe", "handle.exe"),
        ("https://live.sysinternals.com/Dbgview.exe", "dbgview.exe"),
        ("https://live.sysinternals.com/strings.exe", "strings.exe"),
        ("https://live.sysinternals.com/du.exe", "du.exe"),
    ]

    downloaded = 0
    for url, filename in benign_urls:
        filepath = BENIGN_DIR / filename

        if filepath.exists():
            print(f"  Skipping {filename} (exists)")
            continue

        print(f"  Downloading {filename}...")
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200 and len(response.content) > 1000:
                filepath.write_bytes(response.content)
                downloaded += 1
                print(f"    Saved {filename} ({len(response.content)} bytes)")
            else:
                print(f"    Failed: status {response.status_code}")
        except Exception as e:
            print(f"    Error: {e}")

    print(f"Downloaded {downloaded} benign samples")


if __name__ == "__main__":
    download_malware_samples(count=10)
    print()
    download_benign_samples()
    print("\nDone! Samples saved to:")
    print(f"  Malware: {MALWARE_DIR}")
    print(f"  Benign:  {BENIGN_DIR}")
