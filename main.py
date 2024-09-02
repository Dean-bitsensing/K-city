import pygame
from app import *
from config import *

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_LENGTH), pygame.RESIZABLE)
    pygame.display.set_caption('K-City develop tool')

    # Model
    rect_model = MainModel(50, 50, 720, 720)
    rect_model.get_logging_data(FILE_PATH)
    rect_model.set_min_max_scan()

    # View
    viewer = MainViewer(rect_model, screen)

    # Controller
    event_controller = MainController(rect_model, viewer)

    clock = pygame.time.Clock()

    current_scan = rect_model.min_scan

    while viewer.running:
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                viewer.running = False
            else:
                event_controller.handle_event(event)

        screen.fill((0, 0, 0))
        rect_model.parsing(current_scan)
        viewer.draw()
        mouse_pos = pygame.mouse.get_pos()
    
    # 마우스 위치 출력
        print(f"Mouse position: {mouse_pos}")
        pygame.display.flip() # 화면 업데이트

        clock.tick(FPS)  # Limit frame rate to 60 FPS

        current_scan += 1

        if current_scan > rect_model.max_scan:
            break
    pygame.quit()

if __name__ == "__main__":
    main()
