import math
import numpy as np
from .fusion_data_classes import *

BACKWARD_VIEW = ['A04B200002', 'A04B200006',]

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


def local_to_world_coordinate_meter(posx, posy, atm_heading_angle, atm_gps, center_gps):

    radar_diff_x_meter, radar_diff_y_meter = calculate_xy_distance(center_gps, atm_gps)
    theta = np.deg2rad(atm_heading_angle+90)

    transition_matrix_meter = np.array([[math.cos(theta), - math.sin(theta), radar_diff_x_meter],
                                    [math.sin(theta), math.cos(theta), radar_diff_y_meter],
                                    [0,0,1]])
    
    position = np.array([[posx],[posy],[1]]) 
    position = np.dot(transition_matrix_meter,position)

    return position[0][0], position[1][0]

def local_to_world_coordinate_velocity(velx, vely, atm_heading_angle):

    theta = np.deg2rad(atm_heading_angle+90)

    transition_matrix_vector = np.array([
            [np.cos(theta), -np.sin(theta)],
            [np.sin(theta), np.cos(theta)]
        ])
    
    velocity = np.array([[velx],[vely]]) 
    velocity = np.dot(transition_matrix_vector,velocity)

    return velocity[0][0], velocity[1][0]


def input_processing(root_message, devices):
    ATM_info = {}
    #fusion_input = {}

    #Verona Specific Logic
    esterno_fusion_input= {}
    interno_fusion_input = {}
    timestamps = []

    atm_count = len(devices)
    time_length = len(root_message.data)

    center_coordinate = [0,0]

    # Initializing Empty List in Fusion Inputs per Serial Number
    for device in devices:
        serial_number = device['deviceId']
        ATM_info[serial_number] = {}
        ATM_info[serial_number]['lat'] = device['lat']
        ATM_info[serial_number]['lng'] = device['lng']
        ATM_info[serial_number]['headingAngle'] = 360 - device['headingAngle']
        ATM_info[serial_number]['intersection_info'] = device['alias'].split('_')[0]

        center_coordinate[0] += device['lat']
        center_coordinate[1] += device['lng']

        if ATM_info[serial_number]['intersection_info'] == 'esterno':
            fusion_input = esterno_fusion_input
        else:
            fusion_input = interno_fusion_input

        fusion_input[serial_number] = [[] for _ in range(time_length)]


    #Calculate Existing ATM's Center Coordinate to Unite Coordinate
    center_coordinate[0]/=atm_count
    center_coordinate[1]/=atm_count

    ATM_info['center'] = {}
    ATM_info['center']['lat'] = center_coordinate[0]
    ATM_info['center']['lng'] = center_coordinate[1]

    for scan_num, timestamp_data in enumerate(root_message.data):
        timestamps.append(timestamp_data.timestamp)
        object_data = timestamp_data.object_data
        for serial_number in object_data.keys():

            atm_heading_angle = ATM_info[serial_number]['headingAngle']
            atm_coordinate = [ATM_info[serial_number]['lat'], ATM_info[serial_number]['lng']]

            if ATM_info[serial_number]['intersection_info'] == 'esterno':
                fusion_input = esterno_fusion_input
            else:
                fusion_input = interno_fusion_input
            for object in object_data[serial_number].states:
                new_obj = Obj()
                new_obj.id = object.id
                new_obj.info = serial_number
                new_obj.update_state = object.state_0
                new_obj.status = object.state_2
                new_obj.move_state = object.state_3
                new_obj.alive_age = object.aliveage
                new_obj.heading_angle_deg = object.headang
                new_obj.width = object.width
                new_obj.length = object.length
                new_obj.class_id = object.class_type
                new_obj.fusion_type = object.fusion_type
                new_obj.associated_ip = serial_number

                # Local Coordinate to World Coordinate
                new_obj.posx ,new_obj.posy = local_to_world_coordinate_meter(object.xpos, object.ypos, atm_heading_angle, atm_coordinate,center_coordinate)
                new_obj.velx, new_obj.vely = local_to_world_coordinate_velocity(object.xvel, object.yvel, atm_heading_angle)
                new_obj.heading_angle_deg = (object.headang + atm_heading_angle + 90)%360
                    

                # Append to fusion input scan
                fusion_input[serial_number][scan_num].append(new_obj)

    return esterno_fusion_input, interno_fusion_input, timestamps, ATM_info

                 
        
