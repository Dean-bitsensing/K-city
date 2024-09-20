# models/camera_display_model.py

import pygame
import io
from .window_model import WindowModel
from .colors import RED, WHITE, BLACK, YELLOW  # Ensure these are defined

class CamData:
    def __init__(self, ip, image, color, zoom):
        self.ip = ip
        self.image = image
        self.color = color
        # self.zoom = zoom

class CameraDisplayModel(WindowModel):
    def __init__(self, width=1200, length=800):
        super().__init__(width, length)
        
        self.current_page = 0
        self.cams_per_page = 4
        self.cam_bbox_mode = 1
        self.cam_ip_box_color = RED
        self.zoom_init()
        self.update(width, length)

    def cam_list_load(self, intersections):
        self.cam_list = []
        for intersection in intersections:
            for atm in intersection.atms:
                
                image = atm.current_scan_data.image
                fsub = io.BytesIO(image)
                img = pygame.image.load(fsub, 'jpg')

                cam = CamData(atm.ip, img, atm.color, False)
                self.cam_list.append(cam)
                # self.cam_ip_list.append(atm.ip)
                # self.cam_data_list.append(img)
                # self.cam_color.append(color)

    def update(self, width, length):
        super().__init__(width, length)
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
        return self.cam_list[start_idx:end_idx], list(range(start_idx, end_idx))

    def next_page(self):
        if (self.current_page + 1) * self.cams_per_page < len(self.cam_list):
            self.current_page += 1

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
    
    
    def render_cams(self, screen, intersections):
        if len(self.cam_list) == 0:
            return
        
        cams, cam_indices = self.get_current_page_cams()
        
        positions = [
            (self.posx, self.posy),
            (self.center_ver_line_start_pos[0], self.posy),
            (self.posx, self.center_hor_line_start_pos[1]),
            (self.center_ver_line_start_pos[0], self.center_hor_line_start_pos[1])
        ]
        
        # Determine which image is zoomed in, if any
        self.zoomed_image = None
        
        for i, idx in enumerate(cam_indices):
            if idx >= len(self.cam_list):
                break
            
            if self.zoom[idx]: 
                self.zoomed_image = (cams[i], (self.posx, self.posy), idx)
                break
        
        if self.zoomed_image:
            # Render only the zoomed-in image
            cam, pos, idx = self.zoomed_image
            image = cam.image  # cam already contains the loaded image
            image = pygame.transform.scale(image, (self.width, self.length))
            # 글자 쓰기
            myFont = pygame.font.SysFont(None, 30) #(글자체, 글자크기) None=기본글자체
            myText = myFont.render("Cam : " + str(cam.ip), True, (240,10,10), BLACK) #(Text,anti-alias, color)
            rect = pygame.Rect(pos[0], pos[1],self.width, self.length)
            
            screen.blit(image, pos)
            pygame.draw.rect(screen, cam.color, rect, 2)
            screen.blit(myText, pos)
            #TODO bbox rendering
            # self.render_bbox(screen, logging_data[idx].current_scan_data.vision_object_data, idx, (self.width, self.length), pos)
        else:
            # Render all images at their normal size
            for cam, pos, idx in zip(cams, positions, cam_indices):
                image = cam.image  # cam already contains the loaded image
                image = pygame.transform.scale(image, (int(self.width / 2), int(self.length / 2)))
                
                myFont = pygame.font.SysFont(None, 30) #(글자체, 글자크기) None=기본글자체
                myText = myFont.render("Cam : " + str(cam.ip), True, (240,10,10), BLACK) #(Text,anti-alias, color)
                
                rect = pygame.Rect(pos[0], pos[1],self.width/2, self.length/2)
                screen.blit(image, pos)
                pygame.draw.rect(screen, cam.color, rect, 2)
                screen.blit(myText, pos)
                #TODO bbox
                # self.render_bbox(screen, logging_data[idx].current_scan_data.vision_object_data, idx, (self.width/2, self.length/2), pos)

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
                
                if not self.zoom[idx]:
                    self.zoom_init()
                    self.zoom[idx] = True
                
                else:
                    self.zoom[idx] = False
                break  # Only one image can be clicked at a time
    
    def zoom_init(self):
        self.zoom = [False] * 20
        

    def is_zoom(self):
        if True in self.zoom:
            return 1
        else:
            return 0
        # for cam in self.cam_list:
        #     if cam.zoom == True:
        #         return 1
        # else:
        #     return 0
        

    def next_zoom(self):
        # 현재 줌된 카메라의 인덱스를 찾음
        current_zoom_index = None
        for i, zoom in enumerate(self.zoom):
            if zoom:
                current_zoom_index = i
                break
        # 현재 페이지에 마지막 카메라가 줌된 상태이면 페이지 넘기기
        if current_zoom_index is not None:
            next_zoom_index = current_zoom_index + 1
                
            if next_zoom_index >= len(self.cam_list):
                self.zoom_init()
            # 현재 페이지의 마지막 카메라를 넘으면 다음 페이지로 이동
            
            elif (next_zoom_index % self.cams_per_page) == 0:
                self.next_page()  # 페이지 넘기기
                self.zoom_init()  # 줌 초기화
                self.zoom[next_zoom_index] = True  # 다음 페이지의 첫 번째 카메라를 확대
            else:
                # 다음 카메라로 줌 이동
                self.zoom[current_zoom_index] = False
                self.zoom[next_zoom_index] = True

    def previous_zoom(self):
        # 현재 줌된 카메라의 인덱스를 찾음
        current_zoom_index = None
        for i, zoom in enumerate(self.zoom):
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
                    self.zoom[self.cams_per_page - 1] = True  # 이전 페이지의 마지막 카메라를 확대
            else:
                # 이전 카메라로 줌 이동
                self.zoom[current_zoom_index] = False
                self.zoom[previous_zoom_index] = True

"""
"""
"""
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
"""