import pygame
from app import *
import config

def main():
    pygame.init()
    screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_LENGTH), pygame.RESIZABLE)
    pygame.display.set_caption('K-City develop tool')

    # Model
    rect_model = MainModel(50, 50, 60, 60)

    # View
    viewer = MainViewer(rect_model, screen)

    # Controller
    event_controller = MainController(rect_model, viewer)

    clock = pygame.time.Clock()

    scandata = 0
    while viewer.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                viewer.running = False
            else:
                event_controller.handle_event(event)
        screen.fill((0, 0, 0))
        viewer.draw(scandata)
        pygame.display.flip() # 화면 업데이트

        clock.tick(config.FPS)  # Limit frame rate to 60 FPS

    pygame.quit()

if __name__ == "__main__":
    main()
