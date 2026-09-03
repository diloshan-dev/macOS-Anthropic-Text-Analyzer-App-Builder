import os
import math
import threading
import itertools
import customtkinter as ctk
from tkinter import filedialog, messagebox, Canvas
import anthropic

# ------------------------------------------------------------------
# GUI Appearance Setup
# ------------------------------------------------------------------
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

MODEL_NAME = "claude-sonnet-5"
MAX_CHARS = 50_000

# Palette — deep space + violet/cyan accent, used for the gradient
# background and glass-card overlay.
BG_TOP = (18, 18, 30)          # near-black navy
BG_BOTTOM = (35, 20, 55)       # deep violet
ACCENT = "#7C4DFF"             # violet accent
ACCENT_HOVER = "#9C6BFF"
ACCENT_SOFT = "#00E5C7"        # cyan accent for secondary elements
CARD_COLOR = "#1E1B2E"         # glass-card base (opaque, simulated "frosted" look)
CARD_BORDER = "#3A3355"
TEXT_MAIN = "#F4F2FF"
TEXT_MUTED = "#9C97B8"


def lerp_color(c1, c2, t):
    
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % rgb


def draw_vertical_gradient(canvas, width, height, top_rgb, bottom_rgb, steps=120):
   
    canvas.delete("gradient")
    step_h = max(1, height // steps)
    for i in range(steps + 1):
        t = i / steps
        color = rgb_to_hex(lerp_color(top_rgb, bottom_rgb, t))
        y0 = i * step_h
        y1 = y0 + step_h + 1
        canvas.create_rectangle(0, y0, width, y1, fill=color, outline=color, tags="gradient")
    canvas.tag_lower("gradient")


def draw_round_rect(canvas, x1, y1, x2, y2, r=24, **kwargs):
   
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# ------------------------------------------------------------------
# Splash / loading screen
# ------------------------------------------------------------------
class SplashScreen(ctk.CTkToplevel):
    def __init__(self, master, on_done):
        super().__init__(master)
        self.on_done = on_done
        self.overrideredirect(True)
        w, h = 460, 300
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x, y = (sw - w) // 2, (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.attributes("-alpha", 0.0)

        self.canvas = Canvas(self, width=w, height=h, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        draw_vertical_gradient(self.canvas, w, h, BG_TOP, BG_BOTTOM)

        self.canvas.create_text(
            w // 2, h // 2 - 40, text="✦ Anthropic Text Analyzer",
            fill=TEXT_MAIN, font=("Helvetica", 17, "bold")
        )
        self.canvas.create_text(
            w // 2, h // 2 - 12, text="Powered by Diloshan",
            fill=TEXT_MUTED, font=("Helvetica", 11)
        )

        self.spinner_center = (w // 2, h // 2 + 55)
        self.spinner_radius = 22
        self.spinner_angle = 0
        self.spinner_id = None

        self.dots_text_id = self.canvas.create_text(
            w // 2, h // 2 + 100, text="Loading", fill=TEXT_MUTED, font=("Helvetica", 11)
        )
        self._dots_cycle = itertools.cycle(["Loading.", "Loading..", "Loading...", "Loading"])

        self._fade_in()
        self._animate_spinner()
        self._animate_dots()
        self.after(1600, self._fade_out)

    def _fade_in(self, alpha=0.0):
        alpha = min(1.0, alpha + 0.08)
        self.attributes("-alpha", alpha)
        if alpha < 1.0:
            self.after(15, lambda: self._fade_in(alpha))

    def _fade_out(self, alpha=1.0):
        alpha = max(0.0, alpha - 0.08)
        self.attributes("-alpha", alpha)
        if alpha > 0.0:
            self.after(15, lambda: self._fade_out(alpha))
        else:
            self.destroy()
            self.on_done()

    def _animate_spinner(self):
        if self.spinner_id:
            self.canvas.delete(self.spinner_id)
        cx, cy = self.spinner_center
        r = self.spinner_radius
        start = self.spinner_angle
        self.spinner_id = self.canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=start, extent=110, style="arc",
            outline=ACCENT, width=4
        )
        self.spinner_angle = (self.spinner_angle + 14) % 360
        self.after(30, self._animate_spinner)

    def _animate_dots(self):
        self.canvas.itemconfig(self.dots_text_id, text=next(self._dots_cycle))
        self.after(350, self._animate_dots)


# ------------------------------------------------------------------
# Main application
# ------------------------------------------------------------------
class AnthropicMacApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Anthropic Text Analyzer")
        self.minsize(640, 620)
        self._center_window(640, 620)
        self.attributes("-alpha", 0.0)  # fade in once splash finishes
        self.selected_file = None
        self._dots_job = None
        self._dots_cycle = itertools.cycle(["Analyzing.", "Analyzing..", "Analyzing...", "Analyzing"])

        self._build_background()
        self._build_card()
        self.bind("<Configure>", self._on_resize)

    # ---------------- window placement ----------------
    def _center_window(self, w, h):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ---------------- background ----------------
    def _build_background(self):
        self.bg_canvas = Canvas(self, highlightthickness=0, bd=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.update_idletasks()
        draw_vertical_gradient(self.bg_canvas, self.winfo_width() or 640,
                                self.winfo_height() or 620, BG_TOP, BG_BOTTOM)

    def _on_resize(self, event):
        if event.widget is self:
            draw_vertical_gradient(self.bg_canvas, event.width, event.height, BG_TOP, BG_BOTTOM)

    # ---------------- glass card ----------------
    def _build_card(self):
        self.card = ctk.CTkFrame(
            self, corner_radius=22, fg_color=CARD_COLOR,
            border_width=1, border_color=CARD_BORDER
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.88, relheight=0.90)

        title = ctk.CTkLabel(
            self.card, text="✦  Anthropic Text Analyzer",
            font=("Helvetica", 22, "bold"), text_color=TEXT_MAIN
        )
        title.pack(pady=(28, 2))

        subtitle = ctk.CTkLabel(
            self.card, text="Drop a text file in and get a clean, instant analysis.",
            font=("Helvetica", 12), text_color=TEXT_MUTED
        )
        subtitle.pack(pady=(0, 20))

        # API Key
        api_label = ctk.CTkLabel(
            self.card, text="Anthropic API Key", font=("Helvetica", 13, "bold"),
            text_color=TEXT_MAIN, anchor="w"
        )
        api_label.pack(fill="x", padx=40)
        self.api_entry = ctk.CTkEntry(
            self.card, width=460, height=42, show="•",
            placeholder_text="sk-ant-...", corner_radius=12,
            fg_color="#151327", border_color=CARD_BORDER, border_width=1,
        )
        self.api_entry.pack(pady=(8, 20), padx=40, fill="x")

        # File select
        file_row = ctk.CTkFrame(self.card, fg_color="transparent")
        file_row.pack(pady=(0, 8), padx=40, fill="x")

        self.select_btn = self._make_animated_button(
            file_row, "📄  Select Text File", self.load_file,
            fg=ACCENT_SOFT, hover="#33F2D8", text_color="#0A2622"
        )
        self.select_btn.pack(side="left")

        self.file_path_label = ctk.CTkLabel(
            file_row, text="No file selected", font=("Helvetica", 11),
            text_color=TEXT_MUTED
        )
        self.file_path_label.pack(side="left", padx=15)

        # Analyze button
        self.analyze_btn = self._make_animated_button(
            self.card, "✨  Analyze Text", self.start_analysis,
            fg=ACCENT, hover=ACCENT_HOVER, text_color="white", width=460, height=46
        )
        self.analyze_btn.pack(pady=(14, 10), padx=40, fill="x")

        # Progress bar (hidden until running)
        self.progress_bar = ctk.CTkProgressBar(
            self.card, width=460, mode="indeterminate",
            fg_color="#151327", progress_color=ACCENT_SOFT, height=6, corner_radius=6
        )

        self.status_label = ctk.CTkLabel(
            self.card, text="", font=("Helvetica", 11, "italic"), text_color=ACCENT_SOFT
        )

        # Output box
        output_label = ctk.CTkLabel(
            self.card, text="Result", font=("Helvetica", 13, "bold"),
            text_color=TEXT_MAIN, anchor="w"
        )
        output_label.pack(fill="x", padx=40, pady=(14, 4))

        self.output_box = ctk.CTkTextbox(
            self.card, width=460, height=200, corner_radius=14,
            fg_color="#151327", border_color=CARD_BORDER, border_width=1,
            text_color=TEXT_MAIN, font=("Helvetica", 12)
        )
        self.output_box.pack(pady=(0, 26), padx=40, fill="both", expand=True)

    def _make_animated_button(self, parent, text, command, fg, hover, text_color, width=200, height=40):
       
        btn = ctk.CTkButton(
            parent, text=text, command=command, corner_radius=12,
            fg_color=fg, hover_color=hover, text_color=text_color,
            font=("Helvetica", 13, "bold"), width=width, height=height,
            border_width=0,
        )

        def on_enter(_):
            btn.configure(border_width=2, border_color="white")

        def on_leave(_):
            btn.configure(border_width=0)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    # ---------------- fade-in on startup ----------------
    def fade_in(self, alpha=0.0):
        alpha = min(1.0, alpha + 0.07)
        self.attributes("-alpha", alpha)
        if alpha < 1.0:
            self.after(15, lambda: self.fade_in(alpha))

    # ---------------- file logic ----------------
    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            self.selected_file = file_path
            self.file_path_label.configure(text=os.path.basename(file_path), text_color=TEXT_MAIN)

    def start_analysis(self):
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

        self.analyze_btn.configure(state="disabled", text="Analyzing...")
        self.progress_bar.pack(pady=(4, 6), padx=40, fill="x")
        self.progress_bar.start()
        self.status_label.pack(pady=(0, 6))
        self._animate_status_dots()

        self.output_box.delete("1.0", "end")
        if truncated:
            self.output_box.insert(
                "end",
                f"(Note: file was long, only the first {MAX_CHARS} characters were analyzed.)\n\n"
            )

        thread = threading.Thread(target=self._run_analysis, args=(api_key, content), daemon=True)
        thread.start()

    def _animate_status_dots(self):
        if self.progress_bar.winfo_ismapped():
            self.status_label.configure(text=next(self._dots_cycle))
            self._dots_job = self.after(400, self._animate_status_dots)

    def _run_analysis(self, api_key, content):
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
        self._type_in_result(result)

    def _type_in_result(self, text, i=0, chunk=6):
       
        if i == 0:
            self.output_box.delete("1.0", "end")
        end = min(len(text), i + chunk)
        self.output_box.insert("end", text[i:end])
        if end < len(text):
            self.after(8, lambda: self._type_in_result(text, end, chunk))

    def _show_error(self, error_text):
        self._finish_request()
        self.output_box.delete("1.0", "end")
        messagebox.showerror("Error", error_text)

    def _finish_request(self):
        if self._dots_job:
            self.after_cancel(self._dots_job)
            self._dots_job = None
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_label.pack_forget()
        self.analyze_btn.configure(state="normal", text="✨  Analyze Text")


# ------------------------------------------------------------------
# Entry point — splash screen first, then fade into the main app
# ------------------------------------------------------------------
if __name__ == "__main__":
    app = AnthropicMacApp()
    app.withdraw()  # hide main window until splash finishes

    def reveal_main_app():
        app.deiconify()
        app.fade_in()

    splash = SplashScreen(app, on_done=reveal_main_app)
    app.mainloop()