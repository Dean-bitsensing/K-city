import os
import h5py
import numpy as np
import utm  # UTM 좌표계로 변환
import math
from .fusion_data_classes import *
from tqdm import tqdm
# GPS 좌표 (위도, 경도)를 UTM 좌표로 변환하는 함수
def gps_to_utm(latitude, longitude):
    utm_coords = utm.from_latlon(latitude, longitude)
    return np.array([utm_coords[0], utm_coords[1]])  # UTM 좌표계에서 x, y 반환

# Radar 클래스 정의
class Radar:
    def __init__(self, gps_position, radar_orientation_deg):

        self.position = gps_position 
        self.deg = radar_orientation_deg

def calculate_xy_distance(coord1, coord2):
        # 지구 반지름 (미터 단위)
        R = 6378137  

        # 위도와 경도를 라디안으로 변환
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])

        # 위도와 경도의 차이
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # y(남북 방향 거리) 계산
        y_distance = R * dlat

        # x(동서 방향 거리) 계산 (위도에 따른 조정 포함)
        x_distance = R * dlon * math.cos((lat1 + lat2) / 2)

        return x_distance, y_distance


def load_config(config):
    folder_path = config['info']['h5_data_path']

    # esterno_radars 딕셔너리를 생성
    esterno_radars = {
        '1.0.0.20': Radar(config['esterno']['radar_gps_1.0.0.20'], config['esterno']['radar_azi_angle_1.0.0.20']),
        '1.0.0.21': Radar(config['esterno']['radar_gps_1.0.0.21'], config['esterno']['radar_azi_angle_1.0.0.21']),
        '1.0.0.22': Radar(config['esterno']['radar_gps_1.0.0.22'], config['esterno']['radar_azi_angle_1.0.0.22']),
        '1.0.0.23': Radar(config['esterno']['radar_gps_1.0.0.23'], config['esterno']['radar_azi_angle_1.0.0.23']),
        '1.0.0.24': Radar(config['esterno']['radar_gps_1.0.0.24'], config['esterno']['radar_azi_angle_1.0.0.24']),
        '1.0.0.25': Radar(config['esterno']['radar_gps_1.0.0.25'], config['esterno']['radar_azi_angle_1.0.0.25']),
    }

    # interno_radars 딕셔너리를 생성
    interno_radars = {
        '1.0.0.10': Radar(config['interno']['radar_gps_1.0.0.10'], config['interno']['radar_azi_angle_1.0.0.10']),
        '1.0.0.11': Radar(config['interno']['radar_gps_1.0.0.11'], config['interno']['radar_azi_angle_1.0.0.11']),
        '1.0.0.12': Radar(config['interno']['radar_gps_1.0.0.12'], config['interno']['radar_azi_angle_1.0.0.12']),
        '1.0.0.13': Radar(config['interno']['radar_gps_1.0.0.13'], config['interno']['radar_azi_angle_1.0.0.13']),
    }

    # landmark_position 리스트를 생성
    landmark_position = config['info']['center_gps']

    max_scan = config['info']['MAX_SCAN']

    return folder_path, esterno_radars, interno_radars, landmark_position, max_scan


def input_processing(intersection_folder_path : str, radars : dict, landmark_position : list, max_scan_num : int):
    fusion_inputs = {}

    h5_files = [f'{intersection_folder_path}/'+file for file in os.listdir(intersection_folder_path) if file.endswith('.h5')]
    for h5_file in h5_files:
        file_path = os.path.join(intersection_folder_path, h5_file)
        ip = file_path.split('_')[-1][:-3]
        fusion_inputs[ip] = []
        radar = radars[ip]

        radar_gps = radar.position
        landmark_gps = landmark_position

        x_distance, y_distance = calculate_xy_distance(landmark_gps, radar_gps)

        radar_diff_x_meter = x_distance
        radar_diff_y_meter = y_distance

        theta = np.deg2rad(radar.deg + 90)
        
        transition_matrix_meter = np.array([[math.cos(theta), - math.sin(theta), radar_diff_x_meter],
                                    [math.sin(theta), math.cos(theta), radar_diff_y_meter],
                                    [0,0,1]])
        

        transition_matrix_vector = np.array([
            [np.cos(theta), -np.sin(theta)],
            [np.sin(theta), np.cos(theta)]
        ])

        # h5 파일 열기
        with h5py.File(file_path, 'r') as h5_file_data:
            data_dict = h5_file_data
            for scan_num in tqdm(range(max_scan_num)): 
                scan_wise_fusion_inputs = []
                for fobj in data_dict['SCAN_{:05d}'.format(scan_num)]['Object'][:]:
                    new_obj = Obj()
                    new_obj.info       = ip 
                    new_obj.id         = fobj[0]
                    new_obj.status     = fobj[1]
                    new_obj.update_state =fobj[2]
                    new_obj.move_state = fobj[3]
                    new_obj.alive_age  = fobj[4]
                    posx                = fobj[5]
                    posy                = fobj[6]
                    new_obj.ref_posx    = fobj[7]
                    new_obj.ref_posy    = fobj[8]
                    velx                = fobj[9]
                    vely                = fobj[10]
                    heading_angle_deg   = fobj[11]  # 로컬 헤딩
                    new_obj.power       = fobj[12]
                    width               = fobj[13]
                    length              = fobj[14]
                    new_obj.class_id    = fobj[15]
                    new_obj.fusion_type = fobj[16]
                    new_obj.fusion_age  = fobj[17]

                    
                    position = np.array([[posx],[posy],[1]]) 
                    position = np.dot(transition_matrix_meter,position)

                    posx = position[0][0]
                    posy = position[1][0]

                    velocity = np.array([[velx],[vely]])
                    velocity = np.dot(transition_matrix_vector,velocity)

                    velx = velocity[0][0]
                    vely = velocity[1][0]


                    heading_angle_deg += (np.rad2deg(theta))

                    # 업데이트된 좌표와 속도 및 heading angle 적용
                    new_obj.posx   = posx
                    new_obj.posy   = posy
                    new_obj.velx   = velx
                    new_obj.vely   = vely
                    new_obj.width  = width
                    new_obj.length = length
                    new_obj.heading_angle_deg = heading_angle_deg
                    scan_wise_fusion_inputs.append(new_obj)
                fusion_inputs[ip].append(scan_wise_fusion_inputs)
    return fusion_inputs
