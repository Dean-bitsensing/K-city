import pygame

class MainViewer:
    def __init__(self, model, screen):
        self.model = model
        self.screen = screen

    def draw(self):
        pygame.draw.rect(
            self.screen, 
            (255, 0, 0),  # Red color
            pygame.Rect(self.model.x, self.model.y, self.model.width, self.model.height)
        )
