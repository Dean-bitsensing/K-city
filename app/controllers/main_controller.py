import pygame
import yaml
from .UI_windows import *

SKIP_SIZE = 1
BIG_SKIP_SIZE = 20
LARGE_SKIP_SIZE = 100

class MainController:
    def __init__(self, model, viewer):
        self.model = model
        self.viewer = viewer

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.close_all_tk_windows()
            self.viewer.running = False
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

        elif event.key == pygame.K_s:
            self.handle_save()

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
        result = run_save_view()
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
        if self.model.vds_data_model.is_clicked(mouse_pos):
            configs = []
            selected_atms = []
            for intersection in self.model.intersections:
                for atm in intersection.atms:
                    if atm.selected:
                        configs.append(self.model.config[intersection.name])
                        selected_atms.append(atm)

            start_vds_view_thread(configs, selected_atms)
        else:
            self.model.cam_bound_model.handle_image_click(mouse_pos)

    def handle_mouse_right_click(self, mouse_pos):
        self.model.select_object(mouse_pos)

    def update_config(self, width, length):
        self.model.window_resize(width, length)
        self.viewer.window_resize()

    def close_all_tk_windows(self):
        """모든 Tk 창을 닫습니다."""
        for window in self.tk_windows_list:
            if window.winfo_exists():  # 창이 아직 존재하는 경우에만
                window.quit()  # 메인 루프 종료
                window.destroy()  # 창 제거
        self.tk_windows_list.clear()

def load_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    return data

def save_yaml(file_path, data):
    with open(file_path, 'w') as file:
        yaml.dump(data, file, default_flow_style=False)
