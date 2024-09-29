import pygame
import os
from app import *
import yaml
import threading


def load_config():
    # YAML 파일 로드
    with open('config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)

    return config

def run_pygame(config):

    model = MainModel(config['verona'])
    pygame.init()
    screen = pygame.display.set_mode((model.window_model.WINDOW_WIDTH, model.window_model.WINDOW_LENGTH), pygame.RESIZABLE)
    pygame.display.set_caption('K-City develop tool')

    # Model
    
    model.get_logging_data()    
    model.set_min_max_scan()
    
    # View
    viewer = MainViewer(model, screen)
    model.load_data(viewer.current_scan)
    # Controller
    event_controller = MainController(model, viewer)
 
    clock = pygame.time.Clock()

    viewer.current_scan = model.min_scan
    viewer.before_scan = viewer.current_scan

    while viewer.running:
        screen.fill((0, 0, 0))
        if viewer.current_scan != viewer.before_scan:
            viewer.before_scan = viewer.current_scan
            model.load_data(viewer.current_scan)
        viewer.draw()
        # pygame.display.flip() # 화면 업데이트
        pygame.display.update()

        clock.tick(config['fps']) 
        
        if not viewer.paused:
            viewer.current_scan += 1

        for event in pygame.event.get():           
            event_controller.handle_event(event)
        if viewer.current_scan > model.max_scan:
            viewer.paused = True
            viewer.current_scan = model.max_scan
        
    os._exit(0)

def main(config):
    pygame_thread = threading.Thread(target=run_pygame, args=(config, ))
    pygame_thread.start()

if __name__ == "__main__":
    # YAML 파일 로드
    config = load_config()
    main(config)
