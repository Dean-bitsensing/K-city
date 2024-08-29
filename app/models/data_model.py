import h5py

class RectangleModel:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def get_logging_data(self, path):
        logging_data = h5py.File(path)