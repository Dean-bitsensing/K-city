import json
import sys
import os
import requests
from io import BytesIO
from PIL import Image
from pyproj import Transformer
from config import *


class ScanData:
    def __init__(self, h5_dataset,current_scan):
        self.current_scan = current_scan
        
        self.scan_data = h5_dataset['SCAN_{:05d}'.format(current_scan)]
        self.ip = 'ip'
        self.intersection_number = 1


    def parsing_status(self):
        status_data = self.scan_data['Status'][:]
        self.status_json = json.loads(status_data.tobytes().decode('utf-8'))

    def parsing_gps_into_meter(self):
        self.longitude = self.status_json['gps']['longitude']
        self.latitiude = self.status_json['gps']['latitude']

        # WGS84 좌표계 (EPSG:4326)와 UTM Zone 32N 좌표계 (EPSG:32632)를 정의하는 변환기 생성
        transformer = Transformer.from_crs('epsg:4326', 'epsg:32632')

        # 각 GPS 좌표를 UTM 좌표계로 변환
        utm_x1, utm_y1 = transformer.transform(LAT_LANDMARK, LON_LANDMARK)
        utm_x2, utm_y2 = transformer.transform(self.latitiude, self.longitude)

        # 두 좌표 사이의 X, Y 차이 계산
        self.radar_posx = utm_x2 - utm_x1
        self.radar_posy = utm_y2 - utm_y1

    def parsing_image(self):
        self.image = self.scan_data['Image'][()]

def parsing_image_data_from_google():
    map_url = get_static_map_url(LAT_LANDMARK, LON_LANDMARK)

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
                
            if not os.path.exists('images'):
                os.makedirs('images')
            # PNG 파일로 저장
            if not os.path.exists('./images/map_image.png'):
                map_image.save('./images/map_image.png', 'PNG')
                print("Image saved as 'map_image.png'")
            
        except Exception as e:
            print(f"Error processing image: {e}")
            sys.exit()
    else:
        print(f"Error fetching map image: {response.status_code} - {response.text}")
        sys.exit()

        
         

def get_static_map_url(lat, lng, width = GRID_WINDOW_WIDTH, height = GRID_WINDOW_LENGTH, zoom=18, maptype='roadmap'):
    return f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom={zoom}&size={width}x{height}&maptype={maptype}&key={API_KEY}"

def fetch_map_image(url):
    response = requests.get(url)
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        print("Error fetching map image:", response.status_code, response.text)
        return None