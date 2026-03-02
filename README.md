# Android Screen Mirroring App (Python)

A simple desktop app that mirrors an Android phone screen in real-time using Python + ADB + scrcpy.

## Features

- Detects connected Android devices via `adb`
- Start/stop mirroring from a GUI
- Live frame rendering with auto-resize

## Requirements

- Python 3.10+
- Android SDK Platform Tools (`adb`) installed and available in `PATH`
- Android device with:
  - Developer Options enabled
  - USB Debugging enabled

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

## Usage

1. Connect Android phone with USB.
2. Accept USB debugging prompt on phone.
3. Click **Refresh**.
4. Select your device serial.
5. Click **Start Mirror**.

## Notes

- First run may trigger permission prompts on device.
- For wireless debugging, pair your device with `adb` first.
