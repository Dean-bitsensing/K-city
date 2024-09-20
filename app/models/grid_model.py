# models/map_grid_model.py
import os
import sys
import requests
from io import BytesIO
from PIL import Image
from .window_model import WindowModel
from.global_variables import *
from .colors import *

class GridModel(WindowModel):
    def __init__(self, width=1200, length=800):
        super().__init__(width, length)
        self.color = (0, 0, 0)
        self.font_color = (0, 0, 0)
        self.font_size = 10
        self.center_point_color = RED
        self.BACKGROUND_IMAGE_PATH = 'app/resources/map_image.png'
        self.parsing_map()

        self.update()

    def update(self):
        self.start_posx = 0
        self.end_posx = self.GRID_WINDOW_WIDTH
        self.interval_x = int(self.GRID_X_SIZE)
        self.start_posy = 0
        self.end_posy = self.GRID_WINDOW_LENGTH
        self.interval_y = int(self.GRID_Y_SIZE)

    def parsing_map(self, api_key):
        if not os.path.exists(self.BACKGROUND_IMAGE_PATH):
            parsing_image_data_from_google(
                LAT_LANDMARK,
                LON_LANDMARK,
                self.GRID_WINDOW_WIDTH,
                self.GRID_WINDOW_LENGTH,
                api_key,
                zoom=18,
                maptype='satellite',
                image_path=self.BACKGROUND_IMAGE_PATH
            )



    