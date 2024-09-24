# models/button_models.py
from .camera_display_model import CameraDisplayModel
from .window_model import WindowModel
from .colors import *

class CameraReturnButton(CameraDisplayModel):
    def __init__(self, width=1200, length=800):
        super().__init__(width, length)
        self.update(width, length)

    def update(self, width, length):
        super().update(width, length)
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


class VDSDataButton(WindowModel):
    def __init__(self, width=1200, length=800):
        super().__init__(width, length)
        self.update(width,length)

    def update(self, width, length):
        super().update(width, length)
        self.button_width = self.WINDOW_WIDTH//10
        self.button_length = self.WINDOW_LENGTH//10

        self.button_posx = self.WINDOW_WIDTH*4//5 - self.button_width//2
        self.button_posy = self.WINDOW_LENGTH*4//5

        self.color = WHITE
        self.text = "VDS DATA"
        self.text_color = BLACK
        self.outline_color = BLACK

    def is_clicked(self, mouse_pos):
        return (
            self.button_posx <= mouse_pos[0] <= self.button_posx + self.button_width and
            self.button_posy <= mouse_pos[1] <= self.button_posy + self.button_length
        )