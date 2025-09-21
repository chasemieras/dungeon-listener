# Dungeon Scribe

## Tech Stack

Written in Python with:

- [customtkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern UI framework
- [numpy](https://numpy.org/) - Array operations
- [whisperx](https://github.com/m-bain/whisperx) - Transcription and alignment
- [torch](https://pytorch.org/) - Deep learning backend
- [requests](https://docs.python-requests.org/) - HTTP requests (for token validation)
- [pyaudio](https://people.csail.mit.edu/hubert/pyaudio/) - Audio input/output
- [tkinter](https://docs.python.org/3/library/tkinter.html) - Standard Python GUI library
- [datetime](https://docs.python.org/3/library/datetime.html) - Date and time utilities
- [pathlib](https://docs.python.org/3/library/pathlib.html) - Filesystem paths
- [os](https://docs.python.org/3/library/os.html) - OS utilities
- [subprocess](https://docs.python.org/3/library/subprocess.html) - Run system commands
- [threading](https://docs.python.org/3/library/threading.html) - Thread-based parallelism
- [queue](https://docs.python.org/3/library/queue.html) - Thread-safe queues
- [time](https://docs.python.org/3/library/time.html) - Time utilities
- [sys](https://docs.python.org/3/library/sys.html) - System-specific parameters and functions
- [gc](https://docs.python.org/3/library/gc.html) - Garbage collection
- [tkinter.simpledialog](https://docs.python.org/3/library/dialog.html) - Simple dialogs for user input


## Getting Started

1. Clone or download the repository
2. Open the code in VS Code or your preferred editor
3. Open the terminal and enter the following commands:

   ```bash
   python3 -m venv DL
   source DL/bin/activate
   pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu118
   pip install numpy==2.0.2
   pip install requests pyaudio customtkinter pyaudio  
   pip install git+https://github.com/openai/whisper.git
   pip install git+https://github.com/m-bain/whisperx.git

   ```

4. Run the application:

   ```bash
   python3 app.py
   ```

5. Go to [Hugging Face](https://huggingface.co/) and create an API key. This is needed for dictation.
6. Click Set Token and input the token.
7. Select an audio file.
8. Profit

## TODOs

- [ ] Add ability to turn off dictation
- [ ] Add ability to record from tool

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

3. Run the following:

   ```bash
   pyi-makespec app.py
   ```

4. Build the executable:

   ```bash
   pyinstaller app.spec
   ```

The executable will be created in the `dist/` folder.
