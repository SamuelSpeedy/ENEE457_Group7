# Malware Scanner - EMBER 2024

A web-based malware detection tool using XGBoost trained on EMBER 2024.

## Quick Start

From the project root directory:

```bash
./setup_and_run.sh
```

Then open **http://localhost:8000** in your browser.

## Requirements

- Linux (Ubuntu 20.04+ recommended)
- Python 3.10+
- Internet connection (first run only, to download dependencies)

## What It Does

1. Upload any `.exe` file
2. Extracts 2,568 static features using LIEF
3. XGBoost model predicts: **BENIGN** or **MALICIOUS**
4. Shows confidence score

## Tips

- Small files (< 5MB) scan in 1-3 seconds
- Large installers (100MB+) may take 20-60 seconds
- Use Sysinternals tools or small malware samples for demos
