from .data_class_models import *
from .colors import *
import h5py, json
import numpy as np
import math
import os
import sys
import requests
from io import BytesIO
from PIL import Image

######## Data Models ########


# Intersection 

class Intersection():
    def __init__(self, config : dict, intersection_name : str, landmark : tuple): # config = config['verona']['intersection_name']
        
        # Set color set to differenciate ATMs

        self.color_set = (BLUE, SKYBLUE, RED, YELLOW, PINK, INDIGO, RED, YELLOW)

        # Set list to take multiple h5 files and ATMs

        self.h5_files = []
        self.atms = []

        self.landmark = landmark # [0] : lat, [1] : long
        
       
         
        ###need to be reafactorized
        self.config = config
        self.name = intersection_name


        # Set Parameter to check if this intersection is clicked

        self.is_clicked = False

    def initiate(self):
        self.set_h5_files()
        self.set_atms()

    def set_h5_files(self):
        logging_data_path = self.config['folder_path']
        self.h5_files = [f'{logging_data_path}/'+file for file in os.listdir(logging_data_path) if file.endswith('.h5')]
        
    def set_atms(self):
        self.metadata_path = self.config['metadata_path']
        # metadata_folders = [os.path.join(metadata_path, name) for name in os.listdir(metadata_path) 
        #               if os.path.isdir(os.path.join(metadata_path, name))]
        # print(metadata_folders)

        for idx, h5_file in enumerate(self.h5_files):
            ip = h5_file.split('_')[-1][:-3]
            lat = self.config['radar_gps_'+ip][0]
            long = self.config['radar_gps_'+ip][1]
            azi_angle = self.config['radar_azi_angle_'+ip]
            atm_color = self.color_set[idx]

            metadat_folder = os.path.join(self.metadata_path, ip)

            # 각 JSON 파일을 읽어 파싱하는 부분 (UTF-8 인코딩 지정)
            try:
                with open(os.path.join(metadat_folder, 'radar_lane_json.json'), 'r', encoding='utf-8-sig') as f:
                    radar_lane_json = json.load(f)['param']['setup']
            except:
                radar_lane_json = None
                print(f'There is no radar_lane data | path : {metadat_folder}')
                
            try:
                with open(os.path.join(metadat_folder, 'radar_zone_json.json'), 'r', encoding='utf-8-sig') as f:
                    radar_zone_json = json.load(f)['param']['setup']
            except:
                radar_zone_json = None
                print(f'There is no radar zone data | path : {metadat_folder}')

            try:
                with open(os.path.join(metadat_folder, 'image_lane_json.json'), 'r', encoding='utf-8-sig') as f:
                    image_lane_json = json.load(f)['param']['setup']
            except:
                image_lane_json = None
                print(f'There is no image lane data | path : {metadat_folder}')
            try:
                with open(os.path.join(metadat_folder, 'image_zone_json.json'), 'r', encoding='utf-8-sig') as f:
                    image_zone_json = json.load(f)['param']['setup']
            except:
                image_zone_json = None
                print(f'There is no image zone data | path : {metadat_folder}')

            lut_lat     = None
            lut_long    = None
            print(radar_lane_json)
            #TODO should be removed
            if ip[-2] == '1':
                atm_color = INDIGO
            atm = Atm(lat, long, azi_angle, atm_color, h5_file, self.landmark, 
                      radar_lane_json, radar_zone_json, image_lane_json, image_zone_json, lut_lat, lut_long, 
                      self)
            if atm not in self.atms:
                self.atms.append(atm)

    def set_intersection_center_gps(self):
        self.intersection_lat = self.config['center_gps'][0]
        self.intersection_long = self.config['center_gps'][1]


# ATM

class Atm(Intersection):
    def __init__(self, lat, long, azi_angle, atm_color, logging_data_path, landmark, radar_lane_json, radar_zone_json, image_lane_json, image_zone_json, lut_lat, lut_long, intersection):

        self.view = True

        # set IP and Intersection number according to file_path

        self.logging_data_path = logging_data_path
        self.logging_data = h5py.File(logging_data_path)
        self.ip = logging_data_path.split('_')[-1][:-3]
        self.intersection_number = int(self.ip.split('.')[-1])//10


        # set ATM's Latitude, Longitude, Color and Angle that ATM is currently watching oriented from config file

        self.atm_lat = lat
        self.atm_long = long
        self.atm_azi_angle = azi_angle
        self.landmark = landmark
        self.color = atm_color

        self.intersection = intersection

        """ MetaData """
        self.radar_zone_json = radar_zone_json
        self.radar_lane_json = radar_lane_json
        self.image_zone_json = image_zone_json
        self.image_lane_json = image_lane_json
        self.lut_lat = None
        self.lut_long = None

        self.zones = []
        self.lanes = []
        self.get_zone_lane_mode = 1

        # set initial value of list used to get obj info individually
        self.updated = False
        self.selected = False
        self.vds_view = False
        self.selected_vobj_id = []
        self.selected_fobj_id = []
        # self.config = 


        self.center_x = 0 
        self.center_y = 0 

    def get_scan_data(self, current_scan, center_x, center_y):
        
        current_scan_data = ScanData(current_scan, self)
        
        #current_scan_data.parsing_status() -> TODO: if gps coordinates become more accurate then will use sensor info 

        current_scan_data.parsing_gps_into_meter(center_x,center_y)     # 1. gps coordinate to pygame pixel coordinate 
        current_scan_data.parsing_fusion_object_data()                  # 2. parse fusion obj from h5 and change it to world coordinate
        current_scan_data.parsing_vision_object_data()                  # 3. parse vision obj from h5 and change it to world coordinate
        # current_scan_data.parsing_radar_object_data()                 # 4. parse radar obj from h5 and change it to world coordinate -> TODO
        current_scan_data.parsing_image()                               # 5. parse image from h5 

        current_scan_data.calc_lane_and_zone()
        # if self.get_zone_lane_mode:
        #     current_scan_data.calc_lane_and_zone()
        #     self.get_zone_lane_mode = 0

        self.current_scan_data = current_scan_data
    
    def clear_selected_obj_id(self):
        self.selected = False
        self.selected_vobj_id = []
        self.selected_fobj_id = []
    

    def write_radar_zone_to_json(self):
        metadata_folder = self.intersection.metadata_path
        ip = self.ip

        # JSON 파일 경로 설정

        self.radar_diff_x = self.current_scan_data.radar_diff_x
        self.radar_diff_y = self.current_scan_data.radar_diff_y
        self.center_x = self.current_scan_data.center_x
        self.center_y = self.current_scan_data.center_y
        self.azi_theta = self.current_scan_data.azi_theta

        radar_zone_file = os.path.join(metadata_folder, ip, 'radar_zone_json.json')

        # 기존 JSON 데이터 읽어오기
        try:
            with open(radar_zone_file, 'r', encoding='utf-8-sig') as f:
                radar_zone_data = json.load(f)
        except FileNotFoundError:
            print(f"Radar zone JSON file not found at {radar_zone_file}")
            return

        # 역변환 행렬 계산
        azi_theta = self.azi_theta * math.pi / 180  # 북쪽 기준 반시계 방향 각도
        theta = math.pi / 2 - azi_theta

        # 변환 행렬
        transition_matrix = np.array([[math.cos(theta), -math.sin(theta), self.radar_diff_x],
                                    [math.sin(theta), math.cos(theta), self.radar_diff_y],
                                    [0, 0, 1]])
        transition_matrix2 = np.array([[1, 0, self.center_x],
                                    [0, 1, self.center_y],
                                    [0, 0, 1]])

        # 역변환 행렬 계산
        inverse_transform = np.linalg.inv(np.dot(transition_matrix2, transition_matrix))

        # 변경된 좌표 데이터를 반영하여 JSON 파일 수정
        radar_zone_count = len(self.zones)

        for nth_zone in range(radar_zone_count):
            zone = self.zones[nth_zone]
            radar_zone_info = radar_zone_data['param']['setup']['detection_zone'][nth_zone]['lane_info']

            # zone 좌표를 원래의 미터 단위로 변환하여 다시 기록
            for idx in range(zone.step_number):
                # 역변환 행렬 적용 (좌표를 원래 값으로 복원)
                left_pos = np.array([[zone.left_x[idx]], [zone.left_y[idx]], [1]])
                right_pos = np.array([[zone.right_x[idx]], [zone.right_y[idx]], [1]])

                # 역변환
                left_orig = np.dot(inverse_transform, left_pos)
                right_orig = np.dot(inverse_transform, right_pos)

                # 변환된 좌표를 미터로 변환 후 JSON에 저장
                radar_zone_info['lane_pos']['left_lat'][idx] = pixels_to_meters(
                    left_orig[1][0], self.landmark[0], self.landmark[2], (640, 640), (self.center_x * 2, self.center_y * 2)
                )
                radar_zone_info['lane_pos']['left_long'][idx] = pixels_to_meters(
                    (-1) * left_orig[0][0], self.landmark[0], self.landmark[2], (640, 640), (self.center_x * 2, self.center_y * 2)
                )
                radar_zone_info['lane_pos']['right_lat'][idx] = pixels_to_meters(
                    right_orig[1][0], self.landmark[0], self.landmark[2], (640, 640), (self.center_x * 2, self.center_y * 2)
                )
                radar_zone_info['lane_pos']['right_long'][idx] = pixels_to_meters(
                    (-1) * right_orig[0][0], self.landmark[0], self.landmark[2], (640, 640), (self.center_x * 2, self.center_y * 2)
                )

        # 수정된 데이터를 JSON 파일로 기록
        with open(radar_zone_file, 'w', encoding='utf-8') as f:
            json.dump(radar_zone_data, f, ensure_ascii=False, indent=4)

        print(f"Radar zone data successfully written to {radar_zone_file}")




#Scan Data per ATM 
class RadarZone:
    def __init__(self):
        self.changed = False
        self.left_x = []
        self.left_y = []
        self.right_x = []
        self.right_y = []
        self.step_number = 0
        self.guid :str = None


class ScanData(Atm):
    def __init__(self,current_scan, atm):
        self.atm = atm
        self.current_scan = current_scan
        self.logging_data = self.atm.logging_data
        self.current_scan_data = self.logging_data['SCAN_{:05d}'.format(current_scan)]
        self.atm_lat = self.atm.atm_lat
        self.atm_long = self.atm.atm_long
        self.atm_azi_angle = self.atm.atm_azi_angle
        self.landmark = self.atm.landmark

    def parsing_status(self):
        status_data = self.current_scan_data['Status'][:]
        self.status_json = json.loads(status_data.tobytes().decode('utf-8'))

    def parsing_image(self):
        self.image = self.current_scan_data['Image'][()]

    def calc_lane_and_zone(self):
        if self.atm.radar_zone_json == None:
            return 
        self.atm.zones = []
        self.azi_theta = self.atm_azi_angle

        azi_theta = self.azi_theta * math.pi / 180 #  북쪽기준으로 반시계 방향으로 얼마나 회전했는가

        theta = math.pi/2 - azi_theta

        transition_matrix = np.array([[math.cos(theta), - math.sin(theta), self.radar_diff_x],
                                      [math.sin(theta), math.cos(theta), self.radar_diff_y],
                                      [0,0,1]])
        
        transition_matrix2 = np.array([[1, 0, self.center_x],
                                      [0, 1, self.center_y],
                                      [0,0,1]])
        # Radar zone
        def tf(x, y, transition_matrix, transition_matrix2):
            position = np.array([[x],[y],[1]])
            position = np.dot(transition_matrix,position)
            position = np.dot(transition_matrix2, position)
            x = position[0][0]
            y = position[1][0]
            return x, y
        radar_zone_count = self.atm.radar_zone_json['zone_count']

        for nth_zone in range(radar_zone_count):
            radar_zone_info = self.atm.radar_zone_json['detection_zone'][nth_zone]['lane_info']
            zone = RadarZone()
            zone.guid = radar_zone_info['guid']
            zone.step_number = radar_zone_info['num_lane_step']

            zone.left_y = np.array(radar_zone_info['lane_pos']['left_lat'])
            zone.left_x = np.array(radar_zone_info['lane_pos']['left_long'])
            zone.right_y = np.array(radar_zone_info['lane_pos']['right_lat'])
            zone.right_x = np.array(radar_zone_info['lane_pos']['right_long'])


            # zone.left_x = np.array(radar_zone_info['lane_pos']['left_lat'])
            # zone.left_y = np.array(radar_zone_info['lane_pos']['left_long'])
            # zone.right_x = np.array(radar_zone_info['lane_pos']['right_lat'])
            # zone.right_y = np.array(radar_zone_info['lane_pos']['right_long'])

            zone.left_x = (-1) * zone.left_x
            zone.right_x = (-1) * zone.right_x
            
            for idx in range(zone.step_number):
                zone.left_x[idx]  = meters_to_pixels(zone.left_x[idx], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
                zone.left_y[idx]  = meters_to_pixels(zone.left_y[idx], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
                zone.right_x[idx] = meters_to_pixels(zone.right_x[idx], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
                zone.right_y[idx] = meters_to_pixels(zone.right_y[idx], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))

                zone.left_x[idx], zone.left_y[idx] = tf(zone.left_x[idx], zone.left_y[idx], transition_matrix, transition_matrix2)
                zone.right_x[idx], zone.right_y[idx] = tf(zone.right_x[idx], zone.right_y[idx], transition_matrix, transition_matrix2)
                
            self.atm.zones.append(zone)

        # Radar lane

    def parsing_fusion_object_data(self):
        self.fusion_object_data = []
        self.fusion_object_data_vel = []

        theta = np.deg2rad(self.atm_azi_angle + 90)

        transition_matrix_meter = np.array([[math.cos(theta), - math.sin(theta), self.radar_diff_x_meter],
                            [math.sin(theta), math.cos(theta), self.radar_diff_y_meter],
                            [0,0,1]])
        

        transition_matrix_vector = np.array([
            [np.cos(theta), -np.sin(theta)],
            [np.sin(theta), np.cos(theta)]
        ])
        
        
        for fobj in self.current_scan_data['Object'][:]:
            new_fobj = FusionObj()

            new_fobj.id         = fobj[0]
            posx                = fobj[5]
            posy                = fobj[6]
            velx                = fobj[9]
            vely                = fobj[10]
            heading_angle_deg   = fobj[11]
            width               = fobj[13]
            length              = fobj[14]

            position = np.array([[posx],[posy],[1]]) 
            position = np.dot(transition_matrix_meter,position)

            posx = position[0][0]
            posy = position[1][0]

            velocity = np.array([[velx],[vely]])
            velocity = np.dot(transition_matrix_vector,velocity)

            velx = velocity[0][0]
            vely = velocity[1][0]


            heading_angle_deg += (np.rad2deg(theta))

            new_fobj.posx   = posx
            new_fobj.posy   = posy
            new_fobj.velx   = velx
            new_fobj.vely   = vely
            new_fobj.width  = width
            new_fobj.length = length
            new_fobj.heading_angle_deg = heading_angle_deg

            self.fusion_object_data.append(new_fobj)           


    def parsing_vision_object_data(self):
        self.vision_object_data = []
        self.vision_object_data_vel = []

        self.azi_theta = self.atm_azi_angle

        azi_theta = self.azi_theta * math.pi / 180 #  북쪽기준으로 반시계 방향으로 얼마나 회전했는가
        
        theta = math.pi/2 - azi_theta

        transition_matrix = np.array([[math.cos(theta), - math.sin(theta), self.radar_diff_x],
                                      [math.sin(theta), math.cos(theta), self.radar_diff_y],
                                      [0,0,1]])
        
        transition_matrix2 = np.array([[1, 0, self.center_x],
                                      [0, 1, self.center_y],
                                      [0,0,1]])
        
        
        
        def tf(pos, transition_matrix, transition_matrix2):
            
            position = np.array([[pos[0]],[pos[1]],[1]])
            position = np.dot(transition_matrix,position)
            position = np.dot(transition_matrix2, position)
            pos[0] = position[0][0]
            pos[1] = position[1][0]

            return pos
        
        for vobj in self.current_scan_data['Vision_object'][:]:
            new_vobj = VisionObj()

            new_vobj.id          = vobj[0]
            new_vobj.bbox_posx   = vobj[3]
            new_vobj.bbox_posy   = vobj[4]
            new_vobj.bbox_width  = vobj[5]
            new_vobj.bbox_length = vobj[6]

            posx = vobj[11]
            posy = vobj[12]
            posx = -posx

            new_vobj.before_posx = posx
            new_vobj.before_posy = posy

            width = vobj[15]
            length = vobj[16]

            ul_pos = [int(posx - length/2), int(posy - width/2)]
            ur_pos = [int(posx - length/2), int(posy + width/2)]
            dl_pos = [int(posx + length/2), int(posy - width/2)]
            dr_pos = [int(posx + length/2), int(posy + width/2)]

            velx = vobj[13]
            vely = vobj[14]
            velx = -velx
            
            posx = meters_to_pixels(posx, self.landmark[0], 18, (640, 640), (self.center_x*2, self.center_y*2))
            posy = meters_to_pixels(posy, self.landmark[0], 18, (640, 640), (self.center_x*2, self.center_y*2))
            
            ul_pos[0] = meters_to_pixels(ul_pos[0], self.landmark[0], 18, (640, 640), (self.center_x*2, self.center_y*2))
            ul_pos[1] = meters_to_pixels(ul_pos[1], self.landmark[0], 18, (640, 640), (self.center_x*2, self.center_y*2))

            ur_pos[0] = meters_to_pixels(ur_pos[0], self.landmark[0], 18, (640, 640), (self.center_x*2, self.center_y*2))
            ur_pos[1] = meters_to_pixels(ur_pos[1], self.landmark[0], 18, (640, 640), (self.center_x*2, self.center_y*2))
            dl_pos[0] = meters_to_pixels(dl_pos[0], self.landmark[0], 18, (640, 640), (self.center_x*2, self.center_y*2))
            dl_pos[1] = meters_to_pixels(dl_pos[1], self.landmark[0], 18, (640, 640), (self.center_x*2, self.center_y*2))
            dr_pos[0] = meters_to_pixels(dr_pos[0], self.landmark[0], 18, (640, 640), (self.center_x*2, self.center_y*2))
            dr_pos[1] = meters_to_pixels(dr_pos[1], self.landmark[0], 18, (640, 640), (self.center_x*2, self.center_y*2))

            ul_pos = tf(ul_pos, transition_matrix, transition_matrix2)
            ur_pos = tf(ur_pos, transition_matrix, transition_matrix2)
            dl_pos = tf(dl_pos, transition_matrix, transition_matrix2)
            dr_pos = tf(dr_pos, transition_matrix, transition_matrix2)


            velx = meters_to_pixels(velx, self.landmark[0], 18, (640, 640), (self.center_x*2, self.center_y*2))
            vely = meters_to_pixels(vely, self.landmark[0], 18, (640, 640), (self.center_x*2, self.center_y*2))
            
            position = np.array([[posx],[posy],[1]])
            position = np.dot(transition_matrix,position)
            position = np.dot(transition_matrix2, position)
            posx = position[0][0]
            posy = position[1][0]

            velocity = np.array([[velx],[vely],[1]])
            velocity = np.dot(transition_matrix,velocity)
            velocity = np.dot(transition_matrix2, velocity)
            velx = velocity[0][0]
            vely = velocity[1][0]

            new_vobj.posx = posx
            new_vobj.posy = posy
            new_vobj.width = vobj[15] # TODO 수정해야함
            new_vobj.length = vobj[16]
            new_vobj.velx = velx - self.radar_posx
            new_vobj.vely = vely - self.radar_posy

            new_vobj.ul_pos = ul_pos
            new_vobj.ur_pos = ur_pos
            new_vobj.dl_pos = dl_pos
            new_vobj.dr_pos = dr_pos

            self.vision_object_data.append(new_vobj)


    def parsing_gps_into_meter(self, center_x, center_y):
        def latlng_to_pixel(lat, lng, center_lat, center_lng, zoom, map_size, window_size):
            
            TILE_SIZE = 256
            scale = 2 ** zoom  # 줌 레벨에 따른 스케일

            # 경도를 픽셀로 변환
            def lng_to_pixel_x(lng):
                return (lng + 180) / 360 * scale * TILE_SIZE

            # 위도를 픽셀로 변환 (머케이터 도법)
            def lat_to_pixel_y(lat):
                siny = math.sin(lat * math.pi / 180)
                y = math.log((1 + siny) / (1 - siny))
                return (1 - y / (2 * math.pi)) * scale * TILE_SIZE / 2

            # 지도 중심 좌표의 픽셀 좌표 구하기
            center_x = lng_to_pixel_x(center_lng)
            center_y = lat_to_pixel_y(center_lat)

            # 주어진 좌표의 픽셀 좌표 구하기
            pixel_x = lng_to_pixel_x(lng) - center_x + map_size[0] // 2
            pixel_y = lat_to_pixel_y(lat) - center_y + map_size[1] // 2

            # 창 크기 대비 지도 크기에 따른 비율로 스케일링
            scale_x = window_size[0] / map_size[0]
            scale_y = window_size[1] / map_size[1]

            # Pygame 창 상의 픽셀 좌표로 변환
            pixel_x_on_window = int(pixel_x * scale_x)
            pixel_y_on_window = int(pixel_y * scale_y)

            return pixel_x_on_window, pixel_y_on_window
        
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

        # 두 좌표 정의 (위도, 경도)
        radar_gps = (self.atm_lat, self.atm_long)  
        landmark_gps = (self.landmark[0], self.landmark[1]) 

        # x, y 거리 계산
        x_distance, y_distance = calculate_xy_distance(landmark_gps, radar_gps)
        print(f"Radar IP : {self.atm.ip}")
        print(f"x 방향 거리 (동서 방향): {x_distance:.2f} meters")
        print(f"y 방향 거리 (남북 방향): {y_distance:.2f} meters")

        self.latitiude = self.atm_lat
        self.longitude = self.atm_long

       
        
        # test
        ##
        radar_x, radar_y = latlng_to_pixel(self.latitiude, self.longitude, self.landmark[0], self.landmark[1], self.landmark[2], (640, 640), (center_x*2, center_y*2))
    
        self.radar_diff_x_meter = x_distance
        self.radar_diff_y_meter = y_distance

        self.radar_diff_x = radar_x - center_x # pixel
        self.radar_diff_y = radar_y - center_y 
        self.center_x = center_x
        self.center_y = center_y
        self.radar_posx = radar_x
        self.radar_posy = radar_y    
         


### Calculation Functions ###

def tf(pos : tuple, transition_matrix : list , transition_matrix2 : list):
            
            position = np.array([[pos[0]],[pos[1]],[1]])
            position = np.dot(transition_matrix,position)
            position = np.dot(transition_matrix2, position)
            pos[0] = position[0][0]
            pos[1] = position[1][0]

            return pos
    
def meters_to_pixels(meters, lat, zoom, map_size, window_size):

    # 지구의 둘레 (Equatorial Circumference) = 40,075km
    EARTH_RADIUS = 6378137  # meters

    # 위도를 라디안으로 변환
    lat_rad = math.radians(lat)

    # 지도 상에서 한 픽셀당 미터를 계산 (줌 레벨과 위도에 따라 다름)
    meters_per_pixel = (math.cos(lat_rad) * 2 * math.pi * EARTH_RADIUS) / (2 ** zoom * 256)

    # 주어진 미터를 원본 지도 상의 픽셀로 변환
    pixels = meters / meters_per_pixel

    # 창 크기 대비 지도 크기에 따른 비율로 스케일링
    scale_x = window_size[0] / map_size[0]
    scale_y = window_size[1] / map_size[1]

    # 창에서의 픽셀 크기로 변환
    pixels_on_window = pixels * (scale_x + scale_y) / 2  # 가로 세로 비율의 평균 사용

    return pixels_on_window


def pixels_to_meters(pixels, lat, zoom, map_size, window_size):
    # 지구의 둘레 (Equatorial Circumference) = 40,075km
    EARTH_RADIUS = 6378137  # meters

    # 위도를 라디안으로 변환
    lat_rad = math.radians(lat)

    # 지도 상에서 한 픽셀당 미터를 계산 (줌 레벨과 위도에 따라 다름)
    meters_per_pixel = (math.cos(lat_rad) * 2 * math.pi * EARTH_RADIUS) / (2 ** zoom * 256)

    # 창 크기 대비 지도 크기에 따른 비율로 스케일링
    scale_x = window_size[0] / map_size[0]
    scale_y = window_size[1] / map_size[1]

    # 창에서의 픽셀 크기를 지도 상의 픽셀 크기로 변환
    pixels_on_map = pixels / ((scale_x + scale_y) / 2)  # 가로 세로 비율의 평균 사용

    # 지도 상의 픽셀을 다시 미터로 변환
    meters = pixels_on_map * meters_per_pixel

    return meters
