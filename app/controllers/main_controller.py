import pygame
import os
import yaml
from .UI_windows import *
from .UI_save_window import *

SKIP_SIZE = 1
BIG_SKIP_SIZE = 20
LARGE_SKIP_SIZE = 100

class MainController:
    def __init__(self, model, viewer):
        self.model = model
        self.viewer = viewer

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.viewer.running = False
            os._exit(0)
        elif event.type == pygame.VIDEORESIZE:
            self.update_config(event.w, event.h)
        elif event.type == pygame.KEYDOWN:
            self.handle_keydown(event)
            keys = pygame.key.get_pressed()
            self.handle_double_keydown(keys)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                self.handle_mouse_left_click(event.pos)
            elif event.button == 2:  # middle mouse button
                pass 
            elif event.button == 3:  # right mouse button
                self.handle_mouse_right_click(event.pos)

    def handle_keydown(self, event):
        if event.key == pygame.K_LEFT:
            self.viewer.paused = True
            if self.viewer.current_scan - SKIP_SIZE > self.model.min_scan:
                self.viewer.current_scan -= SKIP_SIZE
            else:
                self.viewer.current_scan = self.model.min_scan

        elif event.key == pygame.K_RIGHT:
            self.viewer.paused = True
            if self.viewer.current_scan + SKIP_SIZE < self.model.max_scan:
                self.viewer.current_scan += SKIP_SIZE
            else:
                self.viewer.current_scan = self.model.max_scan

        elif event.key == pygame.K_UP:
            self.viewer.paused = True
            if self.viewer.current_scan + BIG_SKIP_SIZE < self.model.max_scan:
                self.viewer.current_scan += BIG_SKIP_SIZE
            else:
                self.viewer.current_scan = self.model.max_scan

        elif event.key == pygame.K_DOWN:
            self.viewer.paused = True
            if self.viewer.current_scan - BIG_SKIP_SIZE > self.model.min_scan:
                self.viewer.current_scan -= BIG_SKIP_SIZE
            else:
                self.viewer.current_scan = self.model.min_scan

        elif event.key == pygame.K_PERIOD:
            self.viewer.paused = True
            if self.viewer.current_scan + LARGE_SKIP_SIZE < self.model.max_scan:
                self.viewer.current_scan += LARGE_SKIP_SIZE
            else:
                self.viewer.current_scan = self.model.max_scan

        elif event.key == pygame.K_COMMA:
            self.viewer.paused = True
            if self.viewer.current_scan - LARGE_SKIP_SIZE > self.model.min_scan:
                self.viewer.current_scan -= LARGE_SKIP_SIZE
            else:
                self.viewer.current_scan = self.model.min_scan

        elif event.key == pygame.K_ESCAPE:
            self.viewer.running = False

        elif event.key == pygame.K_SPACE:
            self.viewer.paused = not self.viewer.paused

    
        elif event.key == pygame.K_0:
            self.model.object_matching()

        elif event.key == pygame.K_9:
            self.model.clear_selected()

        elif event.key == pygame.K_i:
            for intersection in self.model.intersections:
                for atm in intersection.atms:
                    if atm.selected:
                        atm.atm_lat += 0.000001
                        print(atm.atm_lat)
        elif event.key == pygame.K_j:
            for intersection in self.model.intersections:
                for atm in intersection.atms:
                    if atm.selected:
                        atm.atm_long -= 0.000001
                        print(atm.atm_long)
        elif event.key == pygame.K_k:
            for intersection in self.model.intersections:
                for atm in intersection.atms:
                    if atm.selected:
                        atm.atm_lat -= 0.000001
                        print(atm.atm_lat)
        elif event.key == pygame.K_l:
            for intersection in self.model.intersections:
                for atm in intersection.atms:
                    if atm.selected:
                        atm.atm_long += 0.000001
                        print(atm.atm_long)

        elif event.key == pygame.K_t:
            for intersection in self.model.intersections:
                for atm in intersection.atms:
                    if atm.selected:
                        atm.atm_azi_angle += 1
                        print(atm.atm_azi_angle)

        elif event.key == pygame.K_y:
            for intersection in self.model.intersections:
                for atm in intersection.atms:
                    if atm.selected:
                        atm.atm_azi_angle -= 1
                        print(atm.atm_azi_angle)
        
        elif event.key == pygame.K_8:
            for intersection in self.model.intersections:
                for atm in intersection.atms:
                    if atm.selected:
                        print(f'file name     : {atm.logging_data_path}')
                        print(f'ip            : {atm.ip}')
                        print(f'atm_lat       : {atm.atm_lat}')
                        print(f'atm_long      : {atm.atm_long}')
                        print(f'atm_azi_angle : {atm.atm_azi_angle}')

        elif event.key == pygame.K_F2:
            self.model.view_mode[0] = 1
            
            self.model.landmark[0] = self.model.config['esterno']['intersection_center_gps'][0]
            self.model.landmark[1] = self.model.config['esterno']['intersection_center_gps'][1]
            self.model.landmark[2] = self.model.config['esterno']['intersection_map_zoom']
            self.model.grid_model.parsing_map()
        elif event.key == pygame.K_F1:
            self.model.view_mode[0] = 0
            
            self.model.landmark[0] = self.model.config['info']['center_gps'][0]
            self.model.landmark[1] = self.model.config['info']['center_gps'][1]
            self.model.landmark[2] = self.model.config['info']['map_zoom']
            self.model.grid_model.parsing_map()

        elif event.key == pygame.K_F3:
            self.model.view_mode[0] = 2
            
            self.model.landmark[0] = self.model.config['interno']['intersection_center_gps'][0]
            self.model.landmark[1] = self.model.config['interno']['intersection_center_gps'][1]
            self.model.landmark[2] = self.model.config['interno']['intersection_map_zoom']
            self.model.grid_model.parsing_map()


    def handle_double_keydown(self,keys):
        if keys[pygame.K_DELETE] and keys[pygame.K_0]:
            self.model.intersections[0].atms[0].view = not self.model.intersections[0].atms[0].view
        # elif keys[pygame.K_d] and keys[pygame.K_1]:
        #     self.model.display_atm['1.0.0.21'] = not self.model.display_atm['1.0.0.21']
        elif keys[pygame.K_DELETE] and keys[pygame.K_2]:
            self.model.intersections[0].atms[1].view = not self.model.intersections[0].atms[1].view
        elif keys[pygame.K_DELETE] and keys[pygame.K_3]:
            self.model.intersections[0].atms[2].view = not self.model.intersections[0].atms[2].view
        elif keys[pygame.K_DELETE] and keys[pygame.K_4]:
            self.model.intersections[0].atms[3].view = not self.model.intersections[0].atms[3].view
        elif keys[pygame.K_DELETE] and keys[pygame.K_5]:
            self.model.intersections[0].atms[4].view = not self.model.intersections[0].atms[4].view


        # elif keys[pygame.K_d] and keys[pygame.K_6]:
        #     self.model.display_atm['1.0.0.10'] = not self.model.display_atm['1.0.0.10']
        # elif keys[pygame.K_d] and keys[pygame.K_7]:
        #     self.model.display_atm['1.0.0.11'] = not self.model.display_atm['1.0.0.11']
        elif keys[pygame.K_DELETE] and keys[pygame.K_8]:
            self.model.intersections[1].atms[0].view = not self.model.intersections[1].atms[0].view
        # elif keys[pygame.K_d] and keys[pygame.K_9]:
        #     self.model.display_atm['1.0.0.13'] = not self.model.display_atm['1.0.0.13']

    def handle_save(self):
        result = create_window()
        if result:
            config = load_yaml('config.yaml')
            print('successfully saved')
            for intersection in self.model.intersections:
                for atm in intersection.atms:
                    if atm.updated:
                        config['verona'][intersection.name]['radar_gps_' + atm.ip][0] = atm.atm_lat
                        config['verona'][intersection.name]['radar_gps_' + atm.ip][1] = atm.atm_long
                        config['verona'][intersection.name]['radar_azi_angle_' + atm.ip] = atm.atm_azi_angle

            save_yaml('config.yaml', config)
            self.viewer.running = False
        else:
            print("ㅠㅠ")

    def handle_mouse_left_click(self, mouse_pos):
        if self.model.vds_button_model.is_clicked(mouse_pos):
            selected_atms = []
            for intersection in self.model.intersections:
                for atm in intersection.atms:
                    if atm.selected:
                        selected_atms.append(atm)

            start_vds_view(self.model.config, selected_atms)
        if self.model.save_button_model.is_clicked(mouse_pos):
            self.handle_save()

            
        else:
            self.model.cam_bound_model.handle_image_click(mouse_pos)

    def handle_mouse_right_click(self, mouse_pos):
        self.model.select_object(mouse_pos)

    def update_config(self, width, length):
        self.model.window_resize(width, length)
        self.viewer.window_resize()

def load_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    return data

def save_yaml(file_path, data):
    with open(file_path, 'w') as file:
        yaml.dump(data, file, default_flow_style=False)
