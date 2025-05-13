import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk
import math
import random


class AnimatedModeSwitch(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Fenster konfigurieren
        self.title("Animated Mode Switch")
        self.geometry("500x400")
        self.config(bg="#f0f0f0")
        
        # Modi-Variablen
        self.is_dark_mode = False
        self.animation_running = False
        self.animation_steps = 20
        self.current_step = 0
        
        # Farben
        self.light_bg = "#f0f0f0"
        self.dark_bg = "#1a1a1a"
        self.light_fg = "#333333"
        self.dark_fg = "#ffffff"
        
        # Hauptframe
        self.main_frame = ctk.CTkFrame(self, fg_color=self.light_bg, corner_radius=0)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titel
        self.title_label = ctk.CTkLabel(
            self.main_frame, 
            text="Wähle deinen Modus", 
            font=("Arial", 24, "bold"),
            text_color=self.light_fg
        )
        self.title_label.pack(pady=30)
        
        # Switch-Container
        self.switch_container = ctk.CTkFrame(
            self.main_frame, 
            width=200, 
            height=80, 
            fg_color="#e0e0e0",
            corner_radius=40
        )
        self.switch_container.pack(pady=20)
        self.switch_container.pack_propagate(False)
        
        # Beschriftungen für Modi
        self.light_label = ctk.CTkLabel(
            self.switch_container, 
            text="LIGHT\nMODE", 
            font=("Arial", 12),
            text_color="#555555"
        )
        self.light_label.place(x=30, y=20)
        
        self.dark_label = ctk.CTkLabel(
            self.switch_container, 
            text="DARK\nMODE", 
            font=("Arial", 12),
            text_color="#aaaaaa"
        )
        self.dark_label.place(x=135, y=20)
        
        # Schalterknopf
        self.switch_button = ctk.CTkButton(
            self.switch_container,
            width=60,
            height=60,
            corner_radius=30,
            text="",
            fg_color="#ffffff",
            hover_color="#f5f5f5",
            command=self.toggle_mode
        )
        self.switch_button.place(x=10, y=10)
        
        # Zusätzliche Elemente
        self.create_decorative_elements()
        
        # Demo-Content
        self.content_frame = ctk.CTkFrame(
            self.main_frame,
            width=400,
            height=150,
            fg_color="#e0e0e0",
            corner_radius=15
        )
        self.content_frame.pack(pady=20)
        self.content_frame.pack_propagate(False)
        
        self.content_text = ctk.CTkLabel(
            self.content_frame,
            text="Beispielinhalt für die Demonstration\ndes Themenwechsels",
            font=("Arial", 16),
            text_color=self.light_fg
        )
        self.content_text.pack(pady=50)
        
    def create_decorative_elements(self):
        # Sonne
        self.sun = ctk.CTkCanvas(
            self.main_frame, 
            width=40, 
            height=40, 
            bg=self.light_bg,
            highlightthickness=0
        )
        self.sun.place(x=50, y=40)
        self.sun.create_oval(5, 5, 35, 35, fill="#FFD700", outline="")
        for i in range(8):
            angle = i * math.pi / 4
            x1 = 20 + 15 * math.cos(angle)
            y1 = 20 + 15 * math.sin(angle)
            x2 = 20 + 25 * math.cos(angle)
            y2 = 20 + 25 * math.sin(angle)
            self.sun.create_line(x1, y1, x2, y2, fill="#FFD700", width=2)
        
        # Mond
        self.moon = ctk.CTkCanvas(
            self.main_frame, 
            width=40, 
            height=40, 
            bg=self.light_bg,
            highlightthickness=0
        )
        self.moon.place(x=410, y=40)
        self.moon.create_oval(5, 5, 35, 35, fill="#C0C0C0", outline="")
        self.moon.create_oval(15, 5, 40, 30, fill=self.light_bg, outline="")
        
        # Sterne (unsichtbar im Light-Mode)
        self.stars = []
        for _ in range(20):
            star = ctk.CTkCanvas(
                self.main_frame,
                width=5,
                height=5,
                bg=self.light_bg,
                highlightthickness=0
            )
            x = 300 + 150 * (0.5 - random.random())
            y = 100 + 200 * (0.5 - random.random())
            star.place(x=x, y=y)
            # Erstelle den Stern und speichere seine ID
            star_id = star.create_oval(0, 0, 5, 5, fill="#ffffff", outline="")
            # Verstecke den Stern initial
            star.itemconfig(star_id, state="hidden")
            # Speichere sowohl das Canvas als auch die Item-ID
            self.stars.append((star, star_id))

    
    def toggle_mode(self):
        if not self.animation_running:
            self.animation_running = True
            self.current_step = 0
            self.animate_switch()
    
    def animate_switch(self):
        if self.current_step <= self.animation_steps:
            progress = self.current_step / self.animation_steps
            
            # Position des Schalterknopfs berechnen
            if not self.is_dark_mode:
                new_x = 10 + 120 * progress
            else:
                new_x = 130 - 120 * progress
            
            # Farben interpolieren
            if not self.is_dark_mode:
                bg_r = int(int(self.light_bg[1:3], 16) + (int(self.dark_bg[1:3], 16) - int(self.light_bg[1:3], 16)) * progress)
                bg_g = int(int(self.light_bg[3:5], 16) + (int(self.dark_bg[3:5], 16) - int(self.light_bg[3:5], 16)) * progress)
                bg_b = int(int(self.light_bg[5:7], 16) + (int(self.dark_bg[5:7], 16) - int(self.light_bg[5:7], 16)) * progress)
                
                fg_r = int(int(self.light_fg[1:3], 16) + (int(self.dark_fg[1:3], 16) - int(self.light_fg[1:3], 16)) * progress)
                fg_g = int(int(self.light_fg[3:5], 16) + (int(self.dark_fg[3:5], 16) - int(self.light_fg[3:5], 16)) * progress)
                fg_b = int(int(self.light_fg[5:7], 16) + (int(self.dark_fg[5:7], 16) - int(self.light_fg[5:7], 16)) * progress)
            else:
                bg_r = int(int(self.dark_bg[1:3], 16) + (int(self.light_bg[1:3], 16) - int(self.dark_bg[1:3], 16)) * progress)
                bg_g = int(int(self.dark_bg[3:5], 16) + (int(self.light_bg[3:5], 16) - int(self.dark_bg[3:5], 16)) * progress)
                bg_b = int(int(self.dark_bg[5:7], 16) + (int(self.light_bg[5:7], 16) - int(self.dark_bg[5:7], 16)) * progress)
                
                fg_r = int(int(self.dark_fg[1:3], 16) + (int(self.light_fg[1:3], 16) - int(self.dark_fg[1:3], 16)) * progress)
                fg_g = int(int(self.dark_fg[3:5], 16) + (int(self.light_fg[3:5], 16) - int(self.dark_fg[3:5], 16)) * progress)
                fg_b = int(int(self.dark_fg[5:7], 16) + (int(self.light_fg[5:7], 16) - int(self.dark_fg[5:7], 16)) * progress)
            
            bg_color = f"#{bg_r:02x}{bg_g:02x}{bg_b:02x}"
            fg_color = f"#{fg_r:02x}{fg_g:02x}{fg_b:02x}"
            
            # Anwenden der Änderungen
            self.switch_button.place(x=new_x, y=10)
            self.main_frame.configure(fg_color=bg_color)
            self.title_label.configure(text_color=fg_color)
            self.content_text.configure(text_color=fg_color)
            
            # Container-Farbe anpassen
            container_color = "#303030" if not self.is_dark_mode else "#e0e0e0"
            container_progress = progress
            container_r = int(int(self.light_bg[1:3], 16) + (int(container_color[1:3], 16) - int(self.light_bg[1:3], 16)) * container_progress)
            container_g = int(int(self.light_bg[3:5], 16) + (int(container_color[3:5], 16) - int(self.light_bg[3:5], 16)) * container_progress)
            container_b = int(int(self.light_bg[5:7], 16) + (int(container_color[5:7], 16) - int(self.light_bg[5:7], 16)) * container_progress)
            container_color = f"#{container_r:02x}{container_g:02x}{container_b:02x}"
            
            self.content_frame.configure(fg_color=container_color)
            
            # Sonne/Mond-Animation
            if not self.is_dark_mode:
                self.sun.configure(bg=bg_color)
                self.moon.configure(bg=bg_color)
                self.moon.itemconfig(2, fill=bg_color)
                sun_alpha = 1.0 - progress
                moon_alpha = progress
            else:
                self.sun.configure(bg=bg_color)
                self.moon.configure(bg=bg_color)
                self.moon.itemconfig(2, fill=bg_color)
                sun_alpha = progress
                moon_alpha = 1.0 - progress
            
            # Sterne-Animation
            for star, star_id in self.stars:
                star.configure(bg=bg_color)
                if not self.is_dark_mode:
                    # Sterne beim Übergang zum Dunkelmodus anzeigen
                    star.itemconfig(star_id, state="normal" if progress > 0.5 else "hidden")
                else:
                    # Sterne beim Übergang zum Hellmodus ausblenden
                    star.itemconfig(star_id, state="hidden" if progress > 0.5 else "normal")

        else:
            # Animation abgeschlossen
            self.is_dark_mode = not self.is_dark_mode
            self.animation_running = False
            
            # Schalter-Text aktualisieren
            switch_text = "🌙" if self.is_dark_mode else "☀️"
            self.switch_button.configure(text=switch_text)

if __name__ == "__main__":
    app = AnimatedModeSwitch()
    app.mainloop()
