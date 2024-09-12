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

    def get_logging_data(self, files:list):
        self.logging_data = []
        for file in files:
            self.logging_data.append(h5py.File(file))
        self.logging_data_num = len(self.logging_data)
        
    def set_min_max_scan(self): # 여러개의 logging file중 가장 작은 값으로 설정해야함.
        
        self.min_scan = -1
        self.max_scan = 99999999999

        for file in self.logging_data:
            min = int(file['DATA_INFO']['initScan'][()].item())
            max = int(file['DATA_INFO']['finScan'][()].item())

            if min > self.min_scan:
                self.min_scan = min
            
            if max < self.max_scan:
                self.max_scan = max
            
    

    def parsing(self,current_scan):
        self.current_scan_data = [0] * self.logging_data_num
        color_set = (BLUE, GREEN, RED, YELLOW,BLUE, GREEN, RED, YELLOW) # TODO color 추가해줘야함. 맵에서 잘 보이는거 위주로 추가하기
        for idx, file in enumerate(self.logging_data):
            file_path = Path(file.filename)
            file_stem = file_path.stem
            ip = file_stem.split('_')[-1]
            self.current_scan_data[idx] = ScanData(file, current_scan)    
            self.current_scan_data[idx].parsing_status()
            self.current_scan_data[idx].parsing_gps_into_meter(self.grid_model.GRID_WINDOW_WIDTH//2, self.grid_model.GRID_WINDOW_LENGTH//2)
            self.current_scan_data[idx].parsing_image()
            self.current_scan_data[idx].parsing_vision_object_data()
            self.current_scan_data[idx].ip = ip
            self.current_scan_data[idx].color = color_set[idx]
            self.current_scan_data[idx].speed_color = BLACK
            
        # if not os.path.exists(BACKGROUND_IMAGE_PATH):
        #     parsing_image_data_from_google(LAT_LANDMARK, LON_LANDMARK, self.window_model.GRID_WINDOW_WIDTH, self.window_model.GRID_WINDOW_LENGTH,zoom = 18, maptype = 'satellite')
        # self.BACKGROUND_IMAGE_PATH = 'images/map_image.png'

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
    

    
def object_matching(self):
    azi_thetas = [0] * len(self.current_scan_data)
    for idx, data in enumerate(self.current_scan_data):
        azi_thetas[idx] = data.azi_theta
    
    print(azi_thetas)
    
    self.current_scan_data[1].azi_theta += 10

    


