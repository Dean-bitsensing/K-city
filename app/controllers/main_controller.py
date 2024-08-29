import pygame

class KeyboardController:
    def __init__(self, model):
        self.model = model

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.model.move(-5, 0)
            elif event.key == pygame.K_RIGHT:
                self.model.move(5, 0)
            elif event.key == pygame.K_UP:
                self.model.move(0, -5)
            elif event.key == pygame.K_DOWN:
                self.model.move(0, 5)