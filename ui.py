import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading
import sys
import queue
import pathlib
import requests
import pathlib
import transcription
import unknown_handler
import pathlib
import time

class ConsoleRedirector:
    def __init__(self, textbox, q):
        self.textbox = textbox
        self.q = q

    def write(self, message):
        self.q.put(message)

    def flush(self):
        pass

 #todo - move this into the main and have it disable buttons while running

class DungeonListenerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Dungeon Scribe")
        self.geometry("700x500")
        self.resizable(False, False)

        self.grid_rowconfigure(5, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.select_button = ctk.CTkButton(self, text="Select Audio File", command=self.select_file)
        self.select_button.grid(row=1, column=0, pady=(10, 10), sticky="n")

        self.token_icon = "❌"
        self.token_button = ctk.CTkButton(self, text=f"{self.token_icon} Set Token", command=self.set_token)
        self.token_button.grid(row=2, column=0, pady=(0, 10), sticky="n")

        self.transript_type = tk.IntVar(value=1)

        transcript_frame = ctk.CTkFrame(self, fg_color="transparent")
        transcript_frame.grid(row=3, column=0, pady=(10, 0), sticky="w")

        self.transcript_format_label = ctk.CTkLabel(transcript_frame, text="Transcript Format:")
        self.transcript_format_label.pack(side="left", padx=(20, 10))

        self.transcript_format_md = ctk.CTkRadioButton(transcript_frame, text="Markdown", variable=self.transript_type, value=1)
        self.transcript_format_md.pack(side="left", padx=(0, 8))

        self.transcript_format_html = ctk.CTkRadioButton(transcript_frame, text="HTML", variable=self.transript_type, value=2)
        self.transcript_format_html.pack(side="left", padx=(0, 8))

        self.transcript_format_txt = ctk.CTkRadioButton(transcript_frame, text="Text", variable=self.transript_type, value=3)
        self.transcript_format_txt.pack(side="left")

        transcript_name_frame = ctk.CTkFrame(self, fg_color="transparent")
        transcript_name_frame.grid(row=4, column=0, pady=(10, 0), sticky="w")
        self.transcript_name_label = ctk.CTkLabel(transcript_name_frame, text="Transcript Base File Name:")
        self.transcript_name_label.pack(side="left", padx=(20, 10))
        self.transcript_name = tk.StringVar(value="Session")
        self.transcript_name_input = ctk.CTkEntry(transcript_name_frame, width=200, textvariable=self.transcript_name)
        self.transcript_name_input.pack(side="left", padx=(0, 10))

        self.console_text = ctk.CTkTextbox(self, width=650, height=350, font=("Consolas", 12), wrap="word")
        self.console_text.grid(row=5, column=0, columnspan=2, padx=10, pady=(0, 20), sticky="nsew")
        self.console_text.configure(state="disabled")

        self.print_queue = queue.Queue()
        sys.stdout = ConsoleRedirector(self.console_text, self.print_queue)
        sys.stderr = ConsoleRedirector(self.console_text, self.print_queue)

        self.after(100, self.update_console)
        self.after(200, self.check_token_status)

    def process_audio_thread(self, audio_path, print_queue, file_name, file_type):
            self.select_button.configure(state=tk.DISABLED)
            self.token_button.configure(state=tk.DISABLED)
            self.transcript_name_input.configure(state=tk.DISABLED)
            self.transcript_format_md.configure(state=tk.DISABLED)
            self.transcript_format_html.configure(state=tk.DISABLED)
            self.transcript_format_txt.configure(state=tk.DISABLED)

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
                print_queue.put("[UI] Handling unknown speakers...\n")
                finalized = unknown_handler.handle_unknown_speakers(diarized)
                print_queue.put("[UI] Saving results to file...\n")
                transcription.output_results_to_file(finalized, file_name, file_type)
                elapsed = time.time() - start_time
                print_queue.put("[UI] Transcription and diarization complete.\n")
                print_queue.put(f"[UI] Transcription finished in {elapsed:.2f} seconds.\n")
                
            except Exception as e:
                print_queue.put(f"[UI] Error: {e}\n")
                
            finally:
                self.select_button.configure(state=tk.NORMAL)
                self.token_button.configure(state=tk.NORMAL)
                self.transcript_name_input.configure(state=tk.NORMAL)
                self.transcript_format_md.configure(state=tk.NORMAL)
                self.transcript_format_html.configure(state=tk.NORMAL)
                self.transcript_format_txt.configure(state=tk.NORMAL)
        
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
            threading.Thread(target=self.process_audio_thread, args=(file_path, self.print_queue, self.transcript_name.get(), self.transript_type.get()), daemon=True).start()

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