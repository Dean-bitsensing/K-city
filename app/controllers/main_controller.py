import pygame
import config

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
        elif event.type == pygame.VIDEORESIZE:
            self.update_config(event.w, event.h)
        elif event.type == pygame.KEYDOWN:
            self.handle_keydown(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                self.handle_mouse_left_click(event.pos)
            elif event.button == 2: # middle mouse button
                pass
            elif event.button == 3: # right mouse button
                self.handle_mouse_right_click(event.pos)

    def handle_keydown(self, event):
        if event.key == pygame.K_LEFT:
            self.viewer.paused = True
            if self.viewer.current_scan- SKIP_SIZE > self.model.min_scan:
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
            if self.viewer.current_scan- BIG_SKIP_SIZE > self.model.min_scan:
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
            if self.viewer.current_scan- LARGE_SKIP_SIZE > self.model.min_scan:
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
            for atm in self.model.logging_data:
                if atm.selected:
                    atm.atm_lat += 0.000001
                    print(atm.atm_lat)
        elif event.key == pygame.K_j:
            for atm in self.model.logging_data:
                if atm.selected:
                    atm.atm_long -= 0.000001
                    print(atm.atm_long)
        elif event.key == pygame.K_k:
            for atm in self.model.logging_data:
                if atm.selected:
                    atm.atm_lat -= 0.000001
                    print(atm.atm_lat)
        elif event.key == pygame.K_l:
            for atm in self.model.logging_data:
                if atm.selected:
                    atm.atm_long += 0.000001
                    print(atm.atm_long)
        elif event.key == pygame.K_t:
            for atm in self.model.logging_data:
                if atm.selected:
                    atm.atm_azi_angle += 1
                    print(atm.atm_azi_angle)
        elif event.key == pygame.K_y:
            for atm in self.model.logging_data:
                if atm.selected:
                    atm.atm_azi_angle -= 1
                    print(atm.atm_azi_angle)
        
        elif event.key == pygame.K_8:
            for atm in self.model.logging_data:
                if atm.selected:
                    print(f'file name     : {atm.file_name}')
                    print(f'ip            : {atm.ip}')
                    print(f'atm_lat       : {atm.atm_lat}')
                    print(f'atm_long      : {atm.atm_long}')
                    print(f'atm_azi_angle : {atm.atm_azi_angle}')

    def handle_mouse_left_click(self, mouse_pos):
        # Check if left or right buttons are clicked
        if self.model.cam_change_left_button_model.is_clicked(mouse_pos):
            if True in self.model.cam_bound_model.zoomed_in:
                self.model.cam_bound_model.previous_zoom()
            else:
                self.model.cam_bound_model.previous_page()
                self.model.cam_bound_model.zoom_init()
            
        elif self.model.cam_change_right_button_model.is_clicked(mouse_pos):
            if True in self.model.cam_bound_model.zoomed_in:
                self.model.cam_bound_model.next_zoom()
            else:
                self.model.cam_bound_model.next_page()
                self.model.cam_bound_model.zoom_init()
        
        elif self.model.cam_return_button_model.is_clicked(mouse_pos):
            self.model.cam_bound_model.zoom_init()
        
        

        else:
            self.model.cam_bound_model.handle_image_click(mouse_pos)

    def handle_mouse_right_click(self, mouse_pos):
        self.model.select_object(mouse_pos)




    def update_config(self, width, length):
        self.model.window_resize(width, length)
        self.viewer.window_resize()
        

        


