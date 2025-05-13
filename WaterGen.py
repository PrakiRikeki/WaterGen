import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import pandas as pd
import csv
import threading
import math
# import random # Entfernt, da nicht verwendet
import ctypes
# import matplotlib # Entfernt, da nicht verwendet
# from matplotlib.figure import Figure # Entfernt, da nicht verwendet
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # Entfernt, da nicht verwendet
import numpy as np
import os
from PIL import Image, ImageTk
import sys

# Farbpalette für Darkmode
DISCORD_BG = "#36393F"
DISCORD_DARK = "#2F3136"
DISCORD_DARKER = "#202225"
DISCORD_TEXT = "#DCDDDE"
DISCORD_GRAY_TEXT = "#96989D"
DISCORD_GREEN = "#4ee56e"
DISCORD_INPUT_BG = "#40444B"
BUTTON_COLOR = "#4ee56e"
BUTTON_HOVER = "#3ac558"

# Globale Variable für das Logo im Ladescreen, um Garbage Collection zu verhindern
logo_img_global = None

# Darkmode Titelleiste für Windows
def set_dark_title_bar(window):
    try:
        window.update()
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
        get_parent = ctypes.windll.user32.GetParent
        hwnd = get_parent(window.winfo_id())
        value = ctypes.c_int(2) # 2 für Darkmode, 0 für Lightmode
        set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value))
    except Exception as e:
        print(f"Fehler beim Setzen der dunklen Titelleiste: {e}")

# Abgerundete Rechtecke
def create_rounded_rect(canvas, x1, y1, x2, y2, radius=15, **kwargs):
    points = [x1+radius, y1, x2-radius, y1, x2, y1, x2, y1+radius,
              x2, y2-radius, x2, y2, x2-radius, y2, x1+radius, y2,
              x1, y2, x1, y2-radius, x1, y1+radius, x1, y1]
    return canvas.create_polygon(points, **kwargs, smooth=True)

# Datumseingabe mit Autovervollständigung und Darkmode-Anpassung
class AutoDateEntry(DateEntry):
    def __init__(self, master=None, **kwargs):
        kwargs['locale'] = 'de_DE'
        kwargs['date_pattern'] = 'dd.mm.yy'
        # Darkmode Stile für DateEntry
        style_options = {
            'background': DISCORD_INPUT_BG,
            'foreground': DISCORD_TEXT,
            'borderwidth': 0,
            'relief': 'flat',
            'font': ('Arial', 11),
            'arrowcolor': DISCORD_TEXT,
            'selectbackground': DISCORD_GREEN,
            'selectforeground': DISCORD_DARKER,
            'normalbackground': DISCORD_INPUT_BG,
            'normalforeground': DISCORD_TEXT,
            'othermonthforeground': DISCORD_GRAY_TEXT,
            'othermonthbackground': DISCORD_INPUT_BG,
            'weekendbackground': DISCORD_INPUT_BG,
            'weekendforeground': DISCORD_TEXT,
        }
        kwargs.update(style_options)
        super().__init__(master, **kwargs)
        self.bind("<KeyRelease>", self._format_date_entry)
        self.bind("<FocusOut>", self._close_calendar_on_focus_out)
        self.last_value = ""

        # Darkmode für den Kalender-Popup
        if hasattr(self, '_top_cal'): # Sicherstellen, dass _top_cal existiert
            self._top_cal.configure(background=DISCORD_DARKER)
            for child in self._top_cal.winfo_children():
                if isinstance(child, ttk.Label) or isinstance(child, tk.Label):
                    child.configure(background=DISCORD_DARKER, foreground=DISCORD_TEXT)
                elif isinstance(child, ttk.Button) or isinstance(child, tk.Button):
                     child.configure(background=DISCORD_DARK, foreground=DISCORD_TEXT,
                                       activebackground=DISCORD_GREEN, activeforeground=DISCORD_TEXT,
                                       style="Dark.TButton")
                elif isinstance(child, ttk.Combobox):
                     self.master.style.configure("Dark.TCombobox", fieldbackground=DISCORD_INPUT_BG, background=DISCORD_DARK, foreground=DISCORD_TEXT)
                     child.configure(style="Dark.TCombobox")


    def _close_calendar_on_focus_out(self, event):
        if hasattr(self, '_top_cal') and self._top_cal.winfo_exists():
            self._top_cal.withdraw()

    def _format_date_entry(self, event):
        if event.keysym in ('BackSpace', 'Delete', 'Left', 'Right', 'Up', 'Down', 'Tab', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R'):
            self.last_value = self.get()
            return
        current_text = self.get()
        cursor_pos = self.index(tk.INSERT)

        # Automatische Punkte hinzufügen
        if len(current_text) == 2 and cursor_pos == 2 and current_text.isdigit():
            day = int(current_text)
            if 1 <= day <= 31:
                if day < 10 and not current_text.startswith('0') and len(current_text) == 1:
                     self.delete(0, tk.END)
                     self.insert(0, "0" + current_text)
                self.insert(tk.END, ".")
        elif len(current_text) == 5 and cursor_pos == 5 and current_text[2] == '.' and current_text[3:5].isdigit():
            month_str = current_text[3:5]
            month = int(month_str)
            if 1 <= month <= 12:
                if month < 10 and not month_str.startswith('0') and len(month_str) == 1:
                    self.delete(3, tk.END) # Alten Monatsteil löschen
                    self.insert(3, "0" + month_str + ".") # Neuen Monatsteil mit Punkt einfügen
                else:
                    self.insert(tk.END, ".")


        # Jahr auf YY beschränken, wenn JJJJ eingegeben wird
        if len(current_text) > 8 and current_text[2] == '.' and current_text[5] == '.':
            year_str = current_text[6:]
            if len(year_str) == 4 and year_str.isdigit():
                self.delete(6, tk.END)
                self.insert(6, year_str[2:])

        self.last_value = self.get()


# Formelparameter-Klasse
class FormelParameter:
    def __init__(self):
        self.gw0 = 12.0
        self.a = 1.0
        self.t_periode = 365
        self.freq = 1.0
        self.da = 20
        self.dd = 50
        self.r_scale = 0.12
        # self.autokorrelation = 0.7 # Entfernt, da nicht verwendet
        # self.grundwasser_faktor = 0.15 # Entfernt, da nicht verwendet

    def set_parameters(self, gw0, a, t_periode, freq, da, dd, r_scale):
        self.gw0 = gw0
        self.a = a
        self.t_periode = t_periode
        self.freq = freq
        self.da = da
        self.dd = dd
        self.r_scale = r_scale

    def generiere_formel_string(self):
        return (f"{self.gw0:.2f} + {self.a:.2f}*sin(2*pi*{self.freq:.2f}*t/{self.t_periode:.0f})"
                f"\n+ Anstieg({self.da:.0f}d) / Abkling({self.dd:.0f}d) + Rnd({self.r_scale:.2f})")

    # def calculate_gw_value_at_t(self, t_days, prev_gw_value, r_base_value): # Entfernt, Logik in create_output_files
    #     pass

    def generiere_ereignisse(self, tage):
        # Dummy-Implementierung. Liefert derzeit nur Nullen.
        # Kann erweitert werden, um realistische Ereignisdaten zu generieren.
        regen = np.zeros(tage)
        starkregen = np.zeros(tage)
        schnee = np.zeros(tage)
        # grundwasser_effekt wird hier nicht mehr explizit zurückgegeben, da es in create_output_files
        # nicht separat verwendet wurde bzw. in der Haupt-GW-Berechnung aufgeht.
        return regen, starkregen, schnee


# Ladescreen
def show_loading_screen():
    global logo_img_global
    loading_window = tk.Tk()
    loading_window.overrideredirect(True)
    window_width = 400
    window_height = 300
    screen_width = loading_window.winfo_screenwidth()
    screen_height = loading_window.winfo_screenheight()
    x_pos = int((screen_width/2) - (window_width/2))
    y_pos = int((screen_height/2) - (window_height/2))
    loading_window.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")
    loading_window.configure(bg=DISCORD_DARKER)
    loading_window.attributes("-topmost", True)

    try:
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(base_path, "ribeka 55mm breit_white.png")
        original_logo = Image.open(logo_path)
        logo_width = 200
        aspect_ratio = original_logo.height / original_logo.width
        logo_height = int(logo_width * aspect_ratio)
        resized_logo = original_logo.resize((logo_width, logo_height), Image.LANCZOS)
        logo_img_global = ImageTk.PhotoImage(resized_logo)
        logo_label = tk.Label(loading_window, image=logo_img_global, bg=DISCORD_DARKER)
        # logo_label.image = logo_img_global # Redundant
        logo_label.pack(pady=(60, 20))
    except Exception as e:
        print(f"Fehler beim Laden des Logos: {e}")
        tk.Label(loading_window, text="WaterGen", font=("Arial", 24, "bold"),
                fg=DISCORD_TEXT, bg=DISCORD_DARKER).pack(pady=(60, 20))

    loading_label = tk.Label(loading_window, text="Anwendung wird geladen...",
                           fg=DISCORD_TEXT, bg=DISCORD_DARKER, font=("Arial", 12))
    loading_label.pack(pady=10)

    progress = ttk.Progressbar(loading_window, orient="horizontal", length=300, mode="indeterminate")
    s = ttk.Style()
    s.theme_use('clam')
    s.configure("Loading.Horizontal.TProgressbar", troughcolor=DISCORD_BG, background=DISCORD_GREEN, bordercolor=DISCORD_DARKER, lightcolor=DISCORD_GREEN, darkcolor=DISCORD_GREEN)
    progress.configure(style="Loading.Horizontal.TProgressbar")
    progress.pack(pady=20)
    progress.start(10)

    def close_loading():
        progress.stop()
        loading_window.destroy()

    loading_window.after(2500, close_loading)
    loading_window.mainloop()

# GUI erstellen
def create_gui():
    show_loading_screen()
    root = tk.Tk()
    root.title("WaterGen")
    window_width = 680
    window_height = 800
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_pos = int((screen_width/2) - (window_width/2))
    y_pos = int((screen_height/2) - (window_height/2))
    root.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")
    set_dark_title_bar(root)
    root.configure(bg=DISCORD_BG)

    root.logo_img_main = None
    try:
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        logo_path_main = os.path.join(base_path, "ribeka 55mm breit_white_2.png")
        if os.path.exists(logo_path_main):
            original_logo_main = Image.open(logo_path_main)
            logo_width_main = 100
            aspect_ratio_main = original_logo_main.height / original_logo_main.width
            logo_height_main = int(logo_width_main * aspect_ratio_main)
            resized_logo_main = original_logo_main.resize((logo_width_main, logo_height_main), Image.LANCZOS)
            root.logo_img_main = ImageTk.PhotoImage(resized_logo_main)
            logo_label_main = tk.Label(root, image=root.logo_img_main, bg=DISCORD_BG)
            logo_label_main.place(relx=1, rely=0, anchor='ne', x=-10, y=10)
    except Exception as e:
        print(f"Info: Logo konnte nicht geladen werden: {e}")

    formel_params = FormelParameter()

    root.minsize(680, 800)
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    container_frame = tk.Frame(root, bg=DISCORD_BG)
    container_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    container_frame.grid_rowconfigure(0, weight=1)
    container_frame.grid_columnconfigure(0, weight=1)

    content_frame = tk.Frame(container_frame, bg=DISCORD_BG)

    def center_content(event=None):
        width = container_frame.winfo_width()
        target_width = 580
        if width > target_width:
            padding = (width - target_width) // 2
            content_frame.grid_configure(padx=padding)
        else:
            content_frame.grid_configure(padx=0)

    content_frame.grid(row=0, column=0, sticky="n")
    container_frame.bind("<Configure>", center_content)
    center_content()

    main_frame = tk.Frame(content_frame, bg=DISCORD_BG, width=580)
    main_frame.pack(fill=tk.Y, expand=False, anchor="n")

    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure("TProgressbar",
                   troughcolor=DISCORD_DARKER,
                   background=BUTTON_COLOR,
                   bordercolor=DISCORD_DARKER,
                   lightcolor=BUTTON_COLOR,
                   darkcolor=BUTTON_COLOR)
    style.configure("TScale",
                   background=DISCORD_BG,
                   troughcolor=DISCORD_DARK,
                   sliderrelief=tk.FLAT,
                   sliderlength=20,
                   foreground=DISCORD_TEXT)
    style.map("TScale",
              background=[('active', DISCORD_GREEN)],
              slidercolor=[('!disabled', DISCORD_GREEN)])
    style.configure("Dark.TButton", background=DISCORD_DARK, foreground=DISCORD_TEXT, borderwidth=0, focusthickness=0, focuscolor=DISCORD_DARK)
    style.map("Dark.TButton",
          background=[('active', DISCORD_GREEN), ('pressed', BUTTON_HOVER)],
          foreground=[('active', DISCORD_TEXT), ('pressed', DISCORD_TEXT)])


    label_style = {"bg": DISCORD_DARK, "fg": DISCORD_TEXT}
    entry_style = {"bg": DISCORD_INPUT_BG, "fg": DISCORD_TEXT, "insertbackground": DISCORD_TEXT,
                  "font": ('Arial', 11), "bd": 0, "relief": "flat"}

    header_frame = tk.Frame(main_frame, bg=DISCORD_BG)
    header_frame.pack(fill=tk.X, pady=(0, 25))
    header_canvas = tk.Canvas(header_frame, bg=DISCORD_BG, height=90, highlightthickness=0)
    header_canvas.pack(fill=tk.X)
    create_rounded_rect(header_canvas, 0, 0, 580, 90, radius=15, fill=DISCORD_DARK, outline="")
    header_label = tk.Label(header_canvas, text="WaterGen", bg=DISCORD_DARK, fg=DISCORD_TEXT, font=('Arial', 28, 'bold'))
    header_canvas.create_window(290, 45, window=header_label)

    zeitspan_frame = tk.Frame(main_frame, bg=DISCORD_BG)
    zeitspan_frame.pack(fill=tk.X, pady=(0, 20))
    zeitspan_canvas = tk.Canvas(zeitspan_frame, bg=DISCORD_BG, height=120, highlightthickness=0)
    zeitspan_canvas.pack(fill=tk.X)
    create_rounded_rect(zeitspan_canvas, 0, 0, 580, 120, radius=15, fill=DISCORD_DARK, outline="")

    zeitspanne_label_title = tk.Label(zeitspan_canvas, text="Zeitspanne", **label_style, font=('Arial', 10, 'bold'))
    zeitspan_canvas.create_window(20, 25, window=zeitspanne_label_title, anchor="w")

    startdatum_label = tk.Label(zeitspan_canvas, text="Von:", **label_style)
    zeitspan_canvas.create_window(30, 60, window=startdatum_label, anchor="w")
    startdatum = AutoDateEntry(zeitspan_canvas, width=10)
    # Übergebe das root.style Objekt an AutoDateEntry für ttk.Combobox Styling
    startdatum.master.style = style
    zeitspan_canvas.create_window(100, 60, window=startdatum)


    enddatum_label = tk.Label(zeitspan_canvas, text="Bis:", **label_style)
    zeitspan_canvas.create_window(190, 60, window=enddatum_label, anchor="w")
    enddatum = AutoDateEntry(zeitspan_canvas, width=10)
    # Übergebe das root.style Objekt an AutoDateEntry für ttk.Combobox Styling
    enddatum.master.style = style
    zeitspan_canvas.create_window(260, 60, window=enddatum)


    zeitspanne_anzeige = tk.Label(zeitspan_canvas, text="0 J, 0 M, 0 T", **label_style, width=18, anchor="w")
    zeitspan_canvas.create_window(450, 60, window=zeitspanne_anzeige, anchor="e")

    intervall_label_title = tk.Label(zeitspan_canvas, text="Intervall (Stunden)", **label_style)
    zeitspan_canvas.create_window(30, 95, window=intervall_label_title, anchor="w")
    intervall_entry = tk.Entry(zeitspan_canvas, width=7, **entry_style)
    intervall_entry.insert(0, "1")
    zeitspan_canvas.create_window(170, 95, window=intervall_entry, anchor="w")


    def parse_flexible_date(date_string):
        try:
            return datetime.strptime(date_string, '%d.%m.%y')
        except ValueError:
            try:
                return datetime.strptime(date_string, '%d.%m.%Y')
            except ValueError:
                return None

    def berechne_zeitspanne_und_werte():
        try:
            start_str = startdatum.get()
            end_str = enddatum.get()
            start = parse_flexible_date(start_str)
            end = parse_flexible_date(end_str)

            if start and end:
                if end < start:
                    zeitspanne_anzeige.config(text="Enddatum vor Startdatum")
                else:
                    delta = end - start
                    jahre = delta.days // 365
                    verbleibende_tage = delta.days % 365
                    monate = verbleibende_tage // 30
                    tage_rest = verbleibende_tage % 30
                    zeitspanne_anzeige.config(text=f"{jahre} J, {monate} M, {tage_rest} T")
            else:
                zeitspanne_anzeige.config(text="Ungültiges Datum")

            berechne_werte_anzahl()
        except Exception:
            zeitspanne_anzeige.config(text="Datumsfehler")
            werte_info.config(text="Zu generierende Werte: Fehler")


    def berechne_werte_anzahl():
        try:
            start_str = startdatum.get()
            end_str = enddatum.get()
            start = parse_flexible_date(start_str)
            end = parse_flexible_date(end_str)

            if not start or not end or end < start:
                werte_info.config(text="Zu generierende Werte: -")
                return 0

            delta = end - start
            num_days = delta.days + 1
            
            intervall_val_str = intervall_entry.get()
            if not intervall_val_str:
                werte_info.config(text="Intervall fehlt")
                return 0
            try:
                stunden_intervall = float(intervall_val_str)
                if stunden_intervall <= 0:
                    werte_info.config(text="Intervall > 0 nötig")
                    return 0
            except ValueError:
                werte_info.config(text="Intervall ungültig")
                return 0

            messwerte_pro_messstelle = math.ceil((num_days * 24) / stunden_intervall)

            messstellen_text_inhalt = messstellen_text.get("1.0", tk.END).strip()
            valid, result_messstellen = validiere_messstellen(messstellen_text_inhalt)
            if not valid:
                werte_info.config(text=f"Fehler: {result_messstellen}")
                return 0

            messstellenanzahl = len(result_messstellen)
            if messstellenanzahl == 0:
                werte_info.config(text="Keine Messstellen")
                return 0
            
            gesamt_werte = messwerte_pro_messstelle * messstellenanzahl
            werte_info.config(text=f"Zu generierende Werte: {gesamt_werte:,.0f}".replace(',', '.'))
            return gesamt_werte
        except Exception as e:
            print(f"Fehler in berechne_werte_anzahl: {e}")
            werte_info.config(text="Berechnungsfehler")
            return 0

    startdatum.bind("<FocusOut>", lambda e: berechne_zeitspanne_und_werte())
    startdatum.bind("<KeyRelease>", lambda e: berechne_zeitspanne_und_werte() if len(startdatum.get()) >=8 else None)
    enddatum.bind("<FocusOut>", lambda e: berechne_zeitspanne_und_werte())
    enddatum.bind("<KeyRelease>", lambda e: berechne_zeitspanne_und_werte() if len(enddatum.get()) >=8 else None)
    intervall_entry.bind("<KeyRelease>", lambda e: berechne_zeitspanne_und_werte())
    intervall_entry.bind("<FocusOut>", lambda e: berechne_zeitspanne_und_werte())


    messstellen_frame = tk.Frame(main_frame, bg=DISCORD_BG)
    messstellen_frame.pack(fill=tk.X, pady=(0, 20))
    messstellen_canvas = tk.Canvas(messstellen_frame, bg=DISCORD_BG, height=140, highlightthickness=0)
    messstellen_canvas.pack(fill=tk.X)
    create_rounded_rect(messstellen_canvas, 0, 0, 580, 140, radius=15, fill=DISCORD_DARK, outline="")

    messstellen_label_title = tk.Label(messstellen_canvas, text="Messstellen:", **label_style, font=('Arial', 10, 'bold'))
    messstellen_canvas.create_window(20, 15, window=messstellen_label_title, anchor="w")
    messstellen_text = tk.Text(messstellen_canvas, height=4, width=60, **entry_style, wrap=tk.WORD)
    messstellen_canvas.create_window(290, 55, window=messstellen_text)
    help_label = tk.Label(messstellen_canvas, text="Namen mit Semikolon (;) oder Zeilenumbruch trennen",
                        fg=DISCORD_GRAY_TEXT, bg=DISCORD_DARK, font=('Arial', 9))
    messstellen_canvas.create_window(290, 100, window=help_label)

    messstellen_text.bind("<KeyRelease>", lambda e: berechne_zeitspanne_und_werte())
    messstellen_text.bind("<FocusOut>", lambda e: berechne_zeitspanne_und_werte())


    def validiere_messstellen(text_input):
        if not text_input.strip():
            return False, "Keine Messstellen angegeben"
        raw_messstellen = text_input.replace('\n', ';').split(';')
        messstellen = [m.strip() for m in raw_messstellen if m.strip()]

        if not messstellen:
            return False, "Keine gültigen Messstellen"

        duplicates = set()
        seen = set()
        for m in messstellen:
            if m in seen:
                duplicates.add(m)
            else:
                seen.add(m)
        if duplicates:
            return False, f"Doppelte: {', '.join(duplicates)}"
        return True, messstellen

    formel_frame = tk.Frame(main_frame, bg=DISCORD_BG)
    formel_frame.pack(fill=tk.X, pady=(0, 20))
    formel_canvas = tk.Canvas(formel_frame, bg=DISCORD_BG, height=90, highlightthickness=0)
    formel_canvas.pack(fill=tk.X)
    create_rounded_rect(formel_canvas, 0, 0, 580, 90, radius=15, fill=DISCORD_DARK, outline="")

    formel_label_title = tk.Label(formel_canvas, text="Grundwasser-Modell:", **label_style, font=('Arial', 10, 'bold'))
    formel_canvas.create_window(20, 15, window=formel_label_title, anchor="w")

    formel_anzeige_label = tk.Label(formel_canvas, text=formel_params.generiere_formel_string(),
                                 **label_style, width=60, anchor="w", justify=tk.LEFT, wraplength=480)
    formel_canvas.create_window(20, 45, window=formel_anzeige_label, anchor="w")


    root.s_GW0_var = tk.DoubleVar(value=12.0)
    root.s_A_var = tk.DoubleVar(value=1.0)
    root.s_T_var = tk.DoubleVar(value=365)
    root.s_freq_var = tk.DoubleVar(value=1.0)
    root.s_Da_var = tk.DoubleVar(value=20)
    root.s_Dd_var = tk.DoubleVar(value=50)
    root.s_R_var = tk.DoubleVar(value=0.12)

    formel_params.set_parameters(
        root.s_GW0_var.get(), root.s_A_var.get(), root.s_T_var.get(),
        root.s_freq_var.get(), root.s_Da_var.get(), root.s_Dd_var.get(), root.s_R_var.get()
    )
    formel_anzeige_label.config(text=formel_params.generiere_formel_string())


    def open_formel_submenu():
        if hasattr(root, 'submenu_open') and root.submenu_open:
            return
        root.submenu_open = True
        submenu = tk.Toplevel(root)
        submenu.title("Grundwassermodell anpassen")
        submenu_width = 600
        submenu_height = 520
        root_x = root.winfo_x()
        root_y = root.winfo_y()
        root_width = root.winfo_width()
        root_height = root.winfo_height()
        sub_x_pos = root_x + (root_width // 2) - (submenu_width // 2)
        sub_y_pos = root_y + (root_height // 2) - (submenu_height // 2)
        submenu.geometry(f"{submenu_width}x{submenu_height}+{sub_x_pos}+{sub_y_pos}")
        submenu.minsize(submenu_width, submenu_height)
        submenu.configure(bg=DISCORD_BG)
        set_dark_title_bar(submenu)

        main_submenu_frame = tk.Frame(submenu, bg=DISCORD_BG, padx=20, pady=20)
        main_submenu_frame.pack(fill=tk.BOTH, expand=True)

        parameter_frame = tk.Frame(main_submenu_frame, bg=DISCORD_BG)
        parameter_frame.pack(fill=tk.BOTH, expand=True)


        title_label = tk.Label(parameter_frame, text="Parameter der Grundwasserganglinie",
                            bg=DISCORD_BG, fg=DISCORD_TEXT, font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky="w")

        temp_gw0_var = tk.DoubleVar(value=root.s_GW0_var.get())
        temp_a_var = tk.DoubleVar(value=root.s_A_var.get())
        temp_t_var = tk.DoubleVar(value=root.s_T_var.get())
        temp_freq_var = tk.DoubleVar(value=root.s_freq_var.get())
        temp_da_var = tk.DoubleVar(value=root.s_Da_var.get())
        temp_dd_var = tk.DoubleVar(value=root.s_Dd_var.get())
        temp_r_var = tk.DoubleVar(value=root.s_R_var.get())


        def create_parameter_slider(parent, row, text, from_, to_, var_instance, resolution=0.01, display_format="{:.2f}"):
            sub_frame = tk.Frame(parent, bg=DISCORD_BG)
            sub_frame.grid(row=row, column=0, columnspan=3, pady=5, sticky="ew")
            sub_frame.columnconfigure(1, weight=1)

            label = tk.Label(sub_frame, text=text, bg=DISCORD_BG, fg=DISCORD_TEXT, width=25, anchor="w")
            label.grid(row=0, column=0, padx=(0, 10), sticky="w")

            slider = ttk.Scale(sub_frame, from_=from_, to=to_, variable=var_instance,
                               orient=tk.HORIZONTAL, length=250, style="TScale")
            slider.grid(row=0, column=1, sticky="ew", padx=5)

            value_label = tk.Label(sub_frame, bg=DISCORD_BG, fg=DISCORD_TEXT, width=7, anchor="e")
            value_label.grid(row=0, column=2, padx=(10, 0), sticky="e")

            def update_value_label(val):
                value_label.config(text=display_format.format(float(val)))

            var_instance.trace_add("write", lambda *args: update_value_label(var_instance.get()))
            update_value_label(var_instance.get())
            return slider

        create_parameter_slider(parameter_frame, 1, "Grundniveau (GW0) [m]:", 5, 20, temp_gw0_var, resolution=0.1, display_format="{:.1f}")
        create_parameter_slider(parameter_frame, 2, "Saison. Amplitude (A) [m]:", 0.0, 5.0, temp_a_var, resolution=0.05, display_format="{:.2f}")
        create_parameter_slider(parameter_frame, 3, "Periodendauer (T) [Tage]:", 50, 730, temp_t_var, resolution=1, display_format="{:.0f}")
        create_parameter_slider(parameter_frame, 4, "Sinusfrequenz pro Jahr:", 0.1, 5.0, temp_freq_var, resolution=0.1, display_format="{:.1f}")
        create_parameter_slider(parameter_frame, 5, "Anstiegsdauer (Da) [Tage]:", 1, 150, temp_da_var, resolution=1, display_format="{:.0f}")
        create_parameter_slider(parameter_frame, 6, "Abklingdauer (Dd) [Tage]:", 1, 300, temp_dd_var, resolution=1, display_format="{:.0f}")
        create_parameter_slider(parameter_frame, 7, "Zufallsschw. (R) [m]:", 0.0, 1.0, temp_r_var, resolution=0.01, display_format="{:.2f}")


        btn_frame = tk.Frame(parameter_frame, bg=DISCORD_BG)
        btn_frame.grid(row=8, column=0, columnspan=3, pady=25, sticky="ew")
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)


        def apply_changes_and_close():
            root.s_GW0_var.set(temp_gw0_var.get())
            root.s_A_var.set(temp_a_var.get())
            root.s_T_var.set(temp_t_var.get())
            root.s_freq_var.set(temp_freq_var.get())
            root.s_Da_var.set(temp_da_var.get())
            root.s_Dd_var.set(temp_dd_var.get())
            root.s_R_var.set(temp_r_var.get())

            formel_params.set_parameters(
                root.s_GW0_var.get(), root.s_A_var.get(), root.s_T_var.get(),
                root.s_freq_var.get(), root.s_Da_var.get(), root.s_Dd_var.get(), root.s_R_var.get()
            )
            formel_anzeige_label.config(text=formel_params.generiere_formel_string())
            close_submenu_only()


        def close_submenu_only():
            submenu.destroy()
            root.submenu_open = False

        cancel_btn = tk.Button(btn_frame, text="Abbrechen", bg=DISCORD_DARK, fg=DISCORD_TEXT,
                            activebackground=DISCORD_DARKER, activeforeground=DISCORD_TEXT,
                            relief="flat", padx=15, pady=5, width=10,
                            command=close_submenu_only)
        cancel_btn.pack(side=tk.LEFT, padx=(0,10), expand=True)


        apply_btn = tk.Button(btn_frame, text="Übernehmen", bg=BUTTON_COLOR, fg=DISCORD_TEXT,
                            activebackground=BUTTON_HOVER, activeforeground=DISCORD_TEXT,
                            relief="flat", padx=15, pady=5, width=10,
                            command=apply_changes_and_close)
        apply_btn.pack(side=tk.RIGHT, expand=True)


        submenu.protocol("WM_DELETE_WINDOW", close_submenu_only)
        submenu.transient(root)
        submenu.grab_set()
        root.wait_window(submenu)


    edit_button = tk.Button(formel_canvas, text="✏️", bg=DISCORD_DARK, fg=DISCORD_TEXT,
                          command=open_formel_submenu, bd=0, relief="flat",
                          activebackground=DISCORD_DARKER,
                          font=("Arial", 16), padx=5, pady=0)
    formel_canvas.create_window(540, 15, window=edit_button, anchor="ne")

    progress_frame = tk.Frame(main_frame, bg=DISCORD_BG)
    progress_frame.pack(fill=tk.X, pady=(0, 20))
    progress_canvas = tk.Canvas(progress_frame, bg=DISCORD_BG, height=100, highlightthickness=0)
    progress_canvas.pack(fill=tk.X)
    create_rounded_rect(progress_canvas, 0, 0, 580, 100, radius=15, fill=DISCORD_DARK, outline="")

    progress = ttk.Progressbar(progress_canvas, orient="horizontal", length=540,
                             mode="determinate", style="TProgressbar")
    progress_canvas.create_window(290, 40, window=progress)
    progress_info = tk.Label(progress_canvas, text="0/0 Werte (0%)", **label_style)
    progress_canvas.create_window(290, 70, window=progress_info)


    control_panel_frame = tk.Frame(main_frame, bg=DISCORD_BG)
    control_panel_frame.pack(fill=tk.X, pady=(5, 10))

    control_canvas = tk.Canvas(control_panel_frame, bg=DISCORD_BG, height=120, highlightthickness=0)
    control_canvas.pack(fill=tk.X)
    create_rounded_rect(control_canvas, 0, 0, 580, 120, radius=15, fill=DISCORD_DARK, outline="")


    start_button_canvas = tk.Canvas(control_canvas, width=160, height=40, bg=DISCORD_DARK, highlightthickness=0)
    control_canvas.create_window(130, 45, window=start_button_canvas)
    start_button_bg_rect = create_rounded_rect(start_button_canvas, 0, 0, 160, 40, radius=15, fill=BUTTON_COLOR, outline="")
    start_button_text_item = start_button_canvas.create_text(80, 20, text="Start", fill=DISCORD_TEXT, font=("Arial", 14, "bold"))

    format_switch_canvas = tk.Canvas(control_canvas, width=100, height=30, bg=DISCORD_DARK, highlightthickness=0, cursor="hand2")
    control_canvas.create_window(470, 45, window=format_switch_canvas)

    root.output_format = "csv"
    switch_bg_rect = create_rounded_rect(format_switch_canvas, 0, 0, 100, 30, radius=15, fill="#FF5555")
    switch_button_oval = format_switch_canvas.create_oval(5, 5, 25, 25, fill="white", outline="")
    switch_text_item = format_switch_canvas.create_text(60, 15, text="CSV", fill="white", font=("Arial", 10, "bold"), anchor="w")

    def toggle_format(event=None):
        if root.output_format == "csv":
            root.output_format = "excel"
            format_switch_canvas.itemconfig(switch_bg_rect, fill=DISCORD_GREEN)
            format_switch_canvas.coords(switch_button_oval, 75, 5, 95, 25)
            format_switch_canvas.itemconfig(switch_text_item, text="Excel")
            format_switch_canvas.coords(switch_text_item, 20, 15)
        else:
            root.output_format = "csv"
            format_switch_canvas.itemconfig(switch_bg_rect, fill="#FF5555")
            format_switch_canvas.coords(switch_button_oval, 5, 5, 25, 25)
            format_switch_canvas.itemconfig(switch_text_item, text="CSV")
            format_switch_canvas.coords(switch_text_item, 40, 15)
    format_switch_canvas.bind("<Button-1>", toggle_format)
    for item in [switch_bg_rect, switch_button_oval, switch_text_item]:
        format_switch_canvas.tag_bind(item, "<Button-1>", toggle_format)


    werte_info = tk.Label(control_canvas, text="Zu generierende Werte: -", bg=DISCORD_DARK, fg=DISCORD_GRAY_TEXT, font=('Arial', 10))
    control_canvas.create_window(290, 80, window=werte_info)

    def create_output_files(start_dt, end_dt, messstellen_namen, intervall_stunden, formel_parameter_obj, output_fmt, save_path):
        hourly_interval = timedelta(hours=intervall_stunden)
        
        # Korrekte Anzahl der Tage für die Berechnung der Arrays bestimmen
        num_total_seconds = (end_dt - start_dt).total_seconds()
        num_days_for_calc = math.ceil(num_total_seconds / (24 * 3600)) +1 # +1 um sicherzustellen, dass der Endtag abgedeckt ist

        GW0 = formel_parameter_obj.gw0
        A = formel_parameter_obj.a
        T_periode = formel_parameter_obj.t_periode
        freq = formel_parameter_obj.freq
        Da = formel_parameter_obj.da
        Dd = formel_parameter_obj.dd
        R_scale = formel_parameter_obj.r_scale

        t_daily = np.arange(0, num_days_for_calc, 1)
        
        np.random.seed(int(datetime.now().timestamp()))
        r_base_daily = np.random.normal(0, 1, size=len(t_daily))

        gw_daily_values = np.zeros_like(t_daily, dtype=float)
        seasonal_daily = A * np.sin(2 * np.pi * freq * t_daily / T_periode)
        
        if len(t_daily) > 0:
            gw_daily_values[0] = GW0 + seasonal_daily[0] + R_scale * r_base_daily[0]
        else: # Falls num_days_for_calc 0 ist (sollte nicht passieren bei validen Daten)
            if total_values_to_generate > 0 : # Nur Fehler zeigen wenn wirklich Werte erwartet werden
                 messagebox.showerror("Interner Fehler", "Keine täglichen Werte konnten initialisiert werden.")
            return "Fehler bei GW-Initialisierung"


        for i in range(1, len(t_daily)):
            disturbance_potential = R_scale * r_base_daily[i]
            prev_gw = gw_daily_values[i-1]
            current_gw_base_level = GW0 + seasonal_daily[i]
            target_value_for_disturbance = current_gw_base_level + disturbance_potential
            deviation_from_target = target_value_for_disturbance - prev_gw

            if deviation_from_target > 0:
                daily_change_due_process = deviation_from_target / max(1, Da) # Vermeide Division durch Null
            else:
                daily_change_due_process = deviation_from_target / max(1, Dd) # Vermeide Division durch Null

            gw_daily_values[i] = prev_gw + daily_change_due_process
        
        regen_eff, starkregen_eff, schnee_eff = formel_parameter_obj.generiere_ereignisse(num_days_for_calc)

        total_measurements_per_station = 0
        current_t_count = start_dt
        while current_t_count <= end_dt: # Inklusive Enddatum
            total_measurements_per_station +=1
            current_t_count += hourly_interval
            # Sicherheitsabbruch, falls Intervall zu klein oder Daten falsch
            if total_measurements_per_station > 1000000 / len(messstellen_namen): # Limit pro Messstelle
                print("Warnung: Maximale Anzahl an Messwerten pro Station überschritten. Schleife abgebrochen.")
                break

        total_values_to_generate = total_measurements_per_station * len(messstellen_namen)
        values_created_count = 0

        def update_progress(val):
            if total_values_to_generate > 0:
                progress['value'] = val
                percentage = (val / total_values_to_generate) * 100
                progress_info.config(text=f"{int(val):,}/{int(total_values_to_generate):,} Werte ({percentage:.1f}%)".replace(',', '.'))
            else:
                progress['value'] = 0
                progress_info.config(text="Keine Werte zu generieren")
            root.update_idletasks()

        if total_values_to_generate == 0 and len(messstellen_namen) > 0: # Wenn Messstellen da sind, aber keine Werte
             messagebox.showwarning("Hinweis", "Keine Messwerte zu generieren für den gewählten Zeitraum/Intervall.")
             return "Keine Werte generiert."


        if output_fmt == "excel":
            excel_file_path = os.path.join(save_path, f"Messdaten_WaterGen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
            with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
                for messstelle_idx, messstelle_id in enumerate(messstellen_namen):
                    data_list = []
                    current_time = start_dt
                    
                    messstelle_offset = (messstelle_idx - len(messstellen_namen) / 2) * R_scale * 0.1

                    # Schleife für die Anzahl der Messungen, nicht über die Zeit, um Endlosschleifen zu vermeiden
                    for _ in range(total_measurements_per_station):
                        if current_time > end_dt + timedelta(seconds=1): # Kleine Toleranz für Fließkommavergleiche
                            break

                        time_delta_from_start = current_time - start_dt
                        day_index = int(time_delta_from_start.total_seconds() // (24 * 3600))
                        day_index = min(max(0, day_index), num_days_for_calc - 1)

                        base_gw_for_day = gw_daily_values[day_index] if day_index < len(gw_daily_values) else GW0 # Fallback

                        ereignis_effekt_total = 0
                        if day_index < len(regen_eff): ereignis_effekt_total += regen_eff[day_index]
                        if day_index < len(starkregen_eff): ereignis_effekt_total += starkregen_eff[day_index]
                        if day_index < len(schnee_eff): ereignis_effekt_total += schnee_eff[day_index]

                        final_messwert = base_gw_for_day + ereignis_effekt_total + messstelle_offset
                        # final_messwert += random.uniform(-R_scale*0.05, R_scale*0.05) # Entfernt

                        data_list.append([current_time, round(final_messwert, 3)])
                        current_time += hourly_interval
                        values_created_count += 1
                        if values_created_count % 100 == 0:
                            update_progress(values_created_count)
                    
                    if not data_list and total_measurements_per_station > 0 :
                        print(f"Warnung: Keine Daten für Messstelle {messstelle_id} generiert, obwohl erwartet.")

                    df_messstelle = pd.DataFrame(data_list, columns=['Zeitstempel', 'Messwert'])
                    safe_sheet_name = "".join(c if c.isalnum() else "_" for c in messstelle_id)[:30]
                    if not safe_sheet_name: safe_sheet_name = f"Messstelle_{messstelle_idx+1}" # Fallback Name
                    df_messstelle.to_excel(writer, sheet_name=safe_sheet_name, index=False)
            update_progress(total_values_to_generate)
            return f"Excel-Datei gespeichert: {excel_file_path}"

        elif output_fmt == "csv":
            base_filename = f"Messdaten_WaterGen_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            all_csv_paths = []
            for messstelle_idx, messstelle_id in enumerate(messstellen_namen):
                safe_messstelle_id = "".join(c if c.isalnum() else "_" for c in messstelle_id)
                if not safe_messstelle_id: safe_messstelle_id = f"Messstelle_{messstelle_idx+1}" # Fallback Name
                csv_file_path = os.path.join(save_path, f"{base_filename}_{safe_messstelle_id}.csv")
                all_csv_paths.append(csv_file_path)
                
                messstelle_offset = (messstelle_idx - len(messstellen_namen) / 2) * R_scale * 0.1

                with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    csv_writer = csv.writer(csvfile, delimiter=';')
                    csv_writer.writerow(['Zeitstempel', 'Messwert'])
                    current_time = start_dt
                    
                    for _ in range(total_measurements_per_station):
                        if current_time > end_dt + timedelta(seconds=1):
                            break

                        time_delta_from_start = current_time - start_dt
                        day_index = int(time_delta_from_start.total_seconds() // (24 * 3600))
                        day_index = min(max(0,day_index), num_days_for_calc - 1)

                        base_gw_for_day = gw_daily_values[day_index] if day_index < len(gw_daily_values) else GW0

                        ereignis_effekt_total = 0
                        if day_index < len(regen_eff): ereignis_effekt_total += regen_eff[day_index]
                        if day_index < len(starkregen_eff): ereignis_effekt_total += starkregen_eff[day_index]
                        if day_index < len(schnee_eff): ereignis_effekt_total += schnee_eff[day_index]

                        final_messwert = base_gw_for_day + ereignis_effekt_total + messstelle_offset
                        
                        csv_writer.writerow([current_time.strftime('%d.%m.%Y %H:%M:%S'), f"{final_messwert:.3f}".replace('.',',')])
                        current_time += hourly_interval
                        values_created_count += 1
                        if values_created_count % 100 == 0:
                            update_progress(values_created_count)
            update_progress(total_values_to_generate)
            if all_csv_paths:
                return f"CSV-Dateien gespeichert in: {save_path}"
            else:
                return "Keine CSV-Dateien erstellt (möglicherweise keine Messstellen/Daten)."
        return "Unbekanntes Ausgabeformat"


    def start_generation_thread():
        start_button_canvas.itemconfig(start_button_bg_rect, fill=DISCORD_GRAY_TEXT)
        start_button_canvas.itemconfig(start_button_text_item, text="Generiere...")
        start_button_canvas.unbind("<Button-1>")
        start_button_canvas.tag_unbind(start_button_bg_rect, "<Button-1>")
        start_button_canvas.tag_unbind(start_button_text_item, "<Button-1>")
        start_button_canvas.config(cursor="")


        start_str = startdatum.get()
        end_str = enddatum.get()
        intervall_str = intervall_entry.get()
        messstellen_eingabe = messstellen_text.get("1.0", tk.END).strip()

        start_dt = parse_flexible_date(start_str)
        end_dt = parse_flexible_date(end_str)

        if not start_dt or not end_dt:
            tk.messagebox.showerror("Fehler", "Bitte gültiges Start- und Enddatum eingeben (TT.MM.JJ).")
            reset_start_button()
            return
        if end_dt < start_dt:
            tk.messagebox.showerror("Fehler", "Das Enddatum darf nicht vor dem Startdatum liegen.")
            reset_start_button()
            return
        try:
            intervall_stunden = float(intervall_str)
            if intervall_stunden <= 0:
                raise ValueError("Intervall muss positiv sein.")
            if intervall_stunden < 0.001: # Schutz vor extrem kleinen Intervallen
                raise ValueError("Intervall ist zu klein.")
        except ValueError as ve:
            tk.messagebox.showerror("Fehler", f"Bitte ein gültiges positives Zahlenintervall für Stunden angeben. {ve}")
            reset_start_button()
            return

        is_valid_messstellen, messstellen_namen_or_error = validiere_messstellen(messstellen_eingabe)
        if not is_valid_messstellen:
            tk.messagebox.showerror("Fehler bei Messstellen", messstellen_namen_or_error)
            reset_start_button()
            return
        if not messstellen_namen_or_error:
             tk.messagebox.showerror("Fehler", "Keine Messstellen definiert.")
             reset_start_button()
             return


        save_path = filedialog.askdirectory(title="Speicherort für generierte Dateien wählen")
        if not save_path:
            reset_start_button()
            return

        current_output_format = root.output_format

        def generation_task():
            try:
                status_message = create_output_files(start_dt, end_dt, messstellen_namen_or_error, intervall_stunden, formel_params, current_output_format, save_path)
                if "Fehler" not in status_message and "Keine Werte generiert" not in status_message:
                    tk.messagebox.showinfo("Erfolg", status_message)
                elif "Keine Werte generiert" in status_message:
                    pass # Bereits in create_output_files behandelt
                else:
                    tk.messagebox.showwarning("Hinweis", status_message) # Für kleinere Probleme oder Hinweise
            except Exception as e:
                tk.messagebox.showerror("Fehler bei Generierung", f"Ein Fehler ist aufgetreten:\n{e}")
                import traceback
                print(traceback.format_exc())
            finally:
                reset_start_button()

        thread = threading.Thread(target=generation_task)
        thread.daemon = True
        thread.start()


    def reset_start_button():
        start_button_canvas.itemconfig(start_button_bg_rect, fill=BUTTON_COLOR)
        start_button_canvas.itemconfig(start_button_text_item, text="Start")
        start_button_canvas.bind("<Button-1>", lambda e: start_generation_thread())
        start_button_canvas.tag_bind(start_button_bg_rect, "<Button-1>", lambda e: start_generation_thread())
        start_button_canvas.tag_bind(start_button_text_item, "<Button-1>", lambda e: start_generation_thread())
        start_button_canvas.config(cursor="hand2")
        progress['value'] = 0
        # Den Text des Progress-Infos nur zurücksetzen, wenn keine Fehlermeldung in Werte-Info steht
        if "Fehler" not in werte_info.cget("text") and "Keine Messstellen" not in werte_info.cget("text"):
             progress_info.config(text="0/0 Werte (0%)")
        # Trigger Neuberechnung, um Info-Label zu aktualisieren
        berechne_zeitspanne_und_werte()


    start_button_canvas.bind("<Button-1>", lambda e: start_generation_thread())
    start_button_canvas.tag_bind(start_button_bg_rect, "<Button-1>", lambda e: start_generation_thread())
    start_button_canvas.tag_bind(start_button_text_item, "<Button-1>", lambda e: start_generation_thread())
    start_button_canvas.config(cursor="hand2")

    def on_start_enter(e): start_button_canvas.itemconfig(start_button_bg_rect, fill=BUTTON_HOVER)
    def on_start_leave(e): start_button_canvas.itemconfig(start_button_bg_rect, fill=BUTTON_COLOR)

    start_button_canvas.bind("<Enter>", on_start_enter)
    start_button_canvas.bind("<Leave>", on_start_leave)


    berechne_zeitspanne_und_werte()
    formel_anzeige_label.config(text=formel_params.generiere_formel_string())

    root.mainloop()

if __name__ == "__main__":
    if hasattr(sys, '_MEIPASS'): # Workaround für ctypes bei PyInstaller
        ctypes.windll.kernel32.SetDllDirectoryW(None)
    create_gui()