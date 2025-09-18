# Dungeon Listener

## Tech Stack

Written in Python with:

- [customtkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern UI framework
- [numpy](https://numpy.org/) - Array operations
- Whisperx
- Pyaudio
- Pyannote

## Getting Started

1. Clone or download the repository
2. Open the code in VS Code or your preferred editor
3. Open the terminal and enter the following commands:

   ```bash
   python3 -m venv DL
   source DL/bin/activate
   pip3 install --force-reinstall torch==2.2.2+cpu torchaudio==2.2.2+cpu --index-url https://download.pytorch.org/whl/cpu
   pip3 install requests pyaudio numpy customtkinter whisperx pyaudio pyannote.audio==3.1.1 lightning_fabric==2.2.4
   ```

4. Run the application:

   ```bash
   python3 app.py
   ```

## Building the App

To create a standalone executable:

1. Ensure you are in the venv for fowi:

   ```bash
   source DL/bin/activate 
   ```

2. Install pyinstaller in the venv:

   ```bash
   pip install pyinstaller
   ```

3. Build the executable:

   ```bash
   pyinstaller app.spec
   ```

The executable will be created in the `dist/` folder.
