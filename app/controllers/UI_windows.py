import os
import threading
import queue
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import simpledialog


class DataProcessingThread(threading.Thread):
    def __init__(self, config, atm, result_queue, start_date, day):
        super().__init__()
        self.config = config
        self.atm = atm
        self.result_queue = result_queue
        self.start_date = start_date
        self.day = int(day)

    def run(self):
        df, date_range = self.load_and_merge_csv_files()
        if not df.empty:
            self.atm.vds_view = True
            self.result_queue.put((self.atm, df, date_range))

    def load_and_merge_csv_files(self):
        df_list = []
        date_range = []

        for i in range(self.day):
            date = pd.to_datetime(self.start_date, format='%y%m%d') - pd.Timedelta(days=i)
            date_str = date.strftime('%y%m%d')
            date_range.append(date_str)
            directory = self.config['info']['data_path'] + '/' + date_str + '/' + capitalize_first_letter(self.atm.intersection.name) + '/' + self.atm.ip + '/vds'
            try:
                all_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.csv')]
                if not all_files:
                    print(f"No CSV files found in directory: {directory}")
                    continue
                
                for file in all_files:
                    df = pd.read_csv(file)
                    df['time'] = pd.to_datetime(df['time'], format='%Y%m%d_%H:%M:%S')
                    df['hour_bin'] = df['time'].dt.hour
                    df['weekday'] = df['time'].dt.weekday

                    df['count'] = 1

                    if not df.empty and df.notna().sum().sum() > 0:
                        df_list.append(df)
            except FileNotFoundError:
                print(f"Directory not found: {directory}")
                continue

        date_range = (min(date_range), max(date_range))

        if df_list:
            merged_df = pd.concat(df_list, ignore_index=True)
            return merged_df, date_range
        else:
            return pd.DataFrame(), date_range


class PlotAppThread(threading.Thread):
    def __init__(self, config, atm, result_queue):
        super().__init__()
        self.config = config
        self.atm = atm
        self.result_queue = result_queue
        self.lane_data = {}
        self.active_lanes = {}
        self.date_range = None

    def run(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.check_queue()

        self.root.mainloop()

    def check_queue(self):
        try:
            while not self.result_queue.empty():
                atm, df, date_range = self.result_queue.get_nowait()
                if not df.empty:
                    self.date_range = date_range
                    self.process_lane_data(df)
                    self.create_total_lane_plot_window(atm)
            if self.root.winfo_exists():
                self.root.after(100, self.check_queue)
        except tk.TclError:
            pass

    def process_lane_data(self, df):
        self.weekend_data = df[df['weekday'] >= 5]  # Saturday (5) and Sunday (6)
        self.weekday_data = df[df['weekday'] < 5]   # Monday (0) to Friday (4)

        self.lane_data['weekend'] = {}
        self.lane_data['weekday'] = {}

        for (lane, direction), group_df in df.groupby(['lane', 'direction']):
            key = (str(lane), direction)
            self.active_lanes[key] = True

        for dataset_name, dataset in {'weekend': self.weekend_data, 'weekday': self.weekday_data}.items():
            for (lane, direction), group_df in dataset.groupby(['lane', 'direction']):
                key = (str(lane), direction)
                self.lane_data[dataset_name][key] = group_df

    def create_total_lane_plot_window(self, atm):
        plot_window = tk.Toplevel(self.root)
        plot_window.title(f'ATM: {atm.ip}')

        plot_window.geometry('1600x1300')
        fig, axs = plt.subplots(2, 2, figsize=(16, 12))

        self.axs = axs.flatten()
        self.atm = atm
        self.fig = fig

        plt.subplots_adjust(hspace=0.4, wspace=0.4)

        self.update_graphs()

        canvas = FigureCanvasTkAgg(fig, master=plot_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Add Save button
        save_button = tk.Button(plot_window, text="Save as PNG", command=self.save_as_png)
        save_button.pack(side=tk.BOTTOM, pady=10)

        plot_window.bind('<Key>', self.on_key_press)
        plot_window.protocol("WM_DELETE_WINDOW", self.on_close)

    def save_as_png(self):
    # Generate file name based on date range and atm information
        start_date, end_date = self.date_range
        directory = 'graph'

        # Create the directory if it doesn't exist
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Full path with the graph/ directory
        filename = os.path.join(directory, f'{self.atm.ip}_{start_date}_to_{end_date}.png')

    # Save the figure to a PNG file
        self.fig.savefig(filename)
        print(f"Graph saved as {filename}")

    def on_key_press(self, event):
        if event.char.isdigit():
            self.toggle_lane(event.char)

    def toggle_lane(self, lane):
        for direction in ['oncoming', 'outgoing']:
            key = (str(lane), direction)
            if key in self.active_lanes:
                self.active_lanes[key] = not self.active_lanes[key]
        self.update_graphs()

    def update_graphs(self):
        for ax in self.axs:
            ax.clear()

        hour_bins = range(24)
        x_ticks = [f"{i:02d}:00" for i in range(24)]

        # Plot weekend oncoming data
        self.plot_lane_data(self.lane_data['weekend'], 'oncoming', self.axs[0], 'Weekend Oncoming', hour_bins, x_ticks)

        # Plot weekend outgoing data
        self.plot_lane_data(self.lane_data['weekend'], 'outgoing', self.axs[1], 'Weekend Outgoing', hour_bins, x_ticks)

        # Plot weekday oncoming data
        self.plot_lane_data(self.lane_data['weekday'], 'oncoming', self.axs[2], 'Weekday Oncoming', hour_bins, x_ticks)

        # Plot weekday outgoing data
        self.plot_lane_data(self.lane_data['weekday'], 'outgoing', self.axs[3], 'Weekday Outgoing', hour_bins, x_ticks)

        plt.tight_layout()
        self.fig.canvas.draw()

    def plot_lane_data(self, lane_data, direction, ax, title, hour_bins, x_ticks):
        total_data = pd.Series(0, index=hour_bins)

        for (lane, lane_direction), is_active in self.active_lanes.items():
            if lane_direction == direction and is_active:
                key = (lane, direction)
                if key in lane_data:
                    lane_df = lane_data[key]
                    counts = lane_df.groupby('hour_bin')['count'].sum()

                    ax.plot(counts.index, counts, label=f'{direction.capitalize()} (Lane {lane})')
                    total_data = total_data.add(counts, fill_value=0)

        total_data = total_data.reindex(hour_bins, fill_value=0)

        ax.plot(total_data.index, total_data, color='red', label='Total', linestyle='--')

        start_date, end_date = self.date_range
        ax.set_title(f'{title} Vehicles by Hour\n({start_date} to {end_date})')
        ax.set_xlabel('Time of Day (TOD)')
        ax.set_ylabel('Number of Vehicles')
        ax.grid(True)
        ax.set_xticks(hour_bins)
        ax.set_xticklabels(x_ticks, rotation=45)
        ax.legend()

        max_y_value = total_data.max()
        fig_width, fig_height = self.fig.get_size_inches()
        grid_interval = max(100, int(max_y_value / 10))
        max_y_limit = (int(max_y_value // grid_interval) + 1) * grid_interval

        ax.set_ylim(0, max_y_limit)
        ax.set_yticks(range(0, max_y_limit + 1, grid_interval))

    def on_close(self):
        self.atm.vds_view = False
        self.root.destroy()


def start_vds_view_thread(config, atm, start_date, day):
    result_queue = queue.Queue()
    data_thread = DataProcessingThread(config, atm, result_queue, start_date, day)
    plot_app_thread = PlotAppThread(config, atm, result_queue)

    data_thread.start()
    plot_app_thread.start()


def run_vds_view(config, selected_atms, start_date, day):
    for atm in selected_atms:
        start_vds_view_thread(config, atm, start_date, day)


def start_vds_view(config, selected_atms):
    date, day = open_input_dialog()
    vds_thread = threading.Thread(target=run_vds_view, args=(config, selected_atms, date, day))
    vds_thread.start()


def open_input_dialog():
    root = tk.Tk()
    root.withdraw()

    date = simpledialog.askstring("Input", "Enter the date (YYMMDD):")
    day = simpledialog.askstring("Input", "Enter the period (number of days):")

    root.destroy()  # Close the Tkinter input dialog
    return date, day


def capitalize_first_letter(string):
    if len(string) == 0:
        return string
    return string[0].upper() + string[1:]
