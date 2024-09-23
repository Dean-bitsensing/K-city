import os
import sys
import requests
from io import BytesIO
from PIL import Image

class MapModel:
    def __init__(self, config, window_width, window_length):
        self.config = config
        self.window_width = window_width
        self.window_length = window_length

    def parsing_overall_map(self):
        if not os.path.exists(self.BACKGROUND_IMAGE_PATH):
            parsing_image_data_from_google(
                self.config['info']['center_gps'][0],
                self.config['info']['center_gps'][1],
                self.window_width,
                self.window_length,
                self.config['info']['api_key'],
                zoom=18,
                maptype='satellite',
                image_path=self.BACKGROUND_IMAGE_PATH
            )


####### Calculation Fuction #####


def parsing_image_data_from_google(center_lat, center_lng, grid_width, grid_height, api_key,  zoom, maptype, image_path):
    map_url = get_static_map_url(center_lat, center_lng, grid_width, grid_height, api_key, zoom, maptype)

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

def get_static_map_url(center_lat, center_lng, width, height, api_key, zoom=18, maptype='satellite'):
    return f"https://maps.googleapis.com/maps/api/staticmap?center={center_lat},{center_lng}&zoom={zoom}&size={width}x{height}&maptype={maptype}&key={api_key}"

def fetch_map_image(url):
    response = requests.get(url)
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        print("Error fetching map image:", response.status_code, response.text)
        return None
