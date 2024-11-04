import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import simpledialog, Checkbutton, IntVar, Button, Label
import threading

# Import your custom Tkinter manager from an external file (assuming it's in the same directory)
from .tk_manager import tk_manager

# Ensure '.ids_graph' folder exists
if not os.path.exists('.ids_graph'):
    os.makedirs('.ids_graph')

def parse_date(start_date):
    """Parse the start_date into a valid datetime format."""
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
                    print(f"No CSV files found in directory: {directory}")
                    continue

                for file in all_files:
                    df = pd.read_csv(file)
                    df['time'] = pd.to_datetime(df['time'], format='%Y-%m-%d_%H:%M:%S', errors='coerce')

                    # Extract hour_bin and weekday AFTER shifting the time
                    df['hour_bin'] = df['time'].dt.hour
                    df['weekday'] = df['time'].dt.weekday
                    df_list.append(df)
            except FileNotFoundError:
                print(f"Directory not found: {directory}")
                continue

    if df_list:
        merged_df = pd.concat(df_list, ignore_index=True)
        return merged_df, (min(date_range), max(date_range))
    else:
        return pd.DataFrame(), (None, None)

def filter_by_zone_and_event(df, selected_zone_ids, selected_event_types):
    return df[(df['zone_id'].isin(selected_zone_ids)) & (df['event_type'].isin(selected_event_types))]

class PlotWindow:
    def __init__(self, root, df, zone_ids, event_types, intersection, start_date, days):
        self.root = root
        self.df = df
        self.zone_ids = zone_ids
        self.event_types = event_types
        self.intersection = intersection
        self.start_date = start_date
        self.days = days
        self.create_plot()

    def create_plot(self):
        fig, axs = plt.subplots(len(self.zone_ids), 2, figsize=(12, 6 * len(self.zone_ids)), sharex=True)
        if len(self.zone_ids) == 1:
            axs = [axs]  # Ensure axs is iterable even if there's only one subplot

        hour_bins = range(24)  # Ensure we use all 24 hours
        x_ticks = [f"{hour:02d}:00" for hour in hour_bins]  # X-axis labels 00:00 ~ 23:00
        max_y_value = 0

        # Colors for weekend and weekday bars
        weekend_color = 'skyblue'
        weekday_color = 'lightgreen'

        for idx, zone_id in enumerate(self.zone_ids):
            ax_weekend = axs[idx][1]
            ax_weekday = axs[idx][0]

            for event_type in self.event_types:
                # Filter data by zone and event type for weekend and weekday
                weekend_data = self.df[(self.df['zone_id'] == zone_id) & (self.df['event_type'] == event_type) & (self.df['weekday'] >= 5)]
                weekday_data = self.df[(self.df['zone_id'] == zone_id) & (self.df['event_type'] == event_type) & (self.df['weekday'] < 5)]

                num_weekend_days = len(weekend_data['time'].dt.date.unique())
                num_weekday_days = len(weekday_data['time'].dt.date.unique())

                weekend_avg = weekend_data.groupby('hour_bin')['zone_id'].count().reindex(hour_bins, fill_value=0) / max(num_weekend_days, 1)
                weekday_avg = weekday_data.groupby('hour_bin')['zone_id'].count().reindex(hour_bins, fill_value=0) / max(num_weekday_days, 1)

                # Bar width
                bar_width = 0.4
                x = hour_bins

                # Plot bars
                ax_weekend.bar(x, weekend_avg, width=bar_width, label=f'{event_type} (Weekend Avg.)', color=weekend_color)
                ax_weekday.bar(x, weekday_avg, width=bar_width, label=f'{event_type} (Weekday Avg.)', color=weekday_color)

                max_y_value = max(max_y_value, weekend_avg.max(), weekday_avg.max())

            # Customize axes
            ax_weekend.set_title(f'Weekend Events by Hour (Zone {zone_id})')
            ax_weekday.set_title(f'Weekday Events by Hour (Zone {zone_id})')
            ax_weekend.grid(True)
            ax_weekday.grid(True)

            ax_weekend.set_xticks(hour_bins)
            ax_weekday.set_xticks(hour_bins)
            ax_weekend.set_xticklabels(x_ticks, rotation=45)
            ax_weekday.set_xticklabels(x_ticks, rotation=45)

        for ax_pair in axs:
            ax_weekday, ax_weekend = ax_pair
            ax_weekday.set_ylim(0, max_y_value + 20)
            ax_weekend.set_ylim(0, max_y_value + 20)

        # Adjust spacing between plots
        plt.tight_layout()

        # Embed the plot into a Tkinter window
        canvas = FigureCanvasTkAgg(fig, master=self.root)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Add save button
        save_button = Button(self.root, text="Save Graph", command=lambda: self.save_plot(fig))
        save_button.pack(side=tk.BOTTOM)

    def save_plot(self, fig):
        # Create a descriptive filename
        period = f"{self.start_date.strftime('%y%m%d')} to {(self.start_date - pd.Timedelta(days=self.days-1)).strftime('%y%m%d')}"
        zone_ids_str = '_'.join(map(str, self.zone_ids))
        filename = f"{self.intersection}_{period}_zone_ids_{zone_ids_str}.png"
        save_path = os.path.join('.ids_graph', filename)
        
        # Save the figure with the constructed filename
        fig.savefig(save_path)
        print(f"Graph saved at {save_path}")

def plot_app_thread(df, zone_ids, event_types, intersection, start_date, days):
    """This function runs the Matplotlib plot in a separate thread."""
    root = tk.Tk()
    root.title("Plot Window")
    PlotWindow(root, df, zone_ids, event_types, intersection, start_date, days)
    root.mainloop()

# Function to handle input and run the application
def main_app(root):
    data_path = "D:/kcity_loggingdata"
    ips = ['1.0.0.20','1.0.0.21','1.0.0.22','1.0.0.23', '1.0.0.24', '1.0.0.25']

    # Select intersections, date, days, zone IDs, and event types
    intersection_options = ['Esterno', 'Interno']
    selected_intersections = checkbox_selection_dialog(root, "Intersection", intersection_options)
    intersection = selected_intersections[0]  # Assume one intersection
    
    date = simpledialog.askstring("Input", "Enter the start date (YYMMDD):", parent=root)
    start_date = pd.to_datetime(date, format='%y%m%d')
    days = int(simpledialog.askstring("Input", "Enter the number of days:", parent=root))

    df, date_range = load_and_merge_csv_files(data_path, ips, intersection, date, days)
    if df.empty:
        print("No data found.")
        return

    zone_ids = df['zone_id'].unique()
    selected_zone_ids = checkbox_selection_dialog(root, "Zone ID(s)", zone_ids)
    if not selected_zone_ids:
        print("No zone ID selected.")
        return

    event_types = df['event_type'].unique()
    selected_event_types = checkbox_selection_dialog(root, "Event Type(s)", event_types)
    if not selected_event_types:
        print("No event type selected.")
        return

    filtered_df = filter_by_zone_and_event(df, selected_zone_ids, selected_event_types)
    if filtered_df.empty:
        print("No events found for the selected Zone IDs and Event Types.")
        return

    # Start a separate thread for the plot window
    plot_thread = threading.Thread(target=plot_app_thread, args=(filtered_df, selected_zone_ids, selected_event_types, intersection, start_date, days))
    plot_thread.start()

# Utility function for checkbox selection
def checkbox_selection_dialog(root, title, options):
    top = tk.Toplevel(root)
    top.title(title)
    Label(top, text=f"Select one or more {title.lower()}:").pack()
    vars_dict = {option: IntVar() for option in options}
    for option, var in vars_dict.items():
        Checkbutton(top, text=option, variable=var).pack(anchor=tk.W)

    def on_ok():
        selected_options = [option for option, var in vars_dict.items() if var.get() == 1]
        top.destroy()
        root.selected_options = selected_options

    Button(top, text="OK", command=on_ok).pack()
    root.wait_window(top)
    return root.selected_options if hasattr(root, 'selected_options') else []

# Function to start the Tkinter and plotting apps
def start_ids_view():
    tk_manager.run_tkinter_app(main_app)

