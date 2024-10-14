import os
import h5py
import math
import numpy as np
from copy import deepcopy
from tqdm import tqdm
from dataclasses import asdict
from .fusion_data_classes import Obj, TObj
from .fusion_input_processing import *

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

    def load_intersection_data(self, fusion_inputs):
        # deepcopy는 필요하지 않음, 수정하지 않고 값을 참조만 하기 때문에 얕은 복사 가능
        self.fusion_inputs = fusion_inputs  
        self.mode = 'kcity'
        for fusion_input in self.fusion_inputs.values():
            for objs in fusion_input:
                for obj in objs:
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
            P = tobj.covariance  # covariance는 새로 할당되므로 deepcopy 필요 없음

            X_pred = np.dot(self.system_matrix, X)
            X_pred = X_pred.astype(float)
            P_pred = np.dot(np.dot(self.system_matrix, P), np.transpose(self.system_matrix)) + self.Q
            posx_pred, posy_pred = X_pred[0, 0], X_pred[1, 0]

            # posx, posy, covariance는 각각 새로운 값을 할당하므로 deepcopy 필요 없음
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

                # posx, posy, velx, vely, covariance는 새로 계산된 값으로 덮어쓰기 때문에 deepcopy 필요 없음
                tobj.posx, tobj.posy, tobj.velx, tobj.vely = X_est[0, 0], X_est[1, 0], X_est[2, 0], X_est[3, 0]
                tobj.covariance = P_est

    def management(self, scan_num):
        self.delete_obj()
        self.generate_new_fusion_obj(scan_num)
        self.merge_fusion_obj()

    def fusion(self, scan_num):
        self.prediction()
        self.association(scan_num)
        self.management(scan_num)
        self.update(scan_num)
        
        self.put_fusion_ouput_to_fusion_outputs()

    def put_fusion_ouput_to_fusion_outputs(self):
        # scan_wise_fusion_output이 저장될 때 원본이 수정되면 안 되므로 deepcopy 필요
        self.fusion_outputs.append(deepcopy(self.scan_wise_fusion_output))

    ### for association and update
    def find_obj_with_id(self, objs, id):
        for obj in objs:
            if obj.id == id:
                # 원본 데이터가 수정되지 않고, 참조만 하기 때문에 deepcopy 불필요
                return obj

    def possible_to_associate(self, tobj1, tobj2):
        position_in = abs(tobj1.posx - tobj2.posx) < 20 and abs(tobj1.posy - tobj2.posy) < 20
        velocity_in = abs(tobj1.velx - tobj2.velx) < 20 and abs(tobj1.vely - tobj2.vely) < 20
        return position_in and velocity_in

    def delete_obj(self):
        # associated_info가 없으면 빈 TObj() 객체를 넣고, 그렇지 않으면 기존 tobj 유지
        self.scan_wise_fusion_output = [tobj if tobj.associated_info else TObj() for tobj in self.scan_wise_fusion_output]


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
                    new_tobj.associated_info[new_obj.info] = new_obj.id
                    if empty_index == -1:
                        new_tobj.id = len(self.scan_wise_fusion_output)
                        self.scan_wise_fusion_output.append(new_tobj)
                    else:
                        new_tobj.id = empty_index
                        self.scan_wise_fusion_output[empty_index] = new_tobj

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
        distance = np.sqrt((tobj1.posx - tobj2.posx) ** 2 + (tobj1.posy - tobj2.posy) ** 2)
        velocity_diff = np.sqrt((tobj1.velx - tobj2.velx) ** 2 + (tobj1.vely - tobj2.vely) ** 2)
        position_in = distance < 10
        velocity_in = velocity_diff < 10
        possible_to_associate = not set(tobj1.associated_info.keys()) & set(tobj2.associated_info.keys())
        return position_in and velocity_in and possible_to_associate

    def merge(self, merge_infos):
        for merge_info in merge_infos:
            primary_obj = self.scan_wise_fusion_output[merge_info[0]]
            for merge_obj_idx in merge_info[1:]:
                merge_obj = self.scan_wise_fusion_output[merge_obj_idx]
                primary_obj.associated_info.update(merge_obj.associated_info)
                # primary_obj.posx = (primary_obj.posx + merge_obj.posx) / 2
                # primary_obj.posy = (primary_obj.posy + merge_obj.posy) / 2
                # primary_obj.velx = (primary_obj.velx + merge_obj.velx) / 2
                # primary_obj.vely = (primary_obj.vely + merge_obj.vely) / 2
                self.scan_wise_fusion_output[merge_obj_idx] = TObj()
    
    # def update_status_by_age(self):
    #     for tobj in self.scan_wise_fusion_output:


def output_processing(fusion_outputs):
    pass

# 예시: esterno와 interno radars
esterno_radars = { 
    '1.0.0.20' : Radar([45.43072430000016, 10.98769880000001], 9),
    '1.0.0.21' : Radar([45.430227500000164, 10.987823700000048], 18),
    '1.0.0.22' : Radar([45.430359, 10.9882485], 67),
    '1.0.0.23' : Radar([45.430319, 10.9883385], 0),
    '1.0.0.24' : Radar([45.43077730000001, 10.987771800000045], 246.71),
    '1.0.0.25' : Radar([45.4301545, 10.9879317], -27.1)
}

interno_radars = { 
    '1.0.0.10' : Radar([45.4317387, 10.9882638], 0),
    '1.0.0.11' : Radar([45.4316862, 10.9886965], 0),
    '1.0.0.12' : Radar([45.4316862, 10.9886965], 157.36),
    '1.0.0.13' : Radar([45.4317387, 10.9882638], 0)
}

landmark_position = [45.4310364, 10.988078]

def fusion_main(config):
    esterno = Fusion()
    interno = Fusion()
    verona = Fusion()

    folder_path, esterno_radars, interno_radars, landmark_position, max_scan_num = load_config(config)

    while True:
        esterno_fusion_inputs = input_processing(folder_path + '/esterno', esterno_radars, landmark_position, max_scan_num)
        interno_fusion_inputs = input_processing(folder_path + '/interno', interno_radars, landmark_position, max_scan_num)

        esterno.load_data(esterno_fusion_inputs, 'esterno')
        interno.load_data(interno_fusion_inputs, 'interno')

        for scan_num in tqdm(range(max_scan_num), desc = "intersection fusion tracking"):
            esterno.fusion(scan_num)
        #     interno.fusion(scan_num)

        # intersection_fusion_outputs = {'esterno': esterno.fusion_outputs,
        #                                'interno': interno.fusion_outputs}

        # verona.load_intersection_data(intersection_fusion_outputs)

        # for scan_num in tqdm(range(max_scan_num), desc = "k-city fusion tracking"):
        #     verona.fusion(scan_num)
        
        break

    return esterno.fusion_outputs
