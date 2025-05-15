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
from PIL import Image, ImageTk


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
        # Realistischere Standardwerte für die Grundwasserganglinie
        self.GW0 = 10.0    # Grundniveau in Meter unter GOK (realistischer Ausgangswert)
        self.A = 0.5       # Saisonale Amplitude (typischerweise 0.2-1.5m)
        self.T = 365       # Periodendauer in Tagen
        self.freq = 1.0    # Sinusfrequenz pro Periodendauer
        self.Da = 45       # Anstiegsdauer in Tagen (realistischer: 30-60 Tage)
        self.Dd = 120      # Abklingdauer in Tagen (realistischer: 90-180 Tage)
        self.R_scale = 0.05  # Skalierung für zufällige Schwankungen (kleinerer Wert)
        
        # Neue Parameter für realistischere Grundwassermodellierung
        self.phase = 60    # Phasenverschiebung in Tagen (Maximum im Frühjahr)
        self.trend = 0.0   # Langzeittrend pro Jahr in Meter (Klimawandel-Effekt)

    def generiere_formel(self):
        return (f"Generierung basierend auf GW-Modell: GW0={self.GW0}, A={self.A}, T={self.T}, freq={self.freq}, "
                f"Da={self.Da}, Dd={self.Dd}, R_scale={self.R_scale}, phase={self.phase}, trend={self.trend}")



# Funktion zur Berechnung der Grundwasserganglinie
def calculate_gw_series(t_array, GW0, A, T, freq, Da, Dd, R_scale, phase=60, trend=0.0):
    """
    Erzeugt flexible Grundwasserganglinien mit umfangreichen Einstellmöglichkeiten.
    """
    np.random.seed(42)
    n = len(t_array)
    
    # Basis-Komponenten: Saison + Trend
    seasonal = A * np.sin(2 * np.pi * freq * (t_array - phase) / T)
    trend_component = trend * t_array / 365
    base_level = GW0 + seasonal + trend_component
    
    # Grundwasserstand initialisieren
    GW = np.zeros(n)
    GW[0] = base_level[0]
    
    # Dynamisches Verhalten konfigurieren
    # Bei großem R_scale: mehr und stärkere Ereignisse
    num_events = max(3, int(n / (150 - 100 * R_scale)))
    event_indices = np.sort(np.random.choice(range(n), size=num_events, replace=False))
    event_strengths = 0.5 + np.random.random(size=num_events) * (0.8 + R_scale * 2)
    
    # Parameter für das dynamische Verhalten
    max_daily_change = 0.01 * A * (1 + 2 * R_scale)
    rise_factor = max(0.2, min(5, 1 / (0.2 + Da/100)))  # Anstiegsgeschwindigkeit
    decay_factor = max(0.1, min(3, 1 / (0.1 + Dd/100)))  # Abklinggeschwindigkeit
    
    # Ereigniseinfluss
    event_influence = 0.0
    
    # Hauptschleife für die Ganglinie
    for i in range(1, n):
        # Neues Ereignis?
        current_event = np.where(event_indices == i)[0]
        if len(current_event) > 0:
            # Stärkerer Einfluss bei höherem R_scale
            event_influence += event_strengths[current_event[0]] * A * R_scale
        
        # Ereignisse klingen mit individueller Geschwindigkeit ab
        decay_rate = 0.01 + 0.02 * decay_factor
        event_influence *= (1.0 - decay_rate)
        
        # Zielniveau berechnen
        target_level = base_level[i] + event_influence
        
        # Abweichung und Reaktion
        deviation = GW[i-1] - target_level
        
        # Dynamische Änderungsrate basierend auf Abweichung
        if deviation < 0:  # Anstieg nötig
            # Schneller bei großem A und kleinem Da
            rate = rise_factor * (0.05 + 0.1 * abs(deviation) / A)
        else:  # Abfall nötig
            # Schneller bei großem A und kleinem Dd
            rate = decay_factor * (0.02 + 0.05 * abs(deviation) / A)
        
        # Tägliche Änderung berechnen und begrenzen
        daily_change = -deviation * rate
        daily_change = np.clip(daily_change, -max_daily_change, max_daily_change)
        
        # Hysterese für natürliche Mikroschwankungen
        if abs(daily_change) < 0.2 * max_daily_change:
            daily_change *= 0.5
        
        # Tägliche Änderung anwenden
        GW[i] = GW[i-1] + daily_change
        
        # Zusätzliches Mikrorauschen - stärker bei hohem R_scale
        GW[i] += np.random.normal(0, 0.003 * A * R_scale)
    
    # Glättung anpassen je nach R_scale
    # Bei hohem R_scale: weniger Glättung für "wildere" Kurven
    num_smoothing = max(1, min(4, int(4 - 3 * R_scale)))
    window_size = max(3, min(23, int(17 * (1 - 0.7 * R_scale))))
    window_size += (window_size % 2 == 0)  # Sicherstellen dass Fenstergröße ungerade
    
    # Glättung anwenden
    for _ in range(num_smoothing):
        GW_smoothed = np.zeros_like(GW)
        for i in range(n):
            start = max(0, i - window_size // 2)
            end = min(n, i + window_size // 2 + 1)
            GW_smoothed[i] = np.mean(GW[start:end])
        GW = GW_smoothed.copy()
    
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
        # Prüfe, ob die neuen Parameter vorhanden sind
        phase = getattr(formel_params, 'phase', 60)  # Standardwert falls nicht vorhanden
        trend = getattr(formel_params, 'trend', 0.0)  # Standardwert falls nicht vorhanden
        
        grundwasser_series_daily = calculate_gw_series(
            t_days_array,
            formel_params.GW0,
            formel_params.A,
            formel_params.T,
            formel_params.freq,
            formel_params.Da,
            formel_params.Dd,
            formel_params.R_scale,
            phase,
            trend
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

# GUI erstellen
def create_gui():
    show_loading_screen()
    root = tk.Tk()
    root.title("WaterGen")
    window_width = 620
    window_height = 700
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_pos = int((screen_width/2) - (window_width/2))
    y_pos = int((screen_height/2) - (window_height/2))
    root.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")
    set_dark_title_bar(root)
    root.configure(bg=DISCORD_BG)

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

    # Neue große Überschrift hinzufügen (vor allen anderen Elementen)
    header_frame = tk.Frame(main_frame, bg=DISCORD_BG)
    header_frame.pack(fill=tk.X, pady=(0, 20))

    header_canvas = tk.Canvas(header_frame, bg=DISCORD_BG, height=100,
                              highlightthickness=0, width=580)
    header_canvas.pack(fill=tk.X)

    create_rounded_rect(header_canvas, 0, 0, 580, 100, radius=15,
                        fill=DISCORD_DARK, outline="")

    header_label = tk.Label(header_canvas, text="WaterGen",
                           bg=DISCORD_DARK, fg=DISCORD_TEXT,
                           font=('Arial', 30, 'bold'))
    header_canvas.create_window(290, 50, window=header_label)

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


            # Messstellen validieren
            messstellen_text_inhalt = messstellen_text.get("1.0", tk.END).strip()
            valid, result = validiere_messstellen(messstellen_text_inhalt)
            if not valid:
                werte_info.config(text=f"Fehler: {result}")
                return 0

            messstellenanzahl = len(result)
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
        t_preview = np.arange(0, 1000, 1) # Vorschau für 1000 Tage
        R_base_preview = np.random.normal(0, 1, size=len(t_preview))


        # Funktion zur Berechnung der Grundwasserganglinie für die Plot-Vorschau
        def calculate_gw_preview(t_array, GW0, A, T, freq, Da, Dd, R_scale):
             # np.random.seed(42) # Seed wird einmal am Anfang des Submenüs gesetzt
             # R_base wird außerhalb dieser Funktion im Submenü-Scope erzeugt
             # Stellen Sie sicher, dass T nicht Null ist, um Division durch Null zu vermeiden.
             if T == 0: T = 365 # Fallback-Wert

             seasonal = A * np.sin(2 * np.pi * freq * t_array / T)
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

            # Nutze die calculate_gw_preview Funktion mit t_preview und R_base_preview
            GW_preview = calculate_gw_preview(t_preview, GW0, A, T, freq, Da, Dd, R_scale)

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
        s_R, var_R = create_parameter_slider(parameter_frame, 7, "Zufällige Schwankungen (Skala):", 0.0, 0.5, formel_params.R_scale, precision=2)


        # Button-Frame
        btn_frame = tk.Frame(parameter_frame, bg=DISCORD_BG)
        btn_frame.grid(row=8, column=0, columnspan=3, pady=20, sticky="ew")

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


    # Stift-Button
    edit_button = tk.Button(formel_canvas, text="✏️", bg=DISCORD_DARK, fg=DISCORD_TEXT,
                          command=open_formel_submenu, bd=0, relief="flat",
                          activebackground=DISCORD_DARKER,
                          font=("Arial", 16), padx=5, pady=0)
    formel_canvas.create_window(530, 30, window=edit_button)

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
    copyright_symbol = u"\u00A9"
    copyright_label = tk.Label(root,
                             text=f"{copyright_symbol} ribeka GmbH Alle Rechte reserviert",
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