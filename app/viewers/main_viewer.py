import pygame


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
        self.model.cam_bound_model.render_cams(self.screen, self.model.current_scan_data)
        self.cam_left_button.draw_vision_next_list_button()
        self.cam_right_button.draw_vision_next_list_button()
        if self.model.cam_bound_model.is_zoom():
            self.cam_return_button.draw_return_button()
        self.data_info_window.draw_data_info_window()
        # self.model.object_matching()
    

class GridView:
    def __init__(self, model, screen):
        self.screen = screen
        self.model = model


    def draw_grid(self):
        
        font = pygame.font.SysFont("arial", self.model.font_size, True, False)

        center_x = (self.model.start_posx + self.model.end_posx)//2
        center_y = (self.model.start_posy + self.model.end_posy)//2

        for x in range(center_x, self.model.end_posx, self.model.interval_x):
            pygame.draw.line(self.screen, self.model.color, (x, 0), (x, self.model.GRID_WINDOW_LENGTH))
            label = font.render(str(int(x//self.model.SPLITED_SCALE_RATE_X))+"m", True, self.model.font_color)
            self.screen.blit(label, (x, self.model.GRID_WINDOW_LENGTH - self.model.GRID_X_SIZE))

        for x in range(center_x, self.model.start_posx, - self.model.interval_x):
            pygame.draw.line(self.screen, self.model.color, (x, 0), (x, self.model.GRID_WINDOW_LENGTH))
            label = font.render(str(int(x//self.model.SPLITED_SCALE_RATE_X))+"m", True, self.model.font_color)
            self.screen.blit(label, (x, self.model.GRID_WINDOW_LENGTH - self.model.GRID_X_SIZE))

        for y in range(center_y, self.model.end_posy, self.model.interval_y):
            pygame.draw.line(self.screen, self.model.color, (0, y), (self.model.GRID_WINDOW_WIDTH, y))
            label = font.render(str(y//self.model.SCALED_RATE_Y)+"m", True, self.model.font_color)
            self.screen.blit(label, (0, y))

        for y in range(center_y, self.model.start_posy, -self.model.interval_y):
            pygame.draw.line(self.screen, self.model.color, (0, y), (self.model.GRID_WINDOW_WIDTH, y))
            label = font.render(str(y//self.model.SCALED_RATE_Y)+"m", True, self.model.font_color)
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

    def draw_bbox(self):
        pass

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

        self.center_x = self.model.GRID_WINDOW_WIDTH//2
        self.center_y = self.model.GRID_WINDOW_LENGTH//2

    def draw_background_image(self):
        # TODO 아래 주석 해제
        # background_image = pygame.image.load(self.model.BACKGROUND_IMAGE_PATH)
        # resized_background_image = pygame.transform.scale(background_image, (self.model.GRID_WINDOW_WIDTH ,self.model.GRID_WINDOW_LENGTH))
        # self.screen.blit(resized_background_image, (0, 0))
        pygame.draw.circle(self.screen, self.model.center_point_color, (self.center_x, self.center_y), 5, 0)


        
class MultipleRadarPositionView:
    def __init__(self, model, screen):
        self.model = model
        self.screen = screen

    def draw_radar_positions(self):
        
        for data in self.model.current_scan_data:
            radar_posx = data.radar_posx
            radar_posy = data.radar_posy
            pygame.draw.circle(self.screen, data.color, (radar_posx, radar_posy), 5, 0)
            font = pygame.font.Font(None, 20)
            text = font.render(data.ip, True, self.model.cam_bound_model.cam_ip_box_color)  # 렌더링할 텍스트와 색상
            text_rect = text.get_rect()

            # 텍스트 위치 설정 (원 아래)
            text_rect.center = (radar_posx, radar_posy + 10)  # 원 아래로 10 픽셀만큼 떨어뜨림

            # 텍스트 화면에 표시
            self.screen.blit(text, text_rect)
    
    def draw_vision_object(self):
        
        for data in self.model.current_scan_data:
            for vobj in data.vision_object_data:
                pygame.draw.circle(self.screen, data.color, (vobj.posx, vobj.posy), 2, 0)
                pygame.draw.line(self.screen, data.speed_color, (vobj.posx, vobj.posy), (vobj.velx + vobj.posx, vobj.vely + vobj.posy), 1)
                # pygame.draw.circle(self.screen, RED, (vobj.velx, vobj.vely), 2, 0)
                polygon_pos = [
                    vobj.dl_pos,
                    
                    vobj.ul_pos,
                    vobj.ur_pos,
                    vobj.dr_pos,
                ]
                pygame.draw.polygon(self.screen, data.color, polygon_pos, 2)

    
class DataInfoWindowView:
    def __init__(self, model, screen):
        self.screen = screen
        self.model = model
    
    def draw_data_info_window(self):
        pygame.draw.rect(self.screen, self.model.color, (self.model.posx, self.model.posy, self.model.width, self.model.length),2)