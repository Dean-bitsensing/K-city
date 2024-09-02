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


    def window_resize(self):
        self.class_init()
        

    def draw(self):
        # cam_data_list = ['../resources/1.jpg', '../resources/2.jpg', '../resources/3.jpg', '../resources/4.jpg', '../resources/5.jpg', '../resources/6.jpg', '../resources/7.jpg', '../resources/8.jpg',]
        cam_data_list = ['../resources/1.jpg', '../resources/2.jpg', '../resources/3.jpg', '../resources/4.jpg', '../resources/5.jpg']
        self.grid.draw_grid()
        # self.cambound.draw_vision_box()/
        
        self.model.cam_bound_model.cam_list_load(self.model.current_scan_data)
        self.model.cam_bound_model.render_cams(self.screen)
        self.cam_left_button.draw_vision_next_list_button()
        self.cam_right_button.draw_vision_next_list_button()
    
    


class GridView:
    def __init__(self, model, screen):
        self.screen = screen
        self.model = model


    def draw_grid(self):
        
        font = pygame.font.SysFont("arial", FONT_SIZE, True, False)

        for x in range(self.model.start_posx, self.model.end_posx, self.model.interval_x):
            pygame.draw.line(self.screen, self.model.color, (x, 0), (x, self.model.GRID_WINDOW_LENGTH))
            label = font.render(str(int(x//SPLITED_SCALE_RATE_X))+"m", True, self.model.font_color)
            self.screen.blit(label, (x, self.model.GRID_WINDOW_LENGTH - GRID_X_SIZE))

        for y in range(self.model.start_posy, self.model.end_posy, self.model.interval_y):
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

class BackGroundImageView:
    def __init__(self, model, screen):
        self.model = model
        self.screen = screen

    def draw_background_image(self):
        background_image = pygame.image.load(BACKGROUND_IMAGE_PATH)
        self.screen.blit(background_image, (0, 0))
        
class MultipleRadarPositionView:
    def __init__(self, model, screen):
        self.model = model
        self.screen = screen

    def draw_radar_positions(self):
        #need to consider extending to draw multiple radars
        radar_posx = self.model.current_scan_data.radar_posx
        radar_posy = self.model.current_scan_data.radar_posy
        pygame.draw.circle(self.screen, RED, (radar_posx, radar_posy), 20, 0)
