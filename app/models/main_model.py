import h5py
from .colors import *
import os
from pathlib import Path
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from .window_model import WindowModel
from .map_grid_model import MapGridModel
from .camera_display_model import CameraDisplayModel
from .button_models import CameraReturnButton, CameraLeftButton, CameraRightButton
from .info_window_model import InfoWindowModel
from.data_models import *
from scipy.optimize import minimize

class MainModel:
    def __init__(self, config):

        self.view_mode          = 0  # 0 : OverAll View , 1 : Intersection View , 2 : ATM View
        self.track_mode         = 0  # 0 : Fusion,        1 : Vision,             2 : Radar

        self.config             = config
        self.logging_data_num   = 0
        self.logging_data       = []
        self.intersections      = []
        self.intersection_num   = config['info']['intersection_num']
        self.atm_num            = config['info']['atm_num']

        self.lat_landmark   = config['info']['center_gps'][0]
        self.long_landmark  = config['info']['center_gps'][1]
        self.landmark = (self.lat_landmark, self.long_landmark)
        self.init_model_class()


    def get_logging_data(self): # 로깅데이터 가져오고, ATM 기본 설정들 입력해주기
        for intersection in self.config.keys():
            if intersection == 'None':
                continue
            if intersection != 'info':
                itsc = Intersection(self.config[intersection], intersection, self.landmark)
                itsc.initiate()
                self.intersections.append(itsc)
                self.logging_data.extend(itsc.h5_files)

        
    def set_min_max_scan(self): # 여러개의 logging file중 가장 작은 값으로 설정해야함.
        
        self.min_scan = -1
        self.max_scan = 99999999999

        for file in self.logging_data:
            file = h5py.File(file, 'r')
            max = int(file['DATA_INFO']['finScan'][()].item())
            min = int(file['DATA_INFO']['initScan'][()].item())

            if min > self.min_scan:
                self.min_scan = min
            
            if max < self.max_scan:
                self.max_scan = max
            file.close()
    
    def load_data(self, current_scan):
        for intersection in self.intersections:
            for atm in intersection.atms:
                atm.get_scan_data(current_scan, self.grid_model.GRID_WINDOW_WIDTH//2, self.grid_model.GRID_WINDOW_LENGTH//2)



    def init_model_class(self):
        self.window_model = WindowModel()
        self.grid_model = MapGridModel(self.landmark)
        self.cam_bound_model = CameraDisplayModel(self.window_model.WINDOW_WIDTH, self.window_model.WINDOW_LENGTH)
        self.cam_change_left_button_model = CameraLeftButton()
        self.cam_change_right_button_model = CameraRightButton()
        self.cam_return_button_model = CameraReturnButton()
        self.data_info_window_model = InfoWindowModel()
        
        

    def window_resize(self, width, length):
        self.window_model.update(width, length)
        self.grid_model.update(self.landmark, width, length)
        self.cam_bound_model.update(width, length)
        self.cam_change_left_button_model.update(width, length)
        self.cam_change_right_button_model.update(width, length)
        self.cam_return_button_model.update(width, length)
        self.data_info_window_model.update(width, length)



    def select_object(self, mouse_pos):
        for intersection in self.intersections:
            for atm in intersection.atms:            
                
                    
                dist = math.sqrt((mouse_pos[0] - atm.current_scan_data.radar_posx)**2+ (mouse_pos[1] - atm.current_scan_data.radar_posy)**2)
                if dist < 5:
                    # fobj.selected = True
                    # obj_id = fobj.id
                    atm.selected = True
                    # print(f'data : {idx}, list : {data.selected_fobj_id}')
                for fobj in atm.current_scan_data.fusion_object_data:
                    
                    dist = math.sqrt((mouse_pos[0] - fobj.trns_posx)**2+ (mouse_pos[1] - fobj.trns_posy)**2)
                    if dist < 5:
                        fobj.selected = True
                        obj_id = fobj.id
                        atm.selected_fobj_id.append(obj_id)
                        print(f'data : {atm.ip}, list : {atm.selected_fobj_id}')     

    def clear_selected(self):
        for intersection in self.intersections:
            for atm in intersection.atms:
                atm.clear_selected_obj_id()
        
    def calculate_distance_sum(self, adjusted_azi_thetas):
        selected_points = []
        selected_atm_id = []

        idx = 0
        # Collect the selected points based on the updated azi_thetas
        for intersection in self.intersections:
            for atm in intersection.atms:
                atm.atm_azi_angle = adjusted_azi_thetas[idx]
        
                for cur_scan_data in atm.current_scan_data.fusion_object_data:
                    if cur_scan_data.id in atm.selected_fobj_id:
                        print('in')
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

                        selected_points.append([posx, posy])
                        selected_atm_id.append(idx)
                idx += 1

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
        initial_azi_thetas = []
        for intersection in self.intersections:
            for atm in intersection.atms:
                initial_azi_thetas.append(atm.atm_azi_angle)
        # initial_azi_thetas = [atm.atm_azi_angle for atm in self.logging_data]

        # 각 atm의 azi_angle이 -10도에서 +10도 범위로 조정될 수 있도록 범위를 설정
        bounds = [(atm.atm_azi_angle - 180, atm.atm_azi_angle + 180) 
          for intersection in self.intersections
          for atm in intersection.atms]
        print(bounds)
        # dist_sum을 최소화하는 azi_angle 값 찾기
        result = minimize(self.calculate_distance_sum, initial_azi_thetas, bounds=bounds)

        # 최적화된 azi_thetas로 logging_data를 업데이트
        idx = 0
        for intersection in self.intersections:
            for atm in intersection.atms:
                print('x : ', result.x[idx])
                atm.atm_azi_angle = result.x[idx]
                idx += 1

        # 결과 출력: 최적화된 azi_angle들과 최소화된 거리 합
        print("Optimized azi angles:", result.x)
        print("Minimum distance sum:", result.fun)  
#TODO 살리기
    # def object_matching(self):
    #     azi_thetas = [0] * len(self.logging_data)
    #     for idx, data in enumerate(self.current_scan_data):
    #         azi_thetas[idx] = data.azi_theta
        
    #     print(azi_thetas)
    #     selected_list = []

    #     for idx, data in enumerate(self.current_scan_data):
    #         print(idx)
    #         for vobj in data.vision_object_data:
    #             if vobj.selected:
    #                 selected_list.append((vobj.posx, vobj.posy))

    #     print(selected_list)

        # 각도 돌리기
        # 돌릴때마다 거리 비교
        # 최소값일 때의 각각 각도 적어두기


    


