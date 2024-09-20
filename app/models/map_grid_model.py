# models/map_grid_model.py
import os
import sys
import requests
from io import BytesIO
from PIL import Image
from .window_model import WindowModel
from .colors import *

class MapGridModel(WindowModel):
    def __init__(self, landmark, view_mode, width=1200, length=800):
        super().__init__(width, length)
        self.color = (0, 0, 0)
        self.font_color = (0, 0, 0)
        self.font_size = 10
        self.center_point_color = RED
        
        self.overall_map_image_path = 'app/resources/map_image.png'
        self.intersection1_image_path = 'app/resources/intersection1.png'
        self.intersection2_image_path = 'app/resources/intersection2.png'
        self.BACKGROUND_IMAGE_PATH = self.overall_map_image_path

        self.start_posx = 0
        self.start_posy = 0
        self.landmark = landmark
        self.view_mode = view_mode
        
        self.parsing_map()

        self.update(self.landmark, width, length)

    def update(self, landmark, width, length):
        super().__init__(width, length)
        self.landmark = landmark
        self.interval_x = int(self.GRID_X_SIZE)
        self.end_posx = self.GRID_WINDOW_WIDTH
        
        self.end_posy = self.GRID_WINDOW_LENGTH
        self.interval_y = int(self.GRID_Y_SIZE)

    def parsing_map(self):
        if self.view_mode[0] == 0:
            image_path = self.overall_map_image_path
        elif self.view_mode[0] == 1:
            image_path = self.intersection1_image_path
        elif self.view_mode[0] == 2:
            image_path = self.intersection2_image_path
            
        self.BACKGROUND_IMAGE_PATH = image_path
        if not os.path.exists(image_path):
            parsing_image_data_from_google(
                self.landmark[0],
                self.landmark[1],
                self.GRID_WINDOW_WIDTH,
                self.GRID_WINDOW_LENGTH,
                zoom=self.landmark[2],
                maptype='satellite',
                image_path=image_path
            )


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
    return f"https://maps.googleapis.com/maps/api/staticmap?center={center_lat},{center_lng}&zoom={zoom}&size={width}x{height}&maptype={maptype}&key={'AIzaSyAX-DtCyFMUB13qbSPHNB-M847w4woneWw'}"

def fetch_map_image(url):
    response = requests.get(url)
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        print("Error fetching map image:", response.status_code, response.text)
        return None
    