import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
import anthropic

# GUI Appearance Setup
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Anthropic model used for analysis
MODEL_NAME = "claude-sonnet-5"

# Rough safety limit so we don't send huge files straight to the API
MAX_CHARS = 50_000


class AnthropicMacApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Anthropic Text Analyzer")
        self.geometry("600x520")
        self.minsize(600, 520)

        # API Key Section
        self.api_label = ctk.CTkLabel(
            self, text="Enter Anthropic API Key:", font=("Helvetica", 14, "bold")
        )
        self.api_label.pack(pady=(20, 5))
        self.api_entry = ctk.CTkEntry(self, width=450, show="*")
        self.api_entry.pack(pady=5)

        # File Selection Section
        self.select_btn = ctk.CTkButton(self, text="Select Text File", command=self.load_file)
        self.select_btn.pack(pady=15)
        self.file_path_label = ctk.CTkLabel(
            self, text="No file selected", font=("Helvetica", 11), text_color="gray"
        )
        self.file_path_label.pack(pady=5)

        # Analyze Button
        self.analyze_btn = ctk.CTkButton(
            self, text="Analyze Text", fg_color="green", command=self.start_analysis
        )
        self.analyze_btn.pack(pady=10)

        # Progress indicator (shown only while a request is running)
        self.progress_bar = ctk.CTkProgressBar(self, width=300, mode="indeterminate")

        # Output Text Box
        self.output_box = ctk.CTkTextbox(self, width=520, height=200)
        self.output_box.pack(pady=15)

        self.selected_file = None

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            self.selected_file = file_path
            self.file_path_label.configure(text=os.path.basename(file_path), text_color="white")

    def start_analysis(self):
        """Validate inputs on the main thread, then hand the API call off to a
        background thread so the UI never freezes while waiting for a response."""
        api_key = self.api_entry.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter your API Key!")
            return
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a text file first!")
            return

        try:
            with open(self.selected_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file:\n{e}")
            return

        if not content.strip():
            messagebox.showerror("Error", "The selected file is empty.")
            return

        truncated = False
        if len(content) > MAX_CHARS:
            content = content[:MAX_CHARS]
            truncated = True

        # Lock the UI for this request and show a busy indicator
        self.analyze_btn.configure(state="disabled", text="Analyzing...")
        self.progress_bar.pack(pady=(0, 10))
        self.progress_bar.start()
        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", "Analyzing content, please wait...\n")
        if truncated:
            self.output_box.insert("end", "(Note: file was long, only the first "
                                    f"{MAX_CHARS} characters were analyzed.)\n")

        thread = threading.Thread(target=self._run_analysis, args=(api_key, content), daemon=True)
        thread.start()

    def _run_analysis(self, api_key, content):
        """Runs on a background thread — never touch widgets directly here."""
        try:
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model=MODEL_NAME,
                max_tokens=1000,
                messages=[{"role": "user", "content": f"Analyze this text briefly:\n\n{content}"}],
            )
            result = message.content[0].text
            self.after(0, self._show_result, result)
        except anthropic.AuthenticationError:
            self.after(0, self._show_error, "Invalid API Key. Please check and try again.")
        except anthropic.APIConnectionError:
            self.after(0, self._show_error, "Could not connect to the Anthropic API. Check your internet connection.")
        except Exception as e:
            self.after(0, self._show_error, str(e))

    def _show_result(self, result):
        self._finish_request()
        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", result)

    def _show_error(self, error_text):
        self._finish_request()
        self.output_box.delete("1.0", "end")
        messagebox.showerror("Error", error_text)

    def _finish_request(self):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.analyze_btn.configure(state="normal", text="Analyze Text")


if __name__ == "__main__":
    app = AnthropicMacApp()
    app.mainloop()