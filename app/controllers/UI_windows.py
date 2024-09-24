import os
import threading
import queue
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk

class DataProcessingThread(threading.Thread):
    def __init__(self, config, atm, result_queue):
        super().__init__()
        self.config = config
        self.atm = atm
        self.result_queue = result_queue

    def run(self):
        df = self.load_and_merge_csv_files(self.config, self.atm)
        self.result_queue.put((self.atm, df))

    def load_and_merge_csv_files(self, config, atm):
        directory = config['new_path'] + '/' + atm.ip + '/vds'
        all_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.csv')]
        df_list = []
        for file in all_files:
            df = pd.read_csv(file)
            df['time'] = pd.to_datetime(df['time'], format='%Y%m%d_%H:%M:%S')
            df['time'] = df['time'] - pd.Timedelta(hours=7)
            df['hour_bin'] = df['time'].dt.hour
            if not df.empty and df.notna().sum().sum() > 0:
                df_list.append(df)
        if df_list:
            merged_df = pd.concat(df_list, ignore_index=True)
        else:
            merged_df = pd.DataFrame()  # 빈 데이터프레임 반환
        return merged_df

class PlotApp:
    def __init__(self, root, config, selected_atms):
        self.root = root
        self.config = config
        self.selected_atms = selected_atms
        self.result_queue = queue.Queue()
        self.threads = []
        self.figures = []

        self.root.title('ATM Data Viewer')
        self.root.geometry('800x600')

        self.check_queue()

        for idx, atm in enumerate(self.selected_atms):
            thread = DataProcessingThread(self.config[idx], atm, self.result_queue)
            self.threads.append(thread)
            thread.start()

    def check_queue(self):
        try:
            while not self.result_queue.empty():
                atm, df = self.result_queue.get_nowait()
                self.create_plot_window(atm, df)
            if self.root.winfo_exists():
                self.root.after(100, self.check_queue)  # 100ms 후에 다시 체크
        except tk.TclError:
            # root가 이미 파괴된 경우 발생하는 예외
            pass

    def create_plot_window(self, atm, df):
        # Tkinter 윈도우 설정
        plot_window = tk.Toplevel(self.root)
        plot_window.title(f'ATM: {atm.ip}')
        plot_window.geometry('800x600')

        fig, axs = plt.subplots(2, 1, figsize=(10, 8))

        # Set x-axis as hourly intervals
        hour_bins = range(24)
        x_ticks = [f"{i:02d}:00" for i in range(24)]

        # Draw graphs
        outgoing_counts = df[~df['direction'].isin(['oncoming', 'unknown'])].groupby(['hour_bin']).size()
        axs[0].bar(outgoing_counts.index, outgoing_counts, color='blue', label='Outgoing')
        axs[0].set_title('Outgoing Vehicles by Hour')
        axs[0].set_xlabel('Time')
        axs[0].set_ylabel('Number of Vehicles')
        axs[0].grid(True)
        axs[0].set_xticks(hour_bins)
        axs[0].set_xticklabels(x_ticks, rotation=45)
        axs[0].legend()

        oncoming_counts = df[df['direction'] == 'oncoming'].groupby(['hour_bin']).size()
        axs[1].bar(oncoming_counts.index, oncoming_counts, color='orange', label='Oncoming')
        axs[1].set_title('Oncoming Vehicles by Hour')
        axs[1].set_xlabel('Time')
        axs[1].set_ylabel('Number of Vehicles')
        axs[1].grid(True)
        axs[1].set_xticks(hour_bins)
        axs[1].set_xticklabels(x_ticks, rotation=45)
        axs[1].legend()

        canvas = FigureCanvasTkAgg(fig, master=plot_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.figures.append(fig)  # 그래프 객체를 저장해둠

def run_vds_view(configs, selected_atms):
    root = tk.Tk()
    app = PlotApp(root, configs, selected_atms)
    root.mainloop()

def start_vds_view_thread(configs, selected_atms):
    vds_thread = threading.Thread(target=run_vds_view, args=(configs, selected_atms))
    vds_thread.start()
