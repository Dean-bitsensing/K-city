import pygame
import os
import yaml
import sys
import threading
import tkinter as tk
from tkinter import simpledialog
from app import MainController, MainModel, MainViewer

def load_config():
    # YAML 파일 로드
    with open('config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config

def write_max_scan_num_to_config(config, max_scan_num):
    
    # max_scan_num 값을 config에 추가 또는 업데이트
    config['verona']['info']['MAX_SCAN'] = max_scan_num
    
    # 수정된 config를 다시 파일에 쓰기
    with open('config.yaml', 'w') as file:
        yaml.dump(config, file)

def get_scan_num():
    root = tk.Tk()
    root.withdraw()  # Tkinter 기본 창 숨기기
    
    scannum = simpledialog.askinteger("Input", "Enter the scannum:", parent=root)
    
    if scannum is not None:
        # Scannum 입력이 정상적으로 이루어졌을 때 Pygame 실행
        config = load_config()
        write_max_scan_num_to_config(config, scannum)
    else:
        # 입력이 취소되었을 경우 프로그램 종료
        print("No input provided. Exiting...")
        sys.exit()

def run_pygame(config):
    model = MainModel(config['verona'])
    pygame.init()
    screen = pygame.display.set_mode((model.window_model.WINDOW_WIDTH, model.window_model.WINDOW_LENGTH), pygame.RESIZABLE)
    pygame.display.set_caption('K-City develop tool')

    
    # View
    viewer = MainViewer(model, screen)
    model.get_logging_data()
    model.set_min_max_scan()
    model.load_data(viewer.current_scan)

    # Controller
    event_controller = MainController(model, viewer)
 
    clock = pygame.time.Clock()
    viewer.current_scan = model.min_scan
    viewer.before_scan = viewer.current_scan

    print(model.max_scan)

    kcity_fusion_objs = model.fusion()

    while viewer.running:
        screen.fill((0, 0, 0))
        if viewer.current_scan != viewer.before_scan:
            viewer.before_scan = viewer.current_scan
            model.load_data(viewer.current_scan)
        viewer.draw()

        if viewer.fusion_only_mode:
            viewer.draw_fusion_obj(kcity_fusion_objs[viewer.current_scan])
        # pygame.display.flip() # 화면 업데이트                                                
        pygame.display.update()
        clock.tick(config['fps']) 

        if not viewer.paused:
            viewer.current_scan += 1

        for event in pygame.event.get():
            event_controller.handle_event(event)

        if viewer.current_scan >= model.max_scan:
            viewer.paused = True
            viewer.current_scan = model.max_scan-1
        if viewer.current_scan <= model.min_scan:
            viewer.paused = True
            viewer.current_scan = model.min_scan+1

    os._exit(0)



def main(config):
    pygame_thread = threading.Thread(target=run_pygame, args=(config,))
    pygame_thread.start()

if __name__ == "__main__":
    get_scan_num()
    config = load_config()
    main(config)
