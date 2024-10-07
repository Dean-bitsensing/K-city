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
        self.scan_wise_fusion_output = [] #can be iobj and kobj (flow: aobj -> tobj -> iobj -> tobj -> kobj)

        self.dt = 0.05
        self.system_matrix=np.array([[1,0,self.dt,0],
                            [0,1,0,self.dt],
                            [0,0,1,0],
                            [0,0,0,1]])
    
        self.Q=np.array([[0.01,0,0,0],
                [0,0.01,0,0],
                [0,0,0.01,0],
                [0,0,0,0.01]])
        
        self.R = np.array([[0.1,0,0,0],
               [0,0.1,0,0],
               [0,0,0.1,0],
               [0,0,0,0.1]])
        
    def load_data(self,fusion_inputs):
    
        self.fusion_inputs = fusion_inputs # list, Index is scan_num , fusion_input[scan_num] is dictinary whose item is list of Objs 
        self.fusion_outputs = []

    def prediction(self):
    
        for tobj in self.scan_wise_fusion_output:
            X = np.array([[tobj.posx], [tobj.posy], [tobj.velx], [tobj.vely]])
            P=tobj.covariance

            X_pred=np.dot(self.system_matrix,X)
            X_pred=X_pred.astype(float)
            P_pred=np.dot(np.dot(self.system_matrix,P),np.transpose(self.system_matrix))+self.Q
            posx_pred,posy_pred=X_pred[0,0],X_pred[1,0]

            tobj.posx = posx_pred
            tobj.posy = posy_pred
            tobj.covariance = P_pred

    
    def association(self, scan_num):
        
        for tobj in self.scan_wise_fusion_output:
            new_associated_info ={}
            for info in tobj.associated_info.keys():
                associated_info_idx = tobj.associated_info[info]
                # scan_obj = self.fusion_inputs[info][scan_num][associated_info_idx] # -> find by ID? 
                scan_obj = self.find_obj_with_id(self.fusion_inputs[info][scan_num], associated_info_idx)
                if not scan_obj:
                    continue
                if self.possible_to_associate(tobj, scan_obj):
                    new_associated_info[info] = associated_info_idx
                    scan_obj.associated_fusion_obj_idx = tobj.id
            tobj.associated_info = new_associated_info


    def update(self, scan_num):

        for tobj in self.scan_wise_fusion_output:
            for info in tobj.associated_info.keys():
                associated_info_idx = tobj.associated_info[info]
                # scan_obj = self.fusion_inputs[info][scan_num][associated_info_idx] # -> find by ID? 
                scan_obj = self.find_obj_with_id(self.fusion_inputs[info][scan_num], associated_info_idx)
                X_pred = np.array([[tobj.posx], [tobj.posy], [tobj.velx], [tobj.vely]])
                P_pred = tobj.covariance
                if not scan_obj:
                    print(scan_num)

                X_meas = np.array([[scan_obj.posx], [scan_obj.posy], [scan_obj.velx], [scan_obj.vely]])

                Kalman_gain=np.dot(P_pred,np.linalg.inv(P_pred+self.R))

                X_est=X_pred+np.dot(Kalman_gain,X_meas-X_pred)
                P_est=P_pred-np.dot(Kalman_gain,P_pred)

                tobj.posx, tobj.posy, tobj.velx, tobj.vely=X_est[0,0],X_est[1,0],X_est[2,0],X_est[3,0]
                tobj.covariance = P_est



    def management(self, scan_num):
        self.delete_obj()
        self.generate_new_fusion_obj(scan_num)
        self.merge_fusion_obj()



    def fusion(self, scan_num):
        self.scan_wise_fusion_output = []
        # self.prediction()
        # self.association(scan_num)
        # self.update(scan_num)
        self.management(scan_num)
        self.put_fusion_ouput_to_fusion_outputs()

    def put_fusion_ouput_to_fusion_outputs(self):
        self.fusion_outputs.append(self.scan_wise_fusion_output)
    

    ### for association and update
    def find_obj_with_id(self, objs, id):
        for obj in objs:
            if obj.id ==id:
                return obj

    def possible_to_associate(self, tobj1, tobj2):

        postion_in = abs(tobj1.posx - tobj2.posx) < 10 and abs(tobj1.posy - tobj2.posy) < 10
        velocity_in = abs(tobj1.velx - tobj2.velx) < 10 and abs(tobj1.vely - tobj2.vely) < 10

        return postion_in and velocity_in
    
    ### for management ###

    def delete_obj(self):
        empty_obj = TObj()
        for tobj in self.scan_wise_fusion_output:
            if not tobj.associated_info:
                tobj = deepcopy(empty_obj)

    def find_empty_space(self):
        for tobj in self.scan_wise_fusion_output:
            if tobj.status == 0: #can be changed ask min
                return self.scan_wise_fusion_output.index(tobj)
        return -1
    
    def generate_new_fusion_obj(self,scan_num):
        for ip_address in self.fusion_inputs.keys():
            scan_wise_fusion_input = self.fusion_inputs[ip_address][scan_num]
            for new_obj in scan_wise_fusion_input:
                if new_obj.associated_fusion_obj_idx == -1:
                    empty_index = self.find_empty_space()
                    new_tobj = TObj(**asdict(new_obj))
                    new_tobj.info = 'esterno'
                    new_tobj.associated_info[new_obj.info] = new_obj.id
                    if empty_index == -1:
                        new_tobj.id = len(self.scan_wise_fusion_output)
                        self.scan_wise_fusion_output.append(new_tobj)
                    else:
                        new_tobj.id =  empty_index
                        self.scan_wise_fusion_output[empty_index] = new_tobj

    def merge_fusion_obj(self):
        merge_infos = []
        merged = [False  for _ in range(len(self.scan_wise_fusion_output))] 
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

        postion_in = abs(tobj1.posx - tobj2.posx) < 5 and abs(tobj1.posy - tobj2.posy) < 5
        velocity_in = abs(tobj1.velx - tobj2.velx) < 5 and abs(tobj1.vely - tobj2.vely) < 5
        possible_to_associated= not set(tobj1.associated_info.keys()) & set(tobj2.associated_info.keys())

        return postion_in and velocity_in and possible_to_associated
    

    
    def merge(self,merge_infos):
        #TODO has to be changed
        for merge_info in merge_infos:
            empty_obj = TObj()
            for merge_obj_idx in merge_info[1:]:
                self.scan_wise_fusion_output[merge_info[0]].associated_info.update(self.scan_wise_fusion_output[merge_obj_idx].associated_info)
                self.scan_wise_fusion_output[merge_obj_idx] = empty_obj
                
             
                


def output_processing(fusion_outputs):
    pass




def fusion_main(folder_path):
    esterno = Fusion()
    interno = Fusion()
    verona = Fusion()

    while True:
        esterno_fusion_inputs = input_processing(folder_path + '/esterno')
        # interno_fusion_inputs = input_processing(folder_path) #a_obj 로 변환 필요
        esterno.load_data(esterno_fusion_inputs)
        # interno.load_data(interno_fusion_inputs)

        for scan_num in tqdm(range(200)): #h5 길이에 따라 가변적으로 
            esterno.fusion(scan_num)


            # interno.fusion(scan_num)


        # intersection_fusion_outputs = [esterno.fusion_outputs, interno.fusion_outputs] #i_obj

        # verona.load_data(intersection_fusion_outputs)

        # for scan_num in range(200):   
        #     verona.fusion(scan_num)

        # k_fusion_outputs = output_processing(verona.fusion_outputs) #k_obj

        break

    return esterno.fusion_outputs



    