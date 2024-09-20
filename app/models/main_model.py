import h5py
from .colors import *
import os
from pathlib import Path
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from .window_model import WindowModel
from .grid_model import GridModel
from .camera_display_model import CameraDisplayModel
from .button_models import CameraReturnButton, CameraLeftButton, CameraRightButton
from .info_window_model import InfoWindowModel
from .data_models import *

class MainModel:
    def __init__(self, config):

        self.view_mode = 0  # 0 : OverAll View , 1 : Intersection View , 2 : ATM View

        self.config = config
        self.radar_only_mode = False
        self.logging_data_num = 0
        self.logging_data = []
        self.intersections = []
        self.init_model_class()


    def get_logging_data(self): # 로깅데이터 가져오고, ATM 기본 설정들 입력해주기
        for intersection in self.config.keys():
            if intersection == 'None':
                continue
            if intersection != 'info':
                itsc = Intersection(self.config[intersection], intersection)
                itsc.initiate()
                self.intersections.append(itsc)
                self.logging_data.extend(itsc.h5_files)

        
    def set_map(self):

    
    def set_min_max_scan(self): # 여러개의 logging file중 가장 작은 값으로 설정해야함.
        
        self.min_scan = -1
        self.max_scan = 99999999999

        for file in self.logging_data:
            max = int(file.logging_data['DATA_INFO']['finScan'][()].item())
            min = int(file.logging_data['DATA_INFO']['initScan'][()].item())

            if min > self.min_scan:
                self.min_scan = min
            
            if max < self.max_scan:
                self.max_scan = max
    
    def load_data(self, current_scan):
        for intersection in self.intersections:
            for atm in intersection.atms:
                atm.get_scan_data(current_scan, self.grid_model.GRID_WINDOW_WIDTH//2, self.grid_model.GRID_WINDOW_LENGTH//2)

    def init_model_class(self):
        self.window_model = WindowModel()
        self.grid_model = GridModel()
        self.cam_bound_model = CameraDisplayModel(self.window_model.WINDOW_WIDTH, self.window_model.WINDOW_LENGTH)
        self.cam_change_left_button_model = CameraLeftButton()
        self.cam_change_right_button_model = CameraRightButton()
        self.cam_return_button_model = CameraReturnButton()
        self.data_info_window_model = InfoWindowModel()
        
        

    def window_resize(self, width, length):
        self.window_model = WindowModel(width, length)
        self.grid_model = GridModel(width, length)
        self.cam_bound_model = CameraDisplayModel(width, length)
        self.cam_change_left_button_model = CameraLeftButton(width, length)
        self.cam_change_right_button_model = CameraRightButton(width, length)
        self.cam_return_button_model = CameraReturnButton(width, length)
        self.data_info_window_model = InfoWindowModel(width, length)






    def select_object(self, mouse_pos):
        for idx, data in enumerate(self.logging_data):
            
            for vobj in data.current_scan_data.vision_object_data:
                
                dist = math.sqrt((mouse_pos[0] - vobj.posx)**2+ (mouse_pos[1] - vobj.posy)**2)
                if dist < 5:
                    vobj.selected = True
                    obj_id = vobj.id
                    data.selected_vobj_id.append(obj_id)
                    print(f'data : {idx}, list : {data.selected_vobj_id}')      

    def object_matching(self):
        azi_thetas = [0] * len(self.current_scan_data)
        for idx, data in enumerate(self.current_scan_data):
            azi_thetas[idx] = data.azi_theta
        
        print(azi_thetas)
        selected_list = []

        for idx, data in enumerate(self.current_scan_data):
            print(idx)
            for vobj in data.vision_object_data:
                if vobj.selected:
                    selected_list.append((vobj.posx, vobj.posy))

        print(selected_list)

        # 각도 돌리기
        # 돌릴때마다 거리 비교
        # 최소값일 때의 각각 각도 적어두기


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

