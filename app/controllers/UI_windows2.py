import os
import threading
import queue
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import simpledialog

class TkinterAppManager:
    def __init__(self):
        self.root = None

    def run_tkinter_app(self, app_func, *args, **kwargs):
        """메인 스레드에서 Tkinter 앱 실행"""
        if self.root is None:
            self.root = tk.Tk()
            self.root.withdraw()
        app_func(self.root, *args, **kwargs)

tk_manager = TkinterAppManager()

def capitalize_first_letter(string):
    if len(string) == 0:
        return string
    return string[0].upper() + string[1:]

def create_ip_to_intersection_mapping(config_verona):
    ip_to_intersection = {}
    for intersection_name in ['interno', 'esterno']:
        intersection_data = config_verona.get(intersection_name, {})
        for key in intersection_data.keys():
            if key.startswith('radar_gps_'):
                ip = key[len('radar_gps_'):]
                ip_to_intersection[ip] = intersection_name
    return ip_to_intersection

def get_ips_for_nodes(config_verona, intersection_name, node_numbers):
    ips = set()
    node_info = config_verona['info']['node'][intersection_name]
    for node_number in node_numbers:
        node_key = f'node{node_number}'
        if node_key in node_info:
            node = node_info[node_key]
            if isinstance(node['oncoming'], list):
                for oncoming_ip in node['oncoming']:
                    if oncoming_ip != 0 and oncoming_ip != '0':
                        ips.add(oncoming_ip)
            else:
                oncoming_ip = node['oncoming']
                if oncoming_ip != 0 and oncoming_ip != '0':
                    ips.add(oncoming_ip)

            outgoing_ip = node['outgoing']
            if outgoing_ip != 0 and outgoing_ip != '0':
                ips.add(outgoing_ip)
    return list(ips)

def map_lanes(df, ip):
    if ip == '1.0.0.20':
        df['lane'] = df['lane'].astype(int) + 1
    return df

class NodeDataProcessingThread(threading.Thread):
    def __init__(self, config_verona, ips, result_queue, start_date, day):
        super().__init__()
        self.config_verona = config_verona
        self.ips = ips
        self.result_queue = result_queue
        self.start_date = start_date
        self.day = int(day)

    def run(self):
        df, date_range = self.load_and_merge_csv_files()
        self.result_queue.put((df, date_range))

    def load_and_merge_csv_files(self):
        df_list = []
        date_range = []

        ip_to_intersection = create_ip_to_intersection_mapping(self.config_verona)
        data_path = self.config_verona['info']['data_path']

        for i in range(self.day):
            date = pd.to_datetime(self.start_date, format='%y%m%d') - pd.Timedelta(days=i)
            date_str = date.strftime('%y%m%d')
            date_range.append(date_str)

            for ip in self.ips:
                intersection_name = ip_to_intersection.get(ip)
                if intersection_name is None:
                    print(f"Cannot find intersection for IP: {ip}")
                    continue

                directory = os.path.join(data_path, date_str, capitalize_first_letter(intersection_name), ip, 'vds')

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
                        df['ip'] = ip  # Add IP address

                        if 'lane' not in df.columns:
                            df['lane'] = '0'
                        if 'direction' not in df.columns:
                            df['direction'] = 'unknown'

                        df = map_lanes(df, ip)

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

class NodePlotApp:
    def __init__(self, config_verona, intersection_name, node_numbers, start_date, day):
        self.config_verona = config_verona
        self.intersection_name = intersection_name
        self.node_numbers = node_numbers
        self.start_date = start_date
        self.day = day

        self.ips = get_ips_for_nodes(config_verona, intersection_name, node_numbers)
        if not self.ips:
            print("No valid IPs found for the provided node numbers.")
            return

        self.result_queue = queue.Queue()
        self.axs = None  # Initialize axs to None before it is used

        self.data_thread = NodeDataProcessingThread(
            config_verona,
            self.ips,
            self.result_queue,
            start_date,
            day
        )
        self.data_thread.start()

        self.root = tk.Toplevel()
        self.root.title("VDS Viewer")
        self.root.geometry('1600x1300')

        self.root.bind("<Configure>", self.on_resize)

        self.root.after(100, self.check_queue)

        self.root.mainloop()

    def check_queue(self):
        try:
            if not self.result_queue.empty():
                df, date_range = self.result_queue.get_nowait()
                if not df.empty:
                    self.date_range = date_range
                    self.process_lane_data(df)
                    self.create_total_lane_plot_window()
            else:
                self.root.after(100, self.check_queue)
        except tk.TclError:
            pass

    def process_lane_data(self, df):
        self.weekend_data = df[df['weekday'] >= 5]  # Saturday (5) and Sunday (6)
        self.weekday_data = df[df['weekday'] < 5]   # Monday (0) to Friday (4)

        self.lane_data = {'weekend': {}, 'weekday': {}}
        self.active_lanes = {}

        self.num_weekend_days = len(self.weekend_data['time'].dt.date.unique())
        self.num_weekday_days = len(self.weekday_data['time'].dt.date.unique())

        for (lane, direction), group_df in df.groupby(['lane', 'direction']):
            if direction not in ['oncoming', 'outgoing']:
                continue

            key = (str(lane), direction)
            self.active_lanes[key] = True

        for dataset_name, dataset in {'weekend': self.weekend_data, 'weekday': self.weekday_data}.items():
            for (lane, direction), group_df in dataset.groupby(['lane', 'direction']):
                key = (str(lane), direction)
                if direction in ['oncoming', 'outgoing']:
                    if key in self.lane_data[dataset_name]:
                        self.lane_data[dataset_name][key] = pd.concat([self.lane_data[dataset_name][key], group_df])
                    else:
                        self.lane_data[dataset_name][key] = group_df

    def create_total_lane_plot_window(self):
        ips_str = ', '.join(self.ips)
        self.root.title(f'IPs: {ips_str}')

        fig, axs = plt.subplots(2, 2, figsize=(16, 12))
        self.axs = axs.flatten()
        self.fig = fig

        plt.subplots_adjust(hspace=0.4, wspace=0.4)

        self.update_graphs()

        canvas = FigureCanvasTkAgg(fig, master=self.root)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        save_button = tk.Button(self.root, text="Save as PNG", command=self.save_as_png)
        save_button.pack(side=tk.BOTTOM, pady=10)

        self.root.bind('<Key>', self.on_key_press)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def save_as_png(self):
        start_date, end_date = self.date_range
        directory = 'graph'

        if not os.path.exists(directory):
            os.makedirs(directory)

        ips_str = '_'.join([ip.replace('.', '_') for ip in self.ips])
        nodes_str = '_'.join([f'node{node}' for node in self.node_numbers])
        filename = os.path.join(directory, f'{self.intersection_name}_{nodes_str}_{ips_str}_{start_date}_to_{end_date}.png')

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
        total_max_y_value = 3000 # Fixed maximum Y value
        total_max_y_value = 1000 # Fixed maximum Y value
        total_max_y_value = 2000 # Fixed maximum Y value

        hour_bins = range(24)
        x_ticks = [f"{i:02d}:00" for i in range(24)]

        # Set grid interval
        grid_interval = 200  # Y-axis grid interval

        for ax in self.axs:
            ax.set_ylim(0, total_max_y_value)
            ax.set_yticks(range(0, total_max_y_value + grid_interval, grid_interval))

        # Plot data for each lane
        self.plot_lane_data(self.lane_data['weekday'], 'oncoming', self.axs[0], 'Weekday Oncoming', hour_bins, x_ticks)
        self.plot_lane_data(self.lane_data['weekday'], 'outgoing', self.axs[1], 'Weekday Outgoing', hour_bins, x_ticks)
        self.plot_lane_data(self.lane_data['weekend'], 'oncoming', self.axs[2], 'Weekend Oncoming', hour_bins, x_ticks)
        self.plot_lane_data(self.lane_data['weekend'], 'outgoing', self.axs[3], 'Weekend Outgoing', hour_bins, x_ticks)

        plt.tight_layout()
        self.fig.canvas.draw()

    def plot_lane_data(self, lane_data, direction, ax, title, hour_bins, x_ticks):
        total_data = pd.Series(0, index=hour_bins)

        for (lane, lane_direction), is_active in self.active_lanes.items():
            if lane_direction == direction and is_active:
                key = (str(lane), direction)
                if key in lane_data:
                    lane_df = lane_data[key]
                    counts = lane_df.groupby('hour_bin')['count'].sum()

                    # Calculate average if needed
                    counts = counts / max(self.num_weekday_days, 1) if direction == 'weekday' else counts / max(self.num_weekend_days, 1)

                    ax.plot(counts.index, counts, label=f'{direction.capitalize()} (Lane {lane})')
                    total_data = total_data.add(counts, fill_value=0)

        total_data = total_data.reindex(hour_bins, fill_value=0)

        ax.plot(total_data.index, total_data, color='red', label='Total', linestyle='--')

        start_date, end_date = self.date_range
        ax.set_title(f'{title} Vehicles by Hour\n({start_date} to {end_date})')
        ax.set_xlabel('Time of Day (TOD)')
        ax.set_ylabel('Average Number of Vehicles')
        ax.grid(True)
        ax.set_xticks(hour_bins)
        ax.set_xticklabels(x_ticks, rotation=45)
        ax.legend()

    def on_resize(self, event):
        if self.axs is None:
            return

        width = event.width
        height = event.height

        for ax in self.axs:
            ax.set_xlim(left=0, right=24)
            ax.set_xticks(range(0, 25, 1))

            max_y_value = ax.get_ylim()[1]
            ax.set_yticks(range(0, int(max_y_value) + 200, 200))

        plt.tight_layout()
        self.fig.canvas.draw()

    def on_close(self):
        self.root.quit()
        self.root.destroy()

def start_node_vds_view(config_verona):
    def launch_view(root):
        date = simpledialog.askstring("Input", "Enter the date (YYMMDD):", parent=root)
        day = simpledialog.askstring("Input", "Enter the period (number of days):", parent=root)

        selection_dialog = IntersectionSelectionDialog(root)
        intersection_name = selection_dialog.result

        if not intersection_name:
            print("No intersection was selected.")
            return

        node_info = config_verona['info']['node'][intersection_name]
        node_keys = list(node_info.keys())

        node_selection_dialog = NodeSelectionDialog(root, "Select Nodes", node_keys)
        node_numbers = [node_key[len('node'):] for node_key in node_selection_dialog.selected_nodes]

        if not node_numbers:
            print("No nodes were selected.")
            return

        for node_number in node_numbers:
            NodePlotApp(config_verona, intersection_name, [node_number], date, day)

    tk_manager.run_tkinter_app(launch_view)

class IntersectionSelectionDialog(tk.simpledialog.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Select Intersection")

    def body(self, master):
        tk.Label(master, text="Select an intersection:").pack()
        self.var = tk.StringVar(value='esterno')
        tk.Radiobutton(master, text='esterno', variable=self.var, value='esterno').pack()
        tk.Radiobutton(master, text='interno', variable=self.var, value='interno').pack()
        return None

    def apply(self):
        self.result = self.var.get()

class NodeSelectionDialog(tk.simpledialog.Dialog):
    def __init__(self, parent, title, node_keys):
        self.node_keys = node_keys
        self.selected_nodes = []
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text="Select nodes:").pack()
        self.listbox = tk.Listbox(master, selectmode=tk.MULTIPLE)
        for node_key in self.node_keys:
            self.listbox.insert(tk.END, node_key)
        self.listbox.pack()
        return None

    def apply(self):
        selected_indices = self.listbox.curselection()
        self.selected_nodes = [self.node_keys[i] for i in selected_indices]
