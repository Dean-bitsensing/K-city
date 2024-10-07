import os
import h5py
import numpy as np
import utm  # UTM 좌표계로 변환
from geopy.distance import geodesic  # GPS 거리 계산
from .fusion_data_classes import *

# GPS 좌표 (위도, 경도)를 UTM 좌표로 변환하는 함수
def gps_to_utm(latitude, longitude):
    utm_coords = utm.from_latlon(latitude, longitude)
    return np.array([utm_coords[0], utm_coords[1]])  # UTM 좌표계에서 x, y 반환

# Radar 클래스 정의
class Radar:
    def __init__(self, gps_position, radar_orientation_deg):
        """
        :param gps_position: 레이더의 GPS 좌표 (위도, 경도)
        :param radar_orientation_deg: 레이더의 방향 (각도, degrees)
        """
        self.position = gps_to_utm(*gps_position)  # GPS 좌표를 UTM 좌표로 변환
        self.orientation_rad = np.deg2rad(radar_orientation_deg)  # 각도를 라디안으로 변환
        self.orientation_deg = radar_orientation_deg  # 각도를 그대로 저장

    def transform_to_world_coordinates(self, local_objects, landmark_position):
        """
        로컬 좌표에 있는 객체를 월드 좌표계(landmark 기준)로 변환
        :param local_objects: 레이더 센서에서 수집한 객체들의 좌표 [[x1, y1], [x2, y2], ...]
        :param landmark_position: 랜드마크의 GPS 좌표 (위도, 경도)
        :return: 월드 좌표계로 변환된 객체 좌표 (landmark 기준)
        """
        # 로컬 좌표를 넘파이 배열로 변환
        local_objects = np.array(local_objects)

        # 회전 변환 행렬 (Z축 평면에서의 2D 회전)
        rotation_matrix = np.array([
            [np.cos(self.orientation_rad), -np.sin(self.orientation_rad)],
            [np.sin(self.orientation_rad), np.cos(self.orientation_rad)]
        ])

        # 회전 변환 후 평행 이동
        world_objects = np.dot(local_objects, rotation_matrix.T) + self.position

        # 랜드마크 기준으로 변환 (landmark를 원점으로 설정)
        landmark_utm = gps_to_utm(*landmark_position)
        world_objects_landmark_relative = world_objects - landmark_utm

        return world_objects_landmark_relative

    def transform_heading_to_world(self, heading_angle_local):
        """
        차량의 로컬 heading angle을 월드 좌표계로 변환
        :param heading_angle_local: 로컬 좌표계에서의 차량 heading angle (degrees)
        :return: 월드 좌표계에서의 차량 heading angle (degrees)
        """
        heading_world = (heading_angle_local + self.orientation_deg) % 360
        return heading_world


radars = { 
    '1.0.0.20' : Radar([45.43072430000016, 10.98769880000001], 9),
    '1.0.0.21' : Radar([45.430227500000164, 10.987823700000048], 18),
    '1.0.0.22' : Radar([45.430359, 10.9882485], 67),
    '1.0.0.23' : Radar([45.430319, 10.9883385], 0),
    '1.0.0.24' : Radar([45.43077730000001, 10.987771800000045], 246.71),
    '1.0.0.25' : Radar([45.4301545, 10.9879317], -27.1)
}

landmark_position = [45.4310364, 10.988078] 



def input_processing(intersection_folder_path : str):
    fusion_inputs = {}
    h5_files = [f'{intersection_folder_path}/'+file for file in os.listdir(intersection_folder_path) if file.endswith('.h5')]
    for h5_file in h5_files:
        file_path = os.path.join(intersection_folder_path, h5_file)
        ip = file_path.split('_')[-1][:-3]
        fusion_inputs[ip] = []
        radar = radars[ip]
        # h5 파일 열기
        with h5py.File(file_path, 'r') as h5_file_data:
            data_dict = h5_file_data
            for scan_num in range(200):  # 테스트를 위해 10번만 처리
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

                    # 좌표 변환
                    posx = -posx
                    velx = -velx
                    world_pos = radar.transform_to_world_coordinates([posx, posy], landmark_position)
                    world_vel = radar.transform_to_world_coordinates([velx, vely], landmark_position)
                    posx, posy = world_pos
                    velx, vely = world_vel

                    # Heading angle을 월드 좌표계로 변환
                    heading_angle_world = radar.transform_heading_to_world(heading_angle_deg)

                    # 업데이트된 좌표와 속도 및 heading angle 적용
                    new_obj.posx   = posx
                    new_obj.posy   = posy
                    new_obj.velx   = velx
                    new_obj.vely   = vely
                    new_obj.width  = width
                    new_obj.length = length
                    new_obj.heading_angle_deg = heading_angle_world
                    scan_wise_fusion_inputs.append(new_obj)
                fusion_inputs[ip].append(scan_wise_fusion_inputs)
    return fusion_inputs
