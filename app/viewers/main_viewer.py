import pygame


class MainViewer:
    def __init__(self, model, screen):
        self.model = model
        self.screen = screen

        self.running = True
        self.paused = True
        self.delete_mode = False
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
        self.vds_data_button = InfoButtonView(self.model.vds_button_model, self.screen)
        self.vds_node_data_button = InfoButtonView(self.model.vds_node_button_model, self.screen)
        self.save_change_button = InfoButtonView(self.model.save_button_model, self.screen)
        self.data_info_window = DataInfoWindowView(self.model.data_info_window_model,self.screen)

    def window_resize(self):
        self.class_init()
        

    def draw(self):      
        self.background_image.draw_background_image()
        self.grid.draw_grid()
        self.radar_postions.draw_radar_positions()
        # self.radar_postions.draw_vision_object()
        self.radar_postions.draw_fusion_object()
        self.radar_postions.draw_fusion_object_index()

        if self.delete_mode:
            self.data_info_window.draw_delete_info()
        
        self.model.cam_bound_model.cam_list_load(self.model.intersections)
        self.model.cam_bound_model.render_cams(self.screen, self.model.intersections)
        

        self.cam_left_button.draw_vision_next_list_button()
        self.cam_right_button.draw_vision_next_list_button()

        if self.model.cam_bound_model.is_zoom():
            self.cam_return_button.draw_return_button()
        
        self.vds_data_button.draw_return_button()
        self.vds_node_data_button.draw_return_button()
        self.save_change_button.draw_return_button()
        self.data_info_window.draw_data_info_window()
        self.data_info_window.draw_selected_atms_in_info_model(self.model.intersections)
        
    

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

class InfoButtonView:
    def __init__(self, model, screen):
        self.screen = screen
        self.model = model
        self.font = pygame.font.Font(None, self.model.font_size)  # 기본 폰트 사용, 크기는 36

    def draw_return_button(self):
        # 버튼 그리기
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

        # 텍스트 렌더링
        text_surface = self.font.render(self.model.text, True, self.model.text_color)
        text_rect = text_surface.get_rect()

        # 텍스트를 버튼 중앙에 배치
        text_rect.center = (
            self.model.button_posx + self.model.button_width // 2,
            self.model.button_posy + self.model.button_length // 2
        )

        # 텍스트 그리기
        self.screen.blit(text_surface, text_rect)


class BackGroundImageView:
    def __init__(self, model, screen):
        self.model = model
        self.screen = screen

        self.center_x = self.model.GRID_WINDOW_WIDTH//2
        self.center_y = self.model.GRID_WINDOW_LENGTH//2

    def draw_background_image(self):        
        background_image = pygame.image.load(self.model.BACKGROUND_IMAGE_PATH)
        resized_background_image = pygame.transform.scale(background_image, (self.model.GRID_WINDOW_WIDTH ,self.model.GRID_WINDOW_LENGTH))
        self.screen.blit(resized_background_image, (0, 0))
        pygame.draw.circle(self.screen, self.model.center_point_color, (self.center_x, self.center_y), 5, 0)


        
class MultipleRadarPositionView:
    def __init__(self, model, screen):
        self.model = model
        self.screen = screen

    def check_in_grid_window(self, x, y):
        check_x = False
        check_y = False
        if 0 < x < self.model.window_model.GRID_WINDOW_WIDTH:
            check_x = True
        
        if 0 < y < self.model.window_model.GRID_WINDOW_LENGTH:
            check_y = True

        return check_x and check_y
        
        
    def draw_radar_positions(self):
        for intersection in self.model.intersections:
            for atm in intersection.atms:
                radar_posx = atm.current_scan_data.radar_posx
                radar_posy = atm.current_scan_data.radar_posy
                if atm.selected == False:
                    pygame.draw.circle(self.screen, atm.color, (radar_posx, radar_posy), 7, 0)
                else:
                    pygame.draw.circle(self.screen, (0,0,0), (radar_posx, radar_posy), 7, 0)
                font = pygame.font.Font(None, 20)
                text = font.render(atm.ip, True, self.model.cam_bound_model.cam_ip_box_color)  # 렌더링할 텍스트와 색상
                text_rect = text.get_rect()

                # 텍스트 위치 설정 (원 아래)
                text_rect.center = (radar_posx, radar_posy + 10)  # 원 아래로 10 픽셀만큼 떨어뜨림

                # 텍스트 화면에 표시
                self.screen.blit(text, text_rect)
    
    def draw_vision_object(self):
        
        for data in self.model.logging_data:
            for vobj in data.current_scan_data.vision_object_data:
                if not self.check_in_grid_window(vobj.posx, vobj.posy):
                    continue
                if vobj.id in data.selected_vobj_id:
                    pygame.draw.circle(self.screen, (0,0,0), (vobj.posx, vobj.posy), 2, 0)
                    pygame.draw.circle(self.screen, (250,250,250), (vobj.posx, vobj.posy), 3, 1)
                else:
                    pygame.draw.circle(self.screen, data.current_scan_data.color, (vobj.posx, vobj.posy), 2, 0)
                # pygame.draw.line(self.screen, data.speed_color, (vobj.posx, vobj.posy), (vobj.velx + vobj.posx, vobj.vely + vobj.posy), 1)
                # pygame.draw.circle(self.screen, RED, (vobj.velx, vobj.vely), 2, 0)
                polygon_pos = [
                    vobj.dl_pos,
                    vobj.ul_pos,
                    vobj.ur_pos,
                    vobj.dr_pos,
                ]
                # pygame.draw.polygon(self.screen, data.color, polygon_pos, 2) # vision object square box

    def draw_fusion_object(self):
        for intersection in self.model.intersections:
            for atm in intersection.atms:
                if not atm.view:
                    continue
                for fobj in atm.current_scan_data.fusion_object_data:
                    if not self.check_in_grid_window(fobj.trns_posx, fobj.trns_posy):
                        continue
                    if fobj.id in atm.selected_fobj_id:
                        pygame.draw.circle(self.screen, (0,0,0), (fobj.trns_posx, fobj.trns_posy), 2, 0)
                        pygame.draw.circle(self.screen, (250,250,250), (fobj.trns_posx, fobj.trns_posy), 3, 1)
                    else:
                        pygame.draw.circle(self.screen, atm.color, (fobj.trns_posx, fobj.trns_posy), 2, 0)
                    # pygame.draw.line(self.screen, data.speed_color, (fobj.posx, fobj.posy), (fobj.velx + fobj.posx, fobj.vely + fobj.posy), 1)
                    # pygame.draw.circle(self.screen, RED, (fobj.velx, fobj.vely), 2, 0)
                    polygon_pos = [
                        fobj.dl_pos,
                        
                        fobj.ul_pos,
                        fobj.ur_pos,
                        fobj.dr_pos,
                    ]
                    pygame.draw.polygon(self.screen, atm.color, polygon_pos, 2) # vision object square box

    def draw_fusion_object_index(self): 
        font = pygame.font.Font(None, 20)  # 크기 24로 설정

        for intersection in self.model.intersections: # TODO 현재 모든 atm데이터에 대해서 다 그리고 있지만, atm별로 하는 것으로 구분할 필요있음
            for atm in intersection.atms:
                if not atm.view:
                    continue
                for fobj in atm.current_scan_data.fusion_object_data:
                    if not self.check_in_grid_window(fobj.trns_posx, fobj.trns_posy):
                        continue

                    id_text = str(fobj.id)  # ID를 문자열로 변환
                    pos = (fobj.trns_posx, fobj.trns_posy)

                    # 텍스트를 렌더링 (안티앨리어싱: True, 색상: 흰색)
                    text_surface = font.render(id_text, True, (0, 100, 0))

                    # 텍스트를 pos 위치에 그리기
                    self.screen.blit(text_surface, pos)
    
class DataInfoWindowView:
    def __init__(self, model, screen):
        self.screen = screen
        self.model = model
    
    def draw_data_info_window(self):
        pygame.draw.rect(self.screen, self.model.color, (self.model.posx, self.model.posy, self.model.width, self.model.length),2)

    def draw_delete_info(self):
        font = pygame.font.Font(None, 20)
        text_lines = [
            "delete + 0 : 1.0.0.20",
            "delete + 1 : 1.0.0.21 not able",
            "delete + 2 : 1.0.0.22",
            "delete + 3 : 1.0.0.23",
            "delete + 4 : 1.0.0.24",
            "delete + 5 : 1.0.0.25",
            "",
            "delete + 6 : 1.0.0.10 not able",
            "delete + 7 : 1.0.0.11 not able",
            "delete + 8 : 1.0.0.12",
            "delete + 9 : 1.0.0.13 not able",
        ]

        y_offset = 25  # 처음 텍스트의 y 위치
        for line in text_lines:
            text = font.render(line, True, (255, 255, 255))  # 흰색 텍스트
            self.screen.blit(text, (50, y_offset))  # 텍스트를 화면에 출력
            y_offset += 40  # 다음 텍스트의 y 위치를 아래로 이동

    def draw_selected_atms_in_info_model(self, intersections):
        font = pygame.font.Font(None, self.model.font_size)
        y_offset = self.model.offset
        for intersection in intersections:
            for atm in intersection.atms:
                if atm.selected:
                    if atm.vds_view:
                        text_surface = font.render(atm.ip, True, self.model.selected_font_color)
                    else:
                        text_surface = font.render(atm.ip, True, self.model.base_font_color)   
                    self.screen.blit(text_surface, (self.model.posx + self.model.offset, self.model.posy + y_offset))
                    y_offset +=self.model.offset

