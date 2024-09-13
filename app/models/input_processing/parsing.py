import json
import sys
import os
import requests
import math
import numpy as np
from io import BytesIO
from PIL import Image
from pyproj import Transformer
from config import *
from dataclasses import dataclass


class AtmData:
    def __init__(self):
        self.logging_data = None
        self.ip = '-1'
        self.file_name = None
        self.current_scan_data = ScanData
        # self.selected_vobj_id = []
        self.selected_fobj_id = []

        self.atm_lat = 0
        self.atm_lat = 0
        self.atm_azi_angle = 0
        self.selected = False

        self.atm_posx = 0
        self.atm_posy = 0

    def init_current_scan_data(self):
        self.current_scan_data = ScanData

    def clear_selected_obj_id(self):
        self.selected_vobj_id = []
        self.selected_fobj_id = []
        self.selected = False

class FusionObj:
    def __init__(self):
        
        self.id = 0
        self.status = 0
        self.updata_state = 0
        self.move_state = 0
        self.alive_age = 0

        self.posx = 0 
        self.posy = 0

        self.ref_posx = 0 
        self.ref_posy = 0

        self.velx = 0
        self.vely = 0

        self.heading_angle_deg = 0
        self.power = 0
        self.width = 0
        self.length = 0
        self.class_id = 0
        self.fusion_type = 0
        self.fusion_age = 0
        self.match_vobj_id = 0

        # 변환된 좌표들이 들어오는 공간이다.

        self.trns_posx = 0
        self.trns_posy = 0
        self.ul_pos = [0, 0]
        self.ur_pos = [0, 0]
        self.dl_pos = [0, 0]
        self.dr_pos = [0, 0]

        self.selected = False # 화면 표출 시 색 변환을 위한 변수

        self.before_posx = 0
        self.before_posy = 0

class VisionObj:
    def __init__(self):
        # 변환된 좌표들이 들어오는 공간이다.
        self.id = 0
        self.class_id = 0
        self.confidence = 0

        self.bbox_posx = 0
        self.bbox_posy = 0
        self.bbox_width = 0
        self.bbox_length = 0

        self.match_robj_id = 0
        self.status = 0
        self.move_state = 0
        self.alive_age = 0

        self.posx = 0 
        self.posy = 0

        self.velx = 0
        self.vely = 0

        self.width = 0
        self.length = 0

        self.lane = 0
        self.heading_angle_deg = 0

        self.trns_posx = 0 # Trans pos 따로 저장하기
        self.trns_posy = 0
        self.ul_pos = [0, 0]
        self.ur_pos = [0, 0]
        self.dl_pos = [0, 0]
        self.dr_pos = [0, 0]

        self.selected = False # 화면 표출 시 색 변환을 위한 변수

        self.before_posx = 0
        self.before_posy = 0

class ScanData:
    def __init__(self, h5_dataset,current_scan, atm_data):
        self.current_scan = current_scan
        
        self.h5_dataset = h5_dataset
        self.current_scan_data = h5_dataset['SCAN_{:05d}'.format(current_scan)]
        self.atm_data = atm_data

        self.intersection_number = 1
        self.color = None
        
        # self.transformation = Transformation()

    def parsing_status(self):
        status_data = self.current_scan_data['Status'][:]
        self.status_json = json.loads(status_data.tobytes().decode('utf-8'))


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
        
        # gps에서 들어오는 데이터

        self.latitiude = self.atm_data.atm_lat
        self.longitude = self.atm_data.atm_long

        
        # test
        ##
        radar_x, radar_y = latlng_to_pixel(self.latitiude, self.longitude, LAT_LANDMARK, LON_LANDMARK, 18, (640, 640), (center_x*2, center_y*2))
    

        self.radar_diff_x = radar_x - center_x
        self.radar_diff_y = radar_y - center_y 
        self.center_x = center_x
        self.center_y = center_y
        self.radar_posx = radar_x
        self.radar_posy = radar_y
        


    def parsing_image(self):
        self.image = self.current_scan_data['Image'][()]

    def parsing_fusion_object_data(self):
        self.fusion_object_data = []
        self.fusion_object_data_vel = []

        self.azi_theta = self.atm_data.atm_azi_angle

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
            
            posx = meters_to_pixels(posx, LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            posy = meters_to_pixels(posy, LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            
            ul_pos[0] = meters_to_pixels(ul_pos[0], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            ul_pos[1] = meters_to_pixels(ul_pos[1], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))

            ur_pos[0] = meters_to_pixels(ur_pos[0], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            ur_pos[1] = meters_to_pixels(ur_pos[1], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            dl_pos[0] = meters_to_pixels(dl_pos[0], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            dl_pos[1] = meters_to_pixels(dl_pos[1], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            dr_pos[0] = meters_to_pixels(dr_pos[0], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            dr_pos[1] = meters_to_pixels(dr_pos[1], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))

            

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

        self.azi_theta = self.atm_data.atm_azi_angle

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
            
            posx = meters_to_pixels(posx, LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            posy = meters_to_pixels(posy, LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            
            ul_pos[0] = meters_to_pixels(ul_pos[0], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            ul_pos[1] = meters_to_pixels(ul_pos[1], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))

            ur_pos[0] = meters_to_pixels(ur_pos[0], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            ur_pos[1] = meters_to_pixels(ur_pos[1], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            dl_pos[0] = meters_to_pixels(dl_pos[0], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            dl_pos[1] = meters_to_pixels(dl_pos[1], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            dr_pos[0] = meters_to_pixels(dr_pos[0], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            dr_pos[1] = meters_to_pixels(dr_pos[1], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))

            ul_pos = tf(ul_pos, transition_matrix, transition_matrix2)
            ur_pos = tf(ur_pos, transition_matrix, transition_matrix2)
            dl_pos = tf(dl_pos, transition_matrix, transition_matrix2)
            dr_pos = tf(dr_pos, transition_matrix, transition_matrix2)


            velx = meters_to_pixels(velx, LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            vely = meters_to_pixels(vely, LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            
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


def parsing_image_data_from_google(center_lat, center_lng, grid_width, grid_height, zoom, maptype, image_path):
    map_url = get_static_map_url(center_lat, center_lng, grid_width, grid_height, zoom, maptype)

    # 지도 이미지 가져오기
    try:
        response = requests.get(map_url)
        response.raise_for_status()  # HTTP 요청이 성공적인지 확인
    except requests.exceptions.RequestException as e:
        print(f"Error fetching map image: {e}")
        sys.exit()

    # HTTP 요청이 성공적이라면 PNG 파일로 저장
    if response.status_code == 200:
        try:
            # 이미지를 BytesIO로 읽고, Pillow 이미지로 열기
            map_image = Image.open(BytesIO(response.content))
                
            # if not os.path.exists('app'):
            #     os.makedirs('images')
            # PNG 파일로 저장
            if not os.path.exists(image_path):
                map_image.save(image_path, 'PNG')
                print("Image saved as 'map_image.png'")
            
        except Exception as e:
            print(f"Error processing image: {e}")
            sys.exit()
    else:
        print(f"Error fetching map image: {response.status_code} - {response.text}")
        sys.exit()

        
         

def get_static_map_url(center_lat, center_lng, width, height, zoom=18, maptype='satellite'):
    return f"https://maps.googleapis.com/maps/api/staticmap?center={center_lat},{center_lng}&zoom={zoom}&size={width}x{height}&maptype={maptype}&key={API_KEY}"

def fetch_map_image(url):
    response = requests.get(url)
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        print("Error fetching map image:", response.status_code, response.text)
        return None
    
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