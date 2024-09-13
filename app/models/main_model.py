import h5py
import config
from .colors import *
from .input_processing import *
import pygame
import io, os
from pathlib import Path
import cv2
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from .window_model import *
from scipy.optimize import minimize


FUSION_ONLY = 0
VISION_ONLY = 1
RADAR_ONLY  = 2

class MainModel:
    def __init__(self, config):
        self.logging_data_num = 0
        self.drawing_mode = RADAR_ONLY
        self.config = config
        self.init_model_class()

    def get_logging_data(self, files:list): # 로깅데이터 가져오고, ATM 기본 설정들 입력해주기
        self.logging_data = []
        for file in files:
            logging_data = AtmData()
            logging_data.logging_data = h5py.File(file)
            ip = file.split('_')[-1][:-3]
            logging_data.ip = ip
            logging_data.file_name = file.split('_')[:-1]
            print(ip)
            self.logging_data.append(logging_data)
        self.logging_data_num = len(self.logging_data)
    
    def set_atm_metadata(self):
        # azi angle, gps 좌표, 
        for file in self.logging_data:
            file.atm_lat = file.logging_data['GPS'][()][0]
            file.atm_long = file.logging_data['GPS'][()][1]
            file.atm_azi_angle = file.logging_data['GPS'][()][2]

            


    def set_min_max_scan(self): # 여러개의 logging file중 가장 작은 값으로 설정해야함.
        
        self.min_scan = -1
        self.max_scan = 99999999999

        for file in self.logging_data:
            min = int(file.logging_data['DATA_INFO']['initScan'][()].item())
            max = int(file.logging_data['DATA_INFO']['finScan'][()].item())

            if min > self.min_scan:
                self.min_scan = min
            
            if max < self.max_scan:
                self.max_scan = max
            
    

    def parsing(self,current_scan):
    
        for log_data in self.logging_data:
            log_data.init_current_scan_data()

        # self.current_scan_data = [0] * self.logging_data_num
        color_set = (BLUE, GREEN, RED, YELLOW, PINK, INDIGO, RED, YELLOW) # TODO color 추가해줘야함. 맵에서 잘 보이는거 위주로 추가하기
        for idx, file in enumerate(self.logging_data):
            self.logging_data[idx].current_scan_data = ScanData(file.logging_data, current_scan, file)    
            self.logging_data[idx].current_scan_data.parsing_status()
            self.logging_data[idx].current_scan_data.parsing_gps_into_meter(self.grid_model.GRID_WINDOW_WIDTH//2, self.grid_model.GRID_WINDOW_LENGTH//2)
            self.logging_data[idx].current_scan_data.parsing_image()
            self.logging_data[idx].current_scan_data.parsing_vision_object_data()
            self.logging_data[idx].current_scan_data.parsing_fusion_object_data()
            self.logging_data[idx].current_scan_data.color = color_set[idx]
            self.logging_data[idx].current_scan_data.speed_color = BLACK
            

    def init_model_class(self):
        self.window_model = WindowModel()
        self.grid_model = GridModel()
        self.cam_bound_model = CamBoundModel(self.window_model.WINDOW_WIDTH, self.window_model.WINDOW_LENGTH)
        self.cam_change_left_button_model = CamChangeLeftButtonModel()
        self.cam_change_right_button_model = CamChangeRightButtonModel()
        self.cam_return_button_model = CamReturnButtonModel()
        self.data_info_window_model = DataInfoWindowModel()
        
        
        

    def window_resize(self, width, length):
        self.window_model = WindowModel(width, length)
        self.grid_model = GridModel(width, length)
        self.cam_bound_model = CamBoundModel(width, length)
        self.cam_change_left_button_model = CamChangeLeftButtonModel(width, length)
        self.cam_change_right_button_model = CamChangeRightButtonModel(width, length)
        self.cam_return_button_model = CamReturnButtonModel(width, length)
        self.data_info_window_model = DataInfoWindowModel(width, length)

    def get_h5_datas(self, directory):
    # 폴더 내부의 모든 파일 중 .h5 확장자를 가진 파일을 리스트로 반환
        h5_files = [f'{directory}/'+file for file in os.listdir(directory) if file.endswith('.h5')]
        return h5_files
    

    def select_object(self, mouse_pos):
        for idx, data in enumerate(self.logging_data):
            
            # for vobj in data.current_scan_data.vision_object_data:
                
            #     dist = math.sqrt((mouse_pos[0] - vobj.posx)**2+ (mouse_pos[1] - vobj.posy)**2)
            #     if dist < 5:
            #         vobj.selected = True
            #         obj_id = vobj.id
            #         data.selected_vobj_id.append(obj_id)
            #         print(f'data : {idx}, list : {data.selected_vobj_id}')
            # if data.current_scan_data:
            dist = math.sqrt((mouse_pos[0] - data.current_scan_data.radar_posx)**2+ (mouse_pos[1] - data.current_scan_data.radar_posy)**2)
            if dist < 5:
                # fobj.selected = True
                # obj_id = fobj.id
                data.selected = True
                # print(f'data : {idx}, list : {data.selected_fobj_id}')
            for fobj in data.current_scan_data.fusion_object_data:
                
                dist = math.sqrt((mouse_pos[0] - fobj.trns_posx)**2+ (mouse_pos[1] - fobj.trns_posy)**2)
                if dist < 5:
                    fobj.selected = True
                    obj_id = fobj.id
                    data.selected_fobj_id.append(obj_id)
                    print(f'data : {idx}, list : {data.selected_fobj_id}')

    def clear_selected(self):
        for idx, atm in enumerate(self.logging_data):
            atm.clear_selected_obj_id()

    def object_matching(self):
        azi_thetas = [0] * len(self.logging_data)
        selected_points = []
        selected_atm_id = []

        for idx, atm in enumerate(self.logging_data):
            # azi_thetas[idx] = atm.atm_azi_angle
            for cur_scan_data in atm.current_scan_data.vision_object_data:
                if cur_scan_data.id in atm.selected_vobj_id:
                    selected_points.append([cur_scan_data.posx, cur_scan_data.posy])
                    selected_atm_id.append(idx)
        
        start = [0] * len(selected_atm_id)
        end = [0] * len(selected_atm_id)
        for i,idx in enumerate(selected_atm_id):
            start[i] = self.logging_data[idx].atm_azi_angle - 10
            end[i] = self.logging_data[idx].atm_azi_angle + 10


        min_dist = 0
        # print(selected_points)
        # print(selected_atm_id)


        dist_sum = 0
        for i in range(len(selected_points)):
            for j in range(i+1, len(selected_points)):
                dist_sum += math.sqrt((selected_points[i][0] - selected_points[j][0])**2 + (selected_points[i][1] - selected_points[j][1])**2)

        print(dist_sum)


        # 각도 돌리기
        # 돌릴때마다 거리 비교
        # 최소값일 때의 각각 각도 적어두기
    def calculate_distance_sum(self, adjusted_azi_thetas):
        selected_points = []
        selected_atm_id = []

        # Collect the selected points based on the updated azi_thetas
        for idx, atm in enumerate(self.logging_data):
            atm.atm_azi_angle = adjusted_azi_thetas[idx]  # 업데이트된 azi_thetas 값을 적용
            
            for cur_scan_data in atm.current_scan_data.fusion_object_data:
                if cur_scan_data.id in atm.selected_fobj_id:
                    # posx, posy는 azi_angle에 따라 변환된 값
                    before_posx = cur_scan_data.before_posx
                    before_posy = cur_scan_data.before_posy

                    # before_posx = -before_posx
                    

                    azi_theta = atm.atm_azi_angle

                    azi_theta = azi_theta * math.pi / 180 #  북쪽기준으로 반시계 방향으로 얼마나 회전했는가

                    theta = math.pi/2 - azi_theta
                    
                    transition_matrix = np.array([[math.cos(theta), - math.sin(theta), atm.current_scan_data.radar_diff_x],
                                                [math.sin(theta), math.cos(theta), atm.current_scan_data.radar_diff_y],
                                                [0,0,1]])
                    
                    transition_matrix2 = np.array([[1, 0, atm.current_scan_data.center_x],
                                                [0, 1, atm.current_scan_data.center_y],
                                                [0,0,1]])
                    
                    # position = np.array([[before_posx],[before_posy],[1]])
                    # position = np.dot(transition_matrix2.T, position)
                    # position = np.dot(transition_matrix.T,position)
                    
                    # posx = position[0][0]
                    # posy = position[1][0]

                    
                    position = np.array([[before_posx],[before_posy],[1]])
                    position = np.dot(transition_matrix,position)
                    position = np.dot(transition_matrix2, position)
                    posx = position[0][0]
                    posy = position[1][0]

                    #TODO 변환했을 때 posx, posy를 우리 상황에 맞게 변경
                    # posx = cur_scan_data.posx * math.cos(math.radians(atm.atm_azi_angle))
                    # posy = cur_scan_data.posy * math.sin(math.radians(atm.atm_azi_angle))

                    selected_points.append([posx, posy])
                    selected_atm_id.append(idx)

        # Calculate the sum of distances between each pair of points
        dist_sum = 0
        # 세 점 사이의 거리 구하기
        for i in range(len(selected_points)):
            for j in range(i + 1, len(selected_points)):
                dist_sum += math.sqrt((selected_points[i][0] - selected_points[j][0]) ** 2 +
                                      (selected_points[i][1] - selected_points[j][1]) ** 2)
                
        # 각 점과 중심점 사이의 거리 계산 및 합산
        # centroid_x = sum([p[0] for p in selected_points]) / len(selected_points)
        # centroid_y = sum([p[1] for p in selected_points]) / len(selected_points)
        
        # for point in selected_points:
        #     dist_sum += math.sqrt((point[0] - centroid_x) ** 2 + (point[1] - centroid_y) ** 2)

        return dist_sum
    
    def object_matching(self):
        def wrap_angle(angle):
            return angle % 360
        # 현재 logging_data의 atm_azi_angle 값들을 초기값으로 설정
        initial_azi_thetas = [atm.atm_azi_angle for atm in self.logging_data]

        # 각 atm의 azi_angle이 -10도에서 +10도 범위로 조정될 수 있도록 범위를 설정
        bounds = [(atm.atm_azi_angle - 180, atm.atm_azi_angle + 180) for atm in self.logging_data]
        print(bounds)
        # dist_sum을 최소화하는 azi_angle 값 찾기
        result = minimize(self.calculate_distance_sum, initial_azi_thetas, bounds=bounds)

        # 최적화된 azi_thetas로 logging_data를 업데이트
        for idx, atm in enumerate(self.logging_data):
            atm.atm_azi_angle = result.x[idx]

        # 결과 출력: 최적화된 azi_angle들과 최소화된 거리 합
        print("Optimized azi angles:", result.x)
        print("Minimum distance sum:", result.fun)

    


