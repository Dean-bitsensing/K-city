# models/info_window_model.py

from .window_model import WindowModel

class InfoWindowModel(WindowModel):
    def __init__(self, width=1200, length=800):
        super().__init__(width, length)
        self.color = (100, 100, 100)
        self.font_color = (200, 200, 200)
        self.update(width, length)

    def update(self, width, length):
        super().__init__(width, length)
        self.posx = self.DATA_INFO_X
        self.posy = self.DATA_INFO_Y
        self.width = self.DATA_INFO_WIDTH
        self.length = self.DATA_INFO_LENGTH


