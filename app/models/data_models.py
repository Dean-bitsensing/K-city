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
        for idx, h5_file in enumerate(self.h5_files):
            ip = h5_file.split('_')[-1][:-3]
            lat = self.config['radar_gps_'+ip][0]
            long = self.config['radar_gps_'+ip][1]
            azi_angle = self.config['radar_azi_angle_'+ip]
            atm_color = self.color_set[idx]

            #TODO should be removed
            if ip[-2] == '1':
                atm_color = INDIGO
            atm = Atm(lat, long, azi_angle, atm_color, h5_file, self.landmark, self)

            self.atms.append(atm)

    def set_intersection_center_gps(self):
        self.intersection_lat = self.config['center_gps'][0]
        self.intersection_long = self.config['center_gps'][1]


# ATM

class Atm(Intersection):
    def __init__(self, lat, long, azi_angle, atm_color, logging_data_path, landmark, intersection):

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



        # set initial value of list used to get obj info individually
        self.updated = False
        self.selected = False
        self.vds_view = False
        self.selected_vobj_id = []
        self.selected_fobj_id = []
        # self.config = 

    def get_scan_data(self, current_scan, center_x, center_y):

        current_scan_data = ScanData(current_scan, self)
        
        #current_scan_data.parsing_status() -> TODO: if gps coordinates become more accurate then will use sensor info 

        current_scan_data.parsing_gps_into_meter(center_x,center_y)     # 1. gps coordinate to pygame pixel coordinate 
        current_scan_data.parsing_fusion_object_data()                  # 2. parse fusion obj from h5 and change it to world coordinate
        current_scan_data.parsing_vision_object_data()                  # 3. parse vision obj from h5 and change it to world coordinate
        # current_scan_data.parsing_radar_object_data()                 # 4. parse radar obj from h5 and change it to world coordinate -> TODO
        current_scan_data.parsing_image()                               # 5. parse image from h5 

        self.current_scan_data = current_scan_data
    
    def clear_selected_obj_id(self):
        self.selected = False
        self.selected_vobj_id = []
        self.selected_fobj_id = []


#Scan Data per ATM 

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


    def parsing_fusion_object_data(self):
        self.fusion_object_data = []
        self.fusion_object_data_vel = []

        self.azi_theta = self.atm_azi_angle

        azi_theta = self.azi_theta * math.pi / 180 #  북쪽기준으로 반시계 방향으로 얼마나 회전했는가

        theta = math.pi/2 - azi_theta

        transition_matrix = np.array([[math.cos(theta), - math.sin(theta), self.radar_diff_x],
                                      [math.sin(theta), math.cos(theta), self.radar_diff_y],
                                      [0,0,1]])
        
        transition_matrix2 = np.array([[1, 0, self.center_x],
                                      [0, 1, self.center_y],
                                      [0,0,1]])
        
        
        
        def tf(pos, transition_matrix, transition_matrix2, heading_matrix, posx, posy):
            
            position = np.array([[pos[0]],[pos[1]],[1]])
            
            position = np.dot(transition_matrix,position)
            
            position = np.dot(transition_matrix2, position)
            
            pos[0] = position[0][0]
            pos[1] = position[1][0]

            posx_c = pos[0] - posx
            posy_c = pos[1] - posy

            position = np.array([[posx_c],[posy_c],[1]])
            position = np.dot(heading_matrix,position)

            pos[0] = position[0][0] + posx
            pos[1] = position[1][0] + posy

            return pos
        
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

            new_fobj.posx   = posx
            new_fobj.posy   = posy
            new_fobj.velx   = velx
            new_fobj.vely   = vely
            new_fobj.width  = width
            new_fobj.length = length
            new_fobj.heading_angle_deg = heading_angle_deg


            posx = -posx
            velx = -velx
            
            heading_angle_rad = -heading_angle_deg * math.pi/180
            ul_pos = [int(posx - length/2), int(posy - width/2)]
            ur_pos = [int(posx - length/2), int(posy + width/2)]
            dl_pos = [int(posx + length/2), int(posy - width/2)]
            dr_pos = [int(posx + length/2), int(posy + width/2)]

            heading_transition_matrix = np.array([[math.cos(heading_angle_rad), - math.sin(heading_angle_rad), 0],
                                      [math.sin(heading_angle_rad), math.cos(heading_angle_rad), 0],
                                      [0,0,1]])
            
            # self.landmark[0] : landmark lat, self.landmark[1] : landmark long, self.landmark[2] : map zoom
            posx = meters_to_pixels(posx, self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
            posy = meters_to_pixels(posy, self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
            
            ul_pos[0] = meters_to_pixels(ul_pos[0], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
            ul_pos[1] = meters_to_pixels(ul_pos[1], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))

            ur_pos[0] = meters_to_pixels(ur_pos[0], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
            ur_pos[1] = meters_to_pixels(ur_pos[1], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))


            dl_pos[0] = meters_to_pixels(dl_pos[0], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
            dl_pos[1] = meters_to_pixels(dl_pos[1], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))

            dr_pos[0] = meters_to_pixels(dr_pos[0], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
            dr_pos[1] = meters_to_pixels(dr_pos[1], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))

            new_fobj.before_posx = posx
            new_fobj.before_posy = posy
            
            position = np.array([[posx],[posy],[1]])
            position = np.dot(transition_matrix,position)
            position = np.dot(transition_matrix2, position)
            posx = position[0][0]
            posy = position[1][0]

            new_fobj.trns_posx = posx
            new_fobj.trns_posy = posy
            
            ul_pos = tf(ul_pos, transition_matrix, transition_matrix2, heading_transition_matrix, posx, posy)
            ur_pos = tf(ur_pos, transition_matrix, transition_matrix2, heading_transition_matrix, posx, posy)
            dl_pos = tf(dl_pos, transition_matrix, transition_matrix2, heading_transition_matrix, posx, posy)
            dr_pos = tf(dr_pos, transition_matrix, transition_matrix2, heading_transition_matrix, posx, posy)

            new_fobj.ul_pos = ul_pos
            new_fobj.ur_pos = ur_pos
            new_fobj.dl_pos = dl_pos
            new_fobj.dr_pos = dr_pos

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
        

        self.latitiude = self.atm_lat
        self.longitude = self.atm_long

        
        # test
        ##
        radar_x, radar_y = latlng_to_pixel(self.latitiude, self.longitude, self.landmark[0], self.landmark[1], self.landmark[2], (640, 640), (center_x*2, center_y*2))
    

        self.radar_diff_x = radar_x - center_x
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