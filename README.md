# Gemini Transcriber

I have been looking for a better transcriber solution to whisper. This PoC was an attempt at that. This is a Python application that records live audio from your microphone, periodically processes the audio, transcribes it using the Google Gemini API, and updates a live transcript file. The application also displays a system tray icon that indicates the recording state, and allows you to set transcriptions on, or off.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Using Python Virtual Environments (venv)](#using-python-virtual-environments-venv)
  - [Setup on Windows](#setup-on-windows)
  - [Setup on macOS/Linux](#setup-on-macoslinux)
- [Usage](#usage)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

- **Live Audio Recording:** Continuously records audio from your microphone.
- **Periodic Processing:** Processes audio in configurable intervals.
- **Transcription:** Uses Google’s Gemini API to transcribe the recorded audio.
- **Taskbar Icon:** Provides a system tray icon that shows recording status.
- **Cross-platform:** Works on both Windows and macOS (or any Unix-like system).

---

## Requirements

- Python 3.7 or higher
- The following Python packages:
  - `numpy`
  - `sounddevice`
  - `scipy`
  - `Pillow`
  - `python-dotenv`
  - `pystray`
  - `google-generativeai`

A sample `requirements.txt` is provided:

```txt
numpy
sounddevice
scipy
Pillow
python-dotenv
pystray
google-generativeai
```

*Note:* The built-in libraries such as `os`, `time`, `threading`, `tempfile`, `queue`, `datetime`, and `tkinter` are part of the standard Python distribution.

---

## Installation

### Using Python Virtual Environments (venv)

We highly recommend using Python’s built-in virtual environment to keep your project dependencies isolated. You can create a virtual environment named `venv` with the following command:

```bash
python -m venv venv
```

Then activate the environment:

- **Windows:** `venv\Scripts\activate`
- **macOS/Linux:** `source venv/bin/activate`

After activation, upgrade `pip` and install the required packages:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Setup on Windows

A batch script (`setup.bat`) is provided for Windows users. This script will:

1. Create a virtual environment if it doesn’t already exist.
2. Activate the virtual environment.
3. Upgrade `pip`.
4. Install all required packages from `requirements.txt`.

Create a file named `setup.bat` in the project directory with the following content:

```batch
@echo off
REM Check if the virtual environment folder exists
IF NOT EXIST venv (
    echo Creating virtual environment...
    python -m venv venv
) ELSE (
    echo Virtual environment already exists.
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Upgrading pip...
pip install --upgrade pip

echo Installing required packages...
pip install -r requirements.txt

echo Setup complete. The virtual environment is activated.
pause
```

To run the script, simply double-click `setup.bat` or run it from the command prompt.

### Setup on macOS/Linux

A bash script (`setup.sh`) is provided for macOS/Linux users. This script will:

1. Create a virtual environment if it doesn’t already exist.
2. Activate the virtual environment.
3. Upgrade `pip`.
4. Install all required packages from `requirements.txt`.

Create a file named `setup.sh` in the project directory with the following content:

```bash
#!/bin/bash
# Check if the virtual environment folder exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing required packages..."
pip install -r requirements.txt

echo "Setup complete. The virtual environment is activated."
```

Before running the script, ensure it is executable by running:

```bash
chmod +x setup.sh
```

Then, execute the script:

```bash
./setup.sh
```

---

## Usage

1. **Configure Environment Variables:**
   - Create a `.env` file in the project root.
   - Add your configuration. For example:

     ```env
     GEMINI_API_KEY=YOUR_API_KEY_HERE
     SAMPLE_RATE=16000
     PROCESSING_INTERVAL=5
     TRANSCRIPT_FILE=live_transcript.md
     ```

2. **Run the Application:**
   - After activating your virtual environment, simply run:

     ```bash
     python your_script.py
     ```

   - The application will create a system tray icon. Use the menu options to start or stop transcription.

---

## Environment Variables

The application expects certain environment variables. You can define them in a `.env` file:

- **GEMINI_API_KEY:** Your API key for the Google Gemini service.
- **SAMPLE_RATE:** (Optional) Audio sample rate (default is `16000` Hz).
- **PROCESSING_INTERVAL:** (Optional) How frequently (in seconds) to process the recorded audio (default is `5` seconds).
- **TRANSCRIPT_FILE:** (Optional) The output file for the live transcript (default is `live_transcript.md`).

---

## Troubleshooting

- **Missing API Key:**  
  If the `GEMINI_API_KEY` is not found, the application will show an error message using `tkinter`. Make sure the key is present in the environment variables or your `.env` file.

- **Dependencies Not Installed:**  
  Ensure you have run the setup script for your platform. If a module import fails, check your `requirements.txt` and ensure the virtual environment is activated.

- **Audio Device Errors:**  
  Verify that your microphone is properly connected and configured. The application uses the `sounddevice` library for audio recording.

- **Google Gemini API Errors:**  
  If transcription fails, double-check that you have installed the `google-generativeai` library and that your API key is valid.

---

## License

This project is open source under the MIT License.
