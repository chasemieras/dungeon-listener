import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading
import sys
import queue
import pathlib
import requests
import transcription
import pathlib
    
class ConsoleRedirector:
    def __init__(self, textbox, q):
        self.textbox = textbox
        self.q = q

    def write(self, message):
        self.q.put(message)

    def flush(self):
        pass

def process_audio_thread(audio_path, print_queue):
    import transcription
    import pathlib
    import time

    # Read token from config file
    config_dir = pathlib.Path.home() / ".dungeon-scribe"
    config_file = config_dir / "config"
    token = None
    if config_file.exists():
        with open(config_file, "r") as f:
            for line in f:
                if line.startswith("hf_token="):
                    token = line.strip().split("=", 1)[1]
                    break

    if not token:
        print_queue.put("[UI] Error: HuggingFace token not set. Please set your token first.\n")
        return

    try:
        print_queue.put("[UI] Starting transcription...\n")
        start_time = time.time()
        audio, result = transcription.process_audio(audio_path)
        print_queue.put("[UI] Starting diarization...\n")
        diarized = transcription.diarize_results(token, audio, result)
        print_queue.put("[UI] Saving results to file...\n")
        transcription.output_results_to_file(diarized)
        elapsed = time.time() - start_time
        print_queue.put("[UI] Transcription and diarization complete.\n")
        print_queue.put(f"[UI] Transcription finished in {elapsed:.2f} seconds.\n")

    except Exception as e:
        print_queue.put(f"[UI] Error: {e}\n")

class DungeonListenerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Dungeon Scribe")
        self.geometry("700x500")
        self.resizable(False, False)

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.select_button = ctk.CTkButton(self, text="Select Audio File", command=self.select_file)
        self.select_button.grid(row=1, column=0, pady=(10, 10), sticky="n")

        self.token_icon = "❌"
        self.token_button = ctk.CTkButton(self, text=f"{self.token_icon} Set Token", command=self.set_token)
        self.token_button.grid(row=2, column=0, pady=(0, 10), sticky="n")

        self.console_text = ctk.CTkTextbox(self, width=650, height=350, font=("Consolas", 12), wrap="word")
        self.console_text.grid(row=3, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="nsew")
        self.console_text.configure(state="disabled")

        self.print_queue = queue.Queue()
        sys.stdout = ConsoleRedirector(self.console_text, self.print_queue)
        sys.stderr = ConsoleRedirector(self.console_text, self.print_queue)

        self.after(100, self.update_console)
        self.after(200, self.check_token_status)

    def select_file(self):
        documents_folder = str(pathlib.Path.home() / "Documents")
        file_path = filedialog.askopenfilename(
            initialdir=documents_folder,
            title="Select Audio File",
            filetypes=[("Audio Files", "*.wav *.mp3 *.m4a *.flac *.ogg"), ("All Files", "*.*")]
        )
        if file_path:
            self.console_text.configure(state="normal")
            self.console_text.insert(tk.END, f"[UI] Selected file: {file_path}\n")
            self.console_text.configure(state="disabled")
            threading.Thread(target=process_audio_thread, args=(file_path, self.print_queue), daemon=True).start()

    def update_console(self):
        while not self.print_queue.empty():
            message = self.print_queue.get()
            self.console_text.configure(state="normal")
            self.console_text.insert(tk.END, message)
            self.console_text.see(tk.END)
            self.console_text.configure(state="disabled")
        self.after(100, self.update_console)
        
    def set_token(self):
        token = tk.simpledialog.askstring("HuggingFace Token", "Enter your HuggingFace token:", show="*")
        if token:
            config_dir = pathlib.Path.home() / ".dungeon-scribe"
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / "config"
            with open(config_file, "w") as f:
                f.write(f"hf_token={token}\n")
            self.console_text.configure(state="normal")
            self.console_text.insert(tk.END, "[UI] HuggingFace token saved to config.\n")
            self.console_text.configure(state="disabled")
            self.check_token_status()
        else:
            self.token_status.configure(text="❌")

    def check_token_status(self):
        config_dir = pathlib.Path.home() / ".dungeon-scribe"
        config_file = config_dir / "config"
        token = None
        if config_file.exists():
            with open(config_file, "r") as f:
                for line in f:
                    if line.startswith("hf_token="):
                        token = line.strip().split("=", 1)[1]
                        break
        if token and self.validate_hf_token(token):
            self.token_icon = "✅"
            self.token_button.configure(text=f"{self.token_icon} Set Token")
            self.console_text.configure(state="normal")
            self.console_text.insert(tk.END, "[UI] HuggingFace token is valid.\n")
            self.console_text.configure(state="disabled")
        else:
            self.token_icon = "❌"
            self.token_button.configure(text=f"{self.token_icon} Set Token")
            if token:
                self.console_text.configure(state="normal")
                self.console_text.insert(tk.END, "[UI] HuggingFace token is invalid.\n")
                self.console_text.configure(state="disabled")

    def validate_hf_token(self, token):
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get("https://huggingface.co/api/whoami-v2", headers=headers, timeout=5)
            return response.status_code == 200
        except Exception:
            return False


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = DungeonListenerApp()
    app.mainloop()