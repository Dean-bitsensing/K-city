from dataclasses import dataclass


@dataclass
class RadarObj:
        idx : int

class VisionObj:
    def __init__(self):
        self.posx = 0 
        self.posy = 0
        self.width = 0
        self.length = 0

