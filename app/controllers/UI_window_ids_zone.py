import os
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import simpledialog, Checkbutton, IntVar
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from itertools import cycle
from .tk_manager import tk_manager

def parse_date(start_date):
    try:
        return pd.to_datetime(start_date, format='%y%m%d')
    except ValueError:
        print(f"Error parsing the date: {start_date}. Please enter the date in YYMMDD format.")
        return None

def load_and_merge_csv_files(data_path, ips, intersection, start_date, days):
    df_list = []
    date_range = []

    parsed_start_date = parse_date(start_date)
    if parsed_start_date is None:
        return pd.DataFrame(), (None, None)

    for i in range(days):
        date = parsed_start_date - pd.Timedelta(days=i)
        date_str = date.strftime('%y%m%d')
        date_range.append(date_str)

        for ip in ips:
            directory = os.path.join(data_path, date_str, intersection, ip, 'emergency')

            try:
                all_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.csv')]
                if not all_files:
                    continue

                for file in all_files:
                    df = pd.read_csv(file)
                    df['time'] = pd.to_datetime(df['time'], format='%Y-%m-%d_%H:%M:%S', errors='coerce')
                    df['hour_bin'] = df['time'].dt.hour
                    df['weekday'] = df['time'].dt.weekday
                    df_list.append(df)
            except FileNotFoundError:
                continue

    if df_list:
        merged_df = pd.concat(df_list, ignore_index=True)
        return merged_df, (min(date_range), max(date_range))
    else:
        return pd.DataFrame(), (None, None)

def filter_by_zone_and_event(df, selected_zone_ids, selected_event_types):
    return df[(df['zone_id'].isin(selected_zone_ids)) & (df['event_type'].isin(selected_event_types))]

def create_graph(df, zone_ids, event_types, days):
    weekend_data = df[df['weekday'] >= 5]  # Saturday (5) and Sunday (6)
    weekday_data = df[df['weekday'] < 5]   # Monday (0) to Friday (4)

    hour_bins = range(24)
    x_ticks = [f"{i:02d}:00" for i in range(24)]
    line_styles = cycle(['-', '--', '-.', ':'])
    markers = cycle(['o', 's', 'D', '^'])

    fig, axs = plt.subplots(len(zone_ids), 1, figsize=(10, 6 * len(zone_ids)), sharex=True)
    if len(zone_ids) == 1:
        axs = [axs]

    for ax, zone_id in zip(axs, zone_ids):
        for event_type in event_types:
            linestyle = next(line_styles)
            marker = next(markers)
            
            zone_event_weekend = weekend_data[(weekend_data['zone_id'] == zone_id) & (weekend_data['event_type'] == event_type)]
            zone_event_weekday = weekday_data[(weekday_data['zone_id'] == zone_id) & (weekday_data['event_type'] == event_type)]

            for dataset, label in [(zone_event_weekend, 'Weekend'), (zone_event_weekday, 'Weekday')]:
                counts = dataset.groupby('hour_bin')['zone_id'].count() / max(len(dataset), 1)
                ax.plot(counts.index, counts, linestyle=linestyle, marker=marker, label=f'{event_type} ({label} Avg.)')

        ax.set_title(f'Zone {zone_id} - Events by Hour')
        ax.set_xlabel('Time of Day (Hour)')
        ax.set_ylabel('Average Number of Events')
        ax.grid(True)
        ax.legend()

    plt.xticks(hour_bins, x_ticks, rotation=45)
    plt.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=tk_manager.root)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def checkbox_selection_dialog(root, title, options):
    top = tk.Toplevel(root)
    top.title(title)

    label = tk.Label(top, text=f"Select one or more {title.lower()}:")
    label.pack()

    vars_dict = {}
    for option in options:
        var = IntVar()
        checkbutton = Checkbutton(top, text=option, variable=var)
        checkbutton.pack(anchor=tk.W)
        vars_dict[option] = var

    def on_ok():
        selected_options = [option for option, var in vars_dict.items() if var.get() == 1]
        top.destroy()
        root.selected_options = selected_options

    ok_button = tk.Button(top, text="OK", command=on_ok)
    ok_button.pack()

    root.wait_window(top)
    return root.selected_options if hasattr(root, 'selected_options') else []

def main_app(root):
    data_path = "C:/kcity_loggingdata"
    ips = ['1.0.0.20','1.0.0.21','1.0.0.22','1.0.0.23', '1.0.0.24', '1.0.0.25']

    intersection_options = ['Esterno', 'Interno']
    selected_intersections = checkbox_selection_dialog(root, "Intersection", intersection_options)
    if not selected_intersections:
        return

    date = simpledialog.askstring("Input", "Enter the start date (YYMMDD):", parent=root)
    days = int(simpledialog.askstring("Input", "Enter the number of days:", parent=root))
    
    intersection = selected_intersections[0]
    df, date_range = load_and_merge_csv_files(data_path, ips, intersection, date, days)
    if df.empty:
        return
    
    zone_ids = df['zone_id'].unique()
    selected_zone_ids = checkbox_selection_dialog(root, "Zone ID(s)", zone_ids)
    if not selected_zone_ids:
        return
    
    event_types = df['event_type'].unique()
    selected_event_types = checkbox_selection_dialog(root, "Event Type(s)", event_types)
    if not selected_event_types:
        return

    filtered_df = filter_by_zone_and_event(df, selected_zone_ids, selected_event_types)
    if filtered_df.empty:
        return

    create_graph(filtered_df, selected_zone_ids, selected_event_types, days)


