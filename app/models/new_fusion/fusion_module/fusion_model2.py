import numpy as np
from copy import deepcopy
from tqdm import tqdm
from dataclasses import asdict
from .fusion_data_classes import Obj, TObj
from .fusion_input_processing import *
from .fusion_output_processing import *

ASSOCIATE_DISTANCE_GATE = 10
ASSOCIATE_VELOCITY_GATE = 5

MERGE_DISTANCE_GATE = 10
MEREGE_VELOCITY_GATE = 5

MINMUM_MERGE_PROBOBILITY = 0.2

MAXIMUM_FUSION_RANGE = 400
GRID_SIZE = 10

MAXIMUM_GRID_MAP_SIZE = MAXIMUM_FUSION_RANGE // GRID_SIZE

class Fusion:
    def __init__(self):
        self.scan_wise_fusion_output = []  # can be iobj and kobj (flow: aobj -> tobj -> iobj -> tobj -> kobj)

        self.dt = 0.05
        self.system_matrix = np.array([[1, 0, self.dt, 0],
                                       [0, 1, 0, self.dt],
                                       [0, 0, 1, 0],
                                       [0, 0, 0, 1]])

        self.Q = np.array([[0.01, 0, 0, 0],
                           [0, 0.01, 0, 0],
                           [0, 0, 0.01, 0],
                           [0, 0, 0, 0.01]])

        self.R = np.array([[0.1, 0, 0, 0],
                           [0, 0.1, 0, 0],
                           [0, 0, 0.1, 0],
                           [0, 0, 0, 0.1]])
        
        self.grid_map = [[[]for _ in range(MAXIMUM_GRID_MAP_SIZE)] for _ in range(MAXIMUM_GRID_MAP_SIZE)]
        self.center_gird = (MAXIMUM_GRID_MAP_SIZE//2, MAXIMUM_GRID_MAP_SIZE//2)

        #including direction of x and y(urdl) and steady at last 
        self.dx = [-1,-1,-1,0,0,0,1,1,1]
        self.dy = [-1,0,1,-1,0,1,-1,0,1]
        
    def load_intersection_data(self, fusion_inputs):
        # deepcopy는 필요하지 않음, 수정하지 않고 값을 참조만 하기 때문에 얕은 복사 가능
        self.fusion_inputs = fusion_inputs  
        self.mode = 'kcity'
        for fusion_input in self.fusion_inputs.values():
            for objs in fusion_input:
                for obj in objs:
                    obj.associated = False
                    obj.deletion_age = 0
                    obj.associated_info = {}
                    obj.covariance = np.array([[16, 0, 0, 0],
                                              [0, 16, 0, 0],
                                              [0, 0, 4, 0],
                                              [0, 0, 0, 4]])
        self.fusion_outputs = []

    def load_data(self, fusion_inputs, mode):
        # deepcopy가 필요 없는 경우, 값을 변경할 필요가 없기 때문에 얕은 복사 가능
        self.fusion_inputs = fusion_inputs  
        self.mode = mode
        self.fusion_outputs = []

    def prediction(self):
        for tobj in self.scan_wise_fusion_output:
            if not tobj.info:
                continue
            X = np.array([[tobj.posx], [tobj.posy], [tobj.velx], [tobj.vely]])
            P = tobj.covariance  

            X_pred = np.dot(self.system_matrix, X)
            X_pred = X_pred.astype(float)
            P_pred = np.dot(np.dot(self.system_matrix, P), np.transpose(self.system_matrix)) + self.Q
            posx_pred, posy_pred = X_pred[0, 0], X_pred[1, 0]

            
            tobj.posx = posx_pred
            tobj.posy = posy_pred
            tobj.covariance = P_pred

    def association(self, scan_num):
        for tobj in self.scan_wise_fusion_output:
            if not tobj.info:
                continue
            new_associated_info = {}
            for info in tobj.associated_info.keys():
                associated_info_idx = tobj.associated_info[info]
                scan_obj = self.find_obj_with_id(self.fusion_inputs[info][scan_num], associated_info_idx)
                if not scan_obj:
                    continue
                if self.possible_to_associate(tobj, scan_obj):
                    new_associated_info[info] = associated_info_idx
                    scan_obj.associated= True
            # associated_info가 덮어쓰이기 때문에 deepcopy 불필요
            tobj.associated_info = new_associated_info

    def update(self, scan_num):
        for tobj in self.scan_wise_fusion_output:
            if not tobj.info:
                continue
            for info in tobj.associated_info.keys():
                associated_info_idx = tobj.associated_info[info]
                scan_obj = self.find_obj_with_id(self.fusion_inputs[info][scan_num], associated_info_idx)
                X_pred = np.array([[tobj.posx], [tobj.posy], [tobj.velx], [tobj.vely]])
                P_pred = tobj.covariance
                if not scan_obj:
                    print(scan_num)

                X_meas = np.array([[scan_obj.posx], [scan_obj.posy], [scan_obj.velx], [scan_obj.vely]])

                Kalman_gain = np.dot(P_pred, np.linalg.inv(P_pred + self.R))

                X_est = X_pred + np.dot(Kalman_gain, X_meas - X_pred)
                P_est = P_pred - np.dot(Kalman_gain, P_pred)

                tobj.posx, tobj.posy, tobj.velx, tobj.vely = X_est[0, 0], X_est[1, 0], X_est[2, 0], X_est[3, 0]
                tobj.covariance = P_est

    def management(self, scan_num):
        self.check_to_delete()
        self.delete_obj()
        self.generate_new_fusion_obj(scan_num)
        self.create_grid_map()
        self.merge_fusion_obj_by_grid()
        self.reset_fusion_obj_merge_flag()
        self.reset_grid_map()
        self.update_age()
        self.update_state_by_age()
        self.update_heading_angle_deg(scan_num)
        self.update_stationary()
        self.update_associated_ip(scan_num)

    def fusion(self, scan_num):
        self.prediction()
        self.association(scan_num)
        self.management(scan_num)
        self.update(scan_num)
        
        self.put_fusion_ouput_to_fusion_outputs()

    def put_fusion_ouput_to_fusion_outputs(self):

        self.fusion_outputs.append(deepcopy(self.scan_wise_fusion_output))
 

    ### for association and update
    def find_obj_with_id(self, objs, id):
        for obj in objs:
            if obj.id == id:
                return obj

    def possible_to_associate(self, tobj1, tobj2):
        position_in = abs(tobj1.posx - tobj2.posx) < ASSOCIATE_DISTANCE_GATE and abs(tobj1.posy - tobj2.posy) < ASSOCIATE_DISTANCE_GATE
        velocity_in = abs(tobj1.velx - tobj2.velx) < ASSOCIATE_VELOCITY_GATE and abs(tobj1.vely - tobj2.vely) < ASSOCIATE_VELOCITY_GATE
        return position_in and velocity_in

    def check_to_delete(self):
        for tobj in self.scan_wise_fusion_output:
            if not tobj.associated_info:
                tobj.deletion_age += 1

    def delete_obj(self):
        # associated_info가 없으면 빈 TObj() 객체를 넣고, 그렇지 않으면 기존 tobj 유지
        self.scan_wise_fusion_output = [tobj if tobj.deletion_age <= 20 else TObj() for tobj in self.scan_wise_fusion_output]


    def find_empty_space(self):
        for idx, tobj in enumerate(self.scan_wise_fusion_output):
            if not tobj.info:  # can be changed, ask min
                return idx
        return -1

    def generate_new_fusion_obj(self, scan_num):
        for ip_address in self.fusion_inputs.keys():
            scan_wise_fusion_input = self.fusion_inputs[ip_address][scan_num]
            for new_obj in scan_wise_fusion_input:
                if not new_obj.info:
                    continue
                if not new_obj.associated:
                    empty_index = self.find_empty_space()
                    new_tobj = TObj(**asdict(new_obj))
                    new_tobj.info = self.mode
                    new_tobj.alive_age = 0
                    new_tobj.update_state = 1
                    new_tobj.fusion_type = 1
                    new_tobj.associated_info[new_obj.info] = new_obj.id
                    if empty_index == -1:
                        new_tobj.id = len(self.scan_wise_fusion_output)
                        self.scan_wise_fusion_output.append(new_tobj)
                    else:
                        new_tobj.id = empty_index
                        self.scan_wise_fusion_output[empty_index] = new_tobj

    def create_grid_map(self):
        for tobj in self.scan_wise_fusion_output:
            if not tobj.associated_ip:
                continue
            posx = tobj.posx
            posy = tobj.posy
            id = tobj.id

            x_sign = 1
            y_sign = 1
            if posx < 0:
                x_sign = -1
            if posy < 0:
                y_sign = -1

            col = int(x_sign * (abs(posx)//GRID_SIZE) + self.center_gird[1])
            row = int(self.center_gird[0] - y_sign * (abs(posy)//GRID_SIZE))

            if 0 <= row < MAXIMUM_GRID_MAP_SIZE and 0 <= col < MAXIMUM_GRID_MAP_SIZE:
                tobj.grid_row, tobj.grid_col = row, col
                self.grid_map[row][col].append(id)

        

    def merge_fusion_obj_by_grid(self):
        merge_infos = []
        for tobj in self.scan_wise_fusion_output:
            id = tobj.id
            if tobj.merged:
                continue
            tobj.merged = True
            merge_info = [id]
            x , y = tobj.grid_row, tobj.grid_col
            for i in range(9):
                nx = x + self.dx[i]
                ny = y+ self.dy[i]
                if 0 <= nx < MAXIMUM_GRID_MAP_SIZE and 0 <= ny < MAXIMUM_GRID_MAP_SIZE:
                    for nid in self.grid_map[nx][ny]:
                        ntobj = self.scan_wise_fusion_output[nid]
                        if not ntobj.merged and self.possible_to_merge(tobj, ntobj):
                            ntobj.merged = True
                            merge_info.append(nid)
            merge_infos.append(merge_info)
        self.merge(merge_infos)

    def reset_fusion_obj_merge_flag(self):
        for tobj in self.scan_wise_fusion_output:
            if tobj.merged:
                tobj.merged = False

    def reset_grid_map(self):
        self.grid_map = [[[]for _ in range(MAXIMUM_GRID_MAP_SIZE)] for _ in range(MAXIMUM_GRID_MAP_SIZE)]



    def merge_fusion_obj(self):
        merge_infos = []
        merged = [False for _ in range(len(self.scan_wise_fusion_output))]
        for idx1, tobj1 in enumerate(self.scan_wise_fusion_output):
            if merged[idx1]:
                continue
            merged[idx1] = True
            merge_info = [idx1]
            for idx2, tobj2 in enumerate(self.scan_wise_fusion_output):
                if merged[idx2]:
                    continue
                if self.possible_to_merge(tobj1, tobj2):
                    merged[idx2] = True
                    merge_info.append(idx2)
            merge_infos.append(merge_info)
        self.merge(merge_infos)

    def possible_to_merge(self, tobj1, tobj2):
        possible_to_associate = not set(tobj1.associated_info.keys()) & set(tobj2.associated_info.keys())

        if possible_to_associate:
        
            distance = np.sqrt((tobj1.posx - tobj2.posx) ** 2 + (tobj1.posy - tobj2.posy) ** 2)
            velocity_diff = np.sqrt((tobj1.velx - tobj2.velx) ** 2 + (tobj1.vely - tobj2.vely) ** 2)

            if distance < MERGE_DISTANCE_GATE and velocity_diff < MEREGE_VELOCITY_GATE:
                position_in = 1 - distance/MERGE_DISTANCE_GATE
                velocity_in = 1 - velocity_diff/MEREGE_VELOCITY_GATE
                if position_in * velocity_in > MINMUM_MERGE_PROBOBILITY:
                    return True
            
        return False

    def merge(self, merge_infos):
        for merge_info in merge_infos:
            primary_obj = self.scan_wise_fusion_output[merge_info[0]]
            for merge_obj_idx in merge_info[1:]:
                merge_obj = self.scan_wise_fusion_output[merge_obj_idx]
                primary_obj.associated_info.update(merge_obj.associated_info)
                self.scan_wise_fusion_output[merge_obj_idx] = TObj()
    

    def update_fusion_type(self):
        for tobj in self.scan_wise_fusion_output:
            if len(tobj.associated_info) >= 2:
                tobj.fusion_type = 2

    def update_age(self):
        for tobj in self.scan_wise_fusion_output:
            if tobj.update_state > 0 :
                tobj.alive_age += 1

    def update_state_by_age(self):
        for tobj in self.scan_wise_fusion_output:
            if tobj.fusion_type == 2:
                if tobj.alive_age >= 3:
                    tobj.update_state = 2
            else:
                if tobj.alive_age >= 30:
                    tobj.update_state = 2


    def update_heading_angle_deg(self, scan_num):
        if self.mode != 'kcity':
            for tobj in self.scan_wise_fusion_output:
                if tobj.update_state >= 1:
                    heading_angle_deg_sum = 0
                    heading_angle_deg_num = len(tobj.associated_info)
                    if not heading_angle_deg_num:
                        continue
                    for ip_address in tobj.associated_info.keys():
                        target_obj_id = tobj.associated_info[ip_address]
                        scan_obj = self.find_obj_with_id(self.fusion_inputs[ip_address][scan_num], target_obj_id)
                        heading_angle_deg_sum += scan_obj.heading_angle_deg

                    tobj.heading_angle_deg = heading_angle_deg_sum/heading_angle_deg_num

    def update_stationary(self):
        for tobj in self.scan_wise_fusion_output:
            if abs(tobj.velx) <= 0.3 and abs(tobj.vely) <= 0.3:
                tobj.move_state = 2 #Stopped
            else:
                tobj.move_state = 1 # Moving

    def update_associated_ip(self,scan_num):
        for tobj in self.scan_wise_fusion_output:
            if tobj.update_state == 0 or not tobj.associated_info:
                continue
            associated_ip = next(iter(tobj.associated_info))
            associated_ip_idx = tobj.associated_info[associated_ip]
            scan_wise_fusion_input = self.fusion_inputs[associated_ip][scan_num]
            target_obj = self.find_obj_with_id(scan_wise_fusion_input,associated_ip_idx)
            tobj.associated_ip  = target_obj.associated_ip
            
    def update_fusion_type(self):
        for tobj in self.scan_wise_fusion_output:
            if len(tobj.associated_info)>=2:
                tobj.fusion_type = 2
            elif len(tobj.associated_info) == 1:
                tobj.fusion_type = 1 

def fusion(esterno, interno, verona, root_message, devices):
    

    # Verona Specific Input Processing
    esterno_fusion_inputs,interno_fusion_inputs, timestamps, ATM_info = input_processing(root_message,devices)

    # Esterno , Interno Load and Fusion

    esterno.load_data(esterno_fusion_inputs, 'esterno')
    interno.load_data(interno_fusion_inputs, 'interno')

    for scan_num in tqdm(range(len(root_message.data)), desc = "intersection fusion tracking"):
        esterno.fusion(scan_num)
        interno.fusion(scan_num)

    # Verona (Esterno + Intersno) Load and Fusion

    intersection_fusion_outputs = {'esterno': esterno.fusion_outputs,
                                    'interno': interno.fusion_outputs}

    verona.load_intersection_data(intersection_fusion_outputs)

    for scan_num in tqdm(range(len(root_message.data)), desc = "k-city fusion tracking"):
        verona.fusion(scan_num)
        
    # Output Processing
    fusion_result = output_processing(verona.fusion_outputs, timestamps, ATM_info)


    return verona.fusion_outputs

