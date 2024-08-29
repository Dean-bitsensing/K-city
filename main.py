import pygame
from app import *
import config

def main():
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    pygame.display.set_caption('MVC Pattern Example')

    # Model
    rect_model = RectangleModel(50, 50, 60, 60)

    # View
    rect_view = MainViewer(rect_model, screen)

    # Controller
    rect_controller = KeyboardController(rect_model)

    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                rect_controller.handle_event(event)

        screen.fill((0, 0, 0))  # Clear screen with black color
        rect_view.draw()
        pygame.display.flip()

        clock.tick(config.FPS)  # Limit frame rate to 60 FPS

    pygame.quit()

if __name__ == "__main__":
    main()
