import pygame
from app import *
from config import *
import yaml

def load_config():
    # YAML 파일 로드
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)

    return config

def run_pygame(config):
	model = MainModel()
    pygame.init()
    screen = pygame.display.set_mode((model.window_model.WINDOW_WIDTH, model.window_model.WINDOW_LENGTH), pygame.RESIZABLE)
    pygame.display.set_caption('K-City develop tool')

    # Model
    
    logging_datas = model.get_h5_datas(config)
    model.get_logging_data(logging_datas)
    model.set_min_max_scan()
    
    # View
    viewer = MainViewer(model, screen)
    model.parsing(viewer.current_scan)
    # Controller
    event_controller = MainController(model, viewer)
 
    clock = pygame.time.Clock()

    viewer.current_scan = model.min_scan
    viewer.before_scan = viewer.current_scan

    while viewer.running:
        screen.fill((0, 0, 0))
        if viewer.current_scan != viewer.before_scan:
            viewer.before_scan = viewer.current_scan
            model.parsing(viewer.current_scan)
        viewer.draw()
        pygame.display.flip() # 화면 업데이트
        # pygame.display.update()

        clock.tick(FPS) 
        
        if not viewer.paused:
            viewer.current_scan += 1

        for event in pygame.event.get():           
            event_controller.handle_event(event)
        if viewer.current_scan > model.max_scan:
            viewer.paused = True
            viewer.current_scan = model.max_scan
        
    pygame.quit()

def main(config):
    run_pygame(config)
    
if __name__ == "__main__":
    # YAML 파일 로드
    config = load_config()
    main(config)
