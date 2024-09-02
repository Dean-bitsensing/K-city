import pygame
from app import *
from config import *


LOGGING_DATA_PATH = r'Logging_datas'

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_LENGTH), pygame.RESIZABLE)
    pygame.display.set_caption('K-City develop tool')

    # Model
    model = MainModel()
    model.get_h5_datas(LOGGING_DATA_PATH)
    # model.get_logging_data(FILE_PATH)
    model.set_min_max_scan()
    
    
    # View
    viewer = MainViewer(model, screen)
    model.parsing(viewer.current_scan)
    # Controller
    event_controller = MainController(model, viewer)
 
    clock = pygame.time.Clock()

    
    viewer.current_scan = model.min_scan

    while viewer.running:
        

        screen.fill((0, 0, 0))
        model.parsing(viewer.current_scan)
        viewer.draw()
        pygame.display.flip() # 화면 업데이트

        clock.tick(FPS)  # Limit frame rate to 60 FPS


        if not viewer.paused:
            viewer.current_scan += 1


        for event in pygame.event.get():          
            event_controller.handle_event(event)

        if viewer.current_scan > model.max_scan:
            viewer.paused = True
            viewer.current_scan = model.max_scan
        
    pygame.quit()

if __name__ == "__main__":
    main()
