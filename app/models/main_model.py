import h5py
import config
from .colors import *
from .input_processing import *
import pygame
import io, os
from pathlib import Path
import cv2
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from .window_model import *

class MainModel:
    def __init__(self):
        self.logging_data_num = 0
        
        self.init_model_class()

    def get_logging_data(self, files:list): # 로깅데이터 가져오고, ATM 기본 설정들 입력해주기
        self.logging_data = []
        for file in files:
            logging_data = LoggingData()
            logging_data.logging_data = h5py.File(file)
            ip = file.split('_')[-1]
            logging_data.ip = ip
            self.logging_data.append(logging_data)
        self.logging_data_num = len(self.logging_data)
        
    def set_min_max_scan(self): # 여러개의 logging file중 가장 작은 값으로 설정해야함.
        
        self.min_scan = -1
        self.max_scan = 99999999999

        for file in self.logging_data:
            min = int(file.logging_data['DATA_INFO']['initScan'][()].item())
            max = int(file.logging_data['DATA_INFO']['finScan'][()].item())

            if min > self.min_scan:
                self.min_scan = min
            
            if max < self.max_scan:
                self.max_scan = max
            
    

    def parsing(self,current_scan):
    
        for log_data in self.logging_data:
            log_data.init_current_scan_data()

        # self.current_scan_data = [0] * self.logging_data_num
        color_set = (BLUE, GREEN, RED, YELLOW,BLUE, GREEN, RED, YELLOW) # TODO color 추가해줘야함. 맵에서 잘 보이는거 위주로 추가하기
        for idx, file in enumerate(self.logging_data):
            file_path = Path(file.logging_data.filename)
            self.logging_data[idx].current_scan_data = ScanData(file.logging_data, current_scan)    
            self.logging_data[idx].current_scan_data.parsing_status()
            self.logging_data[idx].current_scan_data.parsing_gps_into_meter(self.grid_model.GRID_WINDOW_WIDTH//2, self.grid_model.GRID_WINDOW_LENGTH//2)
            self.logging_data[idx].current_scan_data.parsing_image()
            self.logging_data[idx].current_scan_data.parsing_vision_object_data()
            self.logging_data[idx].current_scan_data.color = color_set[idx]
            self.logging_data[idx].current_scan_data.speed_color = BLACK
            

    def init_model_class(self):
        self.window_model = WindowModel()
        self.grid_model = GridModel()
        self.cam_bound_model = CamBoundModel(self.window_model.WINDOW_WIDTH, self.window_model.WINDOW_LENGTH)
        self.cam_change_left_button_model = CamChangeLeftButtonModel()
        self.cam_change_right_button_model = CamChangeRightButtonModel()
        self.cam_return_button_model = CamReturnButtonModel()
        self.data_info_window_model = DataInfoWindowModel()
        
        

    def window_resize(self, width, length):
        self.window_model = WindowModel(width, length)
        self.grid_model = GridModel(width, length)
        self.cam_bound_model = CamBoundModel(width, length)
        self.cam_change_left_button_model = CamChangeLeftButtonModel(width, length)
        self.cam_change_right_button_model = CamChangeRightButtonModel(width, length)
        self.cam_return_button_model = CamReturnButtonModel(width, length)
        self.data_info_window_model = DataInfoWindowModel(width, length)

    def get_h5_datas(self, directory):
    # 폴더 내부의 모든 파일 중 .h5 확장자를 가진 파일을 리스트로 반환
        h5_files = [f'{directory}/'+file for file in os.listdir(directory) if file.endswith('.h5')]
        return h5_files
    

    def select_object(self, mouse_pos):
        for idx, data in enumerate(self.logging_data):
            
            for vobj in data.current_scan_data.vision_object_data:
                
                dist = math.sqrt((mouse_pos[0] - vobj.posx)**2+ (mouse_pos[1] - vobj.posy)**2)
                if dist < 5:
                    vobj.selected = True
                    obj_id = vobj.id
                    data.selected_vobj_id.append(obj_id)
                    print(f'data : {idx}, list : {data.selected_vobj_id}')
        

            



    
    def object_matching(self):
        azi_thetas = [0] * len(self.current_scan_data)
        for idx, data in enumerate(self.current_scan_data):
            azi_thetas[idx] = data.azi_theta
        
        print(azi_thetas)
        selected_list = []

        for idx, data in enumerate(self.current_scan_data):
            print(idx)
            for vobj in data.vision_object_data:
                if vobj.selected:
                    selected_list.append((vobj.posx, vobj.posy))

        print(selected_list)

        # 각도 돌리기
        # 돌릴때마다 거리 비교
        # 최소값일 때의 각각 각도 적어두기


    


