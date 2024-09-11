import config 
from .input_processing import *
import pygame
import io, os

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
        self.font_size = 10
        self.center_point_color = RED
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
        self.cam_ip_list = []
        for idx in range(len(image_sets)):
            image = image_sets[idx].image
            ip = image_sets[idx].ip
            fsub = io.BytesIO(image)
            img = pygame.image.load(fsub, 'jpg')
            self.cam_ip_list.append(ip)
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
        return self.cam_data_list[start_idx:end_idx], list(range(start_idx, end_idx)), self.cam_ip_list[start_idx:end_idx]

    def next_page(self):
        if (self.current_page + 1) * self.cams_per_page < len(self.cam_data_list):
            self.current_page += 1

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1

    def render_cams(self, screen):
        if len(self.cam_data_list) == 0:
            return
        
        cams, cam_indices, ips = self.get_current_page_cams()
        
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
                zoomed_image = (cams[i], (self.posx, self.posy), idx, ips[i])
                break
        
        if zoomed_image:
            # Render only the zoomed-in image
            cam, pos, idx, ip = zoomed_image
            image = cam  # cam already contains the loaded image
            image = pygame.transform.scale(image, (self.width, self.length))
            # 글자 쓰기
            myFont = pygame.font.SysFont(None, 30) #(글자체, 글자크기) None=기본글자체
            myText = myFont.render("Cam : " + str(ip), True, (240,10,10), BLACK) #(Text,anti-alias, color)
            
            screen.blit(image, pos)
            screen.blit(myText, pos)
        else:
            # Render all images at their normal size
            for cam, pos, ip in zip(cams, positions, ips):
                image = cam  # cam already contains the loaded image
                image = pygame.transform.scale(image, (int(self.width / 2), int(self.length / 2)))
                
                myFont = pygame.font.SysFont(None, 30) #(글자체, 글자크기) None=기본글자체
                myText = myFont.render("Cam : " + str(ip), True, (240,10,10), BLACK) #(Text,anti-alias, color)
                
                screen.blit(image, pos)
                screen.blit(myText, pos)


    def handle_image_click(self, mouse_pos):
        # Handle click events for camera images
        cams, cam_indices, ips = self.get_current_page_cams()
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


def parsing_map(self):
        # self.BACKGROUND_IMAGE_PATH = 'app/resources/map_image.png'
        if not os.path.exists(self.BACKGROUND_IMAGE_PATH):
            parsing_image_data_from_google(LAT_LANDMARK, LON_LANDMARK, self.window_model.GRID_WINDOW_WIDTH, self.window_model.GRID_WINDOW_LENGTH,zoom = 18, maptype = 'satellite', image_path=self.BACKGROUND_IMAGE_PATH)   