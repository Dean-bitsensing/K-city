# models/button_models.py

from .camera_display_model import CameraDisplayModel
from .colors import *

class CameraReturnButton(CameraDisplayModel):
    def __init__(self, width=1200, length=800):
        super().__init__(width, length)
        self.update()

    def update(self):
        super().update()
        self.button_width = self.width // 20
        self.button_length = self.button_width
        self.button_posx = self.WINDOW_WIDTH - self.button_width
        self.button_posy = self.length - self.button_length
        self.color = WHITE
        self.outline_color = BLACK

    def is_clicked(self, mouse_pos):
        return (
            self.button_posx <= mouse_pos[0] <= self.button_posx + self.button_width and
            self.button_posy <= mouse_pos[1] <= self.button_posy + self.button_length
        )

class CameraLeftButton(CameraDisplayModel):
    def __init__(self, width=1200, length=800):
        super().__init__(width, length)
        self.update(width, length)

    def update(self, width, length):
        super().update(width, length)
        self.button_posx = self.center_hor_line_start_pos[0]
        self.button_posy = self.center_hor_line_start_pos[1] - self.length // 8
        self.button_width = self.width // 30
        self.button_length = 2 * (self.length // 8)
        self.color = WHITE
        self.outline_color = BLACK

    def is_clicked(self, mouse_pos):
        return (
            self.button_posx <= mouse_pos[0] <= self.button_posx + self.button_width and
            self.button_posy <= mouse_pos[1] <= self.button_posy + self.button_length
        )

class CameraRightButton(CameraDisplayModel):
    def __init__(self, width=1200, length=800):
        super().__init__(width, length)
        self.update(width, length)

    def update(self, width, length):
        super().update(width, length)
        self.button_posx = self.center_hor_line_end_pos[0] - self.width // 30
        self.button_posy = self.center_hor_line_start_pos[1] - self.length // 8
        self.button_width = self.width // 30
        self.button_length = 2 * (self.length // 8)
        self.color = WHITE
        self.outline_color = BLACK

    def is_clicked(self, mouse_pos):
        return (
            self.button_posx <= mouse_pos[0] <= self.button_posx + self.button_width and
            self.button_posy <= mouse_pos[1] <= self.button_posy + self.button_length
        )
