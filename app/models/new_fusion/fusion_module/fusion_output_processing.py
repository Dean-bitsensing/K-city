import math
import json
import numpy as np

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


def world_to_local_coordinate_meter(world_x, world_y, atm_heading_angle, atm_gps, center_gps):
    # 중심 GPS와 ATM GPS 사이의 거리 차이를 미터 단위로 계산
    radar_diff_x_meter, radar_diff_y_meter = calculate_xy_distance(center_gps, atm_gps)
    theta = np.deg2rad(atm_heading_angle + 90)

    # 변환 행렬 정의
    transition_matrix_meter = np.array([[math.cos(theta), -math.sin(theta), radar_diff_x_meter],
                                        [math.sin(theta), math.cos(theta), radar_diff_y_meter],
                                        [0, 0, 1]])

    # 변환 행렬의 역행렬 계산
    inverse_transition_matrix_meter = np.linalg.inv(transition_matrix_meter)

    # 월드 좌표를 로컬 좌표로 변환
    world_position = np.array([[world_x], [world_y], [1]])
    local_position = np.dot(inverse_transition_matrix_meter, world_position)

    return local_position[0][0], local_position[1][0]



def save_as_json_file(data : dict, file_name : str):
        with open(file_name, "w") as json_file:
                json.dump(data, json_file, indent=4)


def output_processing(fusion_output, timestamps, ATM_info):
        fusion_result = []

        for scan_num, timestamp in enumerate(timestamps):
                current_scan_fusion_result = {}
                current_scan_fusion_result['timestamp'] = timestamp
                current_scan_fusion_result['objectData'] = {}
                serial_number_fusion_idx = {}

                for serial_number in ATM_info.keys():
                        if serial_number != 'center':
                                current_scan_fusion_result['objectData'][serial_number] = {}
                                current_scan_fusion_result['objectData'][serial_number]['objectID'] = serial_number
                                current_scan_fusion_result['objectData'][serial_number]['states'] = []
                                serial_number_fusion_idx[serial_number] = 0

                fusion_objects = fusion_output[scan_num]

                for fusion_object in fusion_objects:
                        serial_number = fusion_object.associated_ip
                        if not serial_number:
                                continue
                        atm_heading_angle = ATM_info[serial_number]['headingAngle']
                        atm_coordinate = [ATM_info[serial_number]['lat'], ATM_info[serial_number]['lng']]
                        center_coordinate = [ATM_info['center']['lat'], ATM_info['center']['lng']]
                        output_fusion_object = {}
                        output_fusion_object['id'] = serial_number_fusion_idx[serial_number]
                        serial_number_fusion_idx[serial_number] += 1
                        output_fusion_object['state_0'] = fusion_object.update_state
                        output_fusion_object['state_3'] = fusion_object.move_state
                        
                        output_fusion_object['width'] = fusion_object.width
                        output_fusion_object['length'] = fusion_object.length

                        output_fusion_object['xpos'], output_fusion_object['ypos'] = world_to_local_coordinate_meter(fusion_object.posx, fusion_object.posy,atm_heading_angle,atm_coordinate,center_coordinate)
                        output_fusion_object['headang'] = (fusion_object.heading_angle_deg - atm_heading_angle - 90)%360

                        output_fusion_object['classType'] = fusion_object.class_id
                        output_fusion_object['fusionType'] = fusion_object.fusion_type
                        current_scan_fusion_result['objectData'][serial_number]['states'].append(output_fusion_object)

                fusion_result.append(current_scan_fusion_result)

        save_as_json_file(fusion_result, 'fusion_result.json')

        return fusion_result


