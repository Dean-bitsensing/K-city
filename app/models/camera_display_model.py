# models/camera_display_model.py

import pygame
import io
from .window_model import WindowModel
from .colors import RED, WHITE, BLACK, YELLOW  # Ensure these are defined

class CameraDisplayModel(WindowModel):
    def __init__(self, width=1200, length=800):
        super().__init__(width, length)
        self.cam_data_list = []
        self.cam_ip_list = []
        self.cam_color = []
        self.current_page = 0
        self.cams_per_page = 4
        self.cam_bbox_mode = 1
        self.cam_ip_box_color = RED
        self.zoom_init()
        self.update()

    # Rest of the class methods remain the same, just replace `CamBoundModel` with `CameraDisplayModel` in inheritance and references.
