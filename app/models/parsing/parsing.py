import json

class ScanData:
    def __init__(self, h5_dataset,current_scan):
        self.current_scan = current_scan
        self.current_scan_data = h5_dataset['SCAN_{:05d}'.format(current_scan)]

    def parsing_status(self):
        status_data = self.current_scan_data['Status'][:]
        self.status_json = json.loads(status_data.tobytes().decode('utf-8'))

    def parsing_gps(self):
        self.longitude = self.status_json['gps']['longitude']
        self.latitiude = self.status_json['gps']['latitude']