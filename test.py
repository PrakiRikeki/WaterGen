import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import pandas as pd
import csv
import threading
import math
import random
import ctypes
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
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

# Globale Variable für das Logo im Ladescreen
logo_img_global = None

# Darkmode Titelleiste für Windows
def set_dark_title_bar(window):
    try:
        window.update()
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
        get_parent = ctypes.windll.user32.GetParent
        hwnd = get_parent(window.winfo_id())
        value = ctypes.c_int(2)
        set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value))
    except Exception as e:
        print(f"Fehler beim Setzen der dunklen Titelleiste: {e}")

# Abgerundete Rahmen für Frames
class RoundedFrame(tk.Frame):
    def __init__(self, master=None, corner_radius=15, padding=10, bg=DISCORD_DARK, **kwargs):
        super().__init__(master, bg=master['bg'], highlightthickness=0, **kwargs)
        
        self.corner_radius = corner_radius
        self.padding = padding
        self.bg_color = bg
        
        # Inneres Frame mit border und runden Ecken
        self.inner_frame = tk.Frame(self, bg=self.bg_color, bd=0, highlightthickness=0)
        self.inner_frame.pack(fill="both", expand=True, padx=2, pady=2)  # Ein bisschen Platz für den Schatten
        
        # Canvas für die abgerundeten Ecken
        self.canvas = tk.Canvas(self.inner_frame, bg=self.bg_color, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Inhalt-Frame innerhalb des Canvas
        self.container = tk.Frame(self.canvas, bg=self.bg_color, padx=padding, pady=padding)
        self.container_window = self.canvas.create_window(0, 0, window=self.container, anchor="nw")
        
        # Auf Größenänderungen reagieren
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.bind("<Configure>", self._on_frame_configure)
    
    def _on_canvas_configure(self, event):
        # Anpassen der Größe des Inhalts-Containers
        width = event.width
        height = event.height
        self.canvas.configure(width=width, height=height)
        self.canvas.coords(self.container_window, 0, 0)
        
        # Abgerundetes Rechteck neu zeichnen
        self.canvas.delete("rounded_rect")
        self._draw_rounded_rect(0, 0, width, height, self.corner_radius)
    
    def _on_frame_configure(self, event):
        self.canvas.configure(width=event.width-4, height=event.height-4)  # 4px für padding/schatten
    
    def _draw_rounded_rect(self, x1, y1, x2, y2, radius):
        points = [x1+radius, y1,
                 x2-radius, y1,
                 x2, y1,
                 x2, y1+radius,
                 x2, y2-radius,
                 x2, y2,
                 x2-radius, y2,
                 x1+radius, y2,
                 x1, y2,
                 x1, y2-radius,
                 x1, y1+radius,
                 x1, y1]
        self.canvas.create_polygon(points, smooth=True, fill=self.bg_color, tags="rounded_rect", outline="")

# Datumseingabe mit Autovervollständigung
class AutoDateEntry(DateEntry):
    def __init__(self, master=None, **kwargs):
        kwargs['locale'] = 'de_DE'
        kwargs['date_pattern'] = 'dd.mm.yy'
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
        
        # Style für Combobox
        s = ttk.Style()
        try:
            s.configure("Dark.TCombobox", fieldbackground=DISCORD_INPUT_BG, background=DISCORD_DARK, foreground=DISCORD_TEXT, arrowcolor=DISCORD_TEXT)
            s.map("Dark.TCombobox",
                  fieldbackground=[('readonly', DISCORD_INPUT_BG)],
                  selectbackground=[('readonly', DISCORD_GREEN)],
                  selectforeground=[('readonly', DISCORD_DARKER)])
        except tk.TclError:
             print("Warnung: Dark.TCombobox Style konnte nicht vollständig konfiguriert werden")

        super().__init__(master, **kwargs)
        self.bind("<KeyRelease>", self._format_date_entry)
        self.bind("<FocusOut>", self._close_calendar_on_focus_out)
        self.last_value = ""

        # Darkmode für den Kalender-Popup
        if hasattr(self, '_top_cal') and self._top_cal:
            self._top_cal.configure(background=DISCORD_DARKER)
            for child in self._top_cal.winfo_children():
                widget_class = child.winfo_class()
                if widget_class in ['Label', 'TLabel']:
                    child.configure(background=DISCORD_DARKER, foreground=DISCORD_TEXT)
                elif widget_class in ['Button', 'TButton']:
                    try:
                        child.configure(background=DISCORD_DARK, foreground=DISCORD_TEXT,
                                       activebackground=DISCORD_GREEN, activeforeground=DISCORD_TEXT)
                    except tk.TclError:
                        pass
                elif widget_class == 'TCombobox':
                    try:
                        child.configure(style="Dark.TCombobox")
                    except tk.TclError:
                        pass

    def _close_calendar_on_focus_out(self, event):
        if hasattr(self, '_top_cal') and self._top_cal and self._top_cal.winfo_exists():
            self._top_cal.withdraw()

    def _format_date_entry(self, event):
        if event.keysym in ('BackSpace', 'Delete', 'Left', 'Right', 'Up', 'Down', 'Tab', 'ISO_Left_Tab'):
            self.last_value = self.get()
            return
        current_text = self.get()
        cursor_pos = self.index(tk.INSERT)
        original_len = len(current_text)

        # Automatische Punkte hinzufügen
        if len(current_text) == 1 and current_text.isdigit():
            day_first_digit = int(current_text)
            if day_first_digit > 3:
                self.insert(0,"0")
                self.insert(tk.END,".")
        elif len(current_text) == 2 and current_text.isdigit() and original_len < 3:
            day = int(current_text)
            if 0 <= day <= 31:
                 self.insert(tk.END, ".")
        elif len(current_text) == 4 and current_text[2] == '.' and current_text[3].isdigit():
            month_first_digit = int(current_text[3])
            if month_first_digit > 1:
                self.insert(3,"0")
                self.insert(tk.END,".")
        elif len(current_text) == 5 and current_text[2] == '.' and current_text[3:5].isdigit() and original_len < 6:
            month = int(current_text[3:5])
            if 0 <= month <= 12:
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
        self.autokorrelation = 0.7
        self.grundwasser_faktor = 0.15

    def set_parameters(self, gw0, a, t_periode, freq, da, dd, r_scale):
        self.gw0 = gw0
        self.a = a
        self.t_periode = t_periode
        self.freq = freq
        self.da = da
        self.dd = dd
        self.r_scale = r_scale

    def generiere_formel_string(self):
        return (f"GW0: {self.gw0:.2f} A: {self.a:.2f} T: {self.t_periode:.0f} f: {self.freq:.2f}"
                f"\nDa: {self.da:.0f} Dd: {self.dd:.0f} R: {self.r_scale:.2f}")

    def generiere_ereignisse(self, tage):
        regen = np.zeros(tage)
        starkregen = np.zeros(tage)
        schnee = np.zeros(tage)
        grundwasser_effekt = np.zeros(tage)
        return regen, starkregen, schnee, grundwasser_effekt


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
        logo_label.pack(pady=(60, 20))
    except Exception as e:
        print(f"Fehler beim Laden des Logos im Ladescreen: {e}")
        tk.Label(loading_window, text="WaterGen", font=("Arial", 24, "bold"),
                fg=DISCORD_TEXT, bg=DISCORD_DARKER).pack(pady=(60, 20))

    loading_label = tk.Label(loading_window, text="Anwendung wird geladen...",
                           fg=DISCORD_TEXT, bg=DISCORD_DARKER, font=("Arial", 12))
    loading_label.pack(pady=10)

    progress = ttk.Progressbar(loading_window, orient="horizontal", length=300, mode="indeterminate")
    s_load = ttk.Style(loading_window)
    s_load.theme_use('clam')
    s_load.configure("Loading.Horizontal.TProgressbar", troughcolor=DISCORD_BG, background=DISCORD_GREEN, bordercolor=DISCORD_DARKER, lightcolor=DISCORD_GREEN, darkcolor=DISCORD_GREEN)
    progress.configure(style="Loading.Horizontal.TProgressbar")
    progress.pack(pady=20)
    progress.start(10)

    def close_loading():
        progress.stop()
        loading_window.destroy()

    loading_window.after(2000, close_loading)
    loading_window.mainloop()

# GUI erstellen
def create_gui():
    # Ladebildschirm
    #show_loading_screen()

    root = tk.Tk()
    root.title("WaterGen")
    # Größere Höhe für mehr Platz
    window_width = 650
    window_height = 850
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_pos = int((screen_width/2) - (window_width/2))
    y_pos = int((screen_height/2) - (window_height/2))
    root.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")
    set_dark_title_bar(root)
    root.configure(bg=DISCORD_BG)
    
    root.minsize(window_width, window_height)
    
    # Scrollbarer Hauptframe für das Fenster (falls Inhalte zu groß sind)
    main_container = tk.Frame(root, bg=DISCORD_BG)
    main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
    
    # Hauptinhalt
    content_frame = tk.Frame(main_container, bg=DISCORD_BG)
    content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Logo laden
    root.logo_img_main = None
    try:
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        logo_path_main = os.path.join(base_path, "ribeka 55mm breit_white_2.png")
        original_logo_main = Image.open(logo_path_main)
        logo_width_main = 100
        aspect_ratio_main = original_logo_main.height / original_logo_main.width
        logo_height_main = int(logo_width_main * aspect_ratio_main)
        resized_logo_main = original_logo_main.resize((logo_width_main, logo_height_main), Image.LANCZOS)
        root.logo_img_main = ImageTk.PhotoImage(resized_logo_main)
        logo_label_main = tk.Label(root, image=root.logo_img_main, bg=DISCORD_BG)
        logo_label_main.place(relx=1, rely=0, anchor='ne', x=-25, y=25)
    except Exception as e:
        print(f"Fehler beim Laden des Haupt-Logos: {e}")

    formel_params = FormelParameter()

    # Stile für ttk Widgets
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
          
    # Stil-Dictionaries für Labels, Eingabefelder etc.
    label_style = {"bg": DISCORD_DARK, "fg": DISCORD_TEXT, "font": ('Arial', 11)}
    title_style = {"bg": DISCORD_DARK, "fg": DISCORD_TEXT, "font": ('Arial', 11, 'bold')}
    entry_style = {"bg": DISCORD_INPUT_BG, "fg": DISCORD_TEXT, "insertbackground": DISCORD_TEXT,
                  "font": ('Arial', 11), "bd": 0, "relief": "flat"}

    # Header mit Titel "WaterGen"
    header_frame = RoundedFrame(content_frame, corner_radius=15, padding=15, bg=DISCORD_DARK)
    header_frame.pack(fill=tk.X, pady=(0, 20))
    
    header_title = tk.Label(header_frame.container, text="WaterGen", bg=DISCORD_DARK, 
                           fg=DISCORD_TEXT, font=('Arial', 30, 'bold'))
    header_title.pack(pady=10)

    # Frame für Zeitspanne
    zeitspan_frame = RoundedFrame(content_frame, corner_radius=15, padding=15, bg=DISCORD_DARK)
    zeitspan_frame.pack(fill=tk.X, pady=(0, 20))
    
    # Überschrift für den Frame
    zeitspan_title = tk.Label(zeitspan_frame.container, text="Zeitspanne", **title_style)
    zeitspan_title.pack(anchor='w', pady=(0, 15))
    
    # Grid für Datum-Eingaben
    datum_frame = tk.Frame(zeitspan_frame.container, bg=DISCORD_DARK)
    datum_frame.pack(fill=tk.X, pady=5)
    datum_frame.columnconfigure(1, weight=1)
    datum_frame.columnconfigure(3, weight=1)
    
    # Von-Datum
    von_label = tk.Label(datum_frame, text="Von:", **label_style)
    von_label.grid(row=0, column=0, padx=(0, 5), pady=5, sticky='w')
    startdatum = AutoDateEntry(datum_frame, width=12)
    startdatum.grid(row=0, column=1, padx=5, pady=5, sticky='w')
    
    # Bis-Datum
    bis_label = tk.Label(datum_frame, text="Bis:", **label_style)
    bis_label.grid(row=0, column=2, padx=(15, 5), pady=5, sticky='w')
    enddatum = AutoDateEntry(datum_frame, width=12)
    enddatum.grid(row=0, column=3, padx=5, pady=5, sticky='w')
    
    # Anzeige der berechneten Zeitspanne
    zeitspanne_anzeige = tk.Label(datum_frame, text="0 J, 0 M, 0 T", **label_style)
    zeitspanne_anzeige.grid(row=0, column=4, padx=(15, 0), pady=5, sticky='e')
    
    # Intervall-Eingabe
    intervall_frame = tk.Frame(zeitspan_frame.container, bg=DISCORD_DARK)
    intervall_frame.pack(fill=tk.X, pady=(15, 5))
    
    intervall_label = tk.Label(intervall_frame, text="Intervall (Stunden):", **label_style)
    intervall_label.pack(side=tk.LEFT)
    
    intervall_entry = tk.Entry(intervall_frame, width=8, **entry_style)
    intervall_entry.insert(0, "1")
    intervall_entry.pack(side=tk.LEFT, padx=(10, 0))

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
                    zeitspanne_anzeige.config(text="Ende < Start")
                    werte_info.config(text="Zu generierende Werte: Fehler")
                    return
                delta = end - start
                jahre = delta.days // 365
                verbleibende_tage = delta.days % 365
                monate = verbleibende_tage // 30
                tage_rest = verbleibende_tage % 30
                zeitspanne_anzeige.config(text=f"{jahre} J, {monate} M, {tage_rest} T")
            elif not start_str and not end_str:
                 zeitspanne_anzeige.config(text="0 J, 0 M, 0 T")
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

    # Frame für Messstellen
    messstellen_frame = RoundedFrame(content_frame, corner_radius=15, padding=15, bg=DISCORD_DARK)
    messstellen_frame.pack(fill=tk.X, pady=(0, 20))
    
    messstellen_title = tk.Label(messstellen_frame.container, text="Messstellen", **title_style)
    messstellen_title.pack(anchor='w', pady=(0, 15))
    
    messstellen_text = tk.Text(messstellen_frame.container, height=5, width=65, **entry_style, wrap=tk.WORD)
    messstellen_text.pack(fill=tk.X, expand=True, pady=5)
    
    help_label = tk.Label(messstellen_frame.container, text="Namen mit Semikolon (;) oder Zeilenumbruch trennen",
                        fg=DISCORD_GRAY_TEXT, bg=DISCORD_DARK, font=('Arial', 9))
    help_label.pack(anchor='w', pady=(5, 0))

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

    # Frame für Grundwassermodell/Formel
    formel_frame = RoundedFrame(content_frame, corner_radius=15, padding=15, bg=DISCORD_DARK)
    formel_frame.pack(fill=tk.X, pady=(0, 20))
    
    formel_header_frame = tk.Frame(formel_frame.container, bg=DISCORD_DARK)
    formel_header_frame.pack(fill=tk.X, pady=(0, 10))
    
    formel_title = tk.Label(formel_header_frame, text="Grundwasser-Modell", **title_style)
    formel_title.pack(side=tk.LEFT)
    
    edit_button = tk.Button(formel_header_frame, text="✏️", bg=DISCORD_DARK, fg=DISCORD_TEXT,
                         command=lambda: open_formel_submenu(), bd=0, relief="flat",
                         activebackground=DISCORD_DARKER,
                         font=("Arial", 16), padx=5, pady=0)
    edit_button.pack(side=tk.RIGHT)
    
    formel_anzeige_label = tk.Label(formel_frame.container, text=formel_params.generiere_formel_string(),
                                **label_style, width=65, anchor="w", justify=tk.LEFT, wraplength=580)
    formel_anzeige_label.pack(anchor='w', pady=5)

    root.s_GW0_var = tk.DoubleVar(value=formel_params.gw0)
    root.s_A_var = tk.DoubleVar(value=formel_params.a)
    root.s_T_var = tk.DoubleVar(value=formel_params.t_periode)
    root.s_freq_var = tk.DoubleVar(value=formel_params.freq)
    root.s_Da_var = tk.DoubleVar(value=formel_params.da)
    root.s_Dd_var = tk.DoubleVar(value=formel_params.dd)
    root.s_R_var = tk.DoubleVar(value=formel_params.r_scale)

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
            sub_frame.grid(row=row, column=0, columnspan=3, pady=10, sticky="ew")
            sub_frame.columnconfigure(1, weight=1)
            label = tk.Label(sub_frame, text=text, bg=DISCORD_BG, fg=DISCORD_TEXT, width=25, anchor="w")
            label.grid(row=0, column=0, padx=(0, 10), sticky="w")
            slider = ttk.Scale(sub_frame, from_=from_, to=to_, variable=var_instance,
                               orient=tk.HORIZONTAL, length=250, style="TScale")
            slider.grid(row=0, column=1, sticky="ew", padx=5)
            value_label = tk.Label(sub_frame, bg=DISCORD_BG, fg=DISCORD_TEXT, width=7, anchor="e")
            value_label.grid(row=0, column=2, padx=(10, 0), sticky="e")
            
            def update_value_label(*args):
                try:
                    val_float = float(var_instance.get())
                    value_label.config(text=display_format.format(val_float))
                except ValueError:
                    value_label.config(text="Error")

            var_instance.trace_add("write", update_value_label)
            update_value_label()
            return slider

        create_parameter_slider(parameter_frame, 1, "Grundniveau (GW0) [m]:", 5, 20, temp_gw0_var, resolution=0.1, display_format="{:.1f}")
        create_parameter_slider(parameter_frame, 2, "Saison. Amplitude (A) [m]:", 0.0, 5.0, temp_a_var, resolution=0.05, display_format="{:.2f}")
        create_parameter_slider(parameter_frame, 3, "Periodendauer (T) [Tage]:", 50, 730, temp_t_var, resolution=1, display_format="{:.0f}")
        create_parameter_slider(parameter_frame, 4, "Sinusfrequenz pro Jahr:", 0.1, 5.0, temp_freq_var, resolution=0.1, display_format="{:.1f}")
        create_parameter_slider(parameter_frame, 5, "Anstiegsdauer (Da) [Tage]:", 1, 150, temp_da_var, resolution=1, display_format="{:.0f}")
        create_parameter_slider(parameter_frame, 6, "Abklingdauer (Dd) [Tage]:", 1, 300, temp_dd_var, resolution=1, display_format="{:.0f}")
        create_parameter_slider(parameter_frame, 7, "Zufallsschw. (R) [m]:", 0.0, 1.0, temp_r_var, resolution=0.01, display_format="{:.2f}")

        btn_frame = tk.Frame(parameter_frame, bg=DISCORD_BG)
        btn_frame.grid(row=8, column=0, columnspan=3, pady=35, sticky="ew")
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
        apply_btn.pack(side=tk.RIGHT, padx=(10,0), expand=True)

        submenu.protocol("WM_DELETE_WINDOW", close_submenu_only)
        submenu.transient(root)
        submenu.grab_set()
        root.wait_window(submenu)

    # Frame für Fortschrittsbalken
    progress_frame = RoundedFrame(content_frame, corner_radius=15, padding=15, bg=DISCORD_DARK)
    progress_frame.pack(fill=tk.X, pady=(0, 20))
    
    progress = ttk.Progressbar(progress_frame.container, orient="horizontal", length=580,
                            mode="determinate", style="TProgressbar")
    progress.pack(fill=tk.X, pady=10)
    
    progress_info = tk.Label(progress_frame.container, text="0/0 Werte (0%)", **label_style)
    progress_info.pack()

    # Frame für Steuerungsoptionen (Start-Button, Format-Switch usw.)
    control_frame = RoundedFrame(content_frame, corner_radius=15, padding=15, bg=DISCORD_DARK)
    control_frame.pack(fill=tk.X, pady=(0, 10))
    
    # Container für Button und Switch (mit horizontalem Layout)
    controls_container = tk.Frame(control_frame.container, bg=DISCORD_DARK)
    controls_container.pack(fill=tk.X, pady=10)
    
    # Start-Button
    start_button = tk.Button(controls_container, text="Start", bg=BUTTON_COLOR, fg=DISCORD_TEXT,
                         activebackground=BUTTON_HOVER, activeforeground=DISCORD_TEXT,
                         font=("Arial", 14, "bold"), relief="flat", width=15, height=2,
                         command=lambda: start_generation_thread())
    start_button.pack(side=tk.LEFT, padx=(0, 20))
    
    # Format-Auswahl mit Switch
    format_frame = tk.Frame(controls_container, bg=DISCORD_DARK)
    format_frame.pack(side=tk.RIGHT)
    
    format_label = tk.Label(format_frame, text="Format:", bg=DISCORD_DARK, fg=DISCORD_TEXT)
    format_label.pack(side=tk.LEFT, padx=(0, 10))
    
    # Switch-Canvas
    switch_width = 100
    switch_height = 30
    format_switch_canvas = tk.Canvas(format_frame, width=switch_width, height=switch_height, 
                                 bg=DISCORD_DARK, highlightthickness=0, cursor="hand2")
    format_switch_canvas.pack(side=tk.LEFT)
    
    root.output_format = "csv"
    switch_bg_rect = format_switch_canvas.create_rectangle(0, 0, switch_width, switch_height, fill="#FF5555", outline="")
    format_switch_canvas.create_rectangle(0, 0, switch_width/2, switch_height, fill="#FF5555", outline="")
    format_switch_canvas.create_rectangle(switch_width/2, 0, switch_width, switch_height, fill=DISCORD_GREEN, outline="")
    
    # Text für die Switch-Positionen
    format_switch_canvas.create_text(switch_width/4, switch_height/2, text="CSV", fill="white", font=("Arial", 10, "bold"))
    format_switch_canvas.create_text(3*switch_width/4, switch_height/2, text="Excel", fill="white", font=("Arial", 10, "bold"))
    
    # Switch-Button (weißer Kreis)
    button_radius = 10
    button_padding = 5
    switch_button_oval = format_switch_canvas.create_oval(
        button_padding, button_padding, 
        button_padding + 2*button_radius, button_padding + 2*button_radius, 
        fill="white", outline="")
    
    def toggle_format(event=None):
        if root.output_format == "csv":
            root.output_format = "excel"
            # Verschiebe Button nach rechts
            format_switch_canvas.coords(
                switch_button_oval, 
                switch_width - button_padding - 2*button_radius, button_padding,
                switch_width - button_padding, button_padding + 2*button_radius
            )
        else:
            root.output_format = "csv"
            # Verschiebe Button nach links
            format_switch_canvas.coords(
                switch_button_oval, 
                button_padding, button_padding, 
                button_padding + 2*button_radius, button_padding + 2*button_radius
            )
    
    format_switch_canvas.bind("<Button-1>", toggle_format)
    
    # Zeile für Info über zu generierende Werte
    werte_info = tk.Label(control_frame.container, text="Zu generierende Werte: -", 
                       bg=DISCORD_DARK, fg=DISCORD_GRAY_TEXT, font=('Arial', 10))
    werte_info.pack(pady=(15, 0))

    def create_output_files(start_dt, end_dt, messstellen_namen, intervall_stunden, formel_parameter_obj, output_fmt, save_path):
        hourly_interval = timedelta(hours=intervall_stunden)
        if start_dt is None or end_dt is None:
             raise ValueError("Start- oder Enddatum ist nicht gültig für die Berechnung.")
        total_seconds_in_period = (end_dt - start_dt).total_seconds()
        if total_seconds_in_period < 0:
            raise ValueError("Enddatum liegt vor dem Startdatum.")

        num_days_for_calc = math.ceil(total_seconds_in_period / (24 * 3600)) + 1

        GW0 = formel_parameter_obj.gw0
        A = formel_parameter_obj.a
        T_periode = formel_parameter_obj.t_periode if formel_parameter_obj.t_periode > 0 else 365
        freq = formel_parameter_obj.freq
        Da = formel_parameter_obj.da if formel_parameter_obj.da > 0 else 1
        Dd = formel_parameter_obj.dd if formel_parameter_obj.dd > 0 else 1
        R_scale = formel_parameter_obj.r_scale

        t_daily = np.arange(0, num_days_for_calc, 1)
        np.random.seed(int(datetime.now().timestamp()))
        r_base_daily = np.random.normal(0, 1, size=len(t_daily))

        gw_daily_values = np.zeros_like(t_daily, dtype=float)
        seasonal_daily = A * np.sin(2 * np.pi * freq * t_daily / T_periode)
        
        # Initialwert
        gw_daily_values[0] = GW0 + seasonal_daily[0]
        if len(r_base_daily) > 0:
            gw_daily_values[0] += R_scale * r_base_daily[0]

        for i in range(1, len(t_daily)):
            disturbance_potential = R_scale * r_base_daily[i]
            prev_gw = gw_daily_values[i-1]
            current_gw_base_level = GW0 + seasonal_daily[i]
            target_value_for_disturbance = current_gw_base_level + disturbance_potential
            deviation_from_target = target_value_for_disturbance - prev_gw
            if deviation_from_target > 0:
                daily_change_due_process = deviation_from_target / Da
            else:
                daily_change_due_process = deviation_from_target / Dd
            gw_daily_values[i] = prev_gw + daily_change_due_process
        
        regen_eff, starkregen_eff, schnee_eff, gw_eff = formel_parameter_obj.generiere_ereignisse(num_days_for_calc)

        total_measurements_per_station = 0
        current_t_count = start_dt
        while current_t_count <= end_dt:
            total_measurements_per_station +=1
            current_t_count += hourly_interval
        
        total_values_to_generate = total_measurements_per_station * len(messstellen_namen)
        if total_values_to_generate == 0 and len(messstellen_namen) > 0:
            total_values_to_generate = len(messstellen_namen)

        values_created_count = 0

        def update_progress(val):
            if total_values_to_generate > 0:
                progress['value'] = val
                percentage = (val / total_values_to_generate) * 100
                progress_info.config(text=f"{int(val):,}/{int(total_values_to_generate):,} Werte ({percentage:.1f}%)".replace(',', '.'))
            else:
                progress_info.config(text="Keine Werte zu generieren")
            root.update_idletasks()

        if output_fmt == "excel":
            excel_file_path = os.path.join(save_path, f"Messdaten_WaterGen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
            with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
                for messstelle_idx, messstelle_id in enumerate(messstellen_namen):
                    data_list = []
                    current_time = start_dt
                    messstelle_offset = (messstelle_idx - len(messstellen_namen) / 2) * R_scale * 0.1
                    
                    loop_count = 0
                    max_loops = total_measurements_per_station + 10

                    while current_time <= end_dt and loop_count < max_loops:
                        loop_count += 1
                        time_delta_from_start = current_time - start_dt
                        day_index = int(time_delta_from_start.total_seconds() // (24 * 3600))
                        day_index = min(max(0, day_index), num_days_for_calc - 1)

                        base_gw_for_day = gw_daily_values[day_index] if len(gw_daily_values) > day_index else GW0
                        ereignis_effekt_total = 0
                        if day_index < len(regen_eff): ereignis_effekt_total += regen_eff[day_index]
                        final_messwert = base_gw_for_day + ereignis_effekt_total + messstelle_offset
                        data_list.append([current_time, round(final_messwert, 3)])
                        
                        if intervall_stunden == 0 and current_time == end_dt:
                            break
                        if intervall_stunden == 0 and start_dt == end_dt:
                            break
                        
                        current_time += hourly_interval
                        values_created_count += 1
                        if values_created_count % 200 == 0:
                            update_progress(values_created_count)
                    
                    df_messstelle = pd.DataFrame(data_list, columns=['Zeitstempel', 'Messwert'])
                    safe_sheet_name = "".join(c if c.isalnum() else "_" for c in messstelle_id)[:30]
                    if not safe_sheet_name: safe_sheet_name = f"Messstelle_{messstelle_idx+1}"
                    df_messstelle.to_excel(writer, sheet_name=safe_sheet_name, index=False)
            update_progress(total_values_to_generate)
            return f"Excel-Datei gespeichert: {excel_file_path}"

        elif output_fmt == "csv":
            base_filename = f"Messdaten_WaterGen_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            all_csv_paths = []
            for messstelle_idx, messstelle_id in enumerate(messstellen_namen):
                safe_messstelle_id = "".join(c if c.isalnum() else "_" for c in messstelle_id)
                if not safe_messstelle_id: safe_messstelle_id = f"Messstelle_{messstelle_idx+1}"
                csv_file_path = os.path.join(save_path, f"{base_filename}_{safe_messstelle_id}.csv")

                all_csv_paths.append(csv_file_path)
                messstelle_offset = (messstelle_idx - len(messstellen_namen) / 2) * R_scale * 0.1
                with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    csv_writer = csv.writer(csvfile, delimiter=';')
                    csv_writer.writerow(['Zeitstempel', 'Messwert'])
                    current_time = start_dt
                    
                    loop_count = 0
                    max_loops = total_measurements_per_station + 10

                    while current_time <= end_dt and loop_count < max_loops:
                        loop_count += 1
                        time_delta_from_start = current_time - start_dt
                        day_index = int(time_delta_from_start.total_seconds() // (24 * 3600))
                        day_index = min(max(0, day_index), num_days_for_calc - 1)
                        
                        base_gw_for_day = gw_daily_values[day_index] if len(gw_daily_values) > day_index else GW0
                        ereignis_effekt_total = 0
                        if day_index < len(regen_eff): ereignis_effekt_total += regen_eff[day_index]
                        if day_index < len(starkregen_eff): ereignis_effekt_total += starkregen_eff[day_index]
                        if day_index < len(schnee_eff): ereignis_effekt_total += schnee_eff[day_index]
                        
                        final_messwert = base_gw_for_day + ereignis_effekt_total + messstelle_offset
                        csv_writer.writerow([current_time.strftime('%d.%m.%Y %H:%M:%S'), f"{final_messwert:.3f}".replace('.',',')])
                        
                        if intervall_stunden == 0 and current_time == end_dt:
                            break
                        if intervall_stunden == 0 and start_dt == end_dt:
                            break

                        current_time += hourly_interval
                        values_created_count += 1
                        if values_created_count % 200 == 0:
                            update_progress(values_created_count)
            update_progress(total_values_to_generate)
            return f"CSV-Dateien gespeichert in: {save_path}"
        return "Unbekanntes Ausgabeformat"

    def start_generation_thread():
        # Deaktiviere Start-Button während der Generierung
        start_button.config(state=tk.DISABLED, text="Generiere...", bg=DISCORD_GRAY_TEXT)
        
        start_str = startdatum.get()
        end_str = enddatum.get()
        intervall_str = intervall_entry.get()
        messstellen_eingabe = messstellen_text.get("1.0", tk.END).strip()

        start_dt = parse_flexible_date(start_str)
        end_dt = parse_flexible_date(end_str)

        if not start_dt or not end_dt:
            messagebox.showerror("Fehler", "Bitte gültiges Start- und Enddatum eingeben (TT.MM.JJ).")
            reset_start_button()
            return
        if end_dt < start_dt:
            messagebox.showerror("Fehler", "Das Enddatum darf nicht vor dem Startdatum liegen.")
            reset_start_button()
            return
        try:
            intervall_stunden = float(intervall_str)
            if intervall_stunden < 0:
                raise ValueError("Intervall muss >= 0 sein.")
        except ValueError as e:
            messagebox.showerror("Fehler", f"Ungültiges Stundenintervall: {e}")
            reset_start_button()
            return

        is_valid_messstellen, messstellen_namen_or_error = validiere_messstellen(messstellen_eingabe)
        if not is_valid_messstellen:
            messagebox.showerror("Fehler bei Messstellen", messstellen_namen_or_error)
            reset_start_button()
            return
        if not messstellen_namen_or_error:
             messagebox.showerror("Fehler", "Keine Messstellen definiert.")
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
                messagebox.showinfo("Erfolg", status_message)
            except Exception as e:
                messagebox.showerror("Fehler bei Generierung", f"Ein Fehler ist aufgetreten:\n{e}")
                import traceback
                print(traceback.format_exc())
            finally:
                reset_start_button()

        thread = threading.Thread(target=generation_task)
        thread.daemon = True
        thread.start()

    def reset_start_button():
        start_button.config(state=tk.NORMAL, text="Start", bg=BUTTON_COLOR)
        progress['value'] = 0
        progress_info.config(text="0/0 Werte (0%)")

    # Hover-Effekte für Start-Button
    def on_start_enter(e):
        if start_button['state'] == tk.NORMAL:
            start_button.config(bg=BUTTON_HOVER)
    
    def on_start_leave(e):
        if start_button['state'] == tk.NORMAL:
            start_button.config(bg=BUTTON_COLOR)
    
    start_button.bind("<Enter>", on_start_enter)
    start_button.bind("<Leave>", on_start_leave)

    berechne_zeitspanne_und_werte()
    formel_anzeige_label.config(text=formel_params.generiere_formel_string())

    root.mainloop()

if __name__ == "__main__":
    if hasattr(sys, '_MEIPASS'):
        try:
            if os.name == 'nt':
                 ctypes.windll.kernel32.SetDllDirectoryW(None)
        except Exception as e:
            print(f"Info: Konnte SetDllDirectoryW nicht aufrufen: {e}")
    create_gui()
