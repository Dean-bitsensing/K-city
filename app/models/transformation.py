import math

class Transformation:
    def __init__(self):
        pass

    def latlng_to_pixel(lat, lng, center_lat, center_lng, zoom, map_size, window_size):
        # 지도의 중심 lat, long을 알면 상대적인 위치의 pixel 좌표를 구해주는 함수
        TILE_SIZE = 256
        scale = 2 ** zoom  # 줌 레벨에 따른 스케일

        # 경도를 픽셀로 변환
        def lng_to_pixel_x(lng):
            return (lng + 180) / 360 * scale * TILE_SIZE

        # 위도를 픽셀로 변환 (머케이터 도법)
        def lat_to_pixel_y(lat):
            siny = math.sin(lat * math.pi / 180)
            y = math.log((1 + siny) / (1 - siny))
            return (1 - y / (2 * math.pi)) * scale * TILE_SIZE / 2

        # 지도 중심 좌표의 픽셀 좌표 구하기
        center_x = lng_to_pixel_x(center_lng)
        center_y = lat_to_pixel_y(center_lat)

        # 주어진 좌표의 픽셀 좌표 구하기
        pixel_x = lng_to_pixel_x(lng) - center_x + map_size[0] // 2
        pixel_y = lat_to_pixel_y(lat) - center_y + map_size[1] // 2

        # 창 크기 대비 지도 크기에 따른 비율로 스케일링
        scale_x = window_size[0] / map_size[0]
        scale_y = window_size[1] / map_size[1]

        # Pygame 창 상의 픽셀 좌표로 변환
        pixel_x_on_window = int(pixel_x * scale_x)
        pixel_y_on_window = int(pixel_y * scale_y)

        return pixel_x_on_window, pixel_y_on_window