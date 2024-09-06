import h5py
import config 
from .input_processing import *
import pygame
import io, os
from pathlib import Path
import cv2
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist

class MainModel:
    def __init__(self):
        self.logging_data_num = 0
        self.init_model_class()

    def get_logging_data(self, files:list):
        self.logging_data = []
        for file in files:
            self.logging_data.append(h5py.File(file))
        self.logging_data_num = len(self.logging_data)
        
    def set_min_max_scan(self): # 여러개의 logging file중 가장 작은 값으로 설정해야함.
        
        self.min_scan = -1
        self.max_scan = 99999999999

        for file in self.logging_data:
            min = int(file['DATA_INFO']['initScan'][()].item())
            max = int(file['DATA_INFO']['finScan'][()].item())

            if min > self.min_scan:
                self.min_scan = min
            
            if max < self.max_scan:
                self.max_scan = max
            

    def parsing(self,current_scan):
        self.current_scan_data = [0] * self.logging_data_num
        color_set = (BLUE, GREEN, RED, YELLOW) # TODO color 추가해줘야함. 맵에서 잘 보이는거 위주로 추가하기
        for idx, file in enumerate(self.logging_data):
            file_path = Path(file.filename)
            file_stem = file_path.stem 
            ip = file_stem.split('_')[-1]
            self.current_scan_data[idx] = ScanData(file, current_scan)    
            self.current_scan_data[idx].parsing_status()
            self.current_scan_data[idx].parsing_gps_into_meter(self.grid_model.GRID_WINDOW_WIDTH//2, self.grid_model.GRID_WINDOW_LENGTH//2)
            self.current_scan_data[idx].parsing_image()
            self.current_scan_data[idx].parsing_vision_object_data()
            self.current_scan_data[idx].ip = ip
            self.current_scan_data[idx].color = color_set[idx]
            
        if not os.path.exists(BACKGROUND_IMAGE_PATH):
            parsing_image_data_from_google()
    


    def intersection_fusion(self):
        pass

    def output_processing(self):
        pass

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
    
    def object_matching(self):
        sensor_positions = []
        sensor_pos_detections = []
        sensor_vel_detections = []

        # 각 센서의 위치와 감지된 객체 데이터를 수집
        for idx, data in enumerate(self.current_scan_data):
            sensor_positions.append([data.radar_posx, data.radar_posy])  # 센서 위치 추가
            sensor_pos_detections.append([])  # 각 센서마다 새로운 리스트 생성
            sensor_vel_detections.append([])  # 각 센서마다 새로운 리스트 생성

            for vision in data.vision_object_data:
                # 해당 센서에서 감지된 객체들의 위치와 속도를 해당 리스트에 추가
                sensor_pos_detections[idx].append([vision.posx, vision.posy])
                sensor_vel_detections[idx].append([vision.velx, vision.vely])

        def match_objects(sensor_positions, sensor_detections):
            num_sensors = len(sensor_positions)
            base_detections = np.array(sensor_detections[0])  # 첫 번째 센서 기준
            num_objects = len(base_detections)

            # 각 센서에서 감지된 차량들의 위치를 기준으로 매칭 (유클리드 거리 계산)
            # matched_indices = []
            matched_indices = [list(range(len(base_detections)))]
            for i in range(1, num_sensors):
                detections = np.array(sensor_detections[i])

                # 각 센서의 감지된 차량 간의 거리 계산
                distances = cdist(base_detections, detections)
                # 헝가리안 알고리즘을 사용하여 가장 가까운 차량 매칭
                row_ind, col_ind = linear_sum_assignment(distances)

                # 감지된 객체 수보다 큰 인덱스가 생성되지 않도록 필터링
                matched_indices.append([index for index in col_ind if index < len(sensor_detections[i])])

            return matched_indices

        # 각도를 계산하는 함수
        def calculate_angles(sensor_positions, matched_detections):
            angles = []
            for i, sensor_pos in enumerate(sensor_positions):
                detection = np.array(matched_detections[i])
                vector = detection - sensor_pos
                
                # 벡터의 각도를 계산 (-y 방향, 즉 북쪽을 기준으로 반시계 방향으로 각도 계산)
                angle_rad = np.arctan2(vector[1], vector[0])  # 기본적으로 x축 기준
                angle_deg = np.degrees(angle_rad)
                
                # 북쪽(-y축)을 기준으로 각도를 변환 (90도 더하고 360도로 맞춤)
                north_based_angle = (90 - angle_deg) % 360
                
                angles.append(north_based_angle)
            return angles

        # 객체 매칭 수행
        matched_indices = match_objects(sensor_positions, sensor_pos_detections)

        # print(matched_indices)
        # 매칭된 차량 좌표 추출
        matched_detections = []
        for i in range(len(sensor_positions)):
            # matched_indices[i]가 범위를 벗어나지 않도록 확인 후 추가
            matched_detections.append([sensor_pos_detections[i][index] for index in matched_indices[i] if index < len(sensor_pos_detections[i])])

        # # 각도 계산
        angles = calculate_angles(sensor_positions, matched_detections)

        print('matched : ', matched_detections)
        # print('angles : ', angles)

class Observable:
    def __init__(self):
        self._observers = []

    def add_observer(self, observer):
        self._observers.append(observer)

    def notify_observers(self):
        for observer in self._observers:
            observer.update()  


class WindowModel(Observable):
    def __init__(self, width=1200, length=800):
        super().__init__()
        self.WINDOW_WIDTH = width
        self.WINDOW_LENGTH = length
        
        self.update_sizes()

    def update_sizes(self):
        self.GRID_WINDOW_WIDTH          = int(self.WINDOW_WIDTH*3/5)
        self.GRID_WINDOW_LENGTH         = int(self.WINDOW_LENGTH * 9 / 10)
        self.HALF_GRID_WINDOW_WIDTH     = int(self.GRID_WINDOW_WIDTH // 2)
        self.HALF_GRID_WINDOW_LENGTH    = int(self.GRID_WINDOW_LENGTH // 2)
        
        self.CAM_BOUND_X        = int(self.GRID_WINDOW_WIDTH)
        self.CAM_BOUND_Y        = 0
        self.CAM_BOUND_WIDTH    = int(self.WINDOW_WIDTH - self.GRID_WINDOW_WIDTH)
        self.CAM_BOUND_LENGTH   = int(self.CAM_BOUND_WIDTH * 576 / 1024)

        self.DATA_INFO_X        = int(self.GRID_WINDOW_WIDTH)
        self.DATA_INFO_Y        = self.CAM_BOUND_LENGTH
        self.DATA_INFO_WIDTH    = int(self.WINDOW_WIDTH - self.GRID_WINDOW_WIDTH)
        self.DATA_INFO_LENGTH   = int(self.DATA_INFO_WIDTH/2)

        self.notify_observers()  # Notify observers when sizes are updated

    def update(self, width, length):
        self.WINDOW_WIDTH = width
        self.WINDOW_LENGTH = length
        self.update_sizes()

class GridModel(WindowModel):
    def __init__(self, width=1200, length=800):
        super().__init__(width, length)  # 부모 클래스인 WindowModel 초기화
        self.color = (0, 0, 0)
        self.font_color = (0, 0, 0)
        self.update()

    def update(self):
        self.start_posx = 0
        self.end_posx = self.GRID_WINDOW_WIDTH  # WindowModel의 속성 직접 사용
        self.interval_x = int(config.GRID_X_SIZE )
        self.start_posy = 0
        self.end_posy = self.GRID_WINDOW_LENGTH
        self.interval_y = int(config.GRID_Y_SIZE)


class CamBoundModel(WindowModel):
    def __init__(self, width=1200, length=800):
        super().__init__(width, length)
        self.cam_data_list = []
        self.current_page = 0
        self.cams_per_page = 4
        self.zoom_init()
        self.update()

    def cam_list_load(self, image_sets):
        self.cam_data_list = []
        self.cam_ip_list = []
        self.cam_color = []
        
        for idx in range(len(image_sets)):
            image = image_sets[idx].image
            ip = image_sets[idx].ip
            color = image_sets[idx].color
            fsub = io.BytesIO(image)
            img = pygame.image.load(fsub, 'jpg')
            self.cam_ip_list.append(ip)
            self.cam_data_list.append(img) # TODO
            self.cam_color.append(color)

    def update(self):
        self.posx = self.CAM_BOUND_X
        self.posy = self.CAM_BOUND_Y
        self.width = int(self.WINDOW_WIDTH - self.CAM_BOUND_X)
        self.length = self.CAM_BOUND_LENGTH
        self.color = config.WHITE

        self.center_hor_line_start_pos = (self.GRID_WINDOW_WIDTH, int(self.length / 2))
        self.center_hor_line_end_pos = (self.WINDOW_WIDTH, int(self.length / 2))

        self.center_ver_line_start_pos = (self.GRID_WINDOW_WIDTH + int(self.width / 2), 0)
        self.center_ver_line_end_pos = (self.GRID_WINDOW_WIDTH + int(self.width / 2), self.length)
        
    def get_current_page_cams(self):
        start_idx = self.current_page * self.cams_per_page
        end_idx = start_idx + self.cams_per_page
        return self.cam_data_list[start_idx:end_idx], list(range(start_idx, end_idx)), self.cam_ip_list[start_idx:end_idx], self.cam_color[start_idx:end_idx]

    def next_page(self):
        if (self.current_page + 1) * self.cams_per_page < len(self.cam_data_list):
            self.current_page += 1

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
    
    
    def render_cams(self, screen):
        if len(self.cam_data_list) == 0:
            return
        
        cams, cam_indices, ips, colors = self.get_current_page_cams()
        
        positions = [
            (self.posx, self.posy),
            (self.center_ver_line_start_pos[0], self.posy),
            (self.posx, self.center_hor_line_start_pos[1]),
            (self.center_ver_line_start_pos[0], self.center_hor_line_start_pos[1])
        ]
        
        # Determine which image is zoomed in, if any
        zoomed_image = None
        
        for i, idx in enumerate(cam_indices):
            if idx >= len(self.cam_data_list):
                break
            
            if self.zoomed_in[idx]:
                zoomed_image = (cams[i], (self.posx, self.posy), idx, ips[i], colors[i])
                break
        
        if zoomed_image:
            # Render only the zoomed-in image
            cam, pos, idx, ip, color = zoomed_image
            image = cam  # cam already contains the loaded image
            image = pygame.transform.scale(image, (self.width, self.length))
            # 글자 쓰기
            myFont = pygame.font.SysFont(None, 30) #(글자체, 글자크기) None=기본글자체
            myText = myFont.render("Cam : " + str(ip), True, (240,10,10), BLACK) #(Text,anti-alias, color)
            rect = pygame.Rect(pos[0], pos[1],self.width, self.length)
            
            screen.blit(image, pos)
            pygame.draw.rect(screen, color, rect, 2)
            screen.blit(myText, pos)
        else:
            # Render all images at their normal size
            for cam, pos, ip, color in zip(cams, positions, ips, colors):
                image = cam  # cam already contains the loaded image
                image = pygame.transform.scale(image, (int(self.width / 2), int(self.length / 2)))
                
                myFont = pygame.font.SysFont(None, 30) #(글자체, 글자크기) None=기본글자체
                myText = myFont.render("Cam : " + str(ip), True, (240,10,10), BLACK) #(Text,anti-alias, color)
                
                rect = pygame.Rect(pos[0], pos[1],self.width/2, self.length/2)
                screen.blit(image, pos)
                pygame.draw.rect(screen, color, rect, 2)
                screen.blit(myText, pos)


    def handle_image_click(self, mouse_pos):
        # Handle click events for camera images
        cams, cam_indices, ips, colors = self.get_current_page_cams()
        positions = [
            (self.posx, self.posy),
            (self.center_ver_line_start_pos[0], self.posy),
            (self.posx, self.center_hor_line_start_pos[1]),
            (self.center_ver_line_start_pos[0], self.center_hor_line_start_pos[1])
        ]
        for idx, pos in zip(cam_indices, positions):
            rect = pygame.Rect(pos[0], pos[1], int(self.width / 2), int(self.length / 2))
            if rect.collidepoint(mouse_pos):
                
                if not self.zoomed_in[idx]:
                    self.zoom_init()
                    self.zoomed_in[idx] = True
                
                else:
                    self.zoomed_in[idx] = False
                    
                break  # Only one image can be clicked at a time
    
    def zoom_init(self):
        self.zoomed_in = [False] * 20

    def is_zoom(self):
        if True in self.zoomed_in:
            return 1
        else:
            return 0

    def next_zoom(self):
        # 현재 줌된 카메라의 인덱스를 찾음
        current_zoom_index = None
        for i, zoom in enumerate(self.zoomed_in):
            if zoom:
                current_zoom_index = i
                break
        # 현재 페이지에 마지막 카메라가 줌된 상태이면 페이지 넘기기
        if current_zoom_index is not None:
            next_zoom_index = current_zoom_index + 1
                
            if next_zoom_index >= len(self.cam_data_list):
                self.zoom_init()
            # 현재 페이지의 마지막 카메라를 넘으면 다음 페이지로 이동
            
            elif (next_zoom_index % self.cams_per_page) == 0:
                self.next_page()  # 페이지 넘기기
                self.zoom_init()  # 줌 초기화
                self.zoomed_in[next_zoom_index] = True  # 다음 페이지의 첫 번째 카메라를 확대
            else:
                # 다음 카메라로 줌 이동
                self.zoomed_in[current_zoom_index] = False
                self.zoomed_in[next_zoom_index] = True

    def previous_zoom(self):
        # 현재 줌된 카메라의 인덱스를 찾음
        current_zoom_index = None
        for i, zoom in enumerate(self.zoomed_in):
            if zoom:
                current_zoom_index = i
                break

        # 현재 페이지에서 첫 번째 카메라가 줌된 상태이면 페이지 넘기기
        if current_zoom_index is not None:
            previous_zoom_index = current_zoom_index - 1

            # 현재 페이지의 첫 번째 카메라일 경우 이전 페이지로 이동
            if (previous_zoom_index % self.cams_per_page) == 3:
                if self.current_page > 0:
                    self.previous_page()  # 페이지 넘기기
                    self.zoom_init()  # 줌 초기화
                    self.zoomed_in[self.cams_per_page - 1] = True  # 이전 페이지의 마지막 카메라를 확대
            else:
                # 이전 카메라로 줌 이동
                self.zoomed_in[current_zoom_index] = False
                self.zoomed_in[previous_zoom_index] = True

class CamReturnButtonModel(CamBoundModel):
    def __init__(self, width=1200, length=800):
        super().__init__(width, length)  # 부모 클래스인 CamBoundModel 초기화
        self.update()

    def update(self):
        super().update()  # 부모 클래스의 update() 메서드를 먼저 호출하여 CamBoundModel 속성 업데이트
        self.button_width = int(self.width / 20)
        self.button_length = self.button_width
        self.button_posx = self.WINDOW_WIDTH - self.button_width
        self.button_posy = self.length - self.button_length
        
        self.color = config.WHITE
        self.outline_color = config.BLACK
    def is_clicked(self, mouse_pos):
        return (self.button_posx <= mouse_pos[0] <= self.button_posx + self.button_width and
                self.button_posy <= mouse_pos[1] <= self.button_posy + self.button_length)
    
class CamChangeLeftButtonModel(CamBoundModel):
    def __init__(self, width=1200, length=800):
        super().__init__(width, length)  # 부모 클래스인 CamBoundModel 초기화
        self.update()

    def update(self):
        super().update()  # 부모 클래스의 update() 메서드를 먼저 호출하여 CamBoundModel 속성 업데이트
        self.button_posx = self.center_hor_line_start_pos[0]
        self.button_posy = self.center_hor_line_start_pos[1] - int(self.length / 8)
        self.button_width = int(self.width / 30)
        self.button_length = 2 * int(self.length / 8)
        self.color = config.WHITE
        self.outline_color = config.BLACK
    def is_clicked(self, mouse_pos):
        return (self.button_posx <= mouse_pos[0] <= self.button_posx + self.button_width and
                self.button_posy <= mouse_pos[1] <= self.button_posy + self.button_length)
    
    
class CamChangeRightButtonModel(CamBoundModel):
    def __init__(self, width=1200, length=800):
        super().__init__(width, length)  # 부모 클래스인 CamBoundModel 초기화
        self.update()

    def update(self):
        super().update()  # 부모 클래스의 update() 메서드를 먼저 호출하여 CamBoundModel 속성 업데이트
        self.button_posx = self.center_hor_line_end_pos[0] - int(self.width / 30)
        self.button_posy = self.center_hor_line_start_pos[1] - int(self.length / 8)
        self.button_width = int(self.width / 30)
        self.button_length = 2 * int(self.length / 8)
        self.color = config.WHITE
        self.outline_color = config.BLACK
    def  is_clicked(self, mouse_pos):
        return (self.button_posx <= mouse_pos[0] <= self.button_posx + self.button_width and
                self.button_posy <= mouse_pos[1] <= self.button_posy + self.button_length)
    



class DataInfoWindowModel(WindowModel):
    def __init__(self, width=1200, length=800):
        super().__init__(width, length)  # 부모 클래스인 WindowModel 초기화
        self.color = (100, 100, 100)
        self.font_color = (200, 200, 200)
        self.update()

    def update(self):
        self.posx = self.DATA_INFO_X
        self.posy = self.DATA_INFO_Y
        self.width = self.DATA_INFO_WIDTH
        self.length = self.DATA_INFO_LENGTH

