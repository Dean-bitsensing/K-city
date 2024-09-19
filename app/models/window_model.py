import config 
from .input_processing import *
import pygame
import io, os
from .colors import *

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

        self.SCALED_RATE_X = 5
        self.SCALED_RATE_Y = 5

        self.GRID_X_SIZE =  8*self.SCALED_RATE_X
        self.GRID_Y_SIZE = 10*self.SCALED_RATE_Y

        self.SPLITED_SCALE_RATE = 0.75
        self.SPLITED_SCALE_RATE_X = self.SCALED_RATE_X*self.SPLITED_SCALE_RATE
        
        self.initialize_window_size()

    def initialize_window_size(self):
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
        self.initialize_window_size()

class GridModel(WindowModel):
    def __init__(self, width=1200, length=800):
        super().__init__(width, length)  # 부모 클래스인 WindowModel 초기화
        self.color = (0, 0, 0)
        self.font_color = (0, 0, 0)
        self.font_size = 10
        self.center_point_color = RED
        self.BACKGROUND_IMAGE_PATH = 'app/resources/map_image.png'
        self.parsing_map()
        
        self.update()

    def update(self):
        self.start_posx = 0
        self.end_posx = self.GRID_WINDOW_WIDTH  # WindowModel의 속성 직접 사용
        self.interval_x = int(self.GRID_X_SIZE )
        self.start_posy = 0
        self.end_posy = self.GRID_WINDOW_LENGTH
        self.interval_y = int(self.GRID_Y_SIZE)

    def parsing_map(self):
        # self.BACKGROUND_IMAGE_PATH = 'app/resources/map_image.png'
        if not os.path.exists(self.BACKGROUND_IMAGE_PATH):
            parsing_image_data_from_google(LAT_LANDMARK, LON_LANDMARK, self.GRID_WINDOW_WIDTH, self.GRID_WINDOW_LENGTH,zoom = 18, maptype = 'satellite', image_path=self.BACKGROUND_IMAGE_PATH)

class CamBoundModel(WindowModel):
    def __init__(self, width=1200, length=800):
        super().__init__(width, length)
        self.cam_data_list = []
        self.current_page = 0
        self.cams_per_page = 4
        self.cam_bbox_mode = 1
        self.cam_ip_box_color = RED
        self.zoom_init()
        self.update()

    def cam_list_load(self, logging_data):
        
        self.cam_data_list = []
        self.cam_ip_list = []
        self.cam_color = []
        for file in logging_data:
            image = file.current_scan_data.image
            ip = file.ip
            color = file.current_scan_data.color
            fsub = io.BytesIO(image)
            img = pygame.image.load(fsub, 'jpg')
            self.cam_ip_list.append(file.ip)
            self.cam_data_list.append(img)
            self.cam_color.append(color)

    def update(self):
        self.posx = self.CAM_BOUND_X
        self.posy = self.CAM_BOUND_Y
        self.width = int(self.WINDOW_WIDTH - self.CAM_BOUND_X)
        self.length = self.CAM_BOUND_LENGTH
        self.color = WHITE

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
    
    
    def render_cams(self, screen, logging_data):
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
        self.zoomed_image = None
        
        for i, idx in enumerate(cam_indices):
            if idx >= len(self.cam_data_list):
                break
            
            if self.zoomed_in[idx]:
                self.zoomed_image = (cams[i], (self.posx, self.posy), idx, ips[i], colors[i])
                break
        
        if self.zoomed_image:
            # Render only the zoomed-in image
            cam, pos, idx, ip, color = self.zoomed_image
            image = cam  # cam already contains the loaded image
            image = pygame.transform.scale(image, (self.width, self.length))
            # 글자 쓰기
            myFont = pygame.font.SysFont(None, 30) #(글자체, 글자크기) None=기본글자체
            myText = myFont.render("Cam : " + str(ip), True, (240,10,10), BLACK) #(Text,anti-alias, color)
            rect = pygame.Rect(pos[0], pos[1],self.width, self.length)
            
            screen.blit(image, pos)
            pygame.draw.rect(screen, color, rect, 2)
            screen.blit(myText, pos)
            self.render_bbox(screen, logging_data[idx].current_scan_data.vision_object_data, idx, (self.width, self.length), pos)
        else:
            # Render all images at their normal size
            for cam, pos, ip, color, idx in zip(cams, positions, ips, colors, cam_indices):
                image = cam  # cam already contains the loaded image
                image = pygame.transform.scale(image, (int(self.width / 2), int(self.length / 2)))
                
                myFont = pygame.font.SysFont(None, 30) #(글자체, 글자크기) None=기본글자체
                myText = myFont.render("Cam : " + str(ip), True, (240,10,10), BLACK) #(Text,anti-alias, color)
                
                rect = pygame.Rect(pos[0], pos[1],self.width/2, self.length/2)
                screen.blit(image, pos)
                pygame.draw.rect(screen, color, rect, 2)
                screen.blit(myText, pos)
                self.render_bbox(screen, logging_data[idx].current_scan_data.vision_object_data, idx, (self.width/2, self.length/2), pos)

    def render_bbox(self, screen, vision_object_data, idicies, image_size, cam_position):
        origin_size = (1024, 576)
        
        width_scale = image_size[0]/origin_size[0]
        length_scale = image_size[1]/origin_size[1]

        for vobj in vision_object_data:
            bbox_posx = vobj.bbox_posx
            bbox_posy = vobj.bbox_posy
            bbox_width = vobj.bbox_width
            bbox_length = vobj.bbox_length

            bbox_posx = int(width_scale * bbox_posx) + cam_position[0]
            bbox_posy = int(length_scale * bbox_posy) + cam_position[1]
            bbox_width = int(width_scale * bbox_width)
            bbox_length = int(width_scale * bbox_length)

            rect = pygame.Rect(bbox_posx, bbox_posy, bbox_width, bbox_length)
            pygame.draw.rect(screen, YELLOW, rect, 2)



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
        
        self.color = WHITE
        self.outline_color = BLACK
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
        self.color = WHITE
        self.outline_color = BLACK
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
        self.color = WHITE
        self.outline_color = BLACK
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


# def parsing_map(self):
#         # self.BACKGROUND_IMAGE_PATH = 'app/resources/map_image.png'
#         if not os.path.exists(self.BACKGROUND_IMAGE_PATH):
#             parsing_image_data_from_google(LAT_LANDMARK, LON_LANDMARK, self.window_model.GRID_WINDOW_WIDTH, self.window_model.GRID_WINDOW_LENGTH,zoom = 18, maptype = 'satellite', image_path=self.BACKGROUND_IMAGE_PATH)   