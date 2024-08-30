import json
from pyproj import Transformer

class ScanData:
    def __init__(self, h5_dataset,current_scan):
        self.current_scan = current_scan
        self.scan_data = h5_dataset['SCAN_{:05d}'.format(current_scan)]

    def parsing_status(self):
        status_data = self.scan_data['Status'][:]
        self.status_json = json.loads(status_data.tobytes().decode('utf-8'))

    def parsing_gps_into_meter(self):
        self.longitude = self.status_json['gps']['longitude']
        self.latitiude = self.status_json['gps']['latitude']

        # WGS84 좌표계 (EPSG:4326)와 UTM Zone 32N 좌표계 (EPSG:32632)를 정의하는 변환기 생성
        transformer = Transformer.from_crs('epsg:4326', 'epsg:32632')

        # Porta Nuova 교차로 근처 두 GPS 좌표 (위도, 경도) 입력
        lat_landmark, lon_landmark = 45.4313821996343, 10.988091543683414  # 첫 번째 좌표 (예시)

        # 각 GPS 좌표를 UTM 좌표계로 변환
        utm_x1, utm_y1 = transformer.transform(lat_landmark, lon_landmark)
        utm_x2, utm_y2 = transformer.transform(self.latitiude, self.longitude)

        # 두 좌표 사이의 X, Y 차이 계산
        self.radar_posx = utm_x2 - utm_x1
        self.radar_posy = utm_y2 - utm_y1

        


         

