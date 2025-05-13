import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

np.random.seed(42)
t = np.arange(0, 1000, 1)
GW0_init = 12.0
A_init = 1.0
T_init = 365
freq_init = 1.0  # Sinusfrequenz pro Jahr
Da_init = 20     # Anstiegsdauer in Tagen
Dd_init = 50     # Abklingdauer in Tagen
R_scale_init = 0.12

fig, ax = plt.subplots(figsize=(12, 6))
plt.subplots_adjust(left=0.1, bottom=0.35)

R_base = np.random.normal(0, 1, size=len(t))

def calculate_gw(GW0, A, T, freq, Da, Dd, R_scale):
    # Saisonale Schwankung mit einstellbarer Frequenz
    seasonal = A * np.sin(2 * np.pi * freq * t / T)
    GW = np.zeros_like(t, dtype=float)
    GW[0] = GW0 + seasonal[0]
    for i in range(1, len(t)):
        # Zufälliges Ereignis (Störung)
        disturbance = R_scale * R_base[i]
        # Anstieg zum gestörten Wert
        if disturbance > 0:
            GW[i] = GW[i-1] + (disturbance - (GW[i-1] - GW0)) / Da
        # Rückkehr zum Mittelwert (Abklingen)
        else:
            GW[i] = GW[i-1] - (GW[i-1] - GW0) / Dd
        GW[i] += seasonal[i] - seasonal[i-1]
    return GW

GW = calculate_gw(GW0_init, A_init, T_init, freq_init, Da_init, Dd_init, R_scale_init)
line, = ax.plot(t, GW, color='deepskyblue', label='Grundwasserstand')
ax.set_xlabel('Zeit (Tage)')
ax.set_ylabel('Grundwasserstand [m]')
ax.set_title('Grundwasserganglinie')
ax.set_ylim(10, 14)
ax.legend()
ax.grid(True)

# Slider
ax_GW0 = plt.axes([0.1, 0.28, 0.8, 0.03], facecolor='lightgoldenrodyellow')
ax_A = plt.axes([0.1, 0.24, 0.8, 0.03], facecolor='lightgoldenrodyellow')
ax_T = plt.axes([0.1, 0.20, 0.8, 0.03], facecolor='lightgoldenrodyellow')
ax_freq = plt.axes([0.1, 0.16, 0.8, 0.03], facecolor='lightgoldenrodyellow')
ax_Da = plt.axes([0.1, 0.12, 0.8, 0.03], facecolor='lightgoldenrodyellow')
ax_Dd = plt.axes([0.1, 0.08, 0.8, 0.03], facecolor='lightgoldenrodyellow')
ax_R = plt.axes([0.1, 0.04, 0.8, 0.03], facecolor='lightgoldenrodyellow')

s_GW0 = Slider(ax_GW0, 'Grundniveau', 10, 14, valinit=GW0_init)
s_A = Slider(ax_A, 'Saisonale Amplitude', 0.1, 2.0, valinit=A_init)
s_T = Slider(ax_T, 'Periodendauer (Tage)', 100, 500, valinit=T_init)
s_freq = Slider(ax_freq, 'Sinusfrequenz/Jahr', 0.5, 3.0, valinit=freq_init)
s_Da = Slider(ax_Da, 'Anstiegsdauer (Tage)', 1, 100, valinit=Da_init)
s_Dd = Slider(ax_Dd, 'Abklingdauer (Tage)', 1, 200, valinit=Dd_init)
s_R = Slider(ax_R, 'Zufällige Schwankungen', 0.0, 0.5, valinit=R_scale_init)

def update(val):
    GW0 = s_GW0.val
    A = s_A.val
    T = s_T.val
    freq = s_freq.val
    Da = s_Da.val
    Dd = s_Dd.val
    R_scale = s_R.val
    GW = calculate_gw(GW0, A, T, freq, Da, Dd, R_scale)
    line.set_ydata(GW)
    GW_min, GW_max = GW.min(), GW.max()
    margin = 0.5
    ax.set_ylim(GW_min - margin, GW_max + margin)
    fig.canvas.draw_idle()

for s in [s_GW0, s_A, s_T, s_freq, s_Da, s_Dd, s_R]:
    s.on_changed(update)

plt.show()
