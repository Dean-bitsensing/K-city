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
        if not df.empty:
            self.atm.vds_view = True  # 데이터가 처리된 경우 True로 설정
            self.result_queue.put((self.atm, df))

    def load_and_merge_csv_files(self, config, atm):
        directory = config['new_path'] + '/' + atm.ip + '/vds'
        try:
            all_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.csv')]
            if not all_files:
                print(f"No CSV files found in directory: {directory}")  # 로그 메시지
                return pd.DataFrame()  # 파일이 없으면 빈 데이터프레임 반환
            
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
                merged_df = pd.DataFrame()  # 유효한 데이터가 없으면 빈 데이터프레임 반환
            return merged_df
        except FileNotFoundError:
            print(f"Directory not found: {directory}")  # 디렉토리가 없을 경우 로그 메시지
            return pd.DataFrame()  # 빈 데이터프레임 반환

class PlotAppThread(threading.Thread):
    def __init__(self, config, atm, result_queue):
        super().__init__()
        self.config = config
        self.atm = atm
        self.result_queue = result_queue
        self.lane_data = {}  # 각 창의 lane 데이터를 독립적으로 저장
        self.active_lanes = {}  # 활성화된 레인의 리스트, key = (lane, direction)
        self.show_total_traffic = False  # 각 창의 전체 통행량 표시 여부 독립적으로 관리
        self.plot_type = 'bar'  # 그래프 유형 ('bar' 또는 'line')

    def run(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Tkinter 창 숨기기
        self.check_queue()

        self.root.mainloop()

    def check_queue(self):
        try:
            while not self.result_queue.empty():
                atm, df = self.result_queue.get_nowait()
                if not df.empty:
                    self.process_lane_data(df)
                    self.create_total_lane_plot_window(atm)
            if self.root.winfo_exists():
                self.root.after(100, self.check_queue)  # 100ms 후 다시 체크
        except tk.TclError:
            pass

    def process_lane_data(self, df):
        # 각 lane과 direction별로 데이터를 분류하고 저장 (lane 0 제외)
        for (lane, direction), group_df in df.groupby(['lane', 'direction']):
            if lane == 0:
                continue  # lane 0은 제외
            key = (str(lane), direction)
            self.lane_data[key] = group_df
            self.active_lanes[key] = True  # 활성화된 상태로 초기화

        # 전체 통행량을 계산하여 저장
        self.total_outgoing = df[~df['direction'].isin(['oncoming', 'unknown'])].groupby(['hour_bin']).size()
        self.total_oncoming = df[df['direction'] == 'oncoming'].groupby(['hour_bin']).size()

    def create_total_lane_plot_window(self, atm):
        plot_window = tk.Toplevel(self.root)
        plot_window.title(f'ATM: {atm.ip}')
        plot_window.geometry('800x600')

        fig, axs = plt.subplots(2, 1, figsize=(10, 8))
        self.axs = axs
        self.atm = atm
        self.fig = fig

        # 간격 조정 (subplots 간의 간격을 조정)
        plt.subplots_adjust(hspace=0.4)  # 상하 간격 조정

        # 모든 활성화된 레인에 대해 그래프 그리기
        self.update_graphs()

        canvas = FigureCanvasTkAgg(fig, master=plot_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 각 창에서 개별적으로 키보드 이벤트를 처리하도록 설정
        plot_window.bind('<Key>', self.on_key_press)
        plot_window.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_key_press(self, event):
        if event.char.lower() == 't':
            self.toggle_total_traffic()
        elif event.char.lower() == 'r':
            self.toggle_plot_type()
        elif event.char.isdigit():  # 숫자 키 입력 처리
            self.toggle_lane(event.char)

    def toggle_lane(self, lane):
        for direction in ['oncoming', 'outgoing']:
            key = (str(lane), direction)
            if key in self.active_lanes:
                # 활성화된 상태라면 비활성화
                self.active_lanes[key] = not self.active_lanes[key]
        self.update_graphs()

    def toggle_total_traffic(self):
        # 해당 창의 전체 통행량의 표시 상태를 토글
        self.show_total_traffic = not self.show_total_traffic
        self.update_graphs()

    def toggle_plot_type(self):
        # 그래프 유형을 토글 ('bar' <-> 'line')
        self.plot_type = 'line' if self.plot_type == 'bar' else 'bar'
        self.update_graphs()

    def update_graphs(self):
        self.axs[0].clear()
        self.axs[1].clear()

        hour_bins = range(24)
        x_ticks = [f"{i:02d}:00" for i in range(24)]

        # 전체 통행량을 표시할지 여부
        if self.show_total_traffic:
            if self.plot_type == 'bar':
                self.axs[0].bar(self.total_outgoing.index, self.total_outgoing, color='grey', label='Total Outgoing')
                self.axs[1].bar(self.total_oncoming.index, self.total_oncoming, color='grey', label='Total Oncoming')
            elif self.plot_type == 'line':
                self.axs[0].plot(self.total_outgoing.index, self.total_outgoing, color='grey', label='Total Outgoing')
                self.axs[1].plot(self.total_oncoming.index, self.total_oncoming, color='grey', label='Total Oncoming')

        # 활성화된 모든 레인 데이터를 합쳐서 그래프 그리기
        for (lane, direction), is_active in self.active_lanes.items():
            if not is_active:
                continue

            lane_df = self.lane_data[(lane, direction)]
            counts = lane_df.groupby(['hour_bin']).size()

            if direction == 'outgoing':
                if self.plot_type == 'bar':
                    self.axs[0].bar(counts.index, counts, label=f'Outgoing (Lane {lane})')
                elif self.plot_type == 'line':
                    self.axs[0].plot(counts.index, counts, label=f'Outgoing (Lane {lane})')
            elif direction == 'oncoming':
                if self.plot_type == 'bar':
                    self.axs[1].bar(counts.index, counts, label=f'Oncoming (Lane {lane})')
                elif self.plot_type == 'line':
                    self.axs[1].plot(counts.index, counts, label=f'Oncoming (Lane {lane})')

        self.axs[0].set_title('Outgoing Vehicles by Hour')
        self.axs[0].set_xlabel('Time')
        self.axs[0].set_ylabel('Number of Vehicles')
        self.axs[0].grid(True)
        self.axs[0].set_xticks(hour_bins)
        self.axs[0].set_xticklabels(x_ticks, rotation=45)
        self.axs[0].legend()

        self.axs[1].set_title('Oncoming Vehicles by Hour')
        self.axs[1].set_xlabel('Time')
        self.axs[1].set_ylabel('Number of Vehicles')
        self.axs[1].grid(True)
        self.axs[1].set_xticks(hour_bins)
        self.axs[1].set_xticklabels(x_ticks, rotation=45)
        self.axs[1].legend()

        # 레이아웃 조정을 통해 겹침 방지
        plt.tight_layout()
        self.fig.canvas.draw()

    def on_close(self):
        self.atm.vds_view = False
        self.root.destroy()

def start_vds_view_thread(config, atm):
    result_queue = queue.Queue()
    data_thread = DataProcessingThread(config, atm, result_queue)
    plot_app_thread = PlotAppThread(config, atm, result_queue)

    data_thread.start()
    plot_app_thread.start()

def run_vds_view(configs, selected_atms):
    for idx, atm in enumerate(selected_atms):
        start_vds_view_thread(configs[idx], atm)

def start_vds_view(configs, selected_atms):
    vds_thread = threading.Thread(target=run_vds_view, args=(configs, selected_atms))
    vds_thread.start()
