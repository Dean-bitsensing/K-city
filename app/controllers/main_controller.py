import pygame
import os
import yaml
from .UI_windows import *
from .UI_windows2 import *

SKIP_SIZE = 1
BIG_SKIP_SIZE = 20
LARGE_SKIP_SIZE = 100

class MainController:
    def __init__(self, model, viewer):
        self.model = model
        self.viewer = viewer

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.viewer.running = False
            os._exit(0)
        elif event.type == pygame.VIDEORESIZE:
            self.update_config(event.w, event.h)
        elif event.type == pygame.KEYDOWN:
            self.handle_keydown(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.handle_mouse_left_click(event.pos)

    def handle_keydown(self, event):
        if event.key == pygame.K_LEFT:
            self.viewer.paused = True
            if self.viewer.current_scan - SKIP_SIZE > self.model.min_scan:
                self.viewer.current_scan -= SKIP_SIZE
            else:
                self.viewer.current_scan = self.model.min_scan

        elif event.key == pygame.K_RIGHT:
            self.viewer.paused = True
            if self.viewer.current_scan + SKIP_SIZE < self.model.max_scan:
                self.viewer.current_scan += SKIP_SIZE
            else:
                self.viewer.current_scan = self.model.max_scan

        elif event.key == pygame.K_SPACE:
            self.viewer.paused = not self.viewer.paused

        elif event.key == pygame.K_ESCAPE:
            self.viewer.running = False

    def handle_mouse_left_click(self, mouse_pos):
        if self.model.vds_button_model.is_clicked(mouse_pos):
            selected_atms = []
            for intersection in self.model.intersections:
                for atm in intersection.atms:
                    if atm.selected:
                        selected_atms.append(atm)
            start_vds_view(self.model.config, selected_atms)
        elif self.model.vds_node_button_model.is_clicked(mouse_pos):
            start_node_vds_view(self.model.config)

    def update_config(self, width, length):
        self.model.window_resize(width, length)
        self.viewer.window_resize()

def load_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    return data

def save_yaml(file_path, data):
    with open(file_path, 'w') as file:
        yaml.dump(data, file, default_flow_style=False)
