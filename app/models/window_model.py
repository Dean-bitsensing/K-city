from observable import Observable

class WindowModel(Observable):
    def __init__(self, width=1200, length=800):
        super().__init__()
        self.WINDOW_WIDTH = width
        self.WINDOW_LENGTH = length

        self.SCALED_RATE_X = 5
        self.SCALED_RATE_Y = 5

        self.GRID_X_SIZE =  8*self.SCALED_RATE_X
        self.GRID_Y_SIZE = 10*self.SCALED_RATE_Y

        self.SPLITED_SCALE_RATE = 0.75
        self.SPLITED_SCALE_RATE_X = self.SCALED_RATE_X*self.SPLITED_SCALE_RATE
        
        self.initialize_window_size()

    def initialize_window_size(self):
        self.GRID_WINDOW_WIDTH          = int(self.WINDOW_WIDTH*3/5)
        self.GRID_WINDOW_LENGTH         = int(self.WINDOW_LENGTH * 9 / 10)
        self.HALF_GRID_WINDOW_WIDTH     = int(self.GRID_WINDOW_WIDTH // 2)
        self.HALF_GRID_WINDOW_LENGTH    = int(self.GRID_WINDOW_LENGTH // 2)
        
        self.CAM_BOUND_X        = int(self.GRID_WINDOW_WIDTH)
        self.CAM_BOUND_Y        = 0
        self.CAM_BOUND_WIDTH    = int(self.WINDOW_WIDTH - self.GRID_WINDOW_WIDTH)
        self.CAM_BOUND_LENGTH   = int(self.CAM_BOUND_WIDTH * 576 / 1024)

        self.DATA_INFO_X        = int(self.GRID_WINDOW_WIDTH)
        self.DATA_INFO_Y        = self.CAM_BOUND_LENGTH
        self.DATA_INFO_WIDTH    = int(self.WINDOW_WIDTH - self.GRID_WINDOW_WIDTH)
        self.DATA_INFO_LENGTH   = int(self.DATA_INFO_WIDTH/2)

        self.notify_observers()  # Notify observers when sizes are updated

    def update(self, width, length):
        self.WINDOW_WIDTH = width
        self.WINDOW_LENGTH = length
        self.initialize_window_size()





# def parsing_map(self):
#         # self.BACKGROUND_IMAGE_PATH = 'app/resources/map_image.png'
#         if not os.path.exists(self.BACKGROUND_IMAGE_PATH):
#             parsing_image_data_from_google(LAT_LANDMARK, LON_LANDMARK, self.window_model.GRID_WINDOW_WIDTH, self.window_model.GRID_WINDOW_LENGTH,zoom = 18, maptype = 'satellite', image_path=self.BACKGROUND_IMAGE_PATH)   