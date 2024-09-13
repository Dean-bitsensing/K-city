from dataclasses import dataclass
import h5py, json
import math

class Intersection:
    def __init__(self):
        self.atms = []
        self.intersection_id = 0
        self.intersection_name = 'none'

    def atm_insert(self, atm):
         self.atm_list.append(atm)

class Atm:
    def __init__(self):
        self.logging_data = None
        self.ip = '-1'
        self.current_scan_data = ScanData # ScanData
        self.selected_vobj_id = []
        self.selected_fobj_id = []

        self.atm_lat = 0
        self.atm_lat = 0
        self.atm_azi_angle = 0

    def initiate(self, logging_data_path):
        self.logging_data = h5py.File(logging_data_path)
        self.ip = logging_data_path.split('_')[-1][:-3]

        self.atm_lat = self.logging_data['GPS'][()][0]
        self.atm_lat = self.logging_data['GPS'][()][1]
        self.atm_azi_angle = self.logging_data['GPS'][()][2]
    


@dataclass
class RadarObj:
        idx : int


class VisionObj:
    def __init__(self):
        # 변환된 좌표들이 들어오는 공간이다.
        self.id = 0
        self.class_id = 0
        self.confidence = 0

        self.bbox_posx = 0
        self.bbox_posy = 0
        self.bbox_width = 0
        self.bbox_length = 0

        self.match_robj_id = 0
        self.status = 0
        self.move_state = 0
        self.alive_age = 0

        self.posx = 0 
        self.posy = 0

        self.velx = 0
        self.vely = 0

        self.width = 0
        self.length = 0

        self.lane = 0
        self.heading_angle_deg = 0

        self.trns_posx = 0 # Trans pos 따로 저장하기
        self.trns_posy = 0
        self.ul_pos = [0, 0]
        self.ur_pos = [0, 0]
        self.dl_pos = [0, 0]
        self.dr_pos = [0, 0]

        self.selected = False # 화면 표출 시 색 변환을 위한 변수

        self.before_posx = 0
        self.before_posy = 0



class FusionObj:
    def __init__(self):
        
        self.id = 0
        self.status = 0
        self.updata_state = 0
        self.move_state = 0
        self.alive_age = 0

        self.posx = 0 
        self.posy = 0

        self.ref_posx = 0 
        self.ref_posy = 0

        self.velx = 0
        self.vely = 0

        self.heading_angle_deg = 0
        self.power = 0
        self.width = 0
        self.length = 0
        self.class_id = 0
        self.fusion_type = 0
        self.fusion_age = 0
        self.match_vobj_id = 0

        # 변환된 좌표들이 들어오는 공간이다.

        self.trns_posx = 0
        self.trns_posy = 0
        self.ul_pos = [0, 0]
        self.ur_pos = [0, 0]
        self.dl_pos = [0, 0]
        self.dr_pos = [0, 0]

        self.selected = False # 화면 표출 시 색 변환을 위한 변수

        self.before_posx = 0
        self.before_posy = 0

class ScanData:
    def __init__(self, logging_data, current_scan):
        self.current_scan = current_scan
        
        self.logging_data = logging_data
        self.current_scan_data = logging_data['SCAN_{:05d}'.format(current_scan)]

        self.intersection_number = 1
        self.color = None
        

    def parsing_status(self):
        status_data = self.current_scan_data['Status'][:]
        self.status_json = json.loads(status_data.tobytes().decode('utf-8'))


    def parsing_gps_into_meter(self, center_x, center_y):
        def latlng_to_pixel(lat, lng, center_lat, center_lng, zoom, map_size, window_size):
            
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
        

        self.latitiude = self.atm_data.atm_lat
        self.longitude = self.atm_data.atm_long

        
        # test
        ##
        radar_x, radar_y = latlng_to_pixel(self.latitiude, self.longitude, LAT_LANDMARK, LON_LANDMARK, 18, (640, 640), (center_x*2, center_y*2))
    

        self.radar_diff_x = radar_x - center_x
        self.radar_diff_y = radar_y - center_y 
        self.center_x = center_x
        self.center_y = center_y
        self.radar_posx = radar_x
        self.radar_posy = radar_y
        


    def parsing_image(self):
        self.image = self.current_scan_data['Image'][()]

    def parsing_fusion_object_data(self):
        self.fusion_object_data = []
        self.fusion_object_data_vel = []

        self.azi_theta = self.atm_data.atm_azi_angle

        azi_theta = self.azi_theta * math.pi / 180 #  북쪽기준으로 반시계 방향으로 얼마나 회전했는가

        theta = math.pi/2 - azi_theta

        transition_matrix = np.array([[math.cos(theta), - math.sin(theta), self.radar_diff_x],
                                      [math.sin(theta), math.cos(theta), self.radar_diff_y],
                                      [0,0,1]])
        
        transition_matrix2 = np.array([[1, 0, self.center_x],
                                      [0, 1, self.center_y],
                                      [0,0,1]])
        
        
        
        def tf(pos, transition_matrix, transition_matrix2):
            
            position = np.array([[pos[0]],[pos[1]],[1]])
            position = np.dot(transition_matrix,position)
            position = np.dot(transition_matrix2, position)
            pos[0] = position[0][0]
            pos[1] = position[1][0]

            return pos
        
        for fobj in self.current_scan_data['Object'][:]:
            new_fobj = FusionObj()

            new_fobj.id         = fobj[0]
            posx                = fobj[5]
            posy                = fobj[6]
            velx                = fobj[9]
            vely                = fobj[10]
            width               = fobj[13]
            length              = fobj[14]

            new_fobj.posx   = posx
            new_fobj.posy   = posy
            new_fobj.velx   = velx
            new_fobj.vely   = vely
            new_fobj.width  = width
            new_fobj.length = length


            posx = -posx
            velx = -velx
            

            ul_pos = [int(posx - length/2), int(posy - width/2)]
            ur_pos = [int(posx - length/2), int(posy + width/2)]
            dl_pos = [int(posx + length/2), int(posy - width/2)]
            dr_pos = [int(posx + length/2), int(posy + width/2)]

            
            
            posx = meters_to_pixels(posx, LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            posy = meters_to_pixels(posy, LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            
            ul_pos[0] = meters_to_pixels(ul_pos[0], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            ul_pos[1] = meters_to_pixels(ul_pos[1], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))

            ur_pos[0] = meters_to_pixels(ur_pos[0], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            ur_pos[1] = meters_to_pixels(ur_pos[1], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            dl_pos[0] = meters_to_pixels(dl_pos[0], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            dl_pos[1] = meters_to_pixels(dl_pos[1], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            dr_pos[0] = meters_to_pixels(dr_pos[0], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            dr_pos[1] = meters_to_pixels(dr_pos[1], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))

            ul_pos = tf(ul_pos, transition_matrix, transition_matrix2)
            ur_pos = tf(ur_pos, transition_matrix, transition_matrix2)
            dl_pos = tf(dl_pos, transition_matrix, transition_matrix2)
            dr_pos = tf(dr_pos, transition_matrix, transition_matrix2)

            
            position = np.array([[posx],[posy],[1]])
            position = np.dot(transition_matrix,position)
            position = np.dot(transition_matrix2, position)
            posx = position[0][0]
            posy = position[1][0]

            new_fobj.trns_posx = posx
            new_fobj.trns_posy = posy
            

            new_fobj.ul_pos = ul_pos
            new_fobj.ur_pos = ur_pos
            new_fobj.dl_pos = dl_pos
            new_fobj.dr_pos = dr_pos

            self.fusion_object_data.append(new_fobj)


    def parsing_vision_object_data(self):
        self.vision_object_data = []
        self.vision_object_data_vel = []

        self.azi_theta = self.atm_data.atm_azi_angle

        azi_theta = self.azi_theta * math.pi / 180 #  북쪽기준으로 반시계 방향으로 얼마나 회전했는가

        theta = math.pi/2 - azi_theta

        transition_matrix = np.array([[math.cos(theta), - math.sin(theta), self.radar_diff_x],
                                      [math.sin(theta), math.cos(theta), self.radar_diff_y],
                                      [0,0,1]])
        
        transition_matrix2 = np.array([[1, 0, self.center_x],
                                      [0, 1, self.center_y],
                                      [0,0,1]])
        
        
        
        def tf(pos, transition_matrix, transition_matrix2):
            
            position = np.array([[pos[0]],[pos[1]],[1]])
            position = np.dot(transition_matrix,position)
            position = np.dot(transition_matrix2, position)
            pos[0] = position[0][0]
            pos[1] = position[1][0]

            return pos
        
        for vobj in self.current_scan_data['Vision_object'][:]:
            new_vobj = VisionObj()

            new_vobj.id          = vobj[0]
            new_vobj.bbox_posx   = vobj[3]
            new_vobj.bbox_posy   = vobj[4]
            new_vobj.bbox_width  = vobj[5]
            new_vobj.bbox_length = vobj[6]

            posx = vobj[11]
            posy = vobj[12]
            posx = -posx

            new_vobj.before_posx = posx
            new_vobj.before_posy = posy

            width = vobj[15]
            length = vobj[16]

            ul_pos = [int(posx - length/2), int(posy - width/2)]
            ur_pos = [int(posx - length/2), int(posy + width/2)]
            dl_pos = [int(posx + length/2), int(posy - width/2)]
            dr_pos = [int(posx + length/2), int(posy + width/2)]

            velx = vobj[13]
            vely = vobj[14]
            velx = -velx
            
            posx = meters_to_pixels(posx, LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            posy = meters_to_pixels(posy, LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            
            ul_pos[0] = meters_to_pixels(ul_pos[0], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            ul_pos[1] = meters_to_pixels(ul_pos[1], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))

            ur_pos[0] = meters_to_pixels(ur_pos[0], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            ur_pos[1] = meters_to_pixels(ur_pos[1], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            dl_pos[0] = meters_to_pixels(dl_pos[0], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            dl_pos[1] = meters_to_pixels(dl_pos[1], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            dr_pos[0] = meters_to_pixels(dr_pos[0], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            dr_pos[1] = meters_to_pixels(dr_pos[1], LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))

            ul_pos = tf(ul_pos, transition_matrix, transition_matrix2)
            ur_pos = tf(ur_pos, transition_matrix, transition_matrix2)
            dl_pos = tf(dl_pos, transition_matrix, transition_matrix2)
            dr_pos = tf(dr_pos, transition_matrix, transition_matrix2)


            velx = meters_to_pixels(velx, LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            vely = meters_to_pixels(vely, LAT_LANDMARK, 18, (640, 640), (self.center_x*2, self.center_y*2))
            
            position = np.array([[posx],[posy],[1]])
            position = np.dot(transition_matrix,position)
            position = np.dot(transition_matrix2, position)
            posx = position[0][0]
            posy = position[1][0]

            velocity = np.array([[velx],[vely],[1]])
            velocity = np.dot(transition_matrix,velocity)
            velocity = np.dot(transition_matrix2, velocity)
            velx = velocity[0][0]
            vely = velocity[1][0]

            new_vobj.posx = posx
            new_vobj.posy = posy
            new_vobj.width = vobj[15] # TODO 수정해야함
            new_vobj.length = vobj[16]
            new_vobj.velx = velx - self.radar_posx
            new_vobj.vely = vely - self.radar_posy

            new_vobj.ul_pos = ul_pos
            new_vobj.ur_pos = ur_pos
            new_vobj.dl_pos = dl_pos
            new_vobj.dr_pos = dr_pos

            self.vision_object_data.append(new_vobj)