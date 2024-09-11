import h5py
import config 
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
    sensor_positions = []
    sensor_pos_detections = []
    sensor_vel_detections = []

    # 각 센서의 위치와 감지된 객체 데이터를 수집
    for idx, data in enumerate(self.current_scan_data):
        sensor_positions.append([data.radar_posx, data.radar_posy])  # 센서 위치 추가
        sensor_pos_detections.append([])  # 각 센서마다 새로운 리스트 생성
        sensor_vel_detections.append([])  # 각 센서마다 새로운 리스트 생성

        for vision in data.vision_object_data:
            # 해당 센서에서 감지된 객체들의 위치와 속도를 해당 리스트에 추가
            sensor_pos_detections[idx].append([vision.posx, vision.posy])
            sensor_vel_detections[idx].append([vision.velx, vision.vely])

    def match_objects(sensor_positions, sensor_detections):
        num_sensors = len(sensor_positions)
        base_detections = np.array(sensor_detections[0])  # 첫 번째 센서 기준
        num_objects = len(base_detections)

        # 각 센서에서 감지된 차량들의 위치를 기준으로 매칭 (유클리드 거리 계산)
        # matched_indices = []
        matched_indices = [list(range(len(base_detections)))]
        for i in range(1, num_sensors):
            detections = np.array(sensor_detections[i])

            # 각 센서의 감지된 차량 간의 거리 계산
            distances = cdist(base_detections, detections)
            # 헝가리안 알고리즘을 사용하여 가장 가까운 차량 매칭
            row_ind, col_ind = linear_sum_assignment(distances)

            # 감지된 객체 수보다 큰 인덱스가 생성되지 않도록 필터링
            matched_indices.append([index for index in col_ind if index < len(sensor_detections[i])])

        return matched_indices

    # 각도를 계산하는 함수
    def calculate_angles(sensor_positions, matched_detections):
        angles = []
        for i, sensor_pos in enumerate(sensor_positions):
            detection = np.array(matched_detections[i])
            vector = detection - sensor_pos
            
            # 벡터의 각도를 계산 (-y 방향, 즉 북쪽을 기준으로 반시계 방향으로 각도 계산)
            angle_rad = np.arctan2(vector[1], vector[0])  # 기본적으로 x축 기준
            angle_deg = np.degrees(angle_rad)
            
            # 북쪽(-y축)을 기준으로 각도를 변환 (90도 더하고 360도로 맞춤)
            north_based_angle = (90 - angle_deg) % 360
            
            angles.append(north_based_angle)
        return angles

    # 객체 매칭 수행
    matched_indices = match_objects(sensor_positions, sensor_pos_detections)

    # print(matched_indices)
    # 매칭된 차량 좌표 추출
    matched_detections = []
    for i in range(len(sensor_positions)):
        # matched_indices[i]가 범위를 벗어나지 않도록 확인 후 추가
        matched_detections.append([sensor_pos_detections[i][index] for index in matched_indices[i] if index < len(sensor_pos_detections[i])])

    # # 각도 계산
    angles = calculate_angles(sensor_positions, matched_detections)

        # print('matched : ', matched_detections)
        # print('angles : ', angles)


