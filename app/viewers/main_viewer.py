import pygame
import math
import numpy as np

class MainViewer:
    def __init__(self, model, screen):
        self.model = model
        self.screen = screen

        self.running = True
        self.paused = True
        self.delete_mode = False
        self.fusion_only_mode = True
        self.radar_zone_view = False
        self.current_scan = 0
        self.before_scan = 0
        self.class_init()
    

    def class_init(self):
        self.background_image = BackGroundImageView(self.model.grid_model, self.screen)

        self.grid = GridView(self.model.grid_model, self.screen)
        self.radar_postions = MultipleRadarPositionView(self.model,self.screen)
        self.track_view = TrackView(self.model, self.screen)
        self.cambound = CamBoundView(self.model.cam_bound_model, self.screen)
        self.cam_left_button = CamChangeLeftButtonView(self.model.cam_change_left_button_model, self.screen)
        self.cam_right_button = CamChangeRightButtonView(self.model.cam_change_right_button_model, self.screen)
        
        self.cam_return_button = CamReturnButtonView(self.model.cam_return_button_model, self.screen)
        self.vds_data_button = InfoButtonView(self.model.vds_button_model, self.screen)
        self.vds_node_data_button = InfoButtonView(self.model.vds_node_button_model, self.screen)
        self.ids_data_button = InfoButtonView(self.model.ids_button_model, self.screen)
        self.save_change_button = InfoButtonView(self.model.save_button_model, self.screen)
        self.data_info_window = DataInfoWindowView(self.model.data_info_window_model,self.screen)

    def window_resize(self):
        self.class_init()
        

    def draw(self):      
        self.background_image.draw_background_image()
        # self.grid.draw_grid()
        self.radar_postions.draw_radar_positions()
        # self.radar_postions.draw_vision_object()
        if not self.fusion_only_mode:
            self.track_view.draw_fobj()
        
        if self.radar_zone_view:
            self.radar_postions.draw_radar_zone()

            self.radar_postions.draw_radar_positions()
            self.radar_postions.draw_radar_points()        
            self.radar_postions.draw_radar_detection_zone()

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
        self.ids_data_button.draw_return_button()
        self.save_change_button.draw_return_button()
        self.data_info_window.draw_data_info_window()
        self.data_info_window.draw_selected_atms_in_info_model(self.model.intersections)
        self.data_info_window.draw_scan_info(self.current_scan)
        
    def draw_fusion_obj(self, current_scan_kcity_fusion_obj):
        self.track_view.draw_kobj(current_scan_kcity_fusion_obj)
    

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


class TrackView:
    def __init__(self, model, screen):
        self.model = model
        self.screen = screen

        #TODO
        self.landmark = [45.4310364, 10.988078, 18]
        self.center_x = self.model.window_model.GRID_WINDOW_WIDTH//2
        self.center_y = self.model.window_model.GRID_WINDOW_LENGTH//2


    def check_in_grid_window(self, x, y):
        check_x = False
        check_y = False
        if 0 < x < self.model.window_model.GRID_WINDOW_WIDTH:
            check_x = True
        
        if 0 < y < self.model.window_model.GRID_WINDOW_LENGTH:
            check_y = True

        return check_x and check_y
    
    def draw_kobj(self, current_scan_kcity_fusion_obj):

        for kobj in current_scan_kcity_fusion_obj:
            if kobj.update_state < 2:
                continue

            self.draw_single_obj(kobj)

    def draw_fobj(self):
        for intersection in self.model.intersections:
            for atm in intersection.atms:
                if not atm.view:
                    continue
                for fobj in atm.current_scan_data.fusion_object_data:
                    self.draw_single_obj(fobj, atm.color)
    

    def meters_to_pixels(self, meters, lat, zoom, map_size, window_size):

        # 지구의 둘레 (Equatorial Circumference) = 40,075km
        EARTH_RADIUS = 6378137  # meters

        # 위도를 라디안으로 변환
        lat_rad = math.radians(lat)

        # 지도 상에서 한 픽셀당 미터를 계산 (줌 레벨과 위도에 따라 다름)
        meters_per_pixel = (math.cos(lat_rad) * 2 * math.pi * EARTH_RADIUS) / (2 ** zoom * 256)

        # 주어진 미터를 원본 지도 상의 픽셀로 변환
        pixels = meters / meters_per_pixel

        # 창 크기 대비 지도 크기에 따른 비율로 스케일링
        scale_x = window_size[0] / map_size[0]
        scale_y = window_size[1] / map_size[1]

        # 창에서의 픽셀 크기로 변환
        pixels_on_window = pixels * (scale_x + scale_y) / 2  # 가로 세로 비율의 평균 사용

        return pixels_on_window
    
    def rotate_point(self, x, y, angle, origin_x, origin_y):
        """ (x, y)를 중심(origin_x, origin_y) 기준으로 angle 만큼 회전시킨 좌표를 반환 """
        radians = math.radians(-angle)
        cos_theta = math.cos(radians)
        sin_theta = math.sin(radians)
        
        # 원점에서의 좌표 계산
        translated_x = x - origin_x
        translated_y = y - origin_y

        # 회전 변환
        rotated_x = translated_x * cos_theta - translated_y * sin_theta
        rotated_y = translated_x * sin_theta + translated_y * cos_theta

        # 원점 복귀
        final_x = rotated_x + origin_x
        final_y = rotated_y + origin_y

        return [final_x, final_y]    
    
    def draw_single_obj(self, obj, color = (255,255,255)):
        font = pygame.font.Font(None, 20)  

        posx =  obj.posx 
        posy =  - obj.posy 
        width = obj.width 
        length = obj.length 
        heading_angle_deg = obj.heading_angle_deg

        polygon_pos = self.get_polygon_pos(posx, posy, width, length, heading_angle_deg)   

        posx_pixel, posy_pixel = self.get_pixel_position(posx, posy)


        pygame.draw.circle(self.screen, color, (posx_pixel, posy_pixel), 2, 0)
        pygame.draw.polygon(self.screen, color, polygon_pos, 2)

    def get_pixel_position(self, posx, posy):
        posx_pixel = self.meters_to_pixels(posx, self.landmark[0], 18, (640, 640), (self.center_x*2, self.center_y*2))
        posy_pixel = self.meters_to_pixels(posy, self.landmark[0], 18, (640, 640), (self.center_x*2, self.center_y*2))

        posx_pixel += self.center_x
        posy_pixel += self.center_y

        return posx_pixel, posy_pixel
    
    def get_polygon_pos(self, posx, posy, width, length, heading_angle_deg):

        ul_pos = [int(posx - length/2), int(posy - width/2)]
        ur_pos = [int(posx - length/2), int(posy + width/2)]
        dl_pos = [int(posx + length/2), int(posy - width/2)]
        dr_pos = [int(posx + length/2), int(posy + width/2)]

        ul_pos = self.rotate_point(*ul_pos, heading_angle_deg, posx, posy)
        ur_pos = self.rotate_point(*ur_pos, heading_angle_deg, posx, posy)
        dl_pos = self.rotate_point(*dl_pos, heading_angle_deg, posx, posy)
        dr_pos = self.rotate_point(*dr_pos, heading_angle_deg, posx, posy)

        ul_pos[0] = self.meters_to_pixels(ul_pos[0], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
        ul_pos[0] += self.center_x
        ul_pos[1] = self.meters_to_pixels(ul_pos[1], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
        ul_pos[1] += self.center_y

        ur_pos[0] = self.meters_to_pixels(ur_pos[0], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
        ur_pos[0] += self.center_x
        ur_pos[1] = self.meters_to_pixels(ur_pos[1], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
        ur_pos[1] += self.center_y

        dl_pos[0] = self.meters_to_pixels(dl_pos[0], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
        dl_pos[0] += self.center_x
        dl_pos[1] = self.meters_to_pixels(dl_pos[1], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
        dl_pos[1] += self.center_y

        dr_pos[0] = self.meters_to_pixels(dr_pos[0], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
        dr_pos[0] += self.center_x
        dr_pos[1] = self.meters_to_pixels(dr_pos[1], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
        dr_pos[1] += self.center_y

        return [ dl_pos, ul_pos, ur_pos, dr_pos ] 
    
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
    
    # def draw_radar_lane(self):
    #     for intersection in self.model.intersections:
    #         for atm in intersection.atms:


    def draw_radar_zone(self):
        for intersection in self.model.intersections:
            for atm in intersection.atms:
                if atm.radar_zone_json == None:
                    continue
                for zone in atm.zones:
                    for step in range(zone.step_number-1):
                        left_point_start = (zone.left_x[step],zone.left_y[step])
                        left_point_end = (zone.left_x[step+1],zone.left_y[step+1])
                        right_point_start = (zone.right_x[step],zone.right_y[step])
                        right_point_end = (zone.right_x[step+1],zone.right_y[step+1])
                        pygame.draw.circle(self.screen, (255, 0, 0), left_point_start, 5)  # 왼쪽 꼭지점
                        pygame.draw.circle(self.screen, (255, 0, 0), right_point_start, 5)  # 오른쪽 꼭지점
                        pygame.draw.line(self.screen, atm.color, left_point_start, left_point_end, 3)
                        pygame.draw.line(self.screen, atm.color, right_point_start, right_point_end, 3)

                    left_start_point = (zone.left_x[0],zone.left_y[0])
                    right_start_point = (zone.right_x[0],zone.right_y[0])

                    left_end_point = (zone.left_x[zone.step_number-1],zone.left_y[zone.step_number-1])
                    right_end_point = (zone.right_x[zone.step_number-1],zone.right_y[zone.step_number-1])                    

                    pygame.draw.line(self.screen, atm.color, left_start_point, right_start_point, 3)
                    pygame.draw.line(self.screen, atm.color, left_end_point, right_end_point, 3)

                    font = pygame.font.Font(None, 20)
                    # text = font.render(atm.ip, True, self.model.cam_bound_model.cam_ip_box_color)  # 렌더링할 텍스트와 색상
                    
                    # # 텍스트를 렌더링 (안티앨리어싱: True, 색상: 흰색)
                    # text_surface = font.render(zone.guid, True, (0, 255, 0))

                    # 텍스트를 pos 위치에 그리기
                    # self.screen.blit(text_surface, left_start_point)
        
    def draw_radar_detection_zone(self):
        for intersection in self.model.intersections:
            for atm in intersection.atms:
                if atm.selected:
                    atm.detection_zone.draw_sector(self.screen)

    def draw_radar_points(self):
        for intersection in self.model.intersections:
            for atm in intersection.atms:
                if atm.radar_zone_json == None:
                    continue
                for zone in atm.zones:
                    for step in range(zone.step_number):
                        left_point = (zone.left_x[step],zone.left_y[step])
                        right_point = (zone.right_x[step],zone.right_y[step])
                        pygame.draw.circle(self.screen, (255, 0, 0), left_point, 5)  # 왼쪽 꼭지점
                        pygame.draw.circle(self.screen, (255, 0, 0), right_point, 5)  # 오른쪽 꼭지점


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
    

    def draw_fusion_object(self):
        for intersection in self.model.intersections:
            for atm in intersection.atms:
                if not atm.view:
                    continue
                for fobj in atm.current_scan_data.fusion_object_data:
                    self.draw_single_obj(fobj)
                    

    def meters_to_pixels(self, meters, lat, zoom, map_size, window_size):

        # 지구의 둘레 (Equatorial Circumference) = 40,075km
        EARTH_RADIUS = 6378137  # meters

        # 위도를 라디안으로 변환
        lat_rad = math.radians(lat)

        # 지도 상에서 한 픽셀당 미터를 계산 (줌 레벨과 위도에 따라 다름)
        meters_per_pixel = (math.cos(lat_rad) * 2 * math.pi * EARTH_RADIUS) / (2 ** zoom * 256)

        # 주어진 미터를 원본 지도 상의 픽셀로 변환
        pixels = meters / meters_per_pixel

        # 창 크기 대비 지도 크기에 따른 비율로 스케일링
        scale_x = window_size[0] / map_size[0]
        scale_y = window_size[1] / map_size[1]

        # 창에서의 픽셀 크기로 변환
        pixels_on_window = pixels * (scale_x + scale_y) / 2  # 가로 세로 비율의 평균 사용

        return pixels_on_window
    
    def rotate_point(self, x, y, angle, origin_x, origin_y):
        """ (x, y)를 중심(origin_x, origin_y) 기준으로 angle 만큼 회전시킨 좌표를 반환 """
        radians = math.radians(-angle)
        cos_theta = math.cos(radians)
        sin_theta = math.sin(radians)
        
        # 원점에서의 좌표 계산
        translated_x = x - origin_x
        translated_y = y - origin_y

        # 회전 변환
        rotated_x = translated_x * cos_theta - translated_y * sin_theta
        rotated_y = translated_x * sin_theta + translated_y * cos_theta

        # 원점 복귀
        final_x = rotated_x + origin_x
        final_y = rotated_y + origin_y

        return [final_x, final_y]    
    
    def draw_single_obj(self, obj):
        font = pygame.font.Font(None, 20)  

        posx =  obj.posx 
        posy =  - obj.posy 
        width = obj.width 
        length = obj.length 
        heading_angle_deg = obj.heading_angle_deg
        id_text = str(obj.id)  # ID를 문자열로 변환
        color = (255,255,255)

        polygon_pos = self.get_polygon_pos(posx, posy, width, length, heading_angle_deg)   

        posx_pixel, posy_pixel = self.get_pixel_position(posx, posy)

        text_surface = font.render(id_text, True, (0, 100, 0))

        self.screen.blit(text_surface, (posx_pixel, posy_pixel))

        pygame.draw.circle(self.screen, color, (posx_pixel, posy_pixel), 2, 0)
        pygame.draw.polygon(self.screen, color, polygon_pos, 2)

    def get_pixel_position(self, posx, posy):
        posx_pixel = self.meters_to_pixels(posx, self.landmark[0], 18, (640, 640), (self.center_x*2, self.center_y*2))
        posy_pixel = self.meters_to_pixels(posy, self.landmark[0], 18, (640, 640), (self.center_x*2, self.center_y*2))

        posx_pixel += self.center_x
        posy_pixel += self.center_y

        return posx_pixel, posy_pixel
    
    def get_polygon_pos(self, posx, posy, width, length, heading_angle_deg):

        ul_pos = [int(posx - length/2), int(posy - width/2)]
        ur_pos = [int(posx - length/2), int(posy + width/2)]
        dl_pos = [int(posx + length/2), int(posy - width/2)]
        dr_pos = [int(posx + length/2), int(posy + width/2)]

        ul_pos = self.rotate_point(*ul_pos, heading_angle_deg, posx, posy)
        ur_pos = self.rotate_point(*ur_pos, heading_angle_deg, posx, posy)
        dl_pos = self.rotate_point(*dl_pos, heading_angle_deg, posx, posy)
        dr_pos = self.rotate_point(*dr_pos, heading_angle_deg, posx, posy)

        ul_pos[0] = self.meters_to_pixels(ul_pos[0], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
        ul_pos[0] += self.center_x
        ul_pos[1] = self.meters_to_pixels(ul_pos[1], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
        ul_pos[1] += self.center_y

        ur_pos[0] = self.meters_to_pixels(ur_pos[0], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
        ur_pos[0] += self.center_x
        ur_pos[1] = self.meters_to_pixels(ur_pos[1], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
        ur_pos[1] += self.center_y

        dl_pos[0] = self.meters_to_pixels(dl_pos[0], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
        dl_pos[0] += self.center_x
        dl_pos[1] = self.meters_to_pixels(dl_pos[1], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
        dl_pos[1] += self.center_y

        dr_pos[0] = self.meters_to_pixels(dr_pos[0], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
        dr_pos[0] += self.center_x
        dr_pos[1] = self.meters_to_pixels(dr_pos[1], self.landmark[0], self.landmark[2], (640, 640), (self.center_x*2, self.center_y*2))
        dr_pos[1] += self.center_y

        return [ dl_pos, ul_pos, ur_pos, dr_pos ] 

    
class DataInfoWindowView:
    def __init__(self, model, screen):
        self.screen = screen
        self.model = model
    
    def draw_data_info_window(self):
        pygame.draw.rect(self.screen, self.model.color, (self.model.posx, self.model.posy, self.model.width, self.model.length),2)

    def draw_scan_info(self, scan_num):
        font = pygame.font.Font(None, 20)
        text = font.render(str(scan_num), True, (255, 255, 255))  # 흰색 텍스트
        self.screen.blit(text, (50, 50))
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

        y_offset = 100  # 처음 텍스트의 y 위치
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

