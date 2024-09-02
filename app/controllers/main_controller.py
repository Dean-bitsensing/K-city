import pygame
import config

class MainController:
    def __init__(self, model, viewer):
        self.model = model
        self.viewer = viewer

    def handle_event(self, event):
        if event.type == pygame.VIDEORESIZE:
            self.update_config(event.w, event.h)
        elif event.type == pygame.KEYDOWN:
            self.handle_keydown(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                self.handle_mouse_click(event.pos)

    def handle_keydown(self, event):
        if event.key == pygame.K_LEFT:
            self.model.move(-5, 0)
        elif event.key == pygame.K_RIGHT:
            self.model.move(5, 0)
        elif event.key == pygame.K_UP:
            self.model.move(0, -5)
        elif event.key == pygame.K_DOWN:
            self.model.move(0, 5)
        elif event.key == pygame.K_ESCAPE:
            self.viewer.running = False

    def handle_mouse_click(self, mouse_pos):
        # Check if left or right buttons are clicked
        if self.model.cam_change_left_button_model.is_clicked(mouse_pos):
            self.model.cam_bound_model.previous_page()
            self.model.cam_bound_model.zoomed_in = [False] * len(self.model.cam_bound_model.cam_data_list)
            print("Left button clicked!")
        elif self.model.cam_change_right_button_model.is_clicked(mouse_pos):
            self.model.cam_bound_model.next_page()
            self.model.cam_bound_model.zoomed_in = [False] * len(self.model.cam_bound_model.cam_data_list)
            print("Right button clicked!")
        else:
            self.model.cam_bound_model.handle_image_click(mouse_pos)

    def update_config(self, width, length):
        self.model.window_resize(width, length)
        self.viewer.window_resize()
        self.viewer.window_resize()

        


