import tkinter as tk
from tkinter import ttk
from tkcalendar import Calendar

# Darkmode Farben
BG_COLOR = '#23272b'
FG_COLOR = '#e0e0e0'
ENTRY_BG = '#2c2f34'
HIGHLIGHT = '#4e9a06'

class DatePicker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Datumsauswahl')
        self.configure(bg=BG_COLOR)
        self.geometry('300x80')
        self.resizable(False, False)

        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TEntry', fieldbackground=ENTRY_BG, foreground=FG_COLOR, background=BG_COLOR)
        style.configure('TButton', background=BG_COLOR, foreground=FG_COLOR)
        style.configure('TLabel', background=BG_COLOR, foreground=FG_COLOR)

        self.date_var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.date_var, font=('Segoe UI', 12), width=15)
        self.entry.grid(row=0, column=0, padx=(20,0), pady=20)

        self.btn = ttk.Button(self, text='▼', width=2, command=self.show_calendar)
        self.btn.grid(row=0, column=1, padx=(5,0), pady=20)

        self.calendar_win = None
        self.bind('<Configure>', self.on_move)

    def show_calendar(self):
        if self.calendar_win and tk.Toplevel.winfo_exists(self.calendar_win):
            self.calendar_win.destroy()
            self.calendar_win = None
            return
        self.calendar_win = tk.Toplevel(self)
        self.calendar_win.overrideredirect(True)
        self.calendar_win.configure(bg=BG_COLOR)
        self.calendar_win.attributes('-topmost', True)
        self.calendar = Calendar(self.calendar_win, selectmode='day',
                                 background=BG_COLOR, foreground=FG_COLOR,
                                 headersbackground=ENTRY_BG, headersforeground=FG_COLOR,
                                 selectbackground=HIGHLIGHT, selectforeground=FG_COLOR,
                                 weekendbackground=ENTRY_BG, weekendforeground=FG_COLOR,
                                 othermonthbackground=BG_COLOR, othermonthwebackground=BG_COLOR,
                                 othermonthforeground='#888', othermonthweforeground='#888',
                                 bordercolor=BG_COLOR, disabledbackground=BG_COLOR,
                                 disabledforeground='#555', normalbackground=BG_COLOR,
                                 normalforeground=FG_COLOR, font=('Segoe UI', 10))
        self.calendar.pack(padx=2, pady=2)
        self.calendar.bind('<<CalendarSelected>>', self.on_date_selected)
        self.position_calendar()
        self.calendar_win.lift()
        self.calendar_win.focus_force()

    def position_calendar(self):
        if not self.calendar_win:
            return
        x = self.winfo_rootx() + self.entry.winfo_x()
        y = self.winfo_rooty() + self.entry.winfo_y() + self.entry.winfo_height()
        self.calendar_win.geometry(f'+{x}+{y}')
        self.calendar_win.attributes('-topmost', True)

    def on_move(self, event):
        if self.calendar_win and tk.Toplevel.winfo_exists(self.calendar_win):
            self.position_calendar()
            self.calendar_win.lift()
            self.calendar_win.attributes('-topmost', True)

    def on_date_selected(self, event):
        date = self.calendar.get_date()
        self.date_var.set(date)
        self.calendar_win.destroy()

if __name__ == '__main__':
    app = DatePicker()
    app.mainloop()