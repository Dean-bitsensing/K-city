import h5py
import math
from tqdm import tqdm

def find_max_FoV_and_range(h5_file):
    logging_data = h5py.File(h5_file)

    max_FoV_left = 0
    max_FoV_right = 0 
    max_range = 0 

    for scan_num in tqdm(range(len(logging_data)-2), desc = 'calculating detection_zone' + str(h5_file)):
        current_scan_data = logging_data['SCAN_{:05d}'.format(scan_num)]
        for fobj in current_scan_data['Object'][:]:
            posx = fobj[5]
            posy = fobj[6]
            fusion_type = fobj[16]

            if fusion_type < 2:
                continue

            theta = math.atan(abs(posy)/posx)
            distance = math.sqrt(posx * posx + posy * posy)

            if posy>=0:
                if theta >= max_FoV_left:
                    max_FoV_left = theta
                    max_left_obj_scan = scan_num
                    max_left_obj_id = fobj[0]
            else:
                if theta >= max_FoV_right:
                    max_FoV_right = theta
                    max_right_obj_scan = scan_num
                    max_right_obj_id = fobj[0]                    

            if distance >= max_range:
                max_range = distance
                max_range_obj_id = fobj[0]
                max_range_obj_scan = scan_num


    return max_FoV_left, max_FoV_right, max_range
            