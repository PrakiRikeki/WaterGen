import csv
from datetime import datetime, timedelta

# Konstanten
start_date = datetime(1990, 1, 1, 0, 0, 0)
end_date = datetime(2025, 12, 31, 23, 0, 0)
hourly_interval = timedelta(hours=1)


# Messstellen IDs
messstellen_ids = [f'Br. {i}' for i in range(1, 9)]

# Wasserstände
water_levels = [
    29.91, 30.15, 30.21, 30.38, 30.58, 30.57, 30.72, 30.9, 30.91, 30.99, 31.13, 31.21, 31.46, 31.52, 31.57, 31.69,
    31.75, 31.69, 31.89, 31.87, 31.96, 32.02, 31.93, 31.91, 31.94, 31.99, 32.06, 32.06, 31.87, 31.94, 31.89, 31.8,
    31.73, 31.72, 31.78, 31.58, 31.54, 31.5, 31.34, 31.37, 31.27, 31.02, 30.96, 30.81, 30.69, 30.53, 30.52, 30.38,
    30.16, 30.08, 30.08, 29.82, 29.68, 29.62, 29.6, 29.33, 29.3, 29.2, 28.98, 28.97, 28.8, 28.75, 28.66, 28.55,
    28.38, 28.45, 28.28, 28.18, 28.1, 28.16, 28.13, 27.97, 28.04, 27.96, 28.03, 27.93, 28.04, 27.99, 28.12, 27.99,
    28.07, 28.06, 28.28, 28.32, 28.26, 28.41, 28.52, 28.55, 28.64, 28.67, 28.74, 29.01, 29.12, 29.18, 29.23, 29.35,
    29.55, 29.7, 29.83, 29.93
]

# CSV-Dateien erstellen
for messstelle_id in messstellen_ids:
    filename = f'wasserstande_{messstelle_id.replace(" ", "_")}.csv'
    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=';')
        csvwriter.writerow(['GWMST Name', 'Datum/Uhrzeit', 'Messwert'])

        current_time = start_date
        water_level_index = 0
        while current_time <= end_date:
            formatted_date = current_time.strftime("%m.%d.%Y %H:%M:%S")
            messwert = water_levels[water_level_index]
            csvwriter.writerow([messstelle_id, formatted_date, f'{messwert:.2f}'])
            
            current_time += hourly_interval
            water_level_index = (water_level_index + 1) % len(water_levels)

    print(f"CSV-Datei '{filename}' wurde erfolgreich erstellt.")
    