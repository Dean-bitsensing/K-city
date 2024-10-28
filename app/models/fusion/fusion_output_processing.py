import math
import numpy as np

def output_processing(fusion_outputs : list, radars : dict, landmark_position : list):
    new_fusion_outputs = {}
    for scan_num in range(len(fusion_outputs)):
       for kobj in fusion_outputs[scan_num]:
        if not kobj.associated_ip:
           continue

        if kobj.associated_ip not in new_fusion_outputs.keys():
           new_fusion_outputs[kobj.associated_ip] = [[] for _ in range(len(fusion_outputs))]

        radar = radars[kobj.associated_ip]

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

        kobj_output = {}

        kobj_output['id'] = kobj.id

        position = np.array([[kobj.posx],[kobj.posy],[1]]) 
        position = np.dot(np.linalg.inv(transition_matrix_meter),position)

        posx = position[0][0]
        posy = position[1][0]

        velocity = np.array([[kobj.velx],[kobj.vely]])
        velocity = np.dot(np.linalg.inv(transition_matrix_vector),velocity)

        velx = velocity[0][0]
        vely = velocity[1][0]


        heading_angle_deg = kobj.heading_angle_deg + (np.rad2deg(theta))

        kobj_output['posx'] = posx
        kobj_output['posy'] = posy
        kobj_output['velx'] = velx
        kobj_output['vely'] = vely

        kobj_output['width'] = kobj.width
        kobj_output['length'] = kobj.length

        kobj_output['headang'] = heading_angle_deg        

        kobj_output['fusion_type'] = kobj.associated_ip

        new_fusion_outputs[kobj.associated_ip][scan_num].append(kobj_output)

    return new_fusion_outputs

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
