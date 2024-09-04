import pygame
from config import *

class MainViewer:
    def __init__(self, model, screen):
        self.model = model
        self.screen = screen

        self.running = True
        self.paused = True

        self.current_scan = 0
        self.before_scan = 0
        self.class_init()
    

    def class_init(self):
        self.background_image = BackGroundImageView(self.model.grid_model, self.screen)
        self.grid = GridView(self.model.grid_model, self.screen)
        self.radar_postions = MultipleRadarPositionView(self.model,self.screen)
        self.cambound = CamBoundView(self.model.cam_bound_model, self.screen)
        self.cam_left_button = CamChangeLeftButtonView(self.model.cam_change_left_button_model, self.screen)
        self.cam_right_button = CamChangeRightButtonView(self.model.cam_change_right_button_model, self.screen)
        
        self.cam_return_button = CamReturnButtonView(self.model.cam_return_button_model, self.screen)
        self.data_info_window = DataInfoWindowView(self.model.data_info_window_model,self.screen)

    def window_resize(self):
        self.class_init()
        

    def draw(self):
        # cam_data_list = ['../resources/1.jpg', '../resources/2.jpg', '../resources/3.jpg', '../resources/4.jpg', '../resources/5.jpg', '../resources/6.jpg', '../resources/7.jpg', '../resources/8.jpg',]
        cam_data_list = ['../resources/1.jpg', '../resources/2.jpg', '../resources/3.jpg', '../resources/4.jpg', '../resources/5.jpg']
        self.background_image.draw_background_image()
        self.grid.draw_grid()
        self.radar_postions.draw_radar_positions()
        self.radar_postions.draw_vision_object()
        # self.cambound.draw_vision_box()/
        self.model.cam_bound_model.cam_list_load(self.model.current_scan_data)
        self.model.cam_bound_model.render_cams(self.screen)
        self.cam_left_button.draw_vision_next_list_button()
        self.cam_right_button.draw_vision_next_list_button()
        if self.model.cam_bound_model.is_zoom():
            self.cam_return_button.draw_return_button()
        self.data_info_window.draw_data_info_window()
    

class GridView:
    def __init__(self, model, screen):
        self.screen = screen
        self.model = model


    def draw_grid(self):
        
        font = pygame.font.SysFont("arial", FONT_SIZE, True, False)

        center_x = (self.model.start_posx + self.model.end_posx)//2
        center_y = (self.model.start_posy + self.model.end_posy)//2

        for x in range(center_x, self.model.end_posx, self.model.interval_x):
            pygame.draw.line(self.screen, self.model.color, (x, 0), (x, self.model.GRID_WINDOW_LENGTH))
            label = font.render(str(int(x//SPLITED_SCALE_RATE_X))+"m", True, self.model.font_color)
            self.screen.blit(label, (x, self.model.GRID_WINDOW_LENGTH - GRID_X_SIZE))

        for x in range(center_x, self.model.start_posx, - self.model.interval_x):
            pygame.draw.line(self.screen, self.model.color, (x, 0), (x, self.model.GRID_WINDOW_LENGTH))
            label = font.render(str(int(x//SPLITED_SCALE_RATE_X))+"m", True, self.model.font_color)
            self.screen.blit(label, (x, self.model.GRID_WINDOW_LENGTH - GRID_X_SIZE))

        for y in range(center_y, self.model.end_posy, self.model.interval_y):
            pygame.draw.line(self.screen, self.model.color, (0, y), (self.model.GRID_WINDOW_WIDTH, y))
            label = font.render(str(y//SCALED_RATE_Y)+"m", True, self.model.font_color)
            self.screen.blit(label, (0, y))

        for y in range(center_y, self.model.start_posy, -self.model.interval_y):
            pygame.draw.line(self.screen, self.model.color, (0, y), (self.model.GRID_WINDOW_WIDTH, y))
            label = font.render(str(y//SCALED_RATE_Y)+"m", True, self.model.font_color)
            self.screen.blit(label, (0, y))
        # for y in range(center_y, 0, -ToolConfig.GRID_Y_SIZE):
        #     pygame.draw.line(self.screen, grid_color, (0, y), (ToolConfig.GRID_WINDOW_WIDTH, y))
        #     label = font.render(str((center_y-y)//ToolConfig.SCALED_RATE_Y)+"m", True, grid_font_color)
        #     self.screen.blit(label, (0, y))

        # for y in range(center_y, ToolConfig.GRID_WINDOW_LENGTH - ToolConfig.GRID_Y_SIZE, ToolConfig.GRID_Y_SIZE):
        #     pygame.draw.line(self.screen, grid_color, (0, y), (ToolConfig.GRID_WINDOW_WIDTH, y))
        #     label = font.render(str((center_y-y)//ToolConfig.SCALED_RATE_Y)+"m", True, grid_font_color)
        #     self.screen.blit(label, (0, y))
    
class CamBoundView:
    def __init__(self, model, screen):
        self.screen = screen
        self.model = model
    
    def draw_vision_box(self):
        pygame.draw.rect(self.screen, self.model.color, (self.model.posx, self.model.posy, self.model.width, self.model.length),2)
        pygame.draw.line(self.screen, self.model.color, self.model.center_hor_line_start_pos, self.model.center_hor_line_end_pos, 2)
        pygame.draw.line(self.screen, self.model.color, self.model.center_ver_line_start_pos, self.model.center_ver_line_end_pos, 2)

class CamChangeLeftButtonView:
    def __init__(self, model, screen):
        self.screen = screen
        self.model = model

    def draw_vision_next_list_button(self):
        pygame.draw.rect(
            self.screen, 
            self.model.color, 
            (self.model.button_posx, self.model.button_posy, self.model.button_width, self.model.button_length)
            
        )
        pygame.draw.rect(
            self.screen, 
            self.model.outline_color, 
            (self.model.button_posx, self.model.button_posy, self.model.button_width, self.model.button_length),
            2
        )

class CamChangeRightButtonView:
    def __init__(self, model, screen):
        self.screen = screen
        self.model = model

    def draw_vision_next_list_button(self):
        pygame.draw.rect(
            self.screen, 
            self.model.color, 
            (self.model.button_posx, self.model.button_posy, self.model.button_width, self.model.button_length)   
        )
        pygame.draw.rect(
            self.screen, 
            self.model.outline_color, 
            (self.model.button_posx, self.model.button_posy, self.model.button_width, self.model.button_length),
            2
        )

class CamReturnButtonView:
    def __init__(self, model, screen):
        self.screen = screen
        self.model = model

    def draw_return_button(self):
        pygame.draw.rect(
            self.screen, 
            self.model.color, 
            (self.model.button_posx, self.model.button_posy, self.model.button_width, self.model.button_length)   
        )
        pygame.draw.rect(
            self.screen, 
            self.model.outline_color, 
            (self.model.button_posx, self.model.button_posy, self.model.button_width, self.model.button_length),
            2
        )

class BackGroundImageView:
    def __init__(self, model, screen):
        self.model = model
        self.screen = screen

    def draw_background_image(self):
        background_image = pygame.image.load(BACKGROUND_IMAGE_PATH)
        resized_background_image = pygame.transform.scale(background_image, (self.model.GRID_WINDOW_WIDTH ,self.model.GRID_WINDOW_LENGTH))
        self.screen.blit(resized_background_image, (0, 0))
        
class MultipleRadarPositionView:
    def __init__(self, model, screen):
        self.model = model
        self.screen = screen
        self.center_x = self.model.window_model.GRID_WINDOW_WIDTH//2
        self.center_y = self.model.window_model.GRID_WINDOW_LENGTH//2
    def draw_radar_positions(self):
        pygame.draw.circle(self.screen, BLUE, (self.center_x, self.center_y), 5, 0)
        for data in self.model.current_scan_data:
        #need to consider extending to draw multiple radars
            radar_posx = data.radar_posx
            radar_posy = data.radar_posy
            pygame.draw.circle(self.screen, RED, (radar_posx, radar_posy), 5, 0)
            font = pygame.font.Font(None, 20)
            text = font.render(data.ip, True, RED)  # 렌더링할 텍스트와 색상
            text_rect = text.get_rect()

            # 텍스트 위치 설정 (원 아래)
            text_rect.center = (radar_posx, radar_posy + 10)  # 원 아래로 10 픽셀만큼 떨어뜨림

            # 텍스트 화면에 표시
            self.screen.blit(text, text_rect)
    
    def draw_vision_object(self):
        for data in self.model.current_scan_data:
            for vobj in data.vision_object_data:
                pygame.draw.circle(self.screen, GREEN, (self.center_x - vobj.posx, self.center_y - vobj.posy), 2, 0)

class DataInfoWindowView:
    def __init__(self, model, screen):
        self.screen = screen
        self.model = model
    
    def draw_data_info_window(self):
        pygame.draw.rect(self.screen, self.model.color, (self.model.posx, self.model.posy, self.model.width, self.model.length),2)