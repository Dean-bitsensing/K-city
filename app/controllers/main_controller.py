import pygame
import config

class MainController:
    def __init__(self, model, viewer):
        self.model = model
        self.viewer = viewer
    def handle_event(self, event):
        if event.type == pygame.VIDEORESIZE:
                self.update_config(event.w,event.h)
        elif event.type == pygame.KEYDOWN:
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
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if self.model.cam_change_left_button_model.is_clicked(mouse_pos):
                    self.model.cam_bound_model.next_page()
                    print("Left button clicked!")
                elif self.model.cam_change_right_button_model.is_clicked(mouse_pos):
                    self.model.cam_bound_model.previous_page()
                    print("Right button clicked!")

    def update_config(self, width, length):
        # print('resize : ', width, length)
        self.model.window_resize(width, length)
        self.viewer.window_resize()

        


