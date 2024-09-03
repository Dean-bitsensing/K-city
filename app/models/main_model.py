import h5py
import config 
from .input_processing import *
import pygame
import io, os
from pathlib import Path
import cv2

class MainModel:
    def __init__(self):
        
        self.init_model_class()

    def get_logging_data(self, files:list):
        self.logging_data = []
        for file in files:
            self.logging_data.append(h5py.File(file))

    def set_min_max_scan(self):
        self.min_scan = int(self.logging_data[0]['DATA_INFO']['initScan'][()].item())
        self.max_scan = int(self.logging_data[0]['DATA_INFO']['finScan'][()].item())

    def parsing(self,current_scan):
        self.current_scan_data = [0] * len(self.logging_data)
        
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
        

    def window_resize(self, width, length):
        self.window_model = WindowModel(width, length)
        self.grid_model = GridModel(width, length)
        self.cam_bound_model = CamBoundModel(width, length)
        self.cam_change_left_button_model = CamChangeLeftButtonModel(width, length)
        self.cam_change_right_button_model = CamChangeRightButtonModel(width, length)

    def get_h5_datas(self, directory):
    # 폴더 내부의 모든 파일 중 .h5 확장자를 가진 파일을 리스트로 반환
        h5_files = [f'{directory}/'+file for file in os.listdir(directory) if file.endswith('.h5')]
        return h5_files
    
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
        self.GRID_WINDOW_WIDTH = int(self.WINDOW_WIDTH*3/5)
        self.GRID_WINDOW_LENGTH = int(self.WINDOW_LENGTH * 9 / 10)
        self.HALF_GRID_WINDOW_WIDTH = int(self.GRID_WINDOW_WIDTH // 2)
        self.HALF_GRID_WINDOW_LENGTH = int(self.GRID_WINDOW_LENGTH // 2)

        self.CAM_BOUND_X = int(self.GRID_WINDOW_WIDTH)
        self.CAM_BOUND_Y = 0
        self.CAM_BOUND_WIDTH = int(self.WINDOW_WIDTH - self.GRID_WINDOW_WIDTH)
        self.CAM_BOUND_LENGTH = int(self.CAM_BOUND_WIDTH * 576 / 1024)

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
        self.zoomed_in = [False] * 20
        self.update()

    def cam_list_load(self, image_sets):

        
        self.cam_data_list = []
        for idx in range(len(image_sets)):
            image = image_sets[idx].image
            fsub = io.BytesIO(image)
            img = pygame.image.load(fsub, 'jpg')
            
            self.cam_data_list.append(img) # TODO
        
        


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
        return self.cam_data_list[start_idx:end_idx], list(range(start_idx, end_idx))

    def next_page(self):
        if (self.current_page + 1) * self.cams_per_page < len(self.cam_data_list):
            self.current_page += 1

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1

    def render_cams(self, screen):
        if len(self.cam_data_list) == 0:
            return
        
        cams, cam_indices = self.get_current_page_cams()
        
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
                zoomed_image = (cams[i], (self.posx, self.posy), idx)
                break
        
        if zoomed_image:
            # Render only the zoomed-in image
            cam, pos, idx = zoomed_image
            image = cam  # cam already contains the loaded image
            image = pygame.transform.scale(image, (self.width, self.length))
            screen.blit(image, pos)
        else:
            # Render all images at their normal size
            for cam, pos in zip(cams, positions):
                image = cam  # cam already contains the loaded image
                image = pygame.transform.scale(image, (int(self.width / 2), int(self.length / 2)))
                screen.blit(image, pos)


    def handle_image_click(self, mouse_pos):
        # Handle click events for camera images
        cams, cam_indices = self.get_current_page_cams()
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
                    self.zoomed_in = [False] * 20
                    self.zoomed_in[idx] = True
                
                else:
                    self.zoomed_in[idx] = False
                    
                break  # Only one image can be clicked at a time




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
    

class CamImage(WindowModel):
    def __init__(self, image, width=1200, length=800):
        super().__init__(width, length)  # 부모 클래스인 WindowModel 초기화
        self.image = pygame.image.load(image)
        self.update()

    def update(self):
        self.image = pygame.transform.scale(self.image, (300, 200))
        self.posx = self.CAM_BOUND_X
        self.posy = self.CAM_BOUND_Y
        self.width = int(self.WINDOW_WIDTH - self.CAM_BOUND_X)
        self.length = self.CAM_BOUND_LENGTH
        self.color = config.WHITE

        self.center_hor_line_start_pos = (self.GRID_WINDOW_WIDTH, int(self.length/2))
        self.center_hor_line_end_pos = (self.WINDOW_WIDTH, int(self.length/2))

        self.center_ver_line_start_pos = (self.GRID_WINDOW_WIDTH+int(self.width/2), 0)
        self.center_ver_line_end_pos = (self.GRID_WINDOW_WIDTH+int(self.width/2), self.length)

class CamDataModel:
    def __init__(self, image_path):
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (300, 200))  # 캠 이미지 크기 조절



        # fsub = io.BytesIO(image)
        # img = pygame.image.load(fsub, 'jpg')
        # img = pygame.surfarray.array3d(img)
        # if img.shape[-1] == 3:  # 3채널 이미지일 때
        #     img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # img = pygame.surfarray.make_surface(img)
        # img_rect = pygame.Rect(ToolConfig.CAM_POS_X, 0, ToolConfig.CAM_WINDOW_WIDTH, ToolConfig.CAM_WINDOW_LENGTH)

        # # 이미지의 스케일 조정
        # scaled_img = pygame.transform.scale(img, (img_rect.width, img_rect.height))

        # # 이미지 표시할 영역을 흰색으로 지우기
        # pygame.draw.rect(self.screen, (255, 255, 255), img_rect)

        # # 메인 화면(self.screen)에 이미지를 블릿
        # self.screen.blit(scaled_img, img_rect.topleft)