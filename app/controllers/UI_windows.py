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
            self.atm.vds_view = True  # 데이터가 처리된 경우 True로 설정
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
                    print(f"No CSV files found in directory: {directory}")  # 로그 메시지
                    continue  # 파일이 없으면 넘어감
                
                for file in all_files:
                    df = pd.read_csv(file)
                    df['time'] = pd.to_datetime(df['time'], format='%Y%m%d_%H:%M:%S')
                    df['time'] = df['time'] - pd.Timedelta(hours=7)
                    df['hour_bin'] = df['time'].dt.hour
                    if not df.empty and df.notna().sum().sum() > 0:
                        df_list.append(df)
            except FileNotFoundError:
                print(f"Directory not found: {directory}")  # 디렉토리가 없을 경우 로그 메시지
                continue

        date_range = (min(date_range), max(date_range))  # 시작일과 종료일을 구함

        if df_list:
            merged_df = pd.concat(df_list, ignore_index=True)

            # outgoing과 oncoming을 시간대별로 count하고 레인별로 그룹화
            lane_groups = merged_df.groupby(['lane', 'direction', 'hour_bin']).size().unstack(fill_value=0)

            # 레인별 평균 계산
            lane_averages = lane_groups / self.day
            lane_averages = lane_averages.stack().reset_index(name='count')

            return lane_averages, date_range
        else:
            return pd.DataFrame(), date_range  # 유효한 데이터가 없으면 빈 데이터프레임 반환

class PlotAppThread(threading.Thread):
    def __init__(self, config, atm, result_queue):
        super().__init__()
        self.config = config
        self.atm = atm
        self.result_queue = result_queue
        self.lane_data = {}  # 레인별 데이터를 저장
        self.active_lanes = {}  # 활성화된 레인의 리스트
        self.plot_type = 'bar'  # 그래프 유형 ('bar' 또는 'line')
        self.date_range = None  # 날짜 범위를 저장할 변수

    def run(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Tkinter 창 숨기기
        self.check_queue()

        self.root.mainloop()

    def check_queue(self):
        try:
            while not self.result_queue.empty():
                atm, df, date_range = self.result_queue.get_nowait()
                if not df.empty:
                    self.date_range = date_range  # 날짜 범위 저장
                    self.process_lane_data(df)
                    self.create_total_lane_plot_window(atm)
            if self.root.winfo_exists():
                self.root.after(100, self.check_queue)  # 100ms 후 다시 체크
        except tk.TclError:
            pass

    def process_lane_data(self, df):
        # 각 레인별로 데이터를 분류하고 저장
        for (lane, direction), group_df in df.groupby(['lane', 'direction']):
            key = (str(lane), direction)
            self.lane_data[key] = group_df
            self.active_lanes[key] = True  # 모든 레인을 초기화 시 활성화

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

        # 그래프 그리기
        self.update_graphs()

        canvas = FigureCanvasTkAgg(fig, master=plot_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 각 창에서 개별적으로 키보드 이벤트를 처리하도록 설정
        plot_window.bind('<Key>', self.on_key_press)
        plot_window.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_key_press(self, event):
        if event.char.isdigit():  # 숫자 키 입력 처리
            self.toggle_lane(event.char)
        elif event.char.lower() == 'r':
            self.toggle_plot_type()

    def toggle_lane(self, lane):
        for direction in ['oncoming', 'outgoing']:
            key = (str(lane), direction)
            if key in self.active_lanes:
                # 활성화된 상태라면 비활성화
                self.active_lanes[key] = not self.active_lanes[key]
        self.update_graphs()

    def toggle_plot_type(self):
        self.plot_type = 'line' if self.plot_type == 'bar' else 'bar'
        self.update_graphs()

    def update_graphs(self):
        self.axs[0].clear()
        self.axs[1].clear()

        hour_bins = range(24)
        x_ticks = [f"{i:02d}:00" for i in range(24)]

        # 활성화된 모든 레인 데이터를 합쳐서 그래프 그리기
        for (lane, direction), is_active in self.active_lanes.items():
            if not is_active:
                continue

            lane_df = self.lane_data[(lane, direction)]
            counts = lane_df.groupby('hour_bin')['count'].sum()

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

        # 그래프 제목에 날짜 범위 추가
        start_date, end_date = self.date_range
        self.axs[0].set_title(f'Outgoing Vehicles by Hour\n({start_date} to {end_date})')
        self.axs[0].set_xlabel('Time')
        self.axs[0].set_ylabel('Number of Vehicles')
        self.axs[0].grid(True)
        self.axs[0].set_xticks(hour_bins)
        self.axs[0].set_xticklabels(x_ticks, rotation=45)
        self.axs[0].legend()

        self.axs[1].set_title(f'Oncoming Vehicles by Hour\n({start_date} to {end_date})')
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
    root.withdraw()  # Tkinter 메인 창 숨기기

    # 날짜 입력 받기
    date = simpledialog.askstring("Input", "Enter the date (YYMMDD):")
    
    day = simpledialog.askstring("Input", "Enter the period (number of days):")

    root.destroy()  # Tkinter 창 닫기
    return date, day

def capitalize_first_letter(string):
    if len(string) == 0:
        return string
    return string[0].upper() + string[1:]
