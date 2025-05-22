import tkinter as tk
from tkinter import ttk
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
from PIL import Image, ImageTk, ImageDraw, ImageFont
import tksvg

# Verbesserte Farbpalette für konsistenten Darkmode
DISCORD_BG = "#36393F"
DISCORD_DARK = "#2F3136"
DISCORD_DARKER = "#202225"
DISCORD_TEXT = "#DCDDDE"
DISCORD_GRAY_TEXT = "#96989D"
DISCORD_GREEN = "#4ee56e"
DISCORD_INPUT_BG = "#40444B"
BUTTON_COLOR = "#4ee56e"
BUTTON_HOVER = "#3ac558"

# Angepasste DateEntry-Klasse für Darkmode
class DarkDateEntry(DateEntry):
    """
    Eine angepasste DateEntry-Klasse mit Darkmode-Styling.
    """
    def __init__(self, master=None, **kw):
        # Darkmode-Farbdefinitionen für den Kalender
        dark_colors = {
            'background': DISCORD_DARK,          # Haupthintergrund
            'foreground': DISCORD_TEXT,          # Haupttext
            'bordercolor': DISCORD_DARKER,       # Rahmenfarbe
            'headersbackground': DISCORD_DARKER, # Hintergrund der Kopfzeilen
            'headersforeground': DISCORD_TEXT,   # Text der Kopfzeilen
            'selectbackground': DISCORD_GREEN,   # Auswahlhintergrund
            'selectforeground': 'white',         # Auswahltext
            'normalbackground': DISCORD_DARK,    # Hintergrund normaler Tage
            'normalforeground': DISCORD_TEXT,    # Text normaler Tage
            'weekendbackground': DISCORD_DARKER, # Hintergrund am Wochenende
            'weekendforeground': DISCORD_TEXT,   # Text am Wochenende
            'othermonthbackground': '#2C2F33',   # Hintergrund anderer Monate
            'othermonthforeground': '#72767D'    # Text anderer Monate
        }
        
        # Parameter mit dark_colors erweitern
        for key, value in dark_colors.items():
            if key not in kw:
                kw[key] = value
        
        # Eingabefeld-Farben
        if 'background' not in kw:
            kw['background'] = DISCORD_DARK
        if 'foreground' not in kw:
            kw['foreground'] = DISCORD_TEXT
        if 'insertbackground' not in kw:
            kw['insertbackground'] = DISCORD_TEXT  # Cursor-Farbe
                
        # Super-Konstruktor mit Darkmode-Parametern aufrufen
        super().__init__(master, **kw)
        
        # Dropdown-Button anpassen (dieser wird nach der Initialisierung erstellt)
        for child in self.winfo_children():
            if child.winfo_class() == 'Button':
                child.configure(
                    background=DISCORD_DARK,
                    activebackground=DISCORD_GREEN,
                    foreground=DISCORD_TEXT,
                    activeforeground='white'
                )
        
        # Kalenderfenster konfigurieren, wenn es erstellt wird (bei Drop-down)
        self.bind("<<DateEntryPopup>>", self._style_calendar_popup)
    
    def _style_calendar_popup(self, event=None):
        """Style das Kalenderfenster, wenn es geöffnet wird"""
        if hasattr(self, '_top_cal'):
            self._top_cal.configure(background=DISCORD_DARKER)

            # Untergeordnete Widgets im Kalender anpassen
            for child in self._top_cal.winfo_children():
                if child.winfo_class() == 'Label':
                    child.configure(background=DISCORD_DARKER, foreground=DISCORD_TEXT)
                elif child.winfo_class() == 'Button':
                    child.configure(
                        background=DISCORD_DARK, 
                        foreground=DISCORD_TEXT,
                        activebackground=DISCORD_GREEN, 
                        activeforeground='white'
                    )

# Verbesserte DateEntry-Klasse mit deutscher Datumsanzeige und Autovervollständigung
class AutoDateEntry(DarkDateEntry):
    """
    Erweitert die DarkDateEntry-Klasse um deutsche Datumsanzeige und 
    automatische Formatierung im Format dd.mm.yy
    """
    def __init__(self, master=None, **kwargs):
        # Deutsches Datumsformat als Standard setzen
        kwargs['locale'] = 'de_DE'
        kwargs['date_pattern'] = 'dd.mm.yy'

        # Darkmode Stile für DateEntry
        style_options = {
            'background': DISCORD_INPUT_BG,
            'foreground': DISCORD_TEXT,
            'borderwidth': 0,
            # Weitere Styling-Optionen...
        }
        
        kwargs.update(style_options)
        
        # Super-Konstruktor aufrufen
        super().__init__(master, **kwargs)

        # Events binden
        self.bind("<KeyRelease>", self._format_date_entry)
        self.unbind("<FocusOut>")
        self.bind("<FocusOut>", self._smart_close_calendar)
        
        self.last_value = ""

    def _smart_close_calendar(self, event):
        """Schließt den Kalender nur, wenn nicht auf Navigationselemente geklickt wird"""
        if not hasattr(self, '_top_cal') or not self._top_cal.winfo_exists():
            return
            
        # Mausposition und Widget unter der Maus bestimmen
        x, y = self.winfo_pointerxy()
        widget_under_mouse = self.winfo_containing(x, y)
        
        # Prüfen, ob Widget Teil des Kalenders ist
        if widget_under_mouse:
            # Rekursiv nach oben durch die Widget-Hierarchie gehen
            parent = widget_under_mouse
            while parent:
                if parent == self._top_cal:
                    # Maus ist über Kalenderelement -> nicht schließen
                    return
                try:
                    parent = parent.master
                except:
                    break
                    
        # Wenn wir hier ankommen, ist die Maus nicht über dem Kalender
        self._top_cal.withdraw()


    def _format_date_entry(self, event):
        """Automatische Formatierung der Datumseingabe im Format dd.mm.yy"""
        if event.keysym in ('BackSpace', 'Delete', 'Left', 'Right', 'Up', 'Down'):
            self.last_value = self.get()
            return

        current = self.get()
        cursor_pos = self.index(tk.INSERT)

        # Entferne alle nicht-ziffern außer Punkten
        filtered = ''.join(c for c in current if c.isdigit() or c == '.')

        # Automatisches Einfügen von Punkten nach Tag und Monat
        parts = filtered.split('.')

        if len(parts) == 1 and parts[0]:
            # Tag eingeben
            if len(parts[0]) == 1 and parts[0].isdigit():
                if int(parts[0]) > 3:
                    # Wenn erste Ziffer größer als 3, füge führende Null hinzu
                    filtered = '0' + parts[0] + '.'
            elif len(parts[0]) == 2:
                day = int(parts[0])
                if 1 <= day <= 31:
                    filtered = parts[0] + '.'
                else:
                    self.delete(0, tk.END)
                    self.insert(0, self.last_value)
                    self.icursor(cursor_pos - 1)
                    return
        elif len(parts) == 2:
            # Tag und Monat eingeben
            day, month = parts
            if len(month) == 1 and month.isdigit():
                if int(month) > 1:
                    month = '0' + month
            if month and len(month) == 2:
                m = int(month)
                if not (1 <= m <= 12):
                    self.delete(0, tk.END)
                    self.insert(0, self.last_value)
                    self.icursor(cursor_pos - 1)
                    return
            filtered = day + '.' + month + '.'
        elif len(parts) == 3:
            # Tag, Monat und Jahr eingeben
            day, month, year = parts
            if len(year) > 2:
                year = year[-2:]
            filtered = day + '.' + month + '.' + year

        self.delete(0, tk.END)
        self.insert(0, filtered)
        self.icursor(len(filtered))
        self.last_value = filtered

# Dunkle Titelleiste für Windows
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

# Funktion für abgerundete Rechtecke
def create_rounded_rect(canvas, x1, y1, x2, y2, radius=15, **kwargs):
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
    return canvas.create_polygon(points, **kwargs, smooth=True)


# Die Formel-Parameter-Klasse (nur mit Grundwasser-Parametern)
class FormelParameter:
    def __init__(self):
        # Bestehende Parameter beibehalten
        self.GW0 = 10.0  # Grundniveau in Meter unter GOK
        self.A = 0.5     # Saisonale Amplitude
        self.T = 365     # Periodendauer in Tagen
        self.freq = 1.0  # Sinusfrequenz pro Periodendauer
        self.Da = 45     # Anstiegsdauer in Tagen
        self.Dd = 120    # Abklingdauer in Tagen
        self.R_scale = 0.05  # Skalierung für zufällige Schwankungen
        self.phase = 60      # Phasenverschiebung in Tagen
        self.trend = 0.0     # Langzeittrend pro Jahr in Meter
        
        # Neue Parameter für die gewünschten Funktionen
        self.curve_randomness = 0.2  # Variabilität der Wellenform (0-1)
        self.secondary_freq = 3.0    # Frequenz der überlagerten kleineren Wellen


    def generiere_formel(self):
        return (f"\n            Ganglinien Layout bearbeiten:\n")




# Funktion zur Berechnung der Grundwasserganglinie
def calculate_gw_series(t_array, GW0, A, T, freq, Da, Dd, R_scale, phase=60, trend=0.0, curve_randomness=0.2, secondary_freq=3.0):
    # Seed setzen für reproduzierbare Ergebnisse
    np.random.seed(42)
    
    # R_base analog zur Vorschau erstellen
    R_base = np.random.normal(0, 1, size=len(t_array))
    
    # Stellen Sie sicher, dass T nicht Null ist, um Division durch Null zu vermeiden
    if T == 0: T = 365 # Fallback-Wert
    
    # Amplitudenvariationen für jeden Wellenzyklus
    if curve_randomness > 0:
        amplitude_variation = 1.0 + curve_randomness * np.random.normal(0, 1, size=len(t_array))
        seasonal = A * np.sin(2 * np.pi * freq * (t_array - phase) / T) * amplitude_variation
    else:
        seasonal = A * np.sin(2 * np.pi * freq * (t_array - phase) / T)
    
    # Sekundäre kleinere Wellen hinzufügen
    if secondary_freq > 0:
        small_waves = A * 0.3 * np.sin(2 * np.pi * secondary_freq * freq * t_array / T)
        seasonal += small_waves
    
    # Trend-Komponente hinzufügen
    trend_component = trend * t_array / 365
    base_level = GW0 + seasonal + trend_component
    
    # Grundwasserstand initialisieren
    GW = np.zeros_like(t_array, dtype=float)
    if len(t_array) > 0:
        GW[0] = GW0 + seasonal[0]
        
        for i in range(1, len(t_array)):
            disturbance = R_scale * R_base[i]
            diff_from_GW0 = GW[i-1] - GW0
            daily_change = 0
            
            if disturbance > 0 and Da > 0:
                daily_change = (disturbance - diff_from_GW0) / Da
            elif Dd > 0:
                daily_change = -diff_from_GW0 / Dd
                
            GW[i] = GW[i-1] + daily_change
            GW[i] += seasonal[i] - seasonal[i-1]
    
    return GW


def create_csv_files(root, start_date, end_date, messstellen_ids, interval_hours, formel_params, progress, progress_info):
    hourly_interval = timedelta(hours=interval_hours)
    delta = end_date - start_date
    total_days = delta.days + 1
    # Die Anzahl der Stunden in der Zeitspanne
    total_hours = total_days * 24
    # Die Anzahl der Messwerte pro Messstelle basierend auf dem Intervall
    if interval_hours == 0: interval_hours = 1 # Fallback-Wert
    total_measurements_per_station = int(total_hours / interval_hours)
    total_values = total_measurements_per_station * len(messstellen_ids)

    # Zeit-Array für die Grundwasserberechnung (Tages-basiert)
    t_days_array = np.arange(0, total_days, 1)

    # Grundwasserganglinie basierend auf den Parametern berechnen
    try:

        grundwasser_series_daily = calculate_gw_series(
            t_days_array,
            formel_params.GW0,
            formel_params.A,
            formel_params.T,
            formel_params.freq,
            formel_params.Da,
            formel_params.Dd,
            formel_params.R_scale,
            formel_params.phase,
            formel_params.trend,
            formel_params.curve_randomness,
            formel_params.secondary_freq
        )




    except Exception as e:
        print(f"Fehler bei Grundwasserreihen-Berechnung: {e}")
        grundwasser_series_daily = np.full(total_days, formel_params.GW0)

    values_created = 0

    if hasattr(root, 'output_format') and root.output_format == "excel":
        all_data = {}

        for idx, messstelle_id in enumerate(messstellen_ids):
            data = []
            current_time = start_date

            while current_time <= end_date:
                # Berechnen Sie den Tag-Index basierend auf dem aktuellen Zeitpunkt
                days_since_start = (current_time.date() - start_date.date()).days
                tage_index = days_since_start

                # Der Hauptwert ist der Grundwasserstand für diesen Tag aus der berechneten Serie
                # Stellen Sie sicher, dass der Index gültig ist
                if 0 <= tage_index < len(grundwasser_series_daily):
                    basis_value = grundwasser_series_daily[tage_index]
                else:
                    # Fallback: Verwenden Sie das Grundniveau, wenn der Index ungültig ist (sollte nicht passieren)
                    basis_value = formel_params.GW0


                # Individualisierung pro Messstelle (Offset)
                messstellen_offset = (idx - len(messstellen_ids) / 2) * 1.02
                messwert = basis_value + messstellen_offset

                # Optional: Fügen Sie hier sehr kleine, stündliche Zufallsschwankungen hinzu,
                # die nicht Teil des täglichen GW-Modells sind, aber realistisches Rauschen simulieren.
                messwert += random.uniform(-formel_params.R_scale * 1.02, formel_params.R_scale * 1.02) # Beispiel


                # Datum als datetime-Objekt beibehalten für Excel
                data.append([messstelle_id, current_time, float(f'{messwert:.2f}')])

                current_time += hourly_interval
                values_created += 1

                # Fortschrittsbalken aktualisieren
                if values_created % 100 == 0:
                    progress['value'] = int((values_created / total_values) * 100)
                    progress_info.config(text=f"{values_created:,}/{total_values:,} Werte generiert ({progress['value']}%)".replace(',', '.'))
                    root.update_idletasks()

            # Speichern in Dictionary für Excel-Export
            all_data[messstelle_id] = data

        try:
            # Excel-Datei erstellen
            with pd.ExcelWriter('wasserstände_alle_messstellen.xlsx',
                            engine='xlsxwriter',
                            datetime_format='DD/MM/YYYY HH:MM') as writer:

                for messstelle_id, data in all_data.items():
                    # DataFrame erstellen
                    df = pd.DataFrame(data, columns=['GWMST Name', 'Datum/Uhrzeit', 'Messwert'])
                    # In Excel schreiben
                    # Beschränken Sie den Sheetnamen auf 31 Zeichen, da Excel-Limits gelten.
                    sheet_name = messstelle_id[:31] if len(messstelle_id) > 31 else messstelle_id
                    # Entfernen Sie ungültige Zeichen für Sheetnamen, falls vorhanden (Excel-Limitierungen beachten)
                    sheet_name = "".join([c for c in sheet_name if c.isalnum() or c in (' ', '_', '-')])
                     # Stellen Sie sicher, dass der Name nicht leer ist oder mit bestimmten Zeichen beginnt/endet
                    if not sheet_name or sheet_name[0] in ("'", "=") or any(char in sheet_name for char in ':\\/?*[]'):
                         sheet_name = f"Messstelle_{idx+1}" # Fallback Name


                    df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

                    # Formatierung anpassen
                    workbook = writer.book
                    worksheet = writer.sheets[sheet_name]

                    # Spaltenbreiten anpassen
                    worksheet.set_column(1, 1, 20)  # Datum/Uhrzeit-Spalte
                    worksheet.set_column(2, 2, 12)  # Messwert-Spalte

            progress['value'] = 100
            progress_info.config(text=f"{total_values:,}/{total_values:,} Werte generiert (100%)".replace(',', '.'))
            root.update_idletasks()
        except Exception as e:
            progress_info.config(text=f"Fehler beim Excel-Export: {str(e)}")
            print(f"Excel Export Error: {e}") # Zusätzliche Debug-Ausgabe
    else:
        # CSV-Export
        for idx, messstelle_id in enumerate(messstellen_ids):
            filename = f'wasserstände_{messstelle_id.replace(" ", "_")}.csv'

            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=';')
                csvwriter.writerow(['GWMST Name', 'Datum/Zeit', 'Messwert'])

                current_time = start_date

                while current_time <= end_date:
                    formatted_date = current_time.strftime("%d.%m.%Y %H:%M:%S")

                    days_since_start = (current_time.date() - start_date.date()).days
                    tage_index = days_since_start

                    # Der Hauptwert ist der Grundwasserstand für diesen Tag aus der berechneten Serie
                    # Stellen Sie sicher, dass der Index gültig ist
                    if 0 <= tage_index < len(grundwasser_series_daily):
                        basis_value = grundwasser_series_daily[tage_index]
                    else:
                        # Fallback: Verwenden Sie das Grundniveau, wenn der Index ungültig ist
                        basis_value = formel_params.GW0

                    # Individualisierung pro Messstelle (Offset)
                    messstellen_offset = (idx - len(messstellen_ids) / 2) * 0.02
                    messwert = basis_value + messstellen_offset

                    # Optional: Fügen Sie hier sehr kleine, stündliche Zufallsschwankungen hinzu
                    messwert += random.uniform(-formel_params.R_scale * 0.02, formel_params.R_scale * 0.02) # Beispiel


                    csvwriter.writerow([messstelle_id, formatted_date, f'{messwert:.2f}'.replace('.', ',')])

                    current_time += hourly_interval

                    values_created += 1
                    if values_created % 100 == 0:
                        progress['value'] = int((values_created / total_values) * 100)
                        progress_info.config(text=f"{values_created:,}/{total_values:,} Werte generiert ({progress['value']}%)".replace(',', '.'))
                        root.update_idletasks()

        progress['value'] = 100
        progress_info.config(text=f"{total_values:,}/{total_values:,} Werte generiert (100%)".replace(',', '.'))
        root.update_idletasks()


# Ladescreen-Funktion
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

    try:
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ribeka 55mm breit_white.png")
        original_logo = Image.open(logo_path)
        logo_width = 200
        aspect_ratio = original_logo.height / original_logo.width
        logo_height = int(logo_width * aspect_ratio)
        resized_logo = original_logo.resize((logo_width, logo_height), Image.LANCZOS)
        logo_img = ImageTk.PhotoImage(resized_logo)
        logo_img_global = logo_img
        logo_label = tk.Label(loading_window, image=logo_img, bg=DISCORD_DARKER)
        logo_label.image = logo_img
        logo_label.pack(pady=(60, 20))
    except Exception as e:
        print(f"Fehler beim Laden des Logos: {e}")
        tk.Label(loading_window, text="WaterGen", font=("Arial", 24, "bold"),
                fg=DISCORD_TEXT, bg=DISCORD_DARKER).pack(pady=(60, 20))

    loading_label = tk.Label(loading_window, text="Anwendung wird geladen...",
                           fg=DISCORD_TEXT, bg=DISCORD_DARKER, font=("Arial", 12))
    loading_label.pack(pady=10)

    progress = ttk.Progressbar(loading_window, orient="horizontal", length=300, mode="indeterminate")
    style = ttk.Style(loading_window)
    style.configure("TProgressbar", troughcolor=DISCORD_BG, background=DISCORD_GREEN)
    progress.pack(pady=20)
    progress.start(15)

    def close_loading():
        progress.stop()
        loading_window.destroy()

    loading_window.after(2000, close_loading)
    loading_window.mainloop()

def resource_path(relative_path):
    """Ermittelt den korrekten Pfad zu Ressourcen für PyInstaller und normale Python-Ausführung"""
    try:
        # PyInstaller erstellt einen temporären Ordner und speichert den Pfad in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Falls nicht in PyInstaller, verwende den aktuellen Verzeichnispfad
        base_path = os.path.abspath(os.path.dirname(__file__))
    
    return os.path.join(base_path, relative_path)


# GUI erstellen
def create_gui():
    show_loading_screen()
    root = tk.Tk()
    root.title("WaterGen")
    logo_path = resource_path("icon.ico")
    root.iconbitmap(logo_path)
    window_width = 620
    window_height = 700
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_pos = int((screen_width/2) - (window_width/2))
    y_pos = int((screen_height/2) - (window_height/2))
    root.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")
    set_dark_title_bar(root)
    root.configure(bg=DISCORD_BG)

   # Icon für Fenster und Taskleiste setzen
    try:
        root.iconbitmap(resource_path("icon.ico"))
        
        # Für Windows: Taskleisten-Icon konfigurieren
        try:
            from ctypes import windll
            app_id = "ribeka.watergen.app.1.0"  # Eindeutige ID für Ihre App
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except ImportError:
            pass  # Ignorieren, wenn nicht auf Windows
    except Exception as e:
        print(f"Fehler beim Setzen des Icons: {e}")



    # Logo oben rechts
    try:
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ribeka 55mm breit_white.png")
        original_logo = Image.open(logo_path)
        logo_width = 100
        aspect_ratio = original_logo.height / original_logo.width
        logo_height = int(logo_width * aspect_ratio)
        resized_logo = original_logo.resize((logo_width, logo_height), Image.LANCZOS)
        # Globale Referenz erstellen oder die Referenz dem Widget zuweisen
        logo_img = ImageTk.PhotoImage(resized_logo)
        logo_label = tk.Label(root, image=logo_img, bg=DISCORD_BG)
        logo_label.image = logo_img # Diese Zeile ist entscheidend!
        logo_label.place(relx=1, rely=0, anchor='ne', x=-10, y=10)
    except Exception as e:
        print(f"Fehler beim Laden des Logos: {e}")

    formel_params = FormelParameter() # Instanz der FormelParameter-Klasse

    root.minsize(620, 720)
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    container_frame = tk.Frame(root, bg=DISCORD_BG)
    container_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    container_frame.grid_rowconfigure(0, weight=1)
    container_frame.grid_columnconfigure(0, weight=1)

    content_frame = tk.Frame(container_frame, bg=DISCORD_BG)

    def center_content(event=None):
        width = container_frame.winfo_width()
        if width > 600:
            padding = (width - 600) // 2
            content_frame.grid_configure(padx=padding)
        else:
            content_frame.grid_configure(padx=0)

    content_frame.grid(row=0, column=0)
    container_frame.bind("<Configure>", center_content)

    main_frame = tk.Frame(content_frame, bg=DISCORD_BG, padx=15, pady=15)
    main_frame.pack(fill=tk.BOTH, expand=True)

    style = ttk.Style(root)
    style.configure("TProgressbar",
                   troughcolor=DISCORD_DARKER,
                   background=BUTTON_COLOR,
                   borderwidth=0)

    label_style = {"bg": DISCORD_DARK, "fg": DISCORD_TEXT, "font": ('Arial', 11)}
    entry_style = {"bg": DISCORD_INPUT_BG, "fg": DISCORD_TEXT, "insertbackground": DISCORD_TEXT,
                  "font": ('Arial', 11), "bd": 0, "relief": "flat"}


    # Header-Frame erstellen (bestehender Code)
    header_frame = tk.Frame(main_frame, bg=DISCORD_BG)
    header_frame.pack(fill=tk.X, pady=(0, 20))

    header_canvas = tk.Canvas(header_frame, bg=DISCORD_BG, height=100,
                            highlightthickness=0, width=580)
    header_canvas.pack(fill=tk.X)

    create_rounded_rect(header_canvas, 0, 0, 580, 100, radius=15,
                        fill=DISCORD_DARK, outline="")

    # WaterGen-Titel links platzieren
    header_label = tk.Label(header_canvas, text="WaterGen",
                        bg=DISCORD_DARK, fg=DISCORD_TEXT,
                        font=('Arial', 30, 'bold'))
    header_canvas.create_window(120, 50, window=header_label)  # X-Position weiter nach links

    # Ribeka-Logo als SVG-Code mit korrekter Formatierung
    svg_code = '''<?xml version="1.0" encoding="UTF-8"?>
    <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="200px" height="44px" viewBox="0 0 200 44" version="1.1">
    <g id="surface1">
    <path style=" stroke:none;fill-rule:nonzero;fill:rgb(100%,100%,100%);fill-opacity:1;" d="M 156.03125 0 C 170.539062 0 185.050781 0 200 0 C 200 14.519531 200 29.039062 200 44 C 185.488281 44 170.980469 44 156.03125 44 C 156.03125 42.183594 156.03125 40.371094 156.03125 38.5 C 167.015625 38.5 177.996094 38.5 189.3125 38.5 C 189.3125 36.886719 189.3125 35.273438 189.3125 33.609375 C 178.328125 33.609375 167.347656 33.609375 156.03125 33.609375 C 156.03125 22.519531 156.03125 11.429688 156.03125 0 Z M 156.03125 0 "/>
    <path style=" stroke:none;fill-rule:nonzero;fill:rgb(100%,100%,100%);fill-opacity:1;" d="M 0 34.222656 C 62.273438 34.222656 124.542969 34.222656 188.703125 34.222656 C 188.703125 35.433594 188.703125 36.640625 188.703125 37.890625 C 166.730469 38.140625 144.761719 38.238281 122.785156 38.226562 C 119.632812 38.226562 116.480469 38.222656 113.324219 38.222656 C 113.003906 38.222656 113.003906 38.222656 112.679688 38.222656 C 111.59375 38.222656 110.503906 38.222656 109.417969 38.222656 C 101.847656 38.222656 94.277344 38.21875 86.703125 38.21875 C 79.375 38.214844 72.050781 38.210938 64.722656 38.210938 C 64.492188 38.210938 64.265625 38.210938 64.03125 38.210938 C 61.734375 38.210938 59.441406 38.210938 57.148438 38.210938 C 52.480469 38.210938 47.8125 38.207031 43.144531 38.207031 C 42.820312 38.207031 42.820312 38.207031 42.492188 38.207031 C 28.328125 38.203125 14.164062 38.199219 0 38.195312 C 0 36.882812 0 35.574219 0 34.222656 Z M 0 34.222656 "/>
    <path style=" stroke:none;fill-rule:nonzero;fill:rgb(100%,100%,100%);fill-opacity:1;" d="M 45.191406 3.667969 C 46.085938 4.300781 46.644531 4.78125 46.839844 5.894531 C 46.867188 6.714844 46.851562 7.523438 46.8125 8.34375 C 46.800781 8.773438 46.800781 8.773438 46.792969 9.207031 C 46.773438 9.90625 46.75 10.605469 46.71875 11.304688 C 46.890625 11.304688 47.066406 11.300781 47.246094 11.296875 C 49.070312 11.269531 50.890625 11.25 52.714844 11.238281 C 53.394531 11.230469 54.074219 11.222656 54.753906 11.214844 C 55.730469 11.199219 56.710938 11.191406 57.691406 11.1875 C 57.992188 11.179688 58.292969 11.171875 58.605469 11.167969 C 60.699219 11.167969 62.386719 11.507812 63.976562 12.949219 C 65.960938 15.148438 65.753906 17.746094 65.746094 20.523438 C 65.746094 21.214844 65.75 21.90625 65.757812 22.59375 C 65.761719 23.039062 65.761719 23.484375 65.761719 23.925781 C 65.761719 24.328125 65.761719 24.726562 65.761719 25.136719 C 65.519531 27.558594 64.40625 28.925781 62.578125 30.480469 C 61.457031 31.203125 60.355469 31.207031 59.046875 31.214844 C 58.53125 31.21875 58.53125 31.21875 58.003906 31.226562 C 57.632812 31.226562 57.261719 31.226562 56.878906 31.230469 C 56.308594 31.230469 56.308594 31.230469 55.722656 31.234375 C 54.917969 31.238281 54.109375 31.238281 53.300781 31.238281 C 52.269531 31.242188 51.238281 31.25 50.203125 31.257812 C 49.214844 31.265625 48.230469 31.265625 47.242188 31.265625 C 46.871094 31.269531 46.5 31.273438 46.121094 31.277344 C 45.773438 31.277344 45.429688 31.277344 45.074219 31.277344 C 44.773438 31.277344 44.46875 31.277344 44.15625 31.277344 C 43.175781 31.140625 42.785156 31.011719 42.136719 30.25 C 42.015625 29.394531 41.96875 28.660156 41.980469 27.804688 C 41.976562 27.554688 41.976562 27.304688 41.972656 27.050781 C 41.96875 26.226562 41.972656 25.402344 41.976562 24.578125 C 41.972656 24.007812 41.972656 23.433594 41.972656 22.863281 C 41.96875 21.664062 41.972656 20.464844 41.976562 19.265625 C 41.984375 17.726562 41.980469 16.1875 41.972656 14.652344 C 41.96875 13.46875 41.972656 12.289062 41.972656 11.105469 C 41.976562 10.539062 41.972656 9.972656 41.972656 9.40625 C 41.96875 8.613281 41.972656 7.820312 41.980469 7.027344 C 41.976562 6.675781 41.976562 6.675781 41.972656 6.316406 C 41.996094 4.734375 41.996094 4.734375 42.703125 3.980469 C 43.621094 3.539062 44.179688 3.5 45.191406 3.667969 Z M 46.414062 15.890625 C 46.414062 19.417969 46.414062 22.945312 46.414062 26.582031 C 48.304688 26.613281 50.195312 26.636719 52.085938 26.652344 C 52.730469 26.65625 53.371094 26.664062 54.015625 26.675781 C 54.941406 26.691406 55.863281 26.699219 56.789062 26.703125 C 57.078125 26.710938 57.363281 26.714844 57.660156 26.722656 C 59.234375 26.726562 59.234375 26.726562 60.640625 26.082031 C 61.191406 25.152344 61.214844 24.546875 61.199219 23.46875 C 61.195312 23.105469 61.195312 22.742188 61.191406 22.367188 C 61.183594 21.988281 61.171875 21.609375 61.164062 21.21875 C 61.160156 20.835938 61.160156 20.457031 61.15625 20.066406 C 61.164062 18.097656 61.164062 18.097656 60.761719 16.195312 C 60.046875 15.835938 59.621094 15.851562 58.820312 15.855469 C 58.546875 15.855469 58.273438 15.855469 57.988281 15.855469 C 57.691406 15.855469 57.394531 15.859375 57.085938 15.859375 C 56.78125 15.859375 56.480469 15.859375 56.164062 15.859375 C 55.191406 15.863281 54.21875 15.867188 53.246094 15.871094 C 52.585938 15.871094 51.925781 15.871094 51.265625 15.875 C 49.648438 15.878906 48.03125 15.882812 46.414062 15.890625 Z M 46.414062 15.890625 "/>
    <path style=" stroke:none;fill-rule:nonzero;fill:rgb(100%,100%,100%);fill-opacity:1;" d="M 77.199219 11.210938 C 77.488281 11.207031 77.78125 11.203125 78.082031 11.195312 C 78.394531 11.195312 78.707031 11.195312 79.03125 11.191406 C 79.519531 11.1875 79.519531 11.1875 80.015625 11.183594 C 80.703125 11.179688 81.390625 11.175781 82.074219 11.175781 C 83.121094 11.171875 84.167969 11.15625 85.214844 11.140625 C 85.882812 11.136719 86.550781 11.136719 87.21875 11.136719 C 87.683594 11.125 87.683594 11.125 88.160156 11.117188 C 90.449219 11.132812 91.945312 11.679688 93.59375 13.285156 C 95.210938 15.105469 95.382812 16.765625 95.402344 19.097656 C 95.410156 19.355469 95.421875 19.613281 95.429688 19.875 C 95.433594 20.125 95.433594 20.375 95.4375 20.632812 C 95.445312 20.972656 95.445312 20.972656 95.449219 21.316406 C 95.136719 22.480469 94.738281 22.84375 93.742188 23.527344 C 92.398438 23.742188 91.074219 23.707031 89.71875 23.675781 C 89.328125 23.675781 88.933594 23.671875 88.53125 23.671875 C 87.496094 23.664062 86.460938 23.648438 85.425781 23.632812 C 84.367188 23.617188 83.308594 23.609375 82.25 23.601562 C 80.175781 23.585938 78.105469 23.558594 76.03125 23.527344 C 76.132812 24.433594 76.230469 25.34375 76.335938 26.277344 C 76.734375 26.28125 77.132812 26.285156 77.546875 26.285156 C 79.027344 26.296875 80.507812 26.320312 81.992188 26.339844 C 82.632812 26.351562 83.273438 26.355469 83.914062 26.359375 C 84.839844 26.367188 85.761719 26.382812 86.683594 26.398438 C 86.96875 26.398438 87.253906 26.398438 87.550781 26.398438 C 88.835938 26.425781 89.589844 26.476562 90.714844 27.140625 C 91.296875 27.804688 91.296875 27.804688 91.488281 28.875 C 91.296875 29.945312 91.296875 29.945312 90.714844 30.613281 C 89.371094 31.402344 88.222656 31.335938 86.691406 31.316406 C 86.246094 31.320312 86.246094 31.320312 85.789062 31.320312 C 85.160156 31.320312 84.53125 31.316406 83.902344 31.308594 C 82.945312 31.300781 81.988281 31.304688 81.027344 31.308594 C 80.414062 31.304688 79.804688 31.300781 79.191406 31.300781 C 78.90625 31.300781 78.621094 31.300781 78.328125 31.300781 C 76.621094 31.277344 75.417969 31.035156 73.894531 30.25 C 73.894531 30.046875 73.894531 29.847656 73.894531 29.640625 C 73.707031 29.558594 73.519531 29.476562 73.324219 29.390625 C 72.46875 28.914062 72.09375 28.320312 71.6875 27.441406 C 71.195312 25.660156 71.285156 23.785156 71.308594 21.945312 C 71.316406 21.21875 71.3125 20.488281 71.308594 19.757812 C 71.3125 19.289062 71.316406 18.820312 71.316406 18.351562 C 71.316406 18.136719 71.316406 17.921875 71.316406 17.699219 C 71.347656 15.957031 71.714844 14.492188 72.878906 13.160156 C 73.058594 13.023438 73.234375 12.882812 73.417969 12.738281 C 73.59375 12.59375 73.769531 12.449219 73.949219 12.300781 C 75.042969 11.542969 75.859375 11.230469 77.199219 11.210938 Z M 76.410156 16.222656 C 75.835938 16.988281 75.835938 16.988281 76.03125 18.945312 C 80.867188 18.945312 85.703125 18.945312 90.6875 18.945312 C 90.796875 17.269531 90.796875 17.269531 90.40625 16.394531 C 89.355469 15.558594 88.214844 15.722656 86.910156 15.738281 C 86.628906 15.738281 86.347656 15.738281 86.054688 15.734375 C 85.460938 15.738281 84.867188 15.738281 84.273438 15.746094 C 83.363281 15.753906 82.453125 15.753906 81.542969 15.75 C 80.964844 15.75 80.386719 15.753906 79.808594 15.757812 C 79.535156 15.753906 79.261719 15.753906 78.980469 15.753906 C 78.601562 15.757812 78.601562 15.757812 78.214844 15.765625 C 77.992188 15.765625 77.765625 15.769531 77.539062 15.769531 C 76.929688 15.855469 76.929688 15.855469 76.410156 16.222656 Z M 76.410156 16.222656 "/>
    <path style=" stroke:none;fill-rule:nonzero;fill:rgb(100%,100%,100%);fill-opacity:1;" d="M 134.269531 11.144531 C 134.707031 11.140625 134.707031 11.140625 135.152344 11.140625 C 135.765625 11.140625 136.378906 11.140625 136.996094 11.144531 C 137.929688 11.152344 138.867188 11.144531 139.800781 11.136719 C 140.402344 11.140625 141 11.140625 141.597656 11.144531 C 141.875 11.140625 142.152344 11.136719 142.4375 11.136719 C 144.558594 11.167969 146.269531 11.628906 147.804688 13.148438 C 147.941406 13.355469 148.082031 13.558594 148.226562 13.769531 C 148.371094 13.972656 148.515625 14.179688 148.664062 14.390625 C 149.230469 15.34375 149.355469 16.144531 149.371094 17.230469 C 149.375 17.5 149.382812 17.773438 149.386719 18.050781 C 149.398438 19.28125 149.414062 20.515625 149.417969 21.75 C 149.425781 22.398438 149.433594 23.050781 149.445312 23.699219 C 149.460938 24.636719 149.46875 25.574219 149.472656 26.515625 C 149.480469 26.804688 149.488281 27.09375 149.492188 27.394531 C 149.488281 28.675781 149.417969 29.453125 148.78125 30.585938 C 147.210938 31.5 145.691406 31.371094 143.90625 31.347656 C 143.527344 31.347656 143.148438 31.347656 142.757812 31.347656 C 141.75 31.347656 140.742188 31.335938 139.738281 31.324219 C 139.125 31.320312 138.507812 31.320312 137.894531 31.320312 C 136.710938 31.320312 135.527344 31.316406 134.34375 31.308594 C 133.796875 31.308594 133.796875 31.308594 133.238281 31.308594 C 131.03125 31.277344 129.316406 31.183594 127.589844 29.679688 C 126.183594 27.988281 125.328125 26.777344 125.402344 24.480469 C 125.695312 22.472656 126.800781 21.160156 128.339844 19.929688 C 129.398438 19.15625 129.945312 18.867188 131.25 18.875 C 131.699219 18.875 131.699219 18.875 132.15625 18.875 C 132.476562 18.878906 132.800781 18.882812 133.132812 18.882812 C 133.464844 18.886719 133.796875 18.886719 134.136719 18.886719 C 135.195312 18.890625 136.25 18.898438 137.308594 18.90625 C 138.027344 18.910156 138.742188 18.910156 139.460938 18.914062 C 141.21875 18.921875 142.976562 18.929688 144.734375 18.945312 C 144.632812 17.410156 144.632812 17.410156 143.816406 16.195312 C 142.890625 16.132812 141.988281 16.109375 141.0625 16.109375 C 140.5 16.105469 139.9375 16.097656 139.371094 16.09375 C 138.484375 16.085938 137.59375 16.078125 136.703125 16.078125 C 135.847656 16.074219 134.992188 16.066406 134.132812 16.054688 C 133.734375 16.054688 133.734375 16.054688 133.328125 16.058594 C 131.492188 16.027344 131.492188 16.027344 130.519531 15.335938 C 129.867188 14.351562 129.910156 13.679688 130.078125 12.527344 C 131.121094 10.921875 132.535156 11.128906 134.269531 11.144531 Z M 130.4375 24.097656 C 129.976562 24.753906 129.976562 24.753906 130.285156 25.570312 C 130.621094 26.316406 130.621094 26.316406 131.296875 26.582031 C 131.730469 26.609375 132.164062 26.621094 132.601562 26.617188 C 132.871094 26.617188 133.136719 26.617188 133.414062 26.617188 C 133.707031 26.617188 133.996094 26.613281 134.296875 26.613281 C 134.59375 26.613281 134.890625 26.613281 135.199219 26.613281 C 136.148438 26.609375 137.101562 26.605469 138.054688 26.601562 C 138.699219 26.601562 139.34375 26.597656 139.988281 26.597656 C 141.570312 26.59375 143.152344 26.589844 144.734375 26.582031 C 144.734375 25.574219 144.734375 24.566406 144.734375 23.527344 C 142.792969 23.496094 140.851562 23.476562 138.914062 23.460938 C 138.253906 23.453125 137.59375 23.445312 136.933594 23.4375 C 135.984375 23.421875 135.035156 23.414062 134.085938 23.410156 C 133.792969 23.402344 133.496094 23.394531 133.191406 23.390625 C 132.917969 23.390625 132.640625 23.390625 132.359375 23.390625 C 132.117188 23.386719 131.875 23.382812 131.625 23.378906 C 130.9375 23.480469 130.9375 23.480469 130.4375 24.097656 Z M 130.4375 24.097656 "/>
    <path style=" stroke:none;fill-rule:nonzero;fill:rgb(100%,100%,100%);fill-opacity:1;" d="M 104.121094 3.667969 C 104.78125 4.082031 104.78125 4.082031 105.34375 4.890625 C 105.535156 5.972656 105.527344 7.050781 105.53125 8.148438 C 105.539062 8.625 105.539062 8.625 105.542969 9.109375 C 105.558594 10.121094 105.566406 11.132812 105.574219 12.144531 C 105.582031 12.832031 105.589844 13.519531 105.601562 14.203125 C 105.621094 15.886719 105.636719 17.566406 105.648438 19.25 C 107.816406 17.875 109.964844 16.484375 112.070312 15.015625 C 112.597656 14.652344 113.125 14.289062 113.652344 13.925781 C 114.007812 13.679688 114.363281 13.425781 114.71875 13.175781 C 115.246094 12.804688 115.773438 12.441406 116.304688 12.078125 C 116.613281 11.863281 116.921875 11.648438 117.238281 11.425781 C 118.40625 10.890625 119.070312 10.992188 120.304688 11.304688 C 120.917969 11.800781 120.917969 11.800781 121.222656 12.527344 C 121.316406 13.519531 121.316406 13.519531 120.917969 14.667969 C 119.34375 16.292969 117.386719 17.460938 115.429688 18.570312 C 114.769531 18.933594 114.769531 18.933594 114.199219 19.554688 C 114.371094 19.726562 114.546875 19.894531 114.722656 20.070312 C 116.042969 21.375 117.324219 22.691406 118.523438 24.109375 C 118.941406 24.585938 119.375 25.050781 119.816406 25.507812 C 121.980469 27.769531 121.980469 27.769531 122.25 28.96875 C 122.136719 29.945312 122.136719 29.945312 121.527344 30.859375 C 120.609375 31.472656 120.609375 31.472656 119.5625 31.53125 C 118.136719 31.054688 117.597656 30.480469 116.640625 29.332031 C 116.640625 29.132812 116.640625 28.929688 116.640625 28.722656 C 116.441406 28.722656 116.238281 28.722656 116.03125 28.722656 C 115.632812 28.328125 115.632812 28.328125 115.152344 27.75 C 114.109375 26.515625 113.027344 25.324219 111.925781 24.140625 C 111.761719 23.960938 111.59375 23.78125 111.421875 23.59375 C 111.027344 23.164062 110.628906 22.734375 110.230469 22.304688 C 109.085938 22.949219 107.972656 23.574219 106.925781 24.367188 C 105.953125 25.054688 105.953125 25.054688 105.34375 25.054688 C 105.351562 25.398438 105.359375 25.738281 105.363281 26.09375 C 105.371094 26.542969 105.375 26.992188 105.382812 27.441406 C 105.386719 27.667969 105.390625 27.894531 105.398438 28.125 C 105.40625 29.304688 105.402344 29.855469 104.734375 30.859375 C 102.636719 31.335938 102.636719 31.335938 101.546875 30.804688 C 100.554688 29.652344 100.71875 28.234375 100.71875 26.78125 C 100.71875 26.558594 100.71875 26.332031 100.714844 26.101562 C 100.714844 25.363281 100.710938 24.621094 100.710938 23.882812 C 100.710938 23.367188 100.710938 22.851562 100.710938 22.335938 C 100.707031 21.257812 100.707031 20.175781 100.707031 19.097656 C 100.707031 17.714844 100.703125 16.332031 100.699219 14.949219 C 100.695312 13.886719 100.695312 12.824219 100.695312 11.757812 C 100.691406 11.25 100.691406 10.738281 100.691406 10.230469 C 100.6875 9.515625 100.6875 8.804688 100.6875 8.089844 C 100.6875 7.882812 100.6875 7.671875 100.683594 7.457031 C 100.691406 6.265625 100.800781 5.328125 101.375 4.277344 C 102.441406 3.566406 102.867188 3.511719 104.121094 3.667969 Z M 104.121094 3.667969 "/>
    <path style=" stroke:none;fill-rule:nonzero;fill:rgb(100%,100%,100%);fill-opacity:1;" d="M 2.621094 11.152344 C 3.03125 11.148438 3.03125 11.148438 3.453125 11.144531 C 3.75 11.148438 4.042969 11.152344 4.347656 11.152344 C 4.65625 11.152344 4.960938 11.152344 5.273438 11.152344 C 5.921875 11.152344 6.566406 11.15625 7.214844 11.164062 C 8.199219 11.171875 9.1875 11.167969 10.171875 11.164062 C 10.800781 11.167969 11.429688 11.167969 12.058594 11.171875 C 12.5 11.171875 12.5 11.171875 12.949219 11.171875 C 15.023438 11.199219 16.34375 11.535156 17.917969 12.96875 C 19.40625 14.613281 19.957031 15.769531 19.847656 18.027344 C 19.410156 18.984375 19.410156 18.984375 18.625 19.554688 C 17.707031 19.761719 17.152344 19.695312 16.183594 19.554688 C 15.160156 18.671875 14.890625 17.457031 14.351562 16.195312 C 11.125 16.09375 7.902344 15.992188 4.582031 15.890625 C 4.597656 16.863281 4.617188 17.839844 4.632812 18.84375 C 4.644531 19.789062 4.65625 20.734375 4.664062 21.679688 C 4.671875 22.335938 4.683594 22.992188 4.695312 23.648438 C 4.714844 24.59375 4.722656 25.539062 4.730469 26.480469 C 4.738281 26.773438 4.746094 27.066406 4.753906 27.371094 C 4.753906 28.796875 4.742188 29.425781 3.847656 30.59375 C 3.054688 31.167969 3.054688 31.167969 2.390625 31.28125 C 1.792969 31.167969 1.199219 31.015625 0.609375 30.859375 C -0.078125 29.828125 -0.078125 29.46875 -0.0898438 28.261719 C -0.09375 27.917969 -0.0976562 27.570312 -0.101562 27.214844 C -0.101562 26.84375 -0.101562 26.472656 -0.101562 26.089844 C -0.105469 25.707031 -0.105469 25.324219 -0.109375 24.929688 C -0.113281 24.121094 -0.113281 23.3125 -0.113281 22.5 C -0.113281 21.464844 -0.121094 20.429688 -0.132812 19.394531 C -0.140625 18.402344 -0.140625 17.414062 -0.140625 16.425781 C -0.144531 16.054688 -0.148438 15.679688 -0.152344 15.296875 C -0.152344 14.953125 -0.148438 14.605469 -0.148438 14.25 C -0.148438 13.945312 -0.148438 13.644531 -0.152344 13.328125 C 0.144531 11.761719 1.085938 11.152344 2.621094 11.152344 Z M 2.621094 11.152344 "/>
    <path style=" stroke:none;fill-rule:nonzero;fill:rgb(100%,100%,100%);fill-opacity:1;" d="M 26.105469 11.144531 C 26.429688 11.140625 26.75 11.140625 27.082031 11.136719 C 27.414062 11.144531 27.746094 11.148438 28.089844 11.152344 C 28.59375 11.144531 28.59375 11.144531 29.101562 11.136719 C 29.425781 11.140625 29.746094 11.140625 30.078125 11.144531 C 30.515625 11.144531 30.515625 11.144531 30.964844 11.148438 C 31.753906 11.304688 31.753906 11.304688 32.464844 11.726562 C 33.277344 12.996094 33.128906 14.246094 33.097656 15.722656 C 33.09375 16.03125 33.09375 16.34375 33.089844 16.660156 C 33.085938 17.652344 33.070312 18.640625 33.054688 19.632812 C 33.046875 20.304688 33.042969 20.976562 33.035156 21.648438 C 33.023438 23.292969 33.003906 24.9375 32.976562 26.582031 C 33.230469 26.574219 33.484375 26.566406 33.742188 26.558594 C 34.242188 26.550781 34.242188 26.550781 34.746094 26.542969 C 35.074219 26.535156 35.402344 26.527344 35.742188 26.519531 C 36.640625 26.582031 36.640625 26.582031 37.632812 27.25 C 38.167969 28.109375 38.167969 28.109375 38.359375 28.875 C 38.074219 30.019531 37.558594 30.441406 36.640625 31.167969 C 35.738281 31.382812 34.867188 31.375 33.941406 31.359375 C 33.554688 31.359375 33.554688 31.359375 33.15625 31.359375 C 32.613281 31.359375 32.066406 31.355469 31.523438 31.347656 C 30.691406 31.339844 29.859375 31.34375 29.027344 31.347656 C 28.496094 31.347656 27.964844 31.34375 27.433594 31.339844 C 27.0625 31.34375 27.0625 31.34375 26.683594 31.34375 C 25.484375 31.320312 24.859375 31.242188 23.8125 30.613281 C 23.207031 29.945312 23.207031 29.945312 23.015625 28.875 C 23.207031 27.804688 23.207031 27.804688 23.742188 27.0625 C 24.734375 26.582031 24.734375 26.582031 28.398438 26.582031 C 28.398438 23.054688 28.398438 19.523438 28.398438 15.890625 C 27.1875 15.890625 25.980469 15.890625 24.734375 15.890625 C 23.742188 15.238281 23.742188 15.238281 23.207031 14.359375 C 23.035156 13.425781 23.035156 13.425781 23.207031 12.527344 C 24.097656 11.394531 24.679688 11.148438 26.105469 11.144531 Z M 26.105469 11.144531 "/>
    <path style=" stroke:none;fill-rule:nonzero;fill:rgb(100%,100%,100%);fill-opacity:1;" d="M 31.296875 3.609375 C 32.367188 3.972656 32.367188 3.972656 32.976562 4.582031 C 33.238281 5.667969 33.445312 6.597656 32.976562 7.640625 C 32.246094 8.457031 31.59375 8.636719 30.535156 8.707031 C 29.535156 8.667969 29.351562 8.589844 28.550781 7.90625 C 28.007812 6.863281 27.875 6.351562 28.089844 5.195312 C 29.734375 3.246094 29.734375 3.246094 31.296875 3.609375 Z M 31.296875 3.609375 "/>
    </g>
    </svg>
    '''

    # SVG-Logo erstellen
    # Logo-Pfad mit resource_path Funktion ermitteln
    logo_path = resource_path("ribeka 55mm breit_white.png")

    try:
        original_logo = Image.open(logo_path)
        logo_width = 200
        aspect_ratio = original_logo.height / original_logo.width
        logo_height = int(logo_width * aspect_ratio)
        resized_logo = original_logo.resize((logo_width, logo_height), Image.LANCZOS)
        logo_img = ImageTk.PhotoImage(resized_logo)
        logo_img_global = logo_img
        
        # Logo-Label erstellen
        logo_label = tk.Label(header_canvas, image=logo_img, bg=DISCORD_DARK)
        logo_label.image = logo_img
        header_canvas.create_window(420, 50, window=logo_label)
    except Exception as e:
        print(f"Fehler beim Laden des Logos: {e}")
        # Fallback zur Text-Version
        logo_frame = tk.Frame(header_canvas, bg=DISCORD_DARK)
        logo_label = tk.Label(logo_frame, text="ribeka", 
                            bg=DISCORD_DARK, fg=DISCORD_TEXT,
                            font=('Arial', 35, 'bold'))
        logo_label.pack()
        
        # Unterstrich hinzufügen
        underline = tk.Frame(logo_frame, height=3, bg=DISCORD_TEXT)
        underline.pack(fill=tk.X, pady=(0, 5))
        
        header_canvas.create_window(420, 50, window=logo_frame)


    # 1. Zeitspanne und Intervall
    zeitspan_frame = tk.Frame(main_frame, bg=DISCORD_BG)
    zeitspan_frame.pack(fill=tk.X, pady=(0, 10))

    zeitspan_canvas = tk.Canvas(zeitspan_frame, bg=DISCORD_BG, height=100,
                              highlightthickness=0, width=580)
    zeitspan_canvas.pack(fill=tk.X)

    create_rounded_rect(zeitspan_canvas, 0, 0, 580, 100, radius=15,
                       fill=DISCORD_DARK, outline="")

    zeitspanne_label = tk.Label(zeitspan_canvas, text="Zeitspanne", **label_style)
    zeitspan_canvas.create_window(20, 30, window=zeitspanne_label, anchor="w")

    # Nur width angeben, keine anderen Style-Parameter überschreiben
    startdatum = AutoDateEntry(zeitspan_canvas, width=12)
    zeitspan_canvas.create_window(170, 30, window=startdatum)

    zeitspanne_anzeige = tk.Label(zeitspan_canvas, text="0 Jahre, 0 Monate, 0 Tage",
                                **label_style, width=25)
    zeitspan_canvas.create_window(340, 30, window=zeitspanne_anzeige)

    # Nur width angeben, keine anderen Style-Parameter überschreiben
    enddatum = AutoDateEntry(zeitspan_canvas, width=12)
    zeitspan_canvas.create_window(500, 30, window=enddatum)

    intervall_label = tk.Label(zeitspan_canvas, text="Intervall (Stunden)", **label_style)
    zeitspan_canvas.create_window(20, 70, window=intervall_label, anchor="w")

    intervall_entry = tk.Entry(zeitspan_canvas, width=10, **entry_style)
    intervall_entry.insert(0, "1")
    zeitspan_canvas.create_window(200, 70, window=intervall_entry)


    def parse_flexible_date(date_string):
        """Parst deutsches Datum flexibel mit 2- oder 4-stelligem Jahr"""
        try:
            # Erst mit 2-stelligem Jahr versuchen
            return datetime.strptime(date_string, '%d.%m.%y')
        except ValueError:
            try:
                # Dann mit 4-stelligem Jahr versuchen
                return datetime.strptime(date_string, '%d.%m.%Y')
            except ValueError:
                raise ValueError("Ungültiges Datumsformat. Bitte TT.MM.JJ oder TT.MM.JJJJ verwenden.")

    def berechne_zeitspanne():
        try:
            start = parse_flexible_date(startdatum.get())
            end = parse_flexible_date(enddatum.get())
            delta = end - start
            jahre = delta.days // 365
            monate = (delta.days % 365) // 30
            tage = (delta.days % 365) % 30
            zeitspanne_anzeige.config(text=f"{jahre} Jahre, {monate} Monate, {tage} Tage")
            berechne_werte_anzahl()
        except:
            zeitspanne_anzeige.config(text="Ungültiges Datum")

    def berechne_werte_anzahl():
        try:
            start_str = startdatum.get()
            end_str = enddatum.get()
            # Verwenden Sie parse_flexible_date für Robustheit
            start = parse_flexible_date(start_str)
            end = parse_flexible_date(end_str)

            delta = end - start
            # Addiere 1, um den Endtag einzuschließen, falls der Endzeitpunkt am Ende des Tages liegt
            # Für die Anzahl der Intervalle über die Zeitspanne ist die Differenz wichtiger.
            # Die Anzahl der Tage für die GW-Serie ist delta.days + 1, wenn Start und Enddatum gleich sind (1 Tag).
            # Bei 1 Tag, 24h Intervall = 24 Messwerte.
            # Bei 2 Tagen (Start 01.01, End 02.01), 24h Intervall = 48 Messwerte.
            # Anzahl der Stunden: (end - start).total_seconds() / 3600
            total_hours = int(delta.total_seconds() / 3600) # Gesamtzahl der vollen Stunden

            stunden_intervall_str = intervall_entry.get()
            if not stunden_intervall_str:
                 raise ValueError("Intervall darf nicht leer sein.")
            try:
                 stunden_intervall = float(stunden_intervall_str)
            except ValueError:
                 raise ValueError("Intervall muss eine Zahl sein.")


            if stunden_intervall <= 0:
                 werte_info.config(text="Fehler: Intervall > 0")
                 return 0

            # Anzahl der Messwerte pro Messstelle
            # Messpunkte sind am Startdatum + n * Intervall, bis <= Enddatum
            # Die Anzahl ist (Endzeit - Startzeit) / Intervall + 1 (für den Startpunkt)
            # Bei End=Start, Intervall=1h: (0)/1 + 1 = 1 Punkt? Nein, das erste Intervall ist nach 1h.
            # Anzahl der Intervalle = total_hours / stunden_intervall
            # Anzahl der Punkte = Anzahl Intervalle + 1
            # Beispiel: Start 0:00, End 2:00, Intervall 1h. Punkte: 0:00, 1:00, 2:00. = 3 Punkte.
            # total_hours = 2. 2/1 = 2 Intervalle. 2+1 = 3 Punkte.
            # Wenn Enddatum = Startdatum, 0 Stunden, 0/1 + 1 = 1 Punkt. Falsch. Es sind 24h.
            # Anzahl Stunden in der Zeitspanne = (end + 1 Tag) - start, in Stunden.
            # total_hours_span = (end + timedelta(days=1) - start).total_seconds() / 3600 # Das würde bis zum Ende des Endtages gehen
            # Besser: Dauer in Sekunden, geteilt durch Intervall in Sekunden.
            duration_seconds = (end - start).total_seconds()
            interval_seconds = stunden_intervall * 3600

            if interval_seconds <= 0:
                 werte_info.config(text="Fehler: Intervall > 0")
                 return 0

            # Anzahl der Messpunkte = floor(Dauer / Intervall) + 1 (inklusive Startpunkt)
            messwerte_pro_messstelle = math.floor(duration_seconds / interval_seconds) + 1

            # Messstellen-Text holen ohne zu validieren
            messstellen_text_inhalt = messstellen_text.get("1.0", tk.END).strip()
            
            messstellen = [m.strip() for m in messstellen_text_inhalt.split(';') if m.strip()]
            messstellenanzahl = len(messstellen)
            gesamt_werte = messwerte_pro_messstelle * messstellenanzahl
            werte_info.config(text=f"Zu generierende Werte: {gesamt_werte:,}".replace(',', '.'))
            return gesamt_werte
        except Exception as e:
            # print(f"Fehler bei Werteanzahl: {e}") # Debugging
            werte_info.config(text="Zu generierende Werte: Berechnung nicht möglich")
            return 0

    startdatum.bind("<FocusOut>", lambda e: berechne_zeitspanne())
    startdatum.bind("<FocusOut>", lambda e: berechne_zeitspanne())
    enddatum.bind("<FocusOut>", lambda e: berechne_zeitspanne())
    intervall_entry.bind("<FocusOut>", lambda e: berechne_werte_anzahl())

    # 2. Messstellen
    messstellen_frame = tk.Frame(main_frame, bg=DISCORD_BG)
    messstellen_frame.pack(fill=tk.X, pady=(0, 10))

    messstellen_canvas = tk.Canvas(messstellen_frame, bg=DISCORD_BG, height=120,
                                 highlightthickness=0, width=580)
    messstellen_canvas.pack(fill=tk.X)

    create_rounded_rect(messstellen_canvas, 0, 0, 580, 120, radius=15,
                       fill=DISCORD_DARK, outline="")

    messstellen_label = tk.Label(messstellen_canvas, text="Messstellen:",
                               **label_style)
    messstellen_canvas.create_window(20, 30, window=messstellen_label, anchor="w")

    # Mehrzeiliges Textfeld für Messstellen
    messstellen_text = tk.Text(messstellen_canvas, height=3, width=45, **entry_style)
    messstellen_canvas.create_window(290, 50, window=messstellen_text)

    # Hilfetext unter dem Textfeld
    help_label = tk.Label(messstellen_canvas, text="Namen mit einem Semikolon trennen",
                        fg=DISCORD_GRAY_TEXT, bg=DISCORD_DARK, font=('Arial', 9))
    messstellen_canvas.create_window(290, 100, window=help_label)

    # Event für Texteingabe
    messstellen_text.bind("<FocusOut>", lambda e: berechne_werte_anzahl())

    def validiere_messstellen(messstellen_text):
        """Prüft, ob doppelte Messstellennamen vorhanden sind"""
        if not messstellen_text.strip():
            return False, "Keine Messstellen angegeben"

        messstellen = [m.strip() for m in messstellen_text.split(';') if m.strip()]
        if not messstellen:
            return False, "Keine gültigen Messstellen angegeben"

        # Duplikate prüfen
        duplicates = set()
        seen = set()
        for m in messstellen:
            if m in seen:
                duplicates.add(m)
            else:
                seen.add(m)

        if duplicates:
            return False, f"Doppelte Messstellennamen gefunden: {', '.join(duplicates)}"

        return True, messstellen

    # 3. Formel (anzeige der verwendeten Parameter)
    formel_frame = tk.Frame(main_frame, bg=DISCORD_BG)
    formel_frame.pack(fill=tk.X, pady=(0, 10))

    formel_canvas = tk.Canvas(formel_frame, bg=DISCORD_BG, height=60,
                            highlightthickness=0, width=580)
    formel_canvas.pack(fill=tk.X)

    create_rounded_rect(formel_canvas, 0, 0, 580, 60, radius=15,
                       fill=DISCORD_DARK, outline="")

    # Zeige die Parameter-Beschreibung anstelle einer Formel-String
    formel_label = tk.Label(formel_canvas, text=formel_params.generiere_formel(),
                          **label_style, width=65, anchor="w")
    formel_canvas.create_window(270, 30, window=formel_label)

    def open_formel_submenu():
        if hasattr(root, 'submenu_open') and root.submenu_open:
            return

        root.submenu_open = True
        submenu = tk.Toplevel(root)
        submenu.title("Formel-Einstellungen")

        submenu_width = 1050
        submenu_height = 600
        sub_x_pos = int((screen_width/2) - (submenu_width/2))
        sub_y_pos = int((screen_height/2) - (submenu_height/2))
        submenu.geometry(f"{submenu_width}x{submenu_height}+{sub_x_pos}+{sub_y_pos}")

        submenu.minsize(submenu_width, submenu_height)
        submenu.configure(bg=DISCORD_BG)
        set_dark_title_bar(submenu)

        main_submenu_frame = tk.Frame(submenu, bg=DISCORD_BG, padx=20, pady=20)
        main_submenu_frame.pack(fill=tk.BOTH, expand=True)

        parameter_frame = tk.Frame(main_submenu_frame, bg=DISCORD_BG)
        parameter_frame.grid(row=0, column=0, sticky="nw", padx=(0, 20))

        graph_frame = tk.Frame(main_submenu_frame, bg=DISCORD_BG)
        graph_frame.grid(row=0, column=1, sticky="ne")

        # Titel
        title_label = tk.Label(parameter_frame, text="Grundwasserganglinie anpassen",
                            bg=DISCORD_BG, fg=DISCORD_TEXT, font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky="w")

        # Parameter für Grundwasserganglinie für die Plot-Vorschau
        # t und R_base für die Plot-Vorschau im Submenü
        np.random.seed(42) # Konsistenter Seed für die Submenü-Vorschau
        t_preview = np.arange(0, 365, 1) # Vorschau für 365 Tage
        R_base_preview = np.random.normal(0, 1, size=len(t_preview))


        # Funktion zur Berechnung der Grundwasserganglinie für die Plot-Vorschau
        def calculate_gw_preview(t_array, GW0, A, T, freq, Da, Dd, R_scale, curve_randomness=0.2, secondary_freq=3.0):
             # np.random.seed(42) # Seed wird einmal am Anfang des Submenüs gesetzt
             # R_base wird außerhalb dieser Funktion im Submenü-Scope erzeugt
             # Stellen Sie sicher, dass T nicht Null ist, um Division durch Null zu vermeiden.
             if T == 0: T = 365 # Fallback-Wert

             # Amplitudenvariationen für jeden Wellenzyklus
             if curve_randomness > 0:
                 amplitude_variation = 1.0 + curve_randomness * np.random.normal(0, 1, size=len(t_array))
                 seasonal = A * np.sin(2 * np.pi * freq * t_array / T) * amplitude_variation
             else:
                 seasonal = A * np.sin(2 * np.pi * freq * t_array / T)
            
             # Sekundäre kleinere Wellen hinzufügen
             if secondary_freq > 0:
                 small_waves = A * 0.3 * np.sin(2 * np.pi * secondary_freq * freq * t_array / T)
                 seasonal += small_waves


             GW = np.zeros_like(t_array, dtype=float)

             if len(t_array) > 0:
                 GW[0] = GW0 + seasonal[0]

             for i in range(1, len(t_array)):
                 disturbance = R_scale * R_base_preview[i] # Nutze R_base_preview

                 diff_from_GW0 = GW[i-1] - GW0

                 daily_change = 0
                 if disturbance > 0 and Da > 0:
                     daily_change = (disturbance - diff_from_GW0) / Da
                 elif Dd > 0:
                     daily_change = -diff_from_GW0 / Dd

                 GW[i] = GW[i-1] + daily_change
                 GW[i] += seasonal[i] - seasonal[i-1]

             return GW


        # Erstelle die Figure für den Plot
        fig = Figure(figsize=(5, 4), dpi=100, facecolor=DISCORD_DARKER)
        ax = fig.add_subplot(111)
        ax.set_facecolor(DISCORD_DARKER)
        ax.spines['bottom'].set_color(DISCORD_TEXT)
        ax.spines['top'].set_color(DISCORD_TEXT)
        ax.spines['left'].set_color(DISCORD_TEXT)
        ax.spines['right'].set_color(DISCORD_TEXT)
        ax.tick_params(axis='both', colors=DISCORD_TEXT)
        ax.yaxis.label.set_color(DISCORD_TEXT)
        ax.xaxis.label.set_color(DISCORD_TEXT)
        ax.title.set_color(DISCORD_TEXT)
        ax.set_xlabel('Zeit (Tage)', color=DISCORD_TEXT)
        ax.set_ylabel('Grundwasserstand [m]', color=DISCORD_TEXT)
        ax.set_title('Grundwasserganglinie (Vorschau)', color=DISCORD_TEXT)




        # Erstelle die Plot-Canvas
        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()


        # Funktion zur Aktualisierung des Plots im Submenü
        def update_graph():
            ax.clear()
            ax.set_facecolor(DISCORD_DARKER)
            ax.spines['bottom'].set_color(DISCORD_TEXT)
            ax.spines['top'].set_color(DISCORD_TEXT)
            ax.spines['left'].set_color(DISCORD_TEXT)
            ax.spines['right'].set_color(DISCORD_TEXT)
            ax.tick_params(axis='both', colors=DISCORD_TEXT)
            ax.yaxis.label.set_color(DISCORD_TEXT)
            ax.xaxis.label.set_color(DISCORD_TEXT)
            ax.title.set_color(DISCORD_TEXT)
            ax.set_xlabel('Zeit (Tage)', color=DISCORD_TEXT)
            ax.set_ylabel('Grundwasserstand [m]', color=DISCORD_TEXT)
            ax.set_title('Grundwasserganglinie (Vorschau)', color=DISCORD_TEXT)


            # Grundwasserganglinie für die Vorschau berechnen
            # Verwende die aktuellen Werte der Slider-Variablen
            GW0 = var_GW0.get()
            A = var_A.get()
            T = var_T.get()
            freq = var_freq.get()
            Da = var_Da.get()
            Dd = var_Dd.get()
            R_scale = var_R.get()
            curve_randomness = var_randomness.get()
            secondary_freq = var_secondary.get()

            # Nutze die calculate_gw_preview Funktion mit t_preview und R_base_preview
            GW_preview = calculate_gw_preview(t_preview, GW0, A, T, freq, Da, Dd, R_scale, 
                                    curve_randomness, secondary_freq)

            # Plotten
            ax.plot(t_preview, GW_preview, color=DISCORD_GREEN, linewidth=1.5)
            ax.grid(True, color=DISCORD_GRAY_TEXT, alpha=0.3, linestyle='--')


            # Y-Achsen-Limits anpassen, aber nicht zu stark einschränken
            GW_min, GW_max = GW_preview.min(), GW_preview.max()
            margin = (GW_max - GW_min) * 0.1 # 10% Puffer
            if margin == 0 and GW_min == GW_max:
                 margin = 0.5 # Mindest-Puffer falls alle Werte gleich sind
            elif margin == 0:
                 margin = 0.1 * abs(GW_min) # Puffer basierend auf dem Wert selbst

            ax.set_ylim(GW_min - margin, GW_max + margin)


            canvas.draw()

        # Slider erstellen mit angepasstem Stil
        style = ttk.Style(submenu)
        style.configure("TScale", background=DISCORD_BG, troughcolor=DISCORD_DARK)

        # Funktion für Slider-Erstellung
        def create_parameter_slider(parent, row, text, from_, to_, default, precision=1):
            frame = tk.Frame(parent, bg=DISCORD_BG)
            frame.grid(row=row, column=0, columnspan=3, pady=5, sticky="ew")

            label = tk.Label(frame, text=text, bg=DISCORD_BG, fg=DISCORD_TEXT, width=30, anchor="w")
            label.grid(row=0, column=0, padx=(0, 10))

            # Tkinter Variable für den Wert
            value_var = tk.DoubleVar(value=default)

            def on_slider_change(event):
                # Aktualisiere die Anzeige des Werts neben dem Slider
                value_label.config(text=f"{value_var.get():.{precision}f}")
                update_graph() # Aktualisiere den Plot

            # Slider erstellen
            slider = ttk.Scale(frame, from_=from_, to=to_, variable=value_var, # Nutze die Tkinter Variable
                            command=on_slider_change, length=200, style="TScale") # Binde an on_slider_change
            slider.grid(row=0, column=1)

            # Label zur Anzeige des Slider-Werts
            # Initialisiere das Label mit dem Standardwert im richtigen Format
            value_label = tk.Label(frame, text=f"{default:.{precision}f}",
                                   bg=DISCORD_BG, fg=DISCORD_TEXT, width=5)
            value_label.grid(row=0, column=2, padx=(10, 0))

            return slider, value_var # Gebe auch die Variable zurück


        # Grundwasserparameter-Slider erstellen
        # Initialisiere Slider mit den aktuellen Werten aus dem formel_params Objekt
        s_GW0, var_GW0 = create_parameter_slider(parameter_frame, 1, "Grundniveau [m]:", 10, 14, formel_params.GW0, precision=2)
        s_A, var_A = create_parameter_slider(parameter_frame, 2, "Saisonale Amplitude [m]:", 0.1, 20.0, formel_params.A, precision=2)
        s_T, var_T = create_parameter_slider(parameter_frame, 3, "Periodendauer (Tage):", 100, 500, formel_params.T, precision=0)
        s_freq, var_freq = create_parameter_slider(parameter_frame, 4, "Sinusfrequenz/Periode:", 0.5, 3.0, formel_params.freq, precision=1)
        s_Da, var_Da = create_parameter_slider(parameter_frame, 5, "Anstiegsdauer (Tage):", 1, 200, formel_params.Da, precision=0)
        s_Dd, var_Dd = create_parameter_slider(parameter_frame, 6, "Abklingdauer (Tage):", 1, 200, formel_params.Dd, precision=0)
        s_R, var_R = create_parameter_slider(parameter_frame, 7, "Zufällige Schwankungen (Skala):", 0.0, 20, formel_params.R_scale, precision=2)
        s_randomness, var_randomness = create_parameter_slider(parameter_frame, 8, "Wellenform-Variabilität:", 0.0, 1.0, formel_params.curve_randomness, precision=2)
        s_secondary, var_secondary = create_parameter_slider(parameter_frame, 9, "Häufigkeit kleiner Wellen:", 0.0, 10.0, formel_params.secondary_freq, precision=1)


        # Button-Frame
        btn_frame = tk.Frame(parameter_frame, bg=DISCORD_BG)
        btn_frame.grid(row=10, column=0, columnspan=3, pady=20, sticky="ew")

        cancel_btn = tk.Button(btn_frame, text="Abbrechen", bg=DISCORD_DARK, fg=DISCORD_TEXT,
                            activebackground=DISCORD_DARKER, activeforeground=DISCORD_TEXT,
                            relief="flat", padx=15, pady=5,
                            command=lambda: close_submenu(False))
        cancel_btn.pack(side=tk.LEFT, padx=(0, 10))

        apply_btn = tk.Button(btn_frame, text="Übernehmen", bg=BUTTON_COLOR, fg=DISCORD_TEXT,
                            activebackground=BUTTON_HOVER, activeforeground=DISCORD_TEXT,
                            relief="flat", padx=15, pady=5,
                            command=lambda: close_submenu(True))
        apply_btn.pack(side=tk.LEFT)

        # Schließfunktion für Untermanü
        def close_submenu(apply_changes):
            if apply_changes:
                try:
                    # Speichere die aktuellen Slider-Werte zurück in das formel_params Objekt
                    formel_params.GW0 = var_GW0.get()
                    formel_params.A = var_A.get()
                    formel_params.T = var_T.get()
                    formel_params.freq = var_freq.get()
                    formel_params.Da = var_Da.get()
                    formel_params.Dd = var_Dd.get()
                    formel_params.R_scale = var_R.get()
                    formel_params.curve_randomness = var_randomness.get()
                    formel_params.secondary_freq = var_secondary.get()

                    # Aktualisiere die Anzeige der Parameter-Beschreibung im Hauptfenster
                    formel_label.config(text=formel_params.generiere_formel())

                except Exception as e:
                    print(f"Fehler beim Übernehmen der Parameter: {e}")

            # Sicherstellen, dass das Submenü geschlossen wird
            try:
                submenu.destroy()
            except:
                pass # Schon geschlossen

            root.submenu_open = False


        def on_submenu_close():
            root.submenu_open = False
            submenu.destroy()

        # Initialen Plot erstellen
        update_graph()

        # Stelle sicher, dass beim Schließen des Fensters die Flag zurückgesetzt wird
        submenu.protocol("WM_DELETE_WINDOW", on_submenu_close)
        submenu.focus_set()
        submenu.transient(root)
        submenu.grab_set()



    def emoji_img(size, text):
        # Größeres Bild erstellen, um sicherzustellen, dass das Emoji vollständig dargestellt wird
        im = Image.new("RGBA", (size*2, size*2), (255, 255, 255, 0))
        draw = ImageDraw.Draw(im)
        # Text zentriert zeichnen
        font = ImageFont.truetype("seguiemj.ttf", size=int(round(size*72/96, 0)))
        draw.text((size, size), text, embedded_color=True, font=font, anchor="mm")
        return ImageTk.PhotoImage(im)


    # Stift-Emoji erstellen
    pencil_emoji = emoji_img(25, "✏️")

    # Canvas für den Button erstellen
    button_size = 40
    button_canvas2 = tk.Canvas(formel_canvas, width=button_size, height=button_size,
                            bg=DISCORD_DARK, highlightthickness=0)
    formel_canvas.create_window(530, 30, window=button_canvas2)

    # Abgerundeter Button-Hintergrund (ID speichern!)
    bg_rect = create_rounded_rect(button_canvas2, 0, 0, button_size, button_size,
                    radius=10, fill=DISCORD_INPUT_BG, outline="")

    # Stift-Emoji mittig platzieren - mit offset anpassen
    button_canvas2.create_image(button_size/2+14, button_size/2+2, image=pencil_emoji, anchor="center")
    button_canvas2.image = pencil_emoji  # Referenz bewahren

    # Klick-Event hinzufügen
    button_canvas2.bind("<Button-1>", lambda e: open_formel_submenu())

    # Hover-Effekt für den Stift-Button
    def on_pencil_hover(event):
        button_canvas2.itemconfig(bg_rect, fill=DISCORD_DARKER)  # Hintergrund etwas dunkler

    def on_pencil_leave(event):
        button_canvas2.itemconfig(bg_rect, fill=DISCORD_INPUT_BG)  # Originale Farbe

    # Korrekte Bindung an die neuen Funktionen
    button_canvas2.bind("<Enter>", on_pencil_hover)
    button_canvas2.bind("<Leave>", on_pencil_leave)



    # 4. Fortschrittsbalken
    progress_frame = tk.Frame(main_frame, bg=DISCORD_BG)
    progress_frame.pack(fill=tk.X, pady=(0, 10))

    progress_canvas = tk.Canvas(progress_frame, bg=DISCORD_BG, height=80,
                             highlightthickness=0, width=580)
    progress_canvas.pack(fill=tk.X)

    create_rounded_rect(progress_canvas, 0, 0, 580, 80, radius=15,
                       fill=DISCORD_DARK, outline="")

    progress = ttk.Progressbar(progress_canvas, orient="horizontal", length=540,
                             mode="determinate", style="TProgressbar")
    progress_canvas.create_window(290, 30, window=progress)

    progress_info = tk.Label(progress_canvas, text="0/0 Werte generiert (0%)", **label_style)
    progress_canvas.create_window(290, 60, window=progress_info)

    # 5. Start Button
    button_frame = tk.Frame(main_frame, bg=DISCORD_BG)
    button_frame.pack(fill=tk.X, pady=(0, 10))

    button_canvas = tk.Canvas(button_frame, bg=DISCORD_BG, height=100,
                            highlightthickness=0, width=580)
    button_canvas.pack(fill=tk.X)

    create_rounded_rect(button_canvas, 0, 0, 580, 100, radius=15,
                       fill=DISCORD_DARK, outline="")

    start_button_canvas = tk.Canvas(button_canvas, width=160, height=40,
                                  bg=DISCORD_DARK, highlightthickness=0)
    button_canvas.create_window(290, 40, window=start_button_canvas)

    start_button_bg = create_rounded_rect(start_button_canvas, 0, 0, 160, 40,
                                       radius=15, fill=BUTTON_COLOR, outline="")

    start_button_text = start_button_canvas.create_text(80, 20, text="Start",
                                                     fill=DISCORD_TEXT,
                                                     font=("Arial", 14, "bold"))

    werte_info = tk.Label(button_canvas, text="Zu generierende Werte: -",
                        bg=DISCORD_DARK, fg=DISCORD_TEXT, font=('Arial', 11))
    button_canvas.create_window(290, 80, window=werte_info)


    # 6. Toggle Switch für CSV und Excel

    # Format-Switch neben Start-Button hinzufügen
    format_switch_canvas = tk.Canvas(button_canvas, width=100, height=30,
                                bg=DISCORD_DARK, highlightthickness=0)
    button_canvas.create_window(440, 40, window=format_switch_canvas)

    # Variable zum Speichern des Formats
    root.output_format = "csv"  # Standard ist CSV

    # Switch-Hintergrund erstellen - rot für CSV
    switch_bg = create_rounded_rect(format_switch_canvas, 0, 0, 100, 30,
                            radius=15, fill="#FF5555")  # Rot für CSV

    # Toggle-Button (weißer Kreis)
    button_size = 20
    switch_button = format_switch_canvas.create_oval(5, 5, 5 + button_size, 5 + button_size,
                                            fill="white", outline="")

    # Format-Text hinzufügen
    switch_text = format_switch_canvas.create_text(50, 15, text="CSV",
                                            fill="white", font=("Arial", 10, "bold"))

    # Funktion zum Umschalten des Formats
    def toggle_format(event=None):
        if root.output_format == "csv":
            # Zu Excel wechseln
            root.output_format = "excel"
            format_switch_canvas.itemconfig(switch_bg, fill=DISCORD_GREEN)
            format_switch_canvas.coords(switch_button, 75, 5, 75 + button_size, 5 + button_size)
            format_switch_canvas.itemconfig(switch_text, text="Excel")
        else:
            # Zu CSV wechseln
            root.output_format = "csv"
            format_switch_canvas.itemconfig(switch_bg, fill="#FF5555")
            format_switch_canvas.coords(switch_button, 5, 5, 5 + button_size, 5 + button_size)
            format_switch_canvas.itemconfig(switch_text, text="CSV")

    # Klick-Event binden
    format_switch_canvas.bind("<Button-1>", toggle_format)


    # Start-Button Funktion
    def start_process(event=None):
        # Hervorhebung des Buttons während Verarbeitung
        start_button_canvas.itemconfig(start_button_bg, fill=BUTTON_HOVER)
        root.update_idletasks()

        progress['value'] = 0
        progress_info.config(text="Vorbereitung...")

        try:
            start_date_str = startdatum.get()
            end_date_str = enddatum.get()
            # Verwenden Sie parse_flexible_date für Robustheit
            start_date = parse_flexible_date(start_date_str)
            end_date = parse_flexible_date(end_date_str)


            if start_date > end_date:
                raise ValueError("Startdatum muss vor Enddatum liegen")

            interval_hours_str = intervall_entry.get()
            if not interval_hours_str:
                 raise ValueError("Intervall darf nicht leer sein.")

            try:
                 interval_hours = float(interval_hours_str)
            except ValueError:
                 raise ValueError("Intervall muss eine Zahl sein.")


            if interval_hours <= 0:
                raise ValueError("Intervall muss größer als 0 sein")

            # Text aus dem Messstellen-Textfeld holen und validieren
            messstellen_text_inhalt = messstellen_text.get("1.0", tk.END).strip()
            valid, result = validiere_messstellen(messstellen_text_inhalt)
            if not valid:
                raise ValueError(result)

            messstellen_ids = result # Ergebnis der Validierung verwenden


            # Thread starten, um GUI nicht zu blockieren
            # Übergebe formel_params direkt an die Thread-Funktion
            thread = threading.Thread(target=create_csv_files,
                                        args=(root, start_date, end_date, messstellen_ids,
                                            interval_hours, formel_params, progress, progress_info))
            thread.daemon = True
            thread.start()

        except Exception as e:
            progress_info.config(text=f"Fehler: {str(e)}")
            # print(f"Start Process Error: {e}") # Debugging
            # Reset progress bar on error
            progress['value'] = 0

        finally:
            # Reset button appearance after some time
            root.after(100, lambda: start_button_canvas.itemconfig(start_button_bg, fill=BUTTON_COLOR))

    # Hover-Effekt für den Start-Button
    def on_button_hover(event):
        start_button_canvas.itemconfig(start_button_bg, fill=BUTTON_HOVER)

    def on_button_leave(event):
        start_button_canvas.itemconfig(start_button_bg, fill=BUTTON_COLOR)

    start_button_canvas.bind("<Button-1>", start_process)
    start_button_canvas.bind("<Enter>", on_button_hover)
    start_button_canvas.bind("<Leave>", on_button_leave)

    # Copyright-Hinweis unten
    copyright_label = tk.Label(root,
                             text=f" © Copyright ribeka GmbH 2025",
                             bg=DISCORD_BG,
                             fg=DISCORD_GRAY_TEXT,
                             font=('Arial', 9))
    copyright_label.place(relx=0.5, rely=1.0, anchor='s', y=-5)

    # Standard-Werte
    today = datetime.now()
    next_week = today + timedelta(days=7)

    startdatum.set_date(today)
    enddatum.set_date(next_week)

    # Berechne die Zeitspanne und Werteanzahl initial
    berechne_zeitspanne()


    return root

# Hauptfunktion
if __name__ == "__main__":
    app = create_gui()
    app.mainloop()