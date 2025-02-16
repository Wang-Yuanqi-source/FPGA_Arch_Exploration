# -*- coding: utf-8 -*-

import os.path
import sys
import re
import random
import math
import copy
import datetime
import logging

from optparse import OptionParser
import multiprocessing
from collections import Counter

import Caller
import Regex
from Generate_two_stage import From_inf, generateTwoStageMux, readArch2, writeArch2, findSeg, verify_fanin_ok, compute_area

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
from xml.dom import minidom


class SeekerError(Exception):
    pass


class bendSegmentation():
    switch_type = ["U", "D"]

    def __init__(self, _Rmetal=None, _Cmetal=None, _freq=None, _len=None, _bend_list=None, _driver=None, _net_idx=None, _name=None, _driver_para=None):
        self.Rmetal = _Rmetal
        self.Cmetal = _Cmetal
        self.freq = _freq
        self.length = _len
        self.bend_list = _bend_list
        self.driver = _driver
        self.net_idx = _net_idx
        self.name = _name
        self.driver_para = _driver_para
        self.is_shortSeg = False if _len and _len > 6 else True
    
    def __eq__(self, seg):
        if self.Rmetal == seg.Rmetal and \
           self.Cmetal == seg.Cmetal and \
           self.freq == seg.freq and \
           self.length == seg.length and \
           "".join(self.bend_list) == "".join(seg.bend_list) and \
           self.driver == seg.driver :
           return True
        
        return False

    def show(self, logger=None):
        if logger == None:
            print("\t\tSegmentation_"+ str(self.net_idx) +": " + str(self.freq) + "-" + str(self.length) + "(" + " ".join(self.bend_list) + ")-" + \
                    "(" + self.name  + ")-" + self.driver + "_RC(" + self.Rmetal + "," + self.Cmetal + ")")
            print("\t\t\tDriver_parameter: ("+ self.driver_para[0] + "," + self.driver_para[1] + "," + self.driver_para[2] + ")")
        else:
            logger.info("\t\tSegmentation_"+ str(self.net_idx) +": " + str(self.freq) + "-" + str(self.length) + "(" + " ".join(self.bend_list) + ")-" + \
                            "(" + self.name  + ")-" + self.driver + "_RC(" + self.Rmetal + "," + self.Cmetal + ")")
            logger.info("\t\t\tDriver_parameter: ("+ self.driver_para[0] + "," + self.driver_para[1] + "," + self.driver_para[2] + ")")


def prettify(elem):
    """
        Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8').decode("utf-8")
    rough_string = re.sub(">\s*<", "><", rough_string)
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="\t", encoding="utf-8") 

def random_pick(itemList, probs):
    x = random.uniform(0,1)
    c_prob = 0.0
    for item, prob in zip(itemList, probs):
        c_prob += prob
        if x < c_prob: 
            break
    return item


def check_circle(bend_list):

    if "".join(bend_list) == "-" * len(bend_list):
        return False

    visited_points = [(0, 0), (1,0)]
    point = [1,0]
    dir_now = "r"

    for s in bend_list:
        if s == '-':
            if dir_now == "r":
                point[0] += 1
            elif dir_now == "l":
                point[0] -= 1
            elif dir_now == "u":
                point[1] += 1
            elif dir_now == "d":
                point[1] -= 1
        elif s == "U":
            if dir_now == "r":
                point[1] += 1
                dir_now = "u"
            elif dir_now == "u":
                point[0] -= 1
                dir_now = "l"
            elif dir_now == "l":
                point[1] -= 1
                dir_now = "d"
            elif dir_now == "d":
                point[0] += 1
                dir_now = "r"
        elif s == "D":
            if dir_now == "r":
                point[1] -= 1
                dir_now = "d"
            elif dir_now == "d":
                point[0] -= 1
                dir_now = "l"
            elif dir_now == "l":
                point[1] += 1
                dir_now = "u"
            elif dir_now == "u":
                point[0] += 1
                dir_now = "r"
            
        if (point[0], point[1]) in visited_points:
            return True
        else:
            visited_points.append((point[0], point[1]))

    for i in range(len(bend_list)-1):
        cur_b = bend_list[i]
        next_b = bend_list[i+1]
        if cur_b == '-':
            continue
        if cur_b == next_b:
            return True
        
    return False


def randomBendRate(chan_width, max_rate_per_seg, i_len):
    # generate the random rate for a bendRate, rate shoule related to the segment length
    # 1. generate a ranmdom rate 
    # random.random()用于生成一个0到1的随机浮点数: 0 <= n < 1.0
    rate = round(random.random() * max_rate_per_seg, 2)

    # 2. adjust the rate related to the length
    min_rate_step = round(float(i_len) * 2 / float(chan_width), 2)
    rate = min_rate_step * math.floor(rate / min_rate_step)

    return rate


def getSegmentsSet():
    segsSet = {  
        1 : { 'Tdel' : 9.394e-11, 'mux_trans_size' : 1.9613025792, 'buf_size' : 19.6353043302, 'Rmetal' : 259.5614, 'Cmetal' : 3.5491e-15 },
        2 : { 'Tdel' : 9.394e-11, 'mux_trans_size' : 1.9613025792, 'buf_size' : 19.6353043302, 'Rmetal' : 259.5614, 'Cmetal' : 3.5491e-15 },                                                   
        3 : { 'Tdel' : 1.144e-10, 'mux_trans_size' : 1.741, 'buf_size' : 22.2307453173, 'Rmetal' : 259.4815, 'Cmetal' : 3.548e-15 },                                                           
        4 : { 'Tdel' : 1.424e-10, 'mux_trans_size' : 1.50823186576, 'buf_size' : 25.5612499137, 'Rmetal' : 259.0515, 'Cmetal' : 3.5421e-15 },                                                  
        5 : { 'Tdel' : 1.743e-10, 'mux_trans_size' : 1.50823186576, 'buf_size' : 26.216569918, 'Rmetal' : 259.8, 'Cmetal' : 3.5523e-15 },                                                      
        6 : { 'Tdel' : 2.121e-10, 'mux_trans_size' : 1.50823186576, 'buf_size' : 26.4225783752, 'Rmetal' : 259.7362, 'Cmetal' : 3.5515e-15 },                                                  
        7 : { 'Tdel' : 2.538e-10, 'mux_trans_size' : 1.50823186576, 'buf_size' : 27.0706280249, 'Rmetal' : 259.9992, 'Cmetal' : 3.5551e-15 },                                                  
        8 : { 'Tdel' : 3.017e-10, 'mux_trans_size' : 1.50823186576, 'buf_size' : 28.6171271982, 'Rmetal' : 259.2413, 'Cmetal' : 3.5447e-15 },                                                  
        9 : { 'Tdel' : 3.564e-10, 'mux_trans_size' : 1.50823186576, 'buf_size' : 27.5631656927, 'Rmetal' : 259.9267, 'Cmetal' : 3.5541e-15 },                                                  
        10 : { 'Tdel' : 4.32e-10, 'mux_trans_size' : 1.25595750289, 'buf_size' : 27.4439345149, 'Rmetal' : 259.8155, 'Cmetal' : 3.5526e-15 },                                                  
        11 : { 'Tdel' : 4.929e-10, 'mux_trans_size' : 1.25595750289, 'buf_size' : 32.6284510555, 'Rmetal' : 259.7325, 'Cmetal' : 3.5514e-15 },                                                 
        12 : { 'Tdel' : 5.772e-10, 'mux_trans_size' : 1.25595750289, 'buf_size' : 28.3655846906, 'Rmetal' : 259.3041, 'Cmetal' : 3.5456e-15 },                                                 
        13 : { 'Tdel' : 6.502e-10, 'mux_trans_size' : 1.25595750289, 'buf_size' : 28.0303217563, 'Rmetal' : 259.5707, 'Cmetal' : 3.5492e-15 },                                                 
        14 : { 'Tdel' : 7.269e-10, 'mux_trans_size' : 1.25595750289, 'buf_size' : 30.4416927491, 'Rmetal' : 259.6215, 'Cmetal' : 3.5499e-15 },                                                 
        15 : { 'Tdel' : 8.046e-10, 'mux_trans_size' : 1.25595750289, 'buf_size' : 31.1285424055, 'Rmetal' : 259.4418, 'Cmetal' : 3.5474e-15 },                                                 
        16 : { 'Tdel' : 8.946e-10, 'mux_trans_size' : 1.25595750289, 'buf_size' : 32.5794230402, 'Rmetal' : 260.4216, 'Cmetal' : 3.5608e-15 },
    }

    return segsSet

def getArchSegmentation(seg_orig):
     # seed : I use the system time as the seed
    segDrivers = getSegmentsSet()

    segs = []
    idx = 0
    for seg in seg_orig:
        seg_name = seg.get("name")
        if seg_name == "imux_medium" or seg_name == "omux_medium" or seg_name == "gsb_medium":
            continue
        i_len = int(seg.get("length"))
        i_freq = float(seg.get("freq"))
        i_name = str(seg.get("name"))
        i_type = str(seg.get("type"))
        i_Cmetal = str(seg.get("Cmetal"))
        i_Rmetal = str(seg.get("Rmetal"))
        i_driver = str(i_len)
        i_driver_Tdel = str(segDrivers[i_len]['Tdel'])
        i_driver_mux_trans_size = str(segDrivers[i_len]['mux_trans_size'])
        i_driver_buf_size = str(segDrivers[i_len]['buf_size'])
        i_driver_para = (i_driver_Tdel, i_driver_mux_trans_size, i_driver_buf_size)

        bendElem = seg.find("bend")
        if not bendElem is None:
            i_bend_list = bendElem.text.split(" ")
        else:
            i_bend_list = ["-"] * (i_len - 1)

        new_seg = bendSegmentation(i_Rmetal, i_Cmetal, i_freq, i_len, i_bend_list, i_driver, idx, i_name, i_driver_para)
        segs.append(new_seg)
        idx += 1
        
    return segs


def getGsbArchFroms(arch):
    gsb_arch = arch.getroot().find("gsb_arch")

    gsbElem = gsb_arch.find("gsb")
    imuxElem = gsb_arch.find("imux")
    omuxElem = gsb_arch.find("omux")
    gsb = {}
    to_mux_nums = {}
    imux = {}
    omux = {}

    omux["mux_nums"] = omuxElem.get("mux_nums")
    omux["num_foreach"] = omuxElem.find("from").get("num_foreach")

    for seg_group in gsbElem:
        to_seg_name = seg_group.get("name")
        if to_seg_name == None:
            continue
        seg_froms = []
        for fromElem in seg_group:
            seg_froms.append(From_inf(fromElem))
        gsb[to_seg_name] = seg_froms
        to_mux_nums[to_seg_name] = int(seg_group.get("track_nums"))

    for lut_group in imuxElem:
        lut_name = lut_group.get("name")
        if lut_name == None:
            continue
        imux_froms = []
        for fromElem in lut_group:
            imux_froms.append(From_inf(fromElem))
        imux[lut_name] = imux_froms

    if len(imux) > 1:
        raise SeekerError("too many lut_group in imux, only one lut_group is ok")

    return (gsb, to_mux_nums, imux, omux)



def checkSameSeg(seg, segs):
    for i_seg in segs:
        if seg.bend_list == i_seg.bend_list:
            return True
    return False

def RandomOneSegmentation(segs, chan_width, sum_rate, is_short):
     # seed : I use the system time as the seed
    switch_type = ["U", "D", "-"]
    switch_type_prob = [0.15, 0.15, 0.7]
    
    seglen = list(range(1,17))
    tile_length = 30
    segRmetal = 7.862 * tile_length
    segCmetal = round(0.215 * tile_length / 2 ,5) / pow(10,15)
    segDrivers = getSegmentsSet()
    # seglen_prob = [1.0/12.0, 1.0/12.0, 1.0/12.0, 1.0/12.0, 1.0/12.0, 1.0/12.0, 1.0/12.0, 1.0/12.0, 1.0/12.0, 1.0/12.0, 1.0/6.0, 1.0/6.0, 1.0/6.0, 1.0/6.0, 1.0/6.0]
    shortSeglen_prob = [0, 0.2, 0.2, 0.2, 0.2, 0.2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    longSeglen_prob = [0, 0, 0, 0, 0, 0, 1.0/6, 1.0/6, 1.0/6, 1.0/6, 1.0/6, 1.0/6, 0, 0, 0, 0]

    if is_short:
        segLen_prob = shortSeglen_prob
    else:
        segLen_prob = longSeglen_prob

    new_seg = segs[0]
    new_chan_width = chan_width
    while checkSameSeg(new_seg, segs):
        i_len = random_pick(seglen, segLen_prob)
        i_Rmetal = str(segRmetal)
        i_Cmetal = str(segCmetal)
        i_driver = str(i_len)
        i_driver_Tdel = str(segDrivers[i_len]['Tdel'])
        i_driver_mux_trans_size = str(segDrivers[i_len]['mux_trans_size'])
        i_driver_buf_size = str(segDrivers[i_len]['buf_size'])
        i_driver_para = (i_driver_Tdel, i_driver_mux_trans_size, i_driver_buf_size)

        # random a rate
        '''
        i_freq = randomBendRate(chan_width, max_rate_per_seg, i_len)
        if i_freq == 0.0:
            continue
        if rate < i_freq:
            continue
        rate -= i_freq
        '''

        #random a num
        segNum = [2, 4, 6, 8, 10] if is_short else [1, 2]
        segNum_prob = [0.2, 0.2, 0.2, 0.2, 0.2] if is_short else [0.5, 0.5]
        i_num = random_pick(segNum, segNum_prob) * i_len * 2
        new_chan_width = chan_width + i_num
        i_freq = i_num * sum_rate / (new_chan_width - i_num)
        #print("i_num = " + str(i_num))
        #print("i_freq = " + str(i_freq))
        #print("new_chan_width = " + str(new_chan_width))
            
        # random a bend_list
        i_bend_list = ['-'] * (i_len - 1)
        if is_short:
            while True:
                for i in range(i_len - 1):
                    s_type = random_pick(switch_type, switch_type_prob)
                    i_bend_list[i] = s_type
                # check if there is a circle
                if i_bend_list == ['-']:
                    continue
                if check_circle(i_bend_list) == False:
                    break
        else:
            while True:
                i = int(i_len / 2) - 1
                s_type = random_pick(switch_type, switch_type_prob)
                i_bend_list[i] = s_type
                # check if there is a circle
                if check_circle(i_bend_list) == False:
                    break

        idx = len(segs)
        name = "segment_" + str(idx)
        new_seg = bendSegmentation(i_Rmetal, i_Cmetal, i_freq, i_len, i_bend_list, i_driver, idx, name, i_driver_para)

    return (new_chan_width, new_seg)

def getOriginSeg(root):
    return_list = []
    seglist = root.getroot().find("segmentlist")
    for seg in seglist.findall("segment"):
        return_list.append(seg)
    return return_list

def RandomOneImuxFrom(imux_froms, segs, chan_width):
    type_list = ["seg", "omux", "pb", "imux0"]
    type_prob = [0.7, 0.1, 0.1, 0.1]

    opin_types = ["o", "q"]
    opin_types_prob = [1 / 2.0, 1 / 2.0]
    
    sum_rate = 0
    for seg in segs:
        sum_rate += seg.freq

    type_orig = []
    for imux_from in imux_froms:
        type_str = imux_from.type
        if type_str == "imux":
            if imux_from.reuse:
                type_str = type_str + "1"
            else:
                type_str = type_str + "0"
        if type_str not in type_orig:
            type_orig.append(type_str)
    
    seg_orig = []
    for imux_from in imux_froms:
        if imux_from.type == "seg" and imux_from.name not in seg_orig:
            seg_orig.append(imux_from.name)
    
    #print("seg_ori:")
    #print(seg_orig)

    segs_tmp = copy.deepcopy(segs)
    for seg in segs:
        if seg.name in seg_orig:
            segs_tmp.remove(seg)
    
    #print("seg_tmp:")
    #print([seg_tmp.name for seg_tmp in segs_tmp])

    new_type = random_pick(type_list, type_prob)
    while new_type != "seg" and new_type in type_orig:
        new_type = random_pick(type_list, type_prob)
    
    if new_type == "seg":
        if segs_tmp:
            new_seg_from = random.sample(segs_tmp, 1)[0]
            imux_from = From_inf()
            imux_from.type = "seg"
            imux_from.name = new_seg_from.name
            imux_from.num_foreach = 1
            imux_from.total_froms = int(new_seg_from.freq * chan_width / sum_rate / new_seg_from.length / 2)
            imux_from.pin_types = ""
            imux_from.reuse = 1 if new_seg_from.length <= 6 else 0
        else:
            return None

    elif new_type == "imux0":
        imux_from = From_inf()
        imux_from.type = "imux"
        imux_from.name = "plb"
        imux_from.num_foreach = 1
        imux_from.total_froms = 48
        imux_from.pin_types = "Ia Ib Ic Id Ie If Ig Ih"
        imux_from.reuse = 0

    elif new_type == "omux":
        imux_from = From_inf()
        imux_from.type = "omux"
        imux_from.name = "oxbar"
        imux_from.num_foreach = 2
        imux_from.total_froms = 16
        imux_from.pin_types = ""
        imux_from.reuse = 1
    
    else:
        imux_from = From_inf()
        imux_from.type = "pb"
        imux_from.name = "plb"
        imux_from.num_foreach = 2
        imux_from.total_froms = 8
        imux_from.pin_types = random_pick(opin_types, opin_types_prob)
        imux_from.reuse = 1
    
    imux_froms.append(imux_from)

def RandomOneGsbFrom(gsb_froms, segs, chan_width, is_shortSeg):
    '''print("before:")
    for gsb_from in gsb_froms:
        print(gsb_from.name)'''
    type_list = ["seg", "omux", "pb"]
    type_prob = [0.6, 0.2, 0.2]

    opin_types = ["o", "q"]
    opin_types_prob = [1 / 2.0, 1 / 2.0]
    
    sum_rate = 0
    for seg in segs:
        sum_rate += seg.freq

    type_orig = []
    for gsb_from in gsb_froms:
        type_str = gsb_from.type
        if type_str not in type_orig:
            type_orig.append(type_str)
    
    seg_orig = []
    for gsb_from in gsb_froms:
        if gsb_from.type == "seg" and gsb_from.name not in seg_orig:
            seg_orig.append(gsb_from.name)
    
    segs_tmp = copy.deepcopy(segs)
    for seg in segs:
        if seg.name in seg_orig:
            segs_tmp.remove(seg)

    new_type = random_pick(type_list, type_prob)
    while new_type != "seg" and new_type in type_orig:
        new_type = random_pick(type_list, type_prob)
    
    new_to_add = False

    if new_type == "seg":
        if segs_tmp:
            '''print(seg_orig)
            for gsb_from in gsb_froms:
                print(gsb_from.name)'''
            
            new_seg_from = random.sample(segs_tmp,1)[0]
            gsb_from = From_inf()
            gsb_from.type = "seg"
            gsb_from.name = new_seg_from.name
            #print("new_name: " +new_seg_from.name)
            gsb_from.num_foreach = 1 if is_shortSeg else 2
            gsb_from.total_froms = int(new_seg_from.freq * chan_width / sum_rate / new_seg_from.length / 2)
            gsb_from.pin_types = ""
            gsb_from.reuse = 1 if new_seg_from.length <= 6 else 0
            new_to_add = True

    elif new_type == "omux":
        gsb_from = From_inf()
        gsb_from.type = "omux"
        gsb_from.name = "oxbar"
        gsb_from.num_foreach = 2
        gsb_from.total_froms = 16
        gsb_from.pin_types = ""
        gsb_from.reuse = 1
        new_to_add = True
    
    else:
        gsb_from = From_inf()
        gsb_from.type = "pb"
        gsb_from.name = "plb"
        gsb_from.num_foreach = 2
        gsb_from.total_froms = 8
        gsb_from.pin_types = random_pick(opin_types, opin_types_prob)
        gsb_from.reuse = 1
        new_to_add = True
    
    if not is_shortSeg:
        gsb_from.reuse = 0

    if new_to_add:
        gsb_froms.append(gsb_from)
    '''print("after:")
    for gsb_from in gsb_froms:
        print(gsb_from.name)'''

def RandomGsbFroms(segs, chan_width, to_seg_name):
    gsb_froms = []

    opin_types = ["o", "q"]
    opin_types_prob = [1 / 2.0, 1 / 2.0]

    sum_rate = 0
    for seg in segs:
        sum_rate += seg.freq
    
    shortSegs = {}
    longSegs = {}
    for seg in segs:
        if seg.length <= 6:
            shortSegs[seg.name] = int(seg.freq * chan_width / sum_rate / seg.length / 2)
        else:
            longSegs[seg.name] = int(seg.freq * chan_width / sum_rate / seg.length / 2)

    is_shortSeg = True if to_seg_name in shortSegs else False

    #assign omux from
    gsb_from_omux = From_inf()
    gsb_from_omux.type = "omux"
    gsb_from_omux.name = "oxbar"
    gsb_from_omux.num_foreach = 4 if is_shortSeg else random.randint(0, 1)
    gsb_from_omux.total_froms = 16
    gsb_from_omux.pin_types = ""
    gsb_from_omux.reuse = 1 if is_shortSeg else 0
    gsb_froms.append(gsb_from_omux)

    #assign pb from
    gsb_from_pb = From_inf()
    gsb_from_pb.type = "pb"
    gsb_from_pb.name = "plb"
    gsb_from_pb.num_foreach = 4 if is_shortSeg else random.randint(0, 1)
    gsb_from_pb.pin_types = random_pick(opin_types, opin_types_prob)
    opin_types_tmp = copy.deepcopy(opin_types)
    opin_types_tmp.remove(gsb_from_pb.pin_types)
    gsb_from_pb.pin_types += " " + random_pick(opin_types_tmp, [0.5, 0.5])
    gsb_from_pb.total_froms = 16
    gsb_from_pb.reuse = 1 if is_shortSeg else 0
    gsb_froms.append(gsb_from_pb)

    #assign seg from
    #1.same seg
    gsb_from_seg = From_inf()
    gsb_from_seg.type = "seg"
    gsb_from_seg.name = to_seg_name
    gsb_from_seg.pin_types = ""
    #print(shortSegs)
    #print(longSegs)
    #print(origName_map)
    gsb_from_seg.total_froms = shortSegs[to_seg_name] if to_seg_name in shortSegs else longSegs[to_seg_name]
    gsb_from_seg.num_foreach = 1 if is_shortSeg else 3
    gsb_from_seg.reuse = 1 if is_shortSeg else 0
    gsb_froms.append(gsb_from_seg)

    #2.diff seg
    seg_num_candi = [1, 2]
    seg_num_candi_prob = [0.5, 0.5]
    shortSeg_from_num = min(random_pick(seg_num_candi,seg_num_candi_prob), len(shortSegs))
    longSeg_from_num = 1

    shortSeg_from = {}
    longSeg_from = {}

    shortSegs.pop(to_seg_name) if is_shortSeg else longSegs.pop(to_seg_name)
    if shortSegs:
        shortSeg_from = random.sample(list(shortSegs), min(shortSeg_from_num, len(shortSegs)))
    if longSegs:
        longSeg_from = random.sample(list(longSegs), min(longSeg_from_num, len(longSegs)))

    for from_seg_name in shortSeg_from:
        gsb_from_seg = From_inf()
        gsb_from_seg.type = "seg"
        gsb_from_seg.name = from_seg_name
        gsb_from_seg.pin_types = ""
        gsb_from_seg.total_froms = shortSegs[from_seg_name]
        gsb_from_seg.num_foreach = 1 if is_shortSeg else 2
        gsb_from_seg.reuse = 1
        gsb_froms.append(gsb_from_seg)

    for from_seg_name in longSeg_from:
        gsb_from_seg = From_inf()
        gsb_from_seg.type = "seg"
        gsb_from_seg.name = from_seg_name
        gsb_from_seg.pin_types = ""
        gsb_from_seg.total_froms = longSegs[from_seg_name]
        gsb_from_seg.num_foreach = 1 if is_shortSeg else 3
        gsb_from_seg.reuse = 0
        gsb_froms.append(gsb_from_seg)
    
    return gsb_froms

def readArch(caller):
    archTrees = {}
    for arch in caller.optimizeArchs:
        archTrees[arch] = {}
        archTrees[arch]["root"] = ET.parse(caller.vtr_flow_dir + "/" + caller.arch_dir + "/" + arch)
        #print(caller.vtr_flow_dir + "/" + caller.arch_dir + "/" + arch)
        # archTrees[arch]["segPara"] = getSegPara(archTrees[arch]["root"])
        archTrees[arch]["segOrigin"] = getOriginSeg(archTrees[arch]["root"])
    return archTrees

def writeArch(elem, outfile):
    f = open(outfile, "wb+")
    f.write(prettify(elem))
    f.close()
    
# modify the arch in a new version
def modifyArch_V2(segs, archTree, outfile):
    # delete the <segmentlist>
    archTree["root"].getroot().remove(archTree["root"].find("segmentlist"))

    # find the <switchlist>
    switchlist = archTree["root"].getroot().find('switchlist')

    # add the new switches into <switchlist> according to the switches
    added = []
    for seg in segs:
        if seg.length not in added:
            added.append(seg.length)
            switchElem = ET.SubElement(switchlist, 'switch')
            switchElem.set("type", 'mux')
            switchElem.set("name", seg.driver)
            switchElem.set("R", '0.000000')
            switchElem.set("Cin", '0.000000e+00')
            switchElem.set("Cout", '0.000000e+00')
            switchElem.set("Tdel", seg.driver_para[0])
            switchElem.set("mux_trans_size", seg.driver_para[1])
            switchElem.set("buf_size", seg.driver_para[2])

    # add  <segmentlist> and modify the freq of the origin segments
    rate_bend_segment = 0.0
    seglist = ET.SubElement(archTree["root"].getroot(), "segmentlist")
    for seg in segs:
        rate_bend_segment += float(seg.freq)
        segElem = ET.SubElement(seglist, "segment")
        segElem.set("freq", str(seg.freq) ) 
        segElem.set("name", seg.name )
        segElem.set("length", str(seg.length) )
        segElem.set("type", "unidir")
        # segElem.set("Rmetal", seg.Rmetal)
        # segElem.set("Cmetal", seg.Cmetal)
        segElem.set("Rmetal", "0.000000")
        segElem.set("Cmetal", "0.000000e+00")

        mux = ET.SubElement(segElem, "mux")
        mux.set("name", seg.driver)

        sb = ET.SubElement(segElem, "sb")
        sb.set("type", "pattern")
        sb.text = " ".join( ["1"] * (seg.length + 1) )

        cb = ET.SubElement(segElem, "cb")
        cb.set("type", "pattern")
        cb.text = " ".join( ["1"] * seg.length )

        bend = ET.SubElement(segElem, "bend")
        bend.set("type", "pattern")
        bend.text = " ".join(seg.bend_list)

    rate_orgin = 0
    for seg in archTree["segOrigin"]:
        rate_orgin += float(seg.attrib["freq"])
    for seg in archTree["segOrigin"]:
        seg.set("freq", str( round((float(seg.attrib["freq"]) / rate_orgin) * (1 - rate_bend_segment), 2) ))
        seglist.append(seg) 

    # write out .xml file
    writeArch(archTree["root"].getroot(), outfile)


def modifyArch_V3(segs, gsbArchFroms, archTree, omux_changed = False):
    gsb = gsbArchFroms[0]
    to_mux_nums = gsbArchFroms[1]
    imux = gsbArchFroms[2]
    omux = gsbArchFroms[3]

    # delete the <segmentlist>
    archTree["root"].getroot().remove(archTree["root"].find("segmentlist"))

    # add  <segmentlist> and modify the freq of the origin segments
    rate_bend_segment = 0.0
    seglist = ET.SubElement(archTree["root"].getroot(), "segmentlist")
    for seg in segs:
        rate_bend_segment += float(seg.freq)
        segElem = ET.SubElement(seglist, "segment")
        segElem.set("freq", str(seg.freq))
        segElem.set("name", seg.name)
        segElem.set("length", str(seg.length))
        segElem.set("type", "unidir")
        # segElem.set("Rmetal", seg.Rmetal)
        # segElem.set("Cmetal", seg.Cmetal)
        segElem.set("Rmetal", "0.000000")
        segElem.set("Cmetal", "0.000000e+00")

        mux = ET.SubElement(segElem, "mux")
        mux.set("name", seg.driver)

        sb = ET.SubElement(segElem, "sb")
        sb.set("type", "pattern")
        sb.text = " ".join(["0"] * (seg.length - 1))
        sb.text = "1 " + sb.text + " 1"
        sb.text = ' '.join(sb.text.split())

        cb = ET.SubElement(segElem, "cb")
        cb.set("type", "pattern")
        cb.text = " ".join(["0"] * (seg.length - 2)) if seg.length >=2 else ""
        cb.text = "1 " + cb.text + " 1" if seg.length >=2 else "1"
        cb.text = ' '.join(cb.text.split())

    gsb_arch = archTree["root"].getroot().find("gsb_arch")

    if omux_changed:
        omuxElem = gsb_arch.find("omux")
        omuxElem.set("mux_nums", omux["mux_nums"])
        omuxElem.find("from").set("num_foreach", omux["num_foreach"])

    #remove multistage mux info
    if not gsb_arch.find("imux").find("multistage_muxs") is None:
        gsb_arch.find("imux").remove(gsb_arch.find("imux").find("multistage_muxs"))
    if not gsb_arch.find("gsb").find("multistage_muxs") is None:
        gsb_arch.find("gsb").remove(gsb_arch.find("gsb").find("multistage_muxs"))
    
    lut_group = gsb_arch.find("imux").find("group")
    rmElems = lut_group.findall("from")
    for rmElem in rmElems:
        lut_group.remove(rmElem)
    imux_froms = list(imux.values())[0]
    for imux_from in imux_froms:
        fromElem = ET.SubElement(lut_group, "from")
        '''
        print("***************")
        print(imux_from.type)
        print(imux_from.name)
        print(imux_from.total_froms)
        print(imux_from.num_foreach)
        print(imux_from.reuse)
        print(imux_from.pin_types)'''
        
        fromElem.set("type", imux_from.type)
        fromElem.set("name", imux_from.name)
        fromElem.set("total_froms", str(imux_from.total_froms))
        fromElem.set("num_foreach", str(imux_from.num_foreach))
        fromElem.set("reuse", str(imux_from.reuse))
        if imux_from.type == "pb" or imux_from.type == "imux":
            fromElem.set("pin_types", imux_from.pin_types)


    gsbElem = gsb_arch.find("gsb")
    gsbElem.set("gsb_seg_group", str(len(gsb)))
    rmElems = gsbElem.findall("seg_group")
    for rmElem in rmElems:
        gsbElem.remove(rmElem)

    for to_seg_name, gsb_froms in gsb.items():
        seg_group = ET.SubElement(gsbElem, "seg_group")
        seg_group.set("name", to_seg_name)
        seg_group.set("track_nums", str(to_mux_nums[to_seg_name]))

        for gsb_from in gsb_froms:
            fromElem = ET.SubElement(seg_group, "from")
            fromElem.set("type", gsb_from.type)
            fromElem.set("name", gsb_from.name)
            fromElem.set("total_froms", str(gsb_from.total_froms))
            fromElem.set("num_foreach", str(gsb_from.num_foreach))
            fromElem.set("reuse", str(gsb_from.reuse))
            if gsb_from.type == "pb":
                fromElem.set("pin_types", gsb_from.pin_types)

def modifyArch_V3_bent(segs, gsbArchFroms, archTree, omux_changed = False):
    gsb = gsbArchFroms[0]
    to_mux_nums = gsbArchFroms[1]
    imux = gsbArchFroms[2]
    omux = gsbArchFroms[3]

    # delete the <segmentlist>
    archTree["root"].getroot().remove(archTree["root"].find("segmentlist"))

    # add  <segmentlist> and modify the freq of the origin segments
    rate_bend_segment = 0.0
    seglist = ET.SubElement(archTree["root"].getroot(), "segmentlist")
    for seg in segs:
        rate_bend_segment += float(seg.freq)
        segElem = ET.SubElement(seglist, "segment")
        segElem.set("freq", str(seg.freq))
        segElem.set("name", seg.name)
        segElem.set("length", str(seg.length))
        segElem.set("type", "unidir")
        # segElem.set("Rmetal", seg.Rmetal)
        # segElem.set("Cmetal", seg.Cmetal)
        segElem.set("Rmetal", "0.000000")
        segElem.set("Cmetal", "0.000000e+00")

        mux = ET.SubElement(segElem, "mux")
        mux.set("name", seg.driver)

        sb = ET.SubElement(segElem, "sb")
        sb.set("type", "pattern")
        sb.text = " ".join(["0"] * (seg.length - 1))
        sb.text = "1 " + sb.text + " 1"
        sb.text = ' '.join(sb.text.split())

        cb = ET.SubElement(segElem, "cb")
        cb.set("type", "pattern")
        cb.text = " ".join(["0"] * (seg.length - 2)) if seg.length >=2 else ""
        cb.text = "1 " + cb.text + " 1" if seg.length >=2 else "1"
        cb.text = ' '.join(cb.text.split())

        # print(seg.name)
        # print(seg.bend_list)
        if seg.length > 1 and seg.bend_list != None and seg.bend_list != ["-"] * (seg.length - 1):
            bend = ET.SubElement(segElem, "bend")
            bend.set("type", "pattern")
            bend.text = " ".join(seg.bend_list)

    gsb_arch = archTree["root"].getroot().find("gsb_arch")

    if omux_changed:
        omuxElem = gsb_arch.find("omux")
        omuxElem.set("mux_nums", omux["mux_nums"])
        omuxElem.find("from").set("num_foreach", omux["num_foreach"])

    #remove multistage mux info
    if not gsb_arch.find("imux").find("multistage_muxs") is None:
        gsb_arch.find("imux").remove(gsb_arch.find("imux").find("multistage_muxs"))
    if not gsb_arch.find("gsb").find("multistage_muxs") is None:
        gsb_arch.find("gsb").remove(gsb_arch.find("gsb").find("multistage_muxs"))
    
    lut_group = gsb_arch.find("imux").find("group")
    rmElems = lut_group.findall("from")
    for rmElem in rmElems:
        lut_group.remove(rmElem)
    imux_froms = list(imux.values())[0]
    for imux_from in imux_froms:
        fromElem = ET.SubElement(lut_group, "from")
        '''
        print("***************")
        print(imux_from.type)
        print(imux_from.name)
        print(imux_from.total_froms)
        print(imux_from.num_foreach)
        print(imux_from.reuse)
        print(imux_from.pin_types)'''
        
        fromElem.set("type", imux_from.type)
        fromElem.set("name", imux_from.name)
        fromElem.set("total_froms", str(imux_from.total_froms))
        fromElem.set("num_foreach", str(imux_from.num_foreach))
        fromElem.set("reuse", str(imux_from.reuse))
        if imux_from.type == "pb" or imux_from.type == "imux":
            fromElem.set("pin_types", imux_from.pin_types)


    gsbElem = gsb_arch.find("gsb")
    gsbElem.set("gsb_seg_group", str(len(gsb)))
    rmElems = gsbElem.findall("seg_group")
    for rmElem in rmElems:
        gsbElem.remove(rmElem)

    for to_seg_name, gsb_froms in gsb.items():
        seg_group = ET.SubElement(gsbElem, "seg_group")
        seg_group.set("name", to_seg_name)
        seg_group.set("track_nums", str(to_mux_nums[to_seg_name]))

        for gsb_from in gsb_froms:
            fromElem = ET.SubElement(seg_group, "from")
            fromElem.set("type", gsb_from.type)
            fromElem.set("name", gsb_from.name)
            fromElem.set("total_froms", str(gsb_from.total_froms))
            fromElem.set("num_foreach", str(gsb_from.num_foreach))
            fromElem.set("reuse", str(gsb_from.reuse))
            if gsb_from.type == "pb":
                fromElem.set("pin_types", gsb_from.pin_types)

def modifyArch_addMedium(archTree):
    # add  <segmentlist> and modify the freq of the origin segments
    seglist = archTree["root"].getroot().find("segmentlist")
    segs_include_medium = []
    segs_include_medium.append(bendSegmentation(0, 0, 0.0, 1, [], "only_mux", 0, "imux_medium", [0,0,0]))
    segs_include_medium.append(bendSegmentation(0, 0, 0.0, 1, [], "only_mux", 0, "omux_medium", [0,0,0]))
    segs_include_medium.append(bendSegmentation(0, 0, 0.0, 1, [], "only_mux", 0, "gsb_medium", [0, 0, 0]))
    for seg in segs_include_medium:
        segElem = ET.SubElement(seglist, "segment")
        segElem.set("freq", str(seg.freq))
        segElem.set("name", seg.name)
        segElem.set("length", str(seg.length))
        segElem.set("type", "unidir")
        # segElem.set("Rmetal", seg.Rmetal)
        # segElem.set("Cmetal", seg.Cmetal)
        segElem.set("Rmetal", "0.000000")
        segElem.set("Cmetal", "0.000000e+00")

        mux = ET.SubElement(segElem, "mux")
        mux.set("name", seg.driver)

        sb = ET.SubElement(segElem, "sb")
        sb.set("type", "pattern")
        sb.text = " ".join(["0"] * (seg.length - 1))
        sb.text = "1 " + sb.text + " 1"
        sb.text = ' '.join(sb.text.split())

        cb = ET.SubElement(segElem, "cb")
        cb.set("type", "pattern")
        cb.text = " ".join(["0"] * (seg.length - 2)) if seg.length >=2 else ""
        cb.text = "1 " + cb.text + " 1" if seg.length >=2 else "1"
        cb.text = ' '.join(cb.text.split())


def modifyArch_fixLayout(archTree):
    layout = archTree["root"].getroot().find("layout")
    auto_layout = layout.find("auto_layout")
    if not auto_layout is None:
        auto_layout.tag = "fixed_layout"
        auto_layout.attrib.clear()
        auto_layout.attrib["height"] = "130"
        auto_layout.attrib["width"] = "130"
        auto_layout.attrib["name"] = "fixed_layout"

def modifyArch_autoLayout(archTree):
    layout = archTree["root"].getroot().find("layout")
    fixed_layout = layout.find("fixed_layout")
    if not fixed_layout is None:
        fixed_layout.tag = "auto_layout"
        fixed_layout.attrib.clear()
        fixed_layout.attrib["aspect_ratio"] = "1.0"

# Simulater Annealing Used functions
def baselineInfo(baseWorkdir, caller, onlyRoutingDelay):
    results_Dict = {}

    for b in caller.circuits:
        if not os.path.exists(baseWorkdir + "/" + b):
            raise SeekerError("Can't find the " + baseWorkdir + "/" + b)
        
        if b not in results_Dict:
            results_Dict[b] = {}

        area_found = False
        delay_found = False
        logic_area_found = False
        routing_area = None
        logic_area = None
        
        f = open(baseWorkdir + "/" + b + "/vpr.out")
        lines = f.readlines()
        for line in lines:
            area_match = re.match(Regex.regex_reporter("routing_area"), line)
            if not area_match is None:
                routing_area = float(area_match.group(1))
                area_found = True
            logic_area_match = re.match(Regex.regex_reporter("logic_area"), line)
            if not logic_area_match is None:
                logic_area = float(logic_area_match.group(1))
                logic_area_found = True
            delay_match = re.match(Regex.regex_reporter("delay"), line)
            if not delay_match is None:
                results_Dict[b]["delay"] = float(delay_match.group(1))
                delay_found = True
        f.close()

        if onlyRoutingDelay:
            results_Dict[b]["delay"] = calculateRoutingDelay(baseWorkdir, b)

        results_Dict[b]["area"] = routing_area + logic_area
        results_Dict[b]["routing_area"] = routing_area
        if (area_found == False or delay_found == False or logic_area_found == False):
            raise SeekerError("Can't find the area delay in" + baseWorkdir + "/" + b + "/vpr.out" )

    return results_Dict

def baselineInfo_cbsb():
    #0.60.5_158_0.10.1_full
    results_Dict = {}
    results_Dict["arm_core.blif"] = {}
    results_Dict["arm_core.blif"]["delay"] = 12.5708
    results_Dict["arm_core.blif"]["routing_area"] = 3.54E+07

    results_Dict["bgm.blif"] = {}
    results_Dict["bgm.blif"]["delay"] = 12.8901
    results_Dict["bgm.blif"]["routing_area"] = 6.70E+07

    results_Dict["blob_merge.blif"] = {}
    results_Dict["blob_merge.blif"]["delay"] = 6.17411
    results_Dict["blob_merge.blif"]["routing_area"] = 1.78E+07

    results_Dict["boundtop.blif"] = {}
    results_Dict["boundtop.blif"]["delay"] = 1.39269
    results_Dict["boundtop.blif"]["routing_area"] = 2.20E+06

    results_Dict["ch_intrinsics.blif"] = {}
    results_Dict["ch_intrinsics.blif"]["delay"] = 1.87272
    results_Dict["ch_intrinsics.blif"]["routing_area"] = 1.83E+06

    results_Dict["diffeq1.blif"] = {}
    results_Dict["diffeq1.blif"]["delay"] = 19.2207
    results_Dict["diffeq1.blif"]["routing_area"] = 3.89E+06

    results_Dict["diffeq2.blif"] = {}
    results_Dict["diffeq2.blif"]["delay"] = 14.6899
    results_Dict["diffeq2.blif"]["routing_area"] = 3.89E+06

    results_Dict["LU8PEEng.blif"] = {}
    results_Dict["LU8PEEng.blif"]["delay"] = 54.6551
    results_Dict["LU8PEEng.blif"]["routing_area"] = 7.10E+07

    results_Dict["LU32PEEng.blif"] = {}
    results_Dict["LU32PEEng.blif"]["delay"] = 56.5168
    results_Dict["LU32PEEng.blif"]["routing_area"] = 2.40E+08

    results_Dict["mcml.blif"] = {}
    results_Dict["mcml.blif"]["delay"] = 51.3776
    results_Dict["mcml.blif"]["routing_area"] = 2.22E+08

    results_Dict["mkDelayWorker32B.blif"] = {}
    results_Dict["mkDelayWorker32B.blif"]["delay"] = 6.45547
    results_Dict["mkDelayWorker32B.blif"]["routing_area"] = 3.69E+07

    results_Dict["mkPktMerge.blif"] = {}
    results_Dict["mkPktMerge.blif"]["delay"] = 3.62036
    results_Dict["mkPktMerge.blif"]["routing_area"] = 1.11E+07

    results_Dict["mkSMAdapter4B.blif"] = {}
    results_Dict["mkSMAdapter4B.blif"]["delay"] = 4.36347
    results_Dict["mkSMAdapter4B.blif"]["routing_area"] = 5.48E+06

    results_Dict["or1200.blif"] = {}
    results_Dict["or1200.blif"]["delay"] = 9.98287
    results_Dict["or1200.blif"]["routing_area"] = 1.03E+07

    results_Dict["raygentop.blif"] = {}
    results_Dict["raygentop.blif"]["delay"] = 4.53159
    results_Dict["raygentop.blif"]["routing_area"] = 8.08E+06

    results_Dict["sha.blif"] = {}
    results_Dict["sha.blif"]["delay"] = 8.65521
    results_Dict["sha.blif"]["routing_area"] = 7.42E+06

    results_Dict["stereovision0.blif"] = {}
    results_Dict["stereovision0.blif"]["delay"] = 2.58932
    results_Dict["stereovision0.blif"]["routing_area"] = 3.54E+07

    results_Dict["stereovision1.blif"] = {}
    results_Dict["stereovision1.blif"]["delay"] = 4.94999
    results_Dict["stereovision1.blif"]["routing_area"] = 3.39E+07

    results_Dict["stereovision2.blif"] = {}
    results_Dict["stereovision2.blif"]["delay"] = 13.379
    results_Dict["stereovision2.blif"]["routing_area"] = 1.39E+08

    results_Dict["stereovision3.blif"] = {}
    results_Dict["stereovision3.blif"]["delay"] = 1.72077
    results_Dict["stereovision3.blif"]["routing_area"] = 5.48E+05

    return results_Dict

def evaluateCost(workDir, caller, baseInfo, logger, onlyRoutingDelay):

    cost = 0.0
    # Trade-off between delay and the area
    alpha = 0
    beta = 1
    mean_delay = 0
    mean_area = 0
    mean_area_delay = 0

    failed = 0
    logger.info('{0:<20}  {1:<20}  {2:<20}  {3:<20} {4:<20}'.format("circuit", "delay_base", "delay_modified", "delay_percent", "area_delay_precent") + "\n")
    for b in caller.circuits:
        if not os.path.exists(workDir + "/" + b):
            logger.error("Can't find the " + workDir + "/" + b)
            raise SeekerError("Can't find the " + workDir + "/" + b)
        
        area_found = False
        delay_found = False
        logic_area_found = False
        routable = True
        route_sucess = False
        routing_area = 0.0
        delay = 0.0
        logic_area = 0.0
        f = open(workDir + "/" + b + "/vpr.out")
        lines = f.readlines()
        for line in lines:
            area_match = re.match(Regex.regex_reporter("routing_area"), line)
            if area_match != None:
                routing_area = float(area_match.group(1))
                area_found = True
            logic_area_match = re.match(Regex.regex_reporter("logic_area"), line)
            if logic_area_match != None:
                logic_area = float(logic_area_match.group(1))
                logic_area_found = True
            delay_match = re.match(Regex.regex_reporter("delay"), line)
            if delay_match != None:
                delay = float(delay_match.group(1))
                delay_found = True
            routable_match = re.match(Regex.regex_reporter("routable"), line)
            if routable_match != None:
                routable = False
            routable_match2 = re.match(Regex.regex_task("status"), line)
            if routable_match2 != None:
                route_sucess = True

        f.close()
        if (area_found == False or delay_found == False or logic_area_found == False) and routable == True:
            if route_sucess:
                logger.error("Can't find the area delay in" + workDir + "/" + b + "/vpr.out")
                raise SeekerError("Can't find the area delay in" + workDir + "/" + b + "/vpr.out" )
            else:
                failed += 1
                # if failed >= 3:
                #     return None, None, None, None
                continue
        if b not in baseInfo:
            logger.error("Can't find the area delay info in the baseInfo")
            raise SeekerError("Can't find the area delay info in the baseInfo")
        if (area_found == False or delay_found == False or logic_area_found == False) and routable == False:
            failed += 1
            # if failed >= 3:
            #     return None, None, None, None
            continue
        
        if onlyRoutingDelay and delay_found:
            delay = calculateRoutingDelay(workDir, b)

        #print("\t\t" + b + " Routing area: " + str(routing_area) + "  Delay: " + str(delay))
        #area = logic_area + routing_area
        #cost += (math.pow(area / baseInfo[b]['area'], alpha) * math.pow(delay / baseInfo[b]['delay'], beta))
        cost += (math.pow(routing_area / baseInfo[b]['routing_area'], alpha) * math.pow( delay / baseInfo[b]['delay'], beta))

        mean_delay += (delay - baseInfo[b]['delay']) / baseInfo[b]['delay']
        #mean_area += (area - baseInfo[b]['area']) / baseInfo[b]['area']
        #mean_area_delay += (delay * area - baseInfo[b]['area'] * baseInfo[b]['delay']) / (baseInfo[b]['area'] * baseInfo[b]['delay'])
        mean_area += (routing_area - baseInfo[b]['routing_area']) / baseInfo[b]['routing_area']
        mean_area_delay += (delay * routing_area - baseInfo[b]['routing_area'] * baseInfo[b]['delay']) / (baseInfo[b]['routing_area'] * baseInfo[b]['delay'])
        logger.info('{0:<20}  {1:<20}  {2:<20}  {3:<20%} {4:<20%}'.format(
            b, baseInfo[b]['delay'], delay, (delay - baseInfo[b]['delay']) / baseInfo[b]['delay'], (delay * routing_area - baseInfo[b]['routing_area'] * baseInfo[b]['delay']) / (baseInfo[b]['routing_area'] * baseInfo[b]['delay'])) + "\n")

    circuits_num = len(caller.circuits) - failed
    cost = cost / circuits_num if circuits_num > 0 else 0.0
    mean_delay = round( 100 * (mean_delay / circuits_num) , 2) if circuits_num > 0 else 0.0
    mean_area = round(100 * mean_area / circuits_num , 2) if circuits_num > 0 else 0.0
    mean_area_delay = round(100 * mean_area_delay / circuits_num , 2) if circuits_num > 0 else 0.0

    # Added by SZheng
    cost += 2.0 * failed
    # END: Added by SZheng

    return cost, mean_delay, mean_area, mean_area_delay

def evaluateCostMultiObj(workDir, caller, baseInfo, logger, onlyRoutingDelay):

    cost = 0.0
    # Trade-off between delay and the area
    alpha = 0
    beta = 1
    mean_delay = 0
    mean_area = 0
    mean_area_delay = 0

    failed = 0
    logger.info('{0:<20}  {1:<20}  {2:<20}  {3:<20} {4:<20}'.format("circuit", "delay_base", "delay_modified", "delay_percent", "area_delay_precent") + "\n")
    for b in caller.circuits:
        if not os.path.exists(workDir + "/" + b):
            logger.error("Can't find the " + workDir + "/" + b)
            raise SeekerError("Can't find the " + workDir + "/" + b)
        
        area_found = False
        delay_found = False
        logic_area_found = False
        routable = True
        route_sucess = False
        routing_area = 0.0
        delay = 0.0
        logic_area = 0.0
        f = open(workDir + "/" + b + "/vpr.out")
        lines = f.readlines()
        for line in lines:
            area_match = re.match(Regex.regex_reporter("routing_area"), line)
            if area_match != None:
                routing_area = float(area_match.group(1))
                area_found = True
            logic_area_match = re.match(Regex.regex_reporter("logic_area"), line)
            if logic_area_match != None:
                logic_area = float(logic_area_match.group(1))
                logic_area_found = True
            delay_match = re.match(Regex.regex_reporter("delay"), line)
            if delay_match != None:
                delay = float(delay_match.group(1))
                delay_found = True
            routable_match = re.match(Regex.regex_reporter("routable"), line)
            if routable_match != None:
                routable = False
            routable_match2 = re.match(Regex.regex_task("status"), line)
            if routable_match2 != None:
                route_sucess = True

        f.close()
        if (area_found == False or delay_found == False or logic_area_found == False) and routable == True:
            if route_sucess:
                logger.error("Can't find the area delay in" + workDir + "/" + b + "/vpr.out")
                raise SeekerError("Can't find the area delay in" + workDir + "/" + b + "/vpr.out" )
            else:
                failed += 1
                # if failed >= 3:
                #     return None, None, None, None
                continue
        if b not in baseInfo:
            logger.error("Can't find the area delay info in the baseInfo")
            raise SeekerError("Can't find the area delay info in the baseInfo")
        if (area_found == False or delay_found == False or logic_area_found == False) and routable == False:
            failed += 1
            # if failed >= 3:
            #     return None, None, None, None
            continue
        
        if onlyRoutingDelay and delay_found:
            delay = calculateRoutingDelay(workDir, b)

        #print("\t\t" + b + " Routing area: " + str(routing_area) + "  Delay: " + str(delay))
        #area = logic_area + routing_area
        #cost += (math.pow(area / baseInfo[b]['area'], alpha) * math.pow(delay / baseInfo[b]['delay'], beta))
        cost += (math.pow(routing_area / baseInfo[b]['routing_area'], alpha) * math.pow( delay / baseInfo[b]['delay'], beta))

        mean_delay += (delay - baseInfo[b]['delay']) / baseInfo[b]['delay']
        #mean_area += (area - baseInfo[b]['area']) / baseInfo[b]['area']
        #mean_area_delay += (delay * area - baseInfo[b]['area'] * baseInfo[b]['delay']) / (baseInfo[b]['area'] * baseInfo[b]['delay'])
        mean_area += (routing_area - baseInfo[b]['routing_area']) / baseInfo[b]['routing_area']
        mean_area_delay += (delay * routing_area - baseInfo[b]['routing_area'] * baseInfo[b]['delay']) / (baseInfo[b]['routing_area'] * baseInfo[b]['delay'])
        logger.info('{0:<20}  {1:<20}  {2:<20}  {3:<20%} {4:<20%}'.format(
            b, baseInfo[b]['delay'], delay, (delay - baseInfo[b]['delay']) / baseInfo[b]['delay'], (delay * routing_area - baseInfo[b]['routing_area'] * baseInfo[b]['delay']) / (baseInfo[b]['routing_area'] * baseInfo[b]['delay'])) + "\n")

    circuits_num = len(caller.circuits) - failed
    cost = cost / circuits_num if circuits_num > 0 else 0.0
    mean_delay = round( 100 * (mean_delay / circuits_num) , 2) if circuits_num > 0 else 0.0
    mean_area = round(100 * mean_area / circuits_num , 2) if circuits_num > 0 else 0.0
    mean_area_delay = round(100 * mean_area_delay / circuits_num , 2) if circuits_num > 0 else 0.0

    # Added by SZheng
    cost += 2.0 * failed
    # END: Added by SZheng

    return 2.0 * failed, mean_delay, mean_area, mean_area_delay

def evaluateCostNew(workDir, caller, baseInfo, logger, onlyRoutingDelay):

    costNumer = 0.0
    costDenom = 0.0
    cost = 0.0
    # Trade-off between delay and the area
    alpha = 0
    beta = 1
    mean_delay = 0
    mean_area = 0
    mean_area_delay = 0

    failed = 0
    logger.info('{0:<20}  {1:<20}  {2:<20}  {3:<20} {4:<20}'.format("circuit", "delay_base", "delay_modified", "delay_percent", "area_delay_precent") + "\n")
    for b in caller.circuits:
        if not os.path.exists(workDir + "/" + b):
            logger.error("Can't find the " + workDir + "/" + b)
            raise SeekerError("Can't find the " + workDir + "/" + b)
        
        area_found = False
        delay_found = False
        logic_area_found = False
        routable = True
        route_sucess = False
        routing_area = 0.0
        delay = 0.0
        logic_area = 0.0
        f = open(workDir + "/" + b + "/vpr.out")
        lines = f.readlines()
        for line in lines:
            area_match = re.match(Regex.regex_reporter("routing_area"), line)
            if area_match != None:
                routing_area = float(area_match.group(1))
                area_found = True
            logic_area_match = re.match(Regex.regex_reporter("logic_area"), line)
            if logic_area_match != None:
                logic_area = float(logic_area_match.group(1))
                logic_area_found = True
            delay_match = re.match(Regex.regex_reporter("delay"), line)
            if delay_match != None:
                delay = float(delay_match.group(1))
                delay_found = True
            routable_match = re.match(Regex.regex_reporter("routable"), line)
            if routable_match != None:
                routable = False
            routable_match2 = re.match(Regex.regex_task("status"), line)
            if routable_match2 != None:
                route_sucess = True

        f.close()
        if (area_found == False or delay_found == False or logic_area_found == False) and routable == True:
            if route_sucess:
                logger.error("Can't find the area delay in" + workDir + "/" + b + "/vpr.out")
                raise SeekerError("Can't find the area delay in" + workDir + "/" + b + "/vpr.out" )
            else:
                failed += 1
                # if failed >= 3:
                #     return None, None, None, None
                continue
        if b not in baseInfo:
            logger.error("Can't find the area delay info in the baseInfo")
            raise SeekerError("Can't find the area delay info in the baseInfo")
        if (area_found == False or delay_found == False or logic_area_found == False) and routable == False:
            failed += 1
            # if failed >= 3:
            #     return None, None, None, None
            continue
        
        if onlyRoutingDelay and delay_found:
            delay = calculateRoutingDelay(workDir, b)

        #print("\t\t" + b + " Routing area: " + str(routing_area) + "  Delay: " + str(delay))
        #area = logic_area + routing_area
        #cost += (math.pow(area / baseInfo[b]['area'], alpha) * math.pow(delay / baseInfo[b]['delay'], beta))
        costNumer += (routing_area**alpha) * (delay**beta); 
        costDenom += (baseInfo[b]['routing_area']**alpha) * (baseInfo[b]['delay']**beta); 
        cost += (math.pow(routing_area / baseInfo[b]['routing_area'], alpha) * math.pow( delay / baseInfo[b]['delay'], beta))

        mean_delay += (delay - baseInfo[b]['delay']) / baseInfo[b]['delay']
        #mean_area += (area - baseInfo[b]['area']) / baseInfo[b]['area']
        #mean_area_delay += (delay * area - baseInfo[b]['area'] * baseInfo[b]['delay']) / (baseInfo[b]['area'] * baseInfo[b]['delay'])
        mean_area += (routing_area - baseInfo[b]['routing_area']) / baseInfo[b]['routing_area']
        mean_area_delay += (delay * routing_area - baseInfo[b]['routing_area'] * baseInfo[b]['delay']) / (baseInfo[b]['routing_area'] * baseInfo[b]['delay'])
        logger.info('{0:<20}  {1:<20}  {2:<20}  {3:<20%} {4:<20%}'.format(
            b, baseInfo[b]['delay'], delay, (delay - baseInfo[b]['delay']) / baseInfo[b]['delay'], (delay * routing_area - baseInfo[b]['routing_area'] * baseInfo[b]['delay']) / (baseInfo[b]['routing_area'] * baseInfo[b]['delay'])) + "\n")

    circuits_num = len(caller.circuits) - failed
    cost = cost / circuits_num if circuits_num > 0 else 0.0
    cost = costNumer / costDenom if costDenom > 0.0 else 0.0
    mean_delay = round( 100 * (mean_delay / circuits_num) , 2) if circuits_num > 0 else 0.0
    mean_area = round(100 * mean_area / circuits_num , 2) if circuits_num > 0 else 0.0
    mean_area_delay = round(100 * mean_area_delay / circuits_num , 2) if circuits_num > 0 else 0.0

    # Added by SZheng
    cost += 2.0 * failed
    # END: Added by SZheng

    return cost, mean_delay, mean_area, mean_area_delay


def calculateRoutingDelay(workDir, benchmark):
    #logger.info('{0:<20}  {1:<20}  {2:<20}  {3:<20} {4:<20}'.format("circuit", "routingDelay_base", "routingDelay_modified", "routingDelay_percent", "area_routingDelay_precent") + "\n")
    b = benchmark
    if not os.path.exists(workDir + "/" + b):
        logger.error("Can't find the " + workDir + "/" + b)
        raise SeekerError("Can't find the " + workDir + "/" + b)

    status = 0
    delay = 0.0
    f = open(workDir + "/" + b + "/report_timing.setup.rpt")
    lines = f.readlines()
    for line in lines:
        #begin
        if status == 0:
            begin_match = re.match(Regex.regex_routingDelay("begin"), line)
            if not begin_match is None:
                status = 1
            else:
                continue
            
        #calculating
        elif status == 1:
            delay_match = re.match(Regex.regex_routingDelay("routingDelay"), line)
            end_match = re.match(Regex.regex_routingDelay("end"), line)
            if not end_match is None:
                break

            if not delay_match is None:
                delay += float(delay_match.group(1))
            else:
                continue
    return delay

def evaluateCost_test(workDir, T):

    cost = 0.0
    # Trade-off between delay and the area
    alpha = 0
    beta = 1
    mean_delay = 0
    mean_area = 0
    mean_area_delay = 0

    
    cost = random.random() * T
    mean_delay = cost
    mean_area = cost
    mean_area_delay = cost

    return cost, mean_delay, mean_area, mean_area_delay

def clearWorkDir(caller, isFist):
    workDir = caller.task_dir + "/" + caller.run_dir[-1] + "/optimizeArchs/" + archName
    if os.path.exists(workDir + "/" + archName):
        os.system("rm " + workDir + "/" + archName)
    if isFist == True:
        return
    os.chdir(workDir + "/workdir")
    for b in caller.circuits:
        os.system("rm -rf ./*")


def check_seg_same(prev_seg, seg):
    if len(prev_seg) != len(seg):
        return False
    
    visited = []
    for ps in prev_seg:
        found = False
        for s in seg:
            if ps == s and (s not in visited):
                visited.append(s)
                found = True
        if found == False:
            return False 

    if len(seg) == len(visited) and len(visited) == len(prev_seg):
        return True

    return False

def check_duplicate_seg(segs):
    for i in range(len(segs)):
        for j in range(i):
            if "".join(segs[j].bend_list) == "".join(segs[i].bend_list):
                return True
    return False

def is_l2_num_less_4(segs):
    num = 0
    for seg in segs:
        if seg.length == 2:
            num = num + 1

    return False if num > 3 else True

def is_necessary_seg(seg):
    if seg.length == 1:
        return True
    elif seg.length == 2 and seg.bend_list == ['-']:
        return True
    else:
        return False

#origName_map存了更新之后还存在的线型的新旧名字对应，如果能找到，可将from中的名字替换，否则删除
def newSegmentation_V3(segs, T, chan_width, origName_map):
    # length allowed to change
    seglen = list(range(1,17))
    tile_length = 30
    segRmetal = 7.862 * tile_length
    segCmetal = round(0.215 * tile_length / 2 ,5) / pow(10,15)
    segDrivers = getSegmentsSet()
    shortSeglen_prob = [0, 0.2, 0.2, 0.2, 0.2, 0.2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    longSeglen_prob = [0, 0, 0, 0, 0, 0, 1.0/6, 1.0/6, 1.0/6, 1.0/6, 1.0/6, 1.0/6, 0, 0, 0, 0]

    new_chan_width = chan_width

    # max num allowed to add or sub
    maxNumSeg = int(2 * math.exp(-1 / T))

    # possibility to change the switch
    poss_switch = 0.5 * (math.exp(-1/T) + 0.5)
    # possibility to change the length of segment
    poss_len_seg = 0.5 * math.exp(-1/T)
    # possibility to change the rate of the segment
    poss_rate =  0.7 * (math.exp(-1/T) + 0.1)
    # possibility to change the num of segment
    poss_num_seg = 0.5 * math.exp(-1/T)

    # max rate of whole segments
    maxrate = 100.0
    switch_type = ["U","D","-"]
    switch_type_prob_short = [0.25, 0.25, 0.5]
    switch_type_prob_long = [0.1, 0.1, 0.8]

    # calculate the sum of rate
    sum_rate = 0.0
    shortSegs = []
    longSegs = []
    for seg in segs:
        sum_rate += float(seg.freq)
        sum_rate = round(sum_rate, 2)
        if seg.length <= 6:
            shortSegs.append(seg)
        else:
            longSegs.append(seg)

    if sum_rate > maxrate:
        raise SeekerError("Sum rate is too large.")

    #print(sum_rate)
    
    prev_seg = copy.deepcopy(segs)
    while check_seg_same(prev_seg, segs):
        for seg in shortSegs:
            #if change length, it will also change bent_type, so we don't change bent_type again
            len_changed = False

            # 1. change the length of segment
            new_len = random_pick(seglen, shortSeglen_prob)
            if random.random() < poss_len_seg:
                if is_necessary_seg(seg):
                    aa = 1
                elif new_len != seg.length:
                    len_changed = True
                    #change freq because of len changed
                    seg_num_orig = int(seg.freq * chan_width / sum_rate)
                    new_seg_num = seg_num_orig / seg.length * new_len
                    new_chan_width = chan_width - seg_num_orig + new_seg_num
                    if new_chan_width == new_seg_num:
                        new_rate = seg.freq
                    else:
                        new_rate = (sum_rate - seg.freq) * new_seg_num / (new_chan_width - new_seg_num)
                    '''print("seg.freq:" + str(seg.freq))
                    print("chan_width:" + str(chan_width))
                    print("new_rate:" + str(new_rate))
                    print("sum_rate:" + str(sum_rate))
                    print("seg_num_orig:" + str(seg_num_orig))
                    print("new_seg_num:" + str(new_seg_num))
                    print("seg.length:" + str(seg.length))
                    print("new_len:" + str(new_len))
                    print("new_chan_width:" + str(new_chan_width))
                    print("=============\n")'''
                    sum_rate = sum_rate - seg.freq + new_rate
                    seg.freq = new_rate
                    chan_width = new_chan_width
                    #print("sum_rate = " + str(sum_rate))
                    #print("new_rate = " + str(new_rate))
                    #print("chan_width = " + str(chan_width))
                    sum_rate = round(sum_rate, 2)

                    #change length
                    seg.length = new_len
                    seg.Rmetal = str(segRmetal)
                    seg.Cmetal = str(segCmetal)
                    seg.driver = str(new_len)
                    i_driver_Tdel = str(segDrivers[new_len]['Tdel'])
                    i_driver_mux_trans_size = str(segDrivers[new_len]['mux_trans_size'])
                    i_driver_buf_size = str(segDrivers[new_len]['buf_size'])
                    seg.driver_para = (i_driver_Tdel, i_driver_mux_trans_size, i_driver_buf_size)

                    #change freq because of len changed


                    # random a new bend_list
                    i_bend_list = ['-'] * (new_len - 1)
                    if new_len > 2:
                        change_pos = random.randint(0, new_len - 2)
                        s_type = random_pick(switch_type, switch_type_prob_short)
                        i_bend_list[change_pos] = s_type
                    elif new_len == 2:
                        s_type = random_pick(switch_type, [0.5, 0.5, 0])
                        i_bend_list[0] = s_type
                    '''
                    while True:
                        for i in range(new_len - 1):
                            s_type = random_pick(switch_type, switch_type_prob)
                            i_bend_list[i] = s_type
                        
                        if i_bend_list == ['-']:
                            continue
                        # check if there is a circle
                        if check_circle(i_bend_list) == False:
                            break
                    '''
                    seg.bend_list = i_bend_list

            # 2. change the switch of segment
            if not len_changed and random.random() < poss_switch:
                tmp_bend_list = ['-'] * (seg.length - 1)
                #print(seg.bend_list)
                if not is_necessary_seg(seg):
                    if seg.length > 2:
                        change_pos = random.randint(0, seg.length - 2)
                        s_type = random_pick(switch_type, switch_type_prob_short)
                        tmp_bend_list[change_pos] = s_type
                    elif seg.length == 2:
                        s_type = random_pick(switch_type, [0.5, 0.5, 0])
                        tmp_bend_list[0] = s_type
                    '''
                    while True:
                        for i in range(len(seg.bend_list)):
                            if random.random() < poss_switch:
                                tmp_switch = random_pick(switch_type, switch_type_prob)
                                tmp_bend_list[i] = tmp_switch
                        if check_circle(tmp_bend_list) == False:
                            break
                    '''
                    seg.bend_list = tmp_bend_list
    

            # 3. chagne the rate of segment
            if random.random() < poss_rate:
                seg_num_constrain = 0
                if is_necessary_seg(seg):
                    seg_num_constrain = 10 if seg.length == 1 else 20 #5 for l1 and l2

                seg_num_orig = int(seg.freq * chan_width / sum_rate)
                min_seg_num_step = seg.length * 2
                #min_rate_step = round( float(seg.length * 2) / float(chan_width) , 2)
                add_or_sub = int(2 * (random.randint(0, 1) - 0.5))
                new_seg_num = seg_num_orig + add_or_sub * min_seg_num_step
                if new_seg_num <= seg_num_constrain:
                    new_seg_num = seg_num_constrain + min_seg_num_step 

                if (chan_width - seg_num_orig + new_seg_num) < 301:
                    new_chan_width = chan_width - seg_num_orig + new_seg_num
                    if new_chan_width == new_seg_num:
                        new_rate = seg.freq
                    else:
                        new_rate = (sum_rate - seg.freq) * new_seg_num / (new_chan_width - new_seg_num)
                    
                    '''print("seg.freq:" + str(seg.freq))
                    print("chan_width:" + str(chan_width))
                    print("new_rate:" + str(new_rate))
                    print("sum_rate:" + str(sum_rate))
                    print("seg_num_orig:" + str(seg_num_orig))
                    print("new_seg_num:" + str(new_seg_num))
                    print("seg.length:" + str(seg.length))
                    print("new_chan_width:" + str(new_chan_width))
                    print("=============\n")'''
                    sum_rate = sum_rate - seg.freq + new_rate
                    seg.freq = new_rate
                    chan_width = new_chan_width
                    #print("sum_rate = " + str(sum_rate))
                    #print("new_rate = " + str(new_rate))
                    #print("chan_width = " + str(chan_width))
                    
                sum_rate = round(sum_rate, 2)


        for seg in longSegs:
            len_changed = False
            # 1. change the length of segment
            new_len = random_pick(seglen, longSeglen_prob)
            if random.random() < poss_len_seg:
                if new_len != seg.length:
                    len_changed = True
                    #change freq because of len changed
                    seg_num_orig = int(seg.freq * chan_width / sum_rate)
                    new_seg_num = seg_num_orig / seg.length * new_len
                    new_chan_width = chan_width - seg_num_orig + new_seg_num
                    if new_chan_width == new_seg_num:
                        new_rate = seg.freq
                    else:
                        new_rate = (sum_rate - seg.freq) * new_seg_num / (new_chan_width - new_seg_num)
                    
                    '''print("seg.freq:" + str(seg.freq))
                    print("chan_width:" + str(chan_width))
                    print("new_rate:" + str(new_rate))
                    print("sum_rate:" + str(sum_rate))
                    print("seg_num_orig:" + str(seg_num_orig))
                    print("new_seg_num:" + str(new_seg_num))
                    print("seg.length:" + str(seg.length))
                    print("new_len:" + str(new_len))
                    print("new_chan_width:" + str(new_chan_width))
                    print("=============\n")'''
                    sum_rate = sum_rate - seg.freq + new_rate
                    seg.freq = new_rate
                    chan_width = new_chan_width
                    #print("sum_rate = " + str(sum_rate))
                    #print("new_rate = " + str(new_rate))
                    #print("chan_width = " + str(chan_width))
                    sum_rate = round(sum_rate, 2)

                    #change length
                    seg.length = new_len
                    seg.Rmetal = str(segRmetal)
                    seg.Cmetal = str(segCmetal)
                    seg.driver = str(new_len)
                    i_driver_Tdel = str(segDrivers[new_len]['Tdel'])
                    i_driver_mux_trans_size = str(segDrivers[new_len]['mux_trans_size'])
                    i_driver_buf_size = str(segDrivers[new_len]['buf_size'])
                    seg.driver_para = (i_driver_Tdel, i_driver_mux_trans_size, i_driver_buf_size)

                    # random a new bend_list
                    i_bend_list = ['-'] * (new_len - 1)
                    i = int(new_len / 2) - 1
                    s_type = random_pick(switch_type, switch_type_prob_long)
                    i_bend_list[i] = s_type
                    seg.bend_list = i_bend_list

            # 2. change the switch of segment
            if not len_changed:
                tmp_bend_list = copy.deepcopy(seg.bend_list)
                while True:
                    if random.random() < poss_switch:
                        i = int(seg.length / 2) - 1
                        tmp_switch = random_pick(switch_type, switch_type_prob_long)
                        tmp_bend_list[i] = tmp_switch
                    if check_circle(tmp_bend_list) == False:
                        break
                seg.bend_list = tmp_bend_list

            # 3. chagne the rate of segment
            if random.random() < poss_rate:
                seg_num_orig = int(seg.freq * chan_width / sum_rate)
                min_seg_num_step = seg.length * 2
                #min_rate_step = round( float(seg.length * 2) / float(chan_width) , 2)
                add_or_sub = int(2 * (random.randint(0, 1) - 0.5))
                '''
                new_rate = seg.freq + add_or_sub * min_rate_step
                if new_rate <= 0:
                    new_rate = min_rate_step
                if (sum_rate - seg.freq) + new_rate <= maxrate:
                    sum_rate = (sum_rate - seg.freq) + new_rate
                    seg.freq = new_rate
                sum_rate = round(sum_rate, 2)
                '''
                new_seg_num = seg_num_orig + add_or_sub * min_seg_num_step
                if new_seg_num <= 0:
                    new_seg_num = min_seg_num_step
                elif new_seg_num > 2 * min_seg_num_step:
                    new_seg_num = 2 * min_seg_num_step

                if (chan_width - seg_num_orig + new_seg_num) < 301:
                    new_chan_width = chan_width - seg_num_orig + new_seg_num
                    if new_chan_width == new_seg_num:
                        new_rate = seg.freq
                    else:
                        new_rate = (sum_rate - seg.freq) * new_seg_num / (new_chan_width - new_seg_num)
                    '''print("seg.freq:" + str(seg.freq))
                    print("chan_width:" + str(chan_width))
                    print("new_rate:" + str(new_rate))
                    print("sum_rate:" + str(sum_rate))
                    print("seg_num_orig:" + str(seg_num_orig))
                    print("new_seg_num:" + str(new_seg_num))
                    print("seg.length:" + str(seg.length))
                    print("new_chan_width:" + str(new_chan_width))
                    print("=============\n")'''
                    sum_rate = sum_rate - seg.freq + new_rate
                    seg.freq = new_rate
                    chan_width = new_chan_width
                    #print("sum_rate = " + str(sum_rate))
                    #print("new_rate = " + str(new_rate))
                    #print("chan_width = " + str(chan_width))
                    
                sum_rate = round(sum_rate, 2)

        # 4. add or decrease the seg
        if random.random() < poss_num_seg:
            add_or_sub = random.randint(-1,1)
            # do nothing
            if add_or_sub == 0:
                pass
            # add the seg
            elif add_or_sub == +1:
                num_seg_to_add = random.randint(0, maxNumSeg)
                #logger.info("num_to_add"+ str(num_seg_to_add))
                while num_seg_to_add > 0:
                    is_short = random_pick([True, False], [0.8, 0.2])
                    (new_chan_width, seg) = RandomOneSegmentation(segs, chan_width, sum_rate, is_short)
                    if checkSameSeg(seg, segs):
                        continue
                    seg.net_idx = len(segs)
                    seg.name = "segment_" + str(seg.net_idx)
                    segs.append(seg)
                    chan_width = new_chan_width
                    sum_rate = round( sum_rate + seg.freq, 2)
                    num_seg_to_add -= 1
            elif add_or_sub == -1:
                num_seg_to_sub = random.randint(0, maxNumSeg)
                #logger.info("num_to_sub"+ str(num_seg_to_sub))
                while num_seg_to_sub > 0:
                    is_short = random_pick([True, False], [0.8, 0.2])
                    if is_short and len(shortSegs) > 4:
                        remove_seg = shortSegs[random.randint(0, len(shortSegs) - 1)]
                        if remove_seg.length == 1 or remove_seg.bend_list == ['-']:
                            continue
                        remove_num = int(chan_width * remove_seg.freq / sum_rate)
                        chan_width = chan_width - remove_num
                        sum_rate -= remove_seg.freq
                        segs.remove(remove_seg)
                        shortSegs.remove(remove_seg)
                    elif not is_short and len(longSegs) > 1:
                        remove_seg = longSegs[random.randint(0, len(longSegs) - 1)]
                        remove_num = int(chan_width * remove_seg.freq / sum_rate)
                        chan_width = chan_width - remove_num
                        sum_rate -= remove_seg.freq
                        segs.remove(remove_seg)
                        longSegs.remove(remove_seg)
                    num_seg_to_sub -= 1

                    '''
                    if len(segs) > 3:
                        remove_seg = segs[random.randint(0, len(segs) - 1)]
                        remove_num = int(chan_width * remove_seg.freq / sum_rate)
                        chan_width = chan_width - remove_num
                        sum_rate -= remove_seg.freq
                        segs.remove(remove_seg)'''
                    
            sum_rate = round(sum_rate, 2)

        #remove duplicate segment
        #rate会累加到最后一个
        tmp_list = []
        for i in range(len(segs)):
            redundant = False
            for j in range(i):
                if "".join(segs[j].bend_list) == "".join(segs[i].bend_list):
                    redundant = True
                    segs[j].freq += segs[i].freq
            if redundant == True:
                tmp_list.append(segs[i])

        for seg in tmp_list:
            #seg_num = int(seg.freq * chan_width / sum_rate)
            #chan_width = chan_width - seg_num
            segs.remove(seg)

        #if no straight but two more seg, make one staright if it have too much bend
        len_map = {}
        for seg in segs:
            if seg.length not in len_map:
                len_map[seg.length] = [seg]
            else:
                len_map[seg.length].append(seg)
        
        for same_lens in len_map.values():
            find_straight = False
            for seg in same_lens:
                if seg.bend_list == ['-'] * (seg.length - 1):
                    find_straight = True
                    break
            if not find_straight:
                for seg in same_lens:
                    seg.bend_list = ['-'] * (seg.length - 1)
                    break

        origName_map = {}
        for i in range(len(segs)):
            seg = segs[i]
            seg.net_idx = i
            origName_map[seg.name] = "segment_" + str(seg.net_idx)
            seg.name = "segment_" + str(seg.net_idx)

    while sum_rate > maxrate:
        for seg in segs:
            seg.freq = seg.freq / 2.0
        sum_rate = sum_rate / 2.0

    return (chan_width, origName_map)

def computeSegNum(segs, seg_name, chan_width):
    i_freq = 0.0
    i_len = 0
    sum_rate = 0.0
    for seg in segs:
        sum_rate += seg.freq
        if seg.name == seg_name:
            i_freq = seg.freq
            i_len = seg.length
    
    seg_num = int(i_freq * chan_width / sum_rate / i_len / 2)
    return seg_num


def newGsbArchFroms(gsbArchFroms, segs, T, chan_width, origName_map):
    # length allowed to change
    gsb = gsbArchFroms[0]
    to_mux_nums = gsbArchFroms[1]
    imux = gsbArchFroms[2]

    if len(imux) > 1:
        raise SeekerError("too many imux lut_group!!")

    opin_types = ["o", "q"]
    opin_types_prob = [1 / 2.0, 1 / 2.0]

    # max num allowed to add or sub
    maxNumSeg = int(math.exp(-1 / T)+0.5)

    # possibility to change the num_foreach
    poss_num_foreach = 0.2 * (math.exp(-1 / T) + 0.5)

    # possibility to change the pin_types
    poss_pin_types = 0.2 * (math.exp(-1 / T) + 0.5)

    # possibility to change the imux_from_num
    poss_num_froms = 0.2 * (math.exp(-1 / T) + 0.5)

    shortSegs =[]
    longSegs = []
    for seg in segs:
        if seg.length > 6:
            longSegs.append(seg)
        else:
            shortSegs.append(seg)
    
    #***************************for imux*********************************
    for lut_name, imux_froms in imux.items():
        removed_froms = []

        '''print("****one")
        for imux_from in imux_froms:
            print("***************")
            print(imux_from.type)
            print(imux_from.name)
            print(imux_from.total_froms)
            print(imux_from.num_foreach)
            print(imux_from.reuse)
            print(imux_from.pin_types)'''
            
        for imux_from in imux_froms:
            if imux_from.type == "seg":
                #1.用改变后的线型替换原线型
                if imux_from.name in origName_map:
                    new_name = origName_map[imux_from.name]
                    imux_from.name = new_name
                    imux_from.total_froms = computeSegNum(segs, new_name, chan_width)
                    imux_from.num_foreach = min(imux_from.num_foreach, imux_from.total_froms)
                else:
                    removed_froms.append(imux_from)

        #2.移除删除的线型，将num_foreach分给其他线型
        for imux_from in removed_froms:
            num_foreach_orig = imux_from.num_foreach
            from_reuse = True if imux_from.reuse == 1 else False
            seg_candi = shortSegs if from_reuse else longSegs 
            imux_froms.remove(imux_from)
            while num_foreach_orig > 0:
                all_is_enough = True
                for i_imux_from in imux_froms:
                    if i_imux_from.type == "seg" and i_imux_from.num_foreach < i_imux_from.total_froms:
                        seg_to_add = findSeg(seg_candi, i_imux_from.name)
                        if not seg_to_add is None:
                            i_imux_from.num_foreach += 1
                            num_foreach_orig -= 1
                            all_is_enough = False
                if all_is_enough:
                    num_foreach_orig = 0

        #3.改变pin_types
        for imux_from in imux_froms:
            if imux_from.type == "pb":
                if random.random() < poss_pin_types:
                    orig_pin_types = imux_from.pin_types.split(" ")
                    new_pin_types = []
                    i = len(orig_pin_types)
                    if i > 2:
                        raise SeekerError("The pin_types of pb in imux_from is larger than 2!!!")
                    while i > 0:
                        new_pin_type = random_pick(opin_types, opin_types_prob)
                        if new_pin_type not in new_pin_types:
                            new_pin_types.append(new_pin_type)
                            i -= 1
                
                    imux_from.pin_types = " ".join(new_pin_types)

        #4.改变num_foreach
        #removed_froms.clear()
        for imux_from in imux_froms:
            if random.random() < poss_num_foreach:
                add_or_sub = int(2 * (random.randint(0, 1) - 0.5))
                imux_from.num_foreach = imux_from.num_foreach + add_or_sub

                imux_from.num_foreach = max(1, imux_from.num_foreach)
                imux_from.num_foreach = min(imux_from.total_froms, imux_from.num_foreach)
    
        '''print("****two")
        for imux_from in imux_froms:
            print("***************")
            print(imux_from.type)
            print(imux_from.name)
            print(imux_from.total_froms)
            print(imux_from.num_foreach)
            print(imux_from.reuse)
            print(imux_from.pin_types)'''

        #5.改变from数目
        if random.random() < poss_num_froms:
            add_or_sub = random.randint(-1, 1)
            # do nothing
            if add_or_sub == 0:
                pass
            # add the seg
            elif add_or_sub == +1:
                num_seg_to_add = random.randint(0, maxNumSeg)
                for _ in range(num_seg_to_add):
                    RandomOneImuxFrom(imux_froms, segs, chan_width)
            elif add_or_sub == -1:
                num_seg_to_sub = random.randint(0, maxNumSeg)
                for _ in range(num_seg_to_sub):
                    if len(imux_froms) > 1:
                        remove_from = imux_froms[random.randint(0, len(imux_froms) - 1)]
                        imux_froms.remove(remove_from)
        
        
        '''print("****three")
        for imux_from in imux_froms:
            print("***************")
            print(imux_from.type)
            print(imux_from.name)
            print(imux_from.total_froms)
            print(imux_from.num_foreach)
            print(imux_from.reuse)
            print(imux_from.pin_types)'''

    #***************************for gsb*********************************
    '''gsb_tmp = gsb.copy()
    for to_seg_name, gsb_froms in gsb_tmp.items():
        if to_seg_name not in origName_map:
            gsb.pop(to_seg_name)
        else:
            gsb[origName_map[to_seg_name]] = gsb.pop(to_seg_name) '''
    
    #上段代码有点问题，如map有{l1:l2, l2:l3}的情况，可能在将l1改为l2后，在将l2改为l3的过程中，此l2已经是新的了，却仍会将其改为l3，同时l2删除了，有问题
    new_gsb = {}
    for to_seg_name in gsb.keys():
        if to_seg_name in origName_map:
            new_gsb[origName_map[to_seg_name]] = copy.deepcopy(gsb[to_seg_name])
    gsb.clear()
    for k,v in new_gsb.items():
        gsb[k] = v
    
    for to_seg_name, gsb_froms in gsb.items():
        is_shortSeg = False
        for seg in segs:
            if seg.name == to_seg_name and seg.length <= 6:
                is_shortSeg = True
                break

        removed_froms = []
        #1.用改变后的线型替换原线型
        for gsb_from in gsb_froms:
            if gsb_from.type == "seg":
                if gsb_from.name in origName_map:
                    new_name = origName_map[gsb_from.name]
                    gsb_from.name = new_name
                    gsb_from.total_froms = computeSegNum(segs, new_name, chan_width)
                    gsb_from.num_foreach = min(gsb_from.num_foreach, gsb_from.total_froms)
                else:
                    removed_froms.append(gsb_from)

        #2.移除删除的线型，将num_foreach分给其他线型
        for gsb_from in removed_froms:
            num_foreach_orig = gsb_from.num_foreach
            from_reuse = True if gsb_from.reuse == 1 else False
            seg_candi = shortSegs if from_reuse else longSegs 
            gsb_froms.remove(gsb_from)
            while num_foreach_orig > 0:
                all_is_enough = True
                for i_gsb_from in gsb_froms:
                    if i_gsb_from.type == "seg" and i_gsb_from.num_foreach < i_gsb_from.total_froms:
                        seg_to_add = findSeg(seg_candi, i_gsb_from.name)
                        if not seg_to_add is None:
                            i_gsb_from.num_foreach += 1
                            num_foreach_orig -= 1
                            all_is_enough = False
                if all_is_enough:
                    num_foreach_orig = 0

        #3.改变pin_types
        for gsb_from in gsb_froms:
            if gsb_from.type == "pb":
                if random.random() < poss_pin_types:
                    orig_pin_types = gsb_from.pin_types.split(" ")
                    new_pin_types = []
                    i = len(orig_pin_types)
                    if i > 2:
                        raise SeekerError("The pin_types of pb in gsb_from is larger than 2!!!")
                    while i > 0:
                        new_pin_type = random_pick(opin_types, opin_types_prob)
                        if new_pin_type not in new_pin_types:
                            new_pin_types.append(new_pin_type)
                            i -= 1

                    gsb_from.pin_types = " ".join(new_pin_types)

        #4.改变num_foreach
        #removed_froms.clear()
        for gsb_from in gsb_froms:
            if random.random() < poss_num_foreach:
                add_or_sub = random.randint(-1, 1)

                if gsb_from.type == "seg":
                    from_seg = findSeg(segs, gsb_from.name)
                    from_seg_short = True if from_seg.length <=6 else False

                    if is_shortSeg and from_seg_short:
                        if add_or_sub == +1 and gsb_from.num_foreach < 2:
                            gsb_from.num_foreach = gsb_from.num_foreach + 1
                        elif add_or_sub == -1:
                            gsb_from.num_foreach = gsb_from.num_foreach - 1
                        gsb_from.num_foreach = max(1, gsb_from.num_foreach)
                        gsb_from.num_foreach = min(gsb_from.total_froms, gsb_from.num_foreach)
                    elif is_shortSeg and not from_seg_short:
                        if add_or_sub == +1 and gsb_from.num_foreach < 2:
                            gsb_from.num_foreach = gsb_from.num_foreach + 1
                        elif add_or_sub == -1:
                            gsb_from.num_foreach = gsb_from.num_foreach - 1
                        gsb_from.num_foreach = max(1, gsb_from.num_foreach)
                    elif not is_shortSeg:
                        if add_or_sub == +1:
                            gsb_from.num_foreach = gsb_from.num_foreach + 1
                        elif add_or_sub == -1:
                            gsb_from.num_foreach = gsb_from.num_foreach - 1
                        gsb_from.num_foreach = max(1, gsb_from.num_foreach)
                        gsb_from.num_foreach = min(gsb_from.total_froms * 4, gsb_from.num_foreach)
                else:
                    if is_shortSeg:
                        if add_or_sub == +1 and gsb_from.num_foreach < 8:
                            gsb_from.num_foreach = gsb_from.num_foreach + 1
                        elif add_or_sub == -1:
                            gsb_from.num_foreach = gsb_from.num_foreach - 1
                        gsb_from.num_foreach = max(1, gsb_from.num_foreach)
                        gsb_from.num_foreach = min(gsb_from.total_froms, gsb_from.num_foreach)
                    elif not is_shortSeg:
                        if add_or_sub == +1 and gsb_from.num_foreach < 4:
                            gsb_from.num_foreach = gsb_from.num_foreach + 1
                        elif add_or_sub == -1:
                            gsb_from.num_foreach = gsb_from.num_foreach - 1
                        gsb_from.num_foreach = max(1, gsb_from.num_foreach)
                        gsb_from.num_foreach = min(gsb_from.total_froms, gsb_from.num_foreach)
                
        #5.改变from数目
        if random.random() < poss_num_froms:
            add_or_sub = random.randint(-1, 1)
            # do nothing
            if add_or_sub == 0:
                pass
            # add the seg
            elif add_or_sub == +1:
                num_seg_to_add = random.randint(0, maxNumSeg)
                for _ in range(num_seg_to_add):
                    RandomOneGsbFrom(gsb_froms, segs, chan_width, is_shortSeg)
            elif add_or_sub == -1:
                num_seg_to_sub = random.randint(0, maxNumSeg)
                gsb_froms_tmp = copy.deepcopy(gsb_froms)
                #print(to_seg_name)
                for gsb_from in gsb_froms:
                    #gsb_from.show()
                    if gsb_from.name == to_seg_name:
                        gsb_froms_tmp.remove(gsb_from)

                for _ in range(num_seg_to_sub):
                    if len(gsb_froms_tmp) > 0:
                        remove_from = gsb_froms_tmp[random.randint(0, len(gsb_froms_tmp) - 1)]
                        gsb_froms_tmp.remove(remove_from)
                        gsb_froms.remove(remove_from)
        
    for need_to_seg in origName_map.values():
        if need_to_seg not in gsb:
            gsb[need_to_seg] = RandomGsbFroms(segs, chan_width, need_to_seg)

    #**************************change to_mux_num
    to_mux_nums.clear()
    sum_rate = 0
    for seg in segs:
        sum_rate += seg.freq
    #print("sum_rate = " + str(sum_rate))
    for seg in segs:
        #print("seg_name = " + seg.name + "---------")
        to_mux_nums[seg.name] = int(seg.freq * chan_width / sum_rate / seg.length / 2)
        #print("seg.freq = " + str(seg.freq))
        #print("chan_width = " + str(chan_width))
        #print("seg.length = " + str(seg.length))
        #print("track_nums = " + str(to_mux_nums[seg.name]))


def param():
    T0 = 100.0
    alpha = 0.4
    T_end = 1e-2
    maxIter = 50
    k = 0.004
    return (T0, alpha, T_end, maxIter, k)

def mux_trans_sizes():
    size_map = {}
    size_map["gsb_mux"] = 2.96345056513
    size_map["imux_mux"] = 1.25595750289
    size_map["1"] = 2.57691500578
    size_map["2"] = 2.772
    size_map["3"] = 1.9613025792
    size_map["4"] = 1.25595750289
    size_map["5"] = 1.50823186576
    size_map["6"] = 1.50823186576
    size_map["7"] = 3.15180029303
    size_map["8"] = 1.741
    size_map["9"] = 2.96345056513
    size_map["10"] = 2.772
    size_map["11"] = 2.772
    size_map["12"] = 2.772
    return size_map

def Update_t(T, alpha, accept_rate):

    if accept_rate > 0.9:
        T *= alpha * 0.6
    elif accept_rate > 0.7:
        T *= alpha * 0.7
    elif accept_rate > 0.3:
        T *= alpha * 0.8
    else:
        T *= alpha
    return T


def archive(workDir, archiveDir, count, benchMarks):
    if not os.path.exists(archiveDir):
        os.mkdir(archiveDir)
    if os.path.exists(archiveDir + "/" + str(count)):
        raise SeekerError("Wrong Archive Dir")
    else:
        os.system("mkdir " + archiveDir + "/" + str(count))

    os.chdir(workDir)
    for b in benchMarks:
        os.system("cp " + workDir + "/" + b +"/vpr.out " + archiveDir + "/" + str(count) + "/" + b + ".out")


def run_vpr_task(caller, workdir, archfile, archName, circuit, chan_width, isFirst, timelimit=10800):
    caller.run_sa_single(workdir, archfile, archName, circuit, chan_width, isFirst, timelimit)

def arch_test(caller, workdir, archfile, archName, circuit, chan_width, isFirst):
    result=caller.run_arch_test(workdir, archfile, archName, circuit, chan_width, isFirst)
    return result

def logger_init(logger, logdir='./logfiles', logfile='./logfiles/logger_test.log'):

    # Log等级总开关
    logger.setLevel(logging.INFO)

    # 创建log目录
    if not os.path.exists(logdir):
        os.mkdir(logdir)

    # 创建一个handler，用于写入日志文件
    # 以append模式打开日志文件
    fh = logging.FileHandler(logfile, mode='a')

    # 输出到file的log等级的开关
    fh.setLevel(logging.INFO)

    # 再创建一个handler，用于输出到控制台
    ch = logging.StreamHandler()

    # 输出到console的log等级的开关
    ch.setLevel(logging.INFO)

    # 定义handler的输出格式
    formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")

    # formatter = logging.Formatter("%(asctime)s [%(thread)u] %(levelname)s: %(message)s")
    # 为文件输出设定格式
    fh.setFormatter(formatter)
    # 控制台输出设定格式
    #ch.setFormatter(formatter)

    # 设置文件输出到logger
    logger.addHandler(fh)
    # 设置控制台输出到logger
    logger.addHandler(ch)

##################################################################################
#####
#####  if you wanna run the seeker.py :
#####       example : python Seeker.py -o ./ -j 20 -t hard_wire_test
#####                 and set the (optimize_arch_add) in config.txt
#####
#################################################################################

if __name__ == "__main__":
    #print(calculateRoutingDelay("baseline","arm_core.blif"))

    # chan_width
    chan_width = 158

    # analyze the argv 
    caller = Caller.Caller(sys.argv)
    
    # read the arch
    archs = readArch(caller)#for arch in caller.optimizeArchs


    SA_start_time = datetime.datetime.now()

    #for area evaluate
    size_map = mux_trans_sizes()
    area_dict = {}
    area_dict["gsb_mux"] = {}
    area_dict["imux_mux"] = {}
    for i in range(1, 13):
        area_dict[str(i)] = {}

    for k in area_dict.keys():
        for i in range(30):
            area_dict[k][i] = compute_area(i, size_map[k])
    print("area_dict:")
    print(area_dict)
    area_pair = [0, area_dict]
    # for debug test 
    p = param()
    T = p[0]
    alpha = p[1]
    T_end = p[2]
    maxIter = p[3]
    k = p[4]

    count = 0

    is_area_cons = True if caller.area_cons == 1 else False

    #archTree = readArch2("./k6_frac_N10_mem32K_40nm_gsb20.xml")
    #writeArch2(archs["k6_frac_N10_mem32K_40nm_gsb20.xml"]["root"].getroot(), "./test.xml")
    #writeArch2(archTree["root"].getroot(), "./test.xml")
    #for archName, archTree in archs.items():
    #    writeArch(archTree["root"].getroot(), "./test.xml")
    #    count += 1
    #    print(count)
    # for archName, archTree in archs.items():

    #     # init_seg = initialSegmentation_V2(caller.seed, chan_width)
    #     # for seg in init_seg:
    #     #     seg.show()
    #     # originTree = copy.deepcopy(archTree)
    #     # modifyArch_V2(init_seg, originTree, caller.task_dir + "/" + caller.run_dir[-1] + "/optimizeArchs/" + archName + "/" + archName)

    #     while(T > T_end): # outer loop
    #         for i in range(maxIter):
    #             count += 1
    #         T = Update_t(T, alpha, 10)
    #         print(T)

    #     print(count)

    # exit()

    logger = logging.getLogger('main')
    
    for archName, archTree in archs.items():  # 以task中的optimize_arch作为基准，开始进行模拟退火，如果没有指定optimize_arch，则会跳过整个模拟退火过程
        # Get the parameters  (T0, alpha, T_end, maxIter)
        p = param()
        T = p[0]
        alpha = p[1]
        T_end = p[2]
        maxIter = p[3]
        k = p[4]
        
        # record the num of decreasing the temperature
        outerCount = 0
        innerCount = 0
        Count = 0

        logdir = caller.task_dir + "/" + caller.run_dir[-1] + "/optimizeArchs/" + archName
        logfile = logdir + "/logfile.log"
        logger_init(logger, logdir, logfile)

         # get baseline info
        '''baseWorkdir = caller.task_dir + "/" + caller.run_dir[-1] + "/optimizeArchs/" + archName + "/baseline"
        archfile = caller.vtr_flow_dir + "/" + caller.arch_dir + "/" + archName
        if os.path.exists(baseWorkdir):
            logger.error("Base work dir is already exist")
            raise SeekerError("Base work dir is already exist")
        else:
            os.system("mkdir " + baseWorkdir)
        
        pool = multiprocessing.Pool(processes = caller.processes)
        for circuit in caller.circuits:
            workdir = baseWorkdir + "/" + circuit
            pool.apply_async(func=run_vpr_task,args=(caller, workdir, archfile, archName, circuit, chan_width, False,))
        pool.close()
        pool.join()'''
        baseInfo = baselineInfo_cbsb()
        logger.info(baseInfo)
        
        #writeArch(archTree["root"].getroot(), "./test.xml")
        #print(archTree["root"].getroot())
        # get InitialSegmentation
        #init_seg = initialSegmentation_V2(caller.seed, chan_width)  #起点为随机生成的线型
        init_seg = getArchSegmentation(archTree["segOrigin"])
        init_gsbArchFroms = getGsbArchFroms(archTree["root"])

        _prev_segs = copy.deepcopy(init_seg)
        _prev_froms = copy.deepcopy(init_gsbArchFroms)
        _prev_chan_width = chan_width

        #origName_map = {}
        #(chan_width, origName_map) = newSegmentation_V3(init_seg, T, chan_width, origName_map)
        #newGsbArchFroms(init_gsbArchFroms, init_seg, T, chan_width, origName_map)
        #modifyArch_V3(init_seg, init_gsbArchFroms, archTree)
        #modifyArch_addMedium(archTree)
        (gsb_mux_fanin, imux_mux_fanin) = generateTwoStageMux(archTree)
        verify_fanin_ok(gsb_mux_fanin, imux_mux_fanin, init_seg, list(init_gsbArchFroms[2].values())[0], area_pair, logger, is_area_cons)
        '''
        while not verify_fanin_ok(gsb_mux_fanin, imux_mux_fanin, init_seg):
            init_seg = copy.deepcopy(_prev_segs)
            init_gsbArchFroms = copy.deepcopy(_prev_froms)
            chan_width = _prev_chan_width
            (chan_width, origName_map) = newSegmentation_V3(init_seg, T, chan_width, origName_map)
            newGsbArchFroms(init_gsbArchFroms, init_seg, T, chan_width, origName_map)
            modifyArch_V3(init_seg, init_gsbArchFroms, archTree)
            modifyArch_addMedium(archTree)
            (gsb_mux_fanin, imux_mux_fanin) = generateTwoStageMux(archTree)'''

        #writeArch(archTree["root"].getroot(), "./test.xml")
        #########################################改变来源

        # init the work dir
        optWorkDir = caller.task_dir + "/" + caller.run_dir[-1] + "/optimizeArchs/" + archName + "/workdir"
        optArchiveDir = caller.task_dir + "/" + caller.run_dir[-1] + "/optimizeArchs/" + archName + "/archive"
        if os.path.exists(optWorkDir):
            logger.error("Opt Work dir is already exist")
            raise SeekerError("Opt Work dir is already exist")
        else:
            os.system("mkdir " + optWorkDir)

        # run the vtr to evaluate cost
        #originTree = copy.deepcopy(archTree)
        #clearWorkDir(caller, True)
        archfile_start = caller.task_dir + "/" + caller.run_dir[-1] + "/optimizeArchs/" + archName + "/startpoint"
        archfile = archfile_start + "/" + archName
        if os.path.exists(archfile_start):
            logger.error("archfile start dir is already exist")
            raise SeekerError("archfile start dir is already exist")
        else:
            os.system("mkdir " + archfile_start)
        writeArch(archTree["root"].getroot(), archfile)
        #modifyArch_V2(init_seg, originTree, archfile)
        
        '''pool = multiprocessing.Pool(processes = caller.processes)
        for circuit in caller.circuits:
            workdir = archfile_start + "/" + circuit
            pool.apply_async(func=run_vpr_task,args=(caller, workdir, archfile, archName, circuit, chan_width, False,))
        pool.close()
        pool.join()
        cost, mean_delay, mean_area, mean_area_delay = evaluateCost(archfile_start, caller, baseInfo, logger, False)'''
        #cost, mean_delay, mean_area, mean_area_delay = evaluateCost_test(optWorkDir, T)#如果有布不通的直接全返回None
        cost = 0.9478
        mean_delay = -5.22
        mean_area = -1.08
        mean_area_delay = -6.53

        logger.info("Init cost (" + str(cost) + ")" + "  mean delay (" + str(mean_delay) + "%)")
        logger.info("Initial Segmentations: ")
        for seg in init_seg:
            seg.show(logger)

        best_cost = cost
        best_segs = copy.deepcopy(init_seg)
        best_arch_count = -1
        best_chan_width = 158
        best_mean_delay = mean_delay
        best_mean_area = mean_area
        best_mean_area_delay = mean_area_delay
        #archive(optWorkDir, optArchiveDir, Count, caller.circuits)

        arch_tmp = caller.task_dir + "/" + caller.run_dir[-1] + "/optimizeArchs/" + archName + "/arch_tmp"
        os.system("mkdir " + arch_tmp)
        while(T > T_end): # outer loop
            innerCount = 1
            accept_rate = 0
            logger.info("\n")
            logger.info("T :" + str(T))
            try_count = 0
            for i in range(maxIter):
                loop_start_time = datetime.datetime.now()
                _prev_segs = copy.deepcopy(init_seg)
                _prev_froms = copy.deepcopy(init_gsbArchFroms)
                _prev_chan_width = chan_width
                #_prev_archTree = copy.deepcopy(archTree)
                #newSegmentation_V2(init_seg, T, chan_width)
                
                while True:
                    chan_widths = []
                    seg_vec = []
                    froms_vec = []
                    archTrees = []
                    archfiles = []
                    for i in range(10):
                        origName_map = {}
                        init_seg = copy.deepcopy(_prev_segs)
                        init_gsbArchFroms = copy.deepcopy(_prev_froms)
                        chan_width = _prev_chan_width
                        #archTree = copy.deepcopy(_prev_archTree)
                        (chan_width, origName_map) = newSegmentation_V3(init_seg, T, chan_width, origName_map)
                        '''logger.info( "\tsegs : first")
                        for s in init_seg:
                            s.show(logger)'''
                        newGsbArchFroms(init_gsbArchFroms, init_seg, T, chan_width, origName_map)
                        modifyArch_V3(init_seg, init_gsbArchFroms, archTree)
                        modifyArch_addMedium(archTree)
                        (gsb_mux_fanin, imux_mux_fanin) = generateTwoStageMux(archTree)

                        while not verify_fanin_ok(gsb_mux_fanin, imux_mux_fanin, init_seg, list(init_gsbArchFroms[2].values())[0], area_pair, logger, is_area_cons):
                            init_seg = copy.deepcopy(_prev_segs)
                            init_gsbArchFroms = copy.deepcopy(_prev_froms)
                            chan_width = _prev_chan_width
                            (chan_width, origName_map) = newSegmentation_V3(init_seg, T, chan_width, origName_map)
                            '''logger.info( "\tsegs :" + str(i) + " try_count" + str(try_count))
                            for s in init_seg:
                                s.show(logger)'''
                            newGsbArchFroms(init_gsbArchFroms, init_seg, T, chan_width, origName_map)
                            modifyArch_V3(init_seg, init_gsbArchFroms, archTree)
                            modifyArch_addMedium(archTree)
                            (gsb_mux_fanin, imux_mux_fanin) = generateTwoStageMux(archTree)
                            #writeArch(archTree["root"].getroot(), "./tt/test.xml" + str(try_count))
                            #try_count += 1
                    
                        '''logger.info( "\tsegs :" + str(i))
                        for s in init_seg:
                            s.show(logger)'''
                        archfile_tmp_count = arch_tmp + "/" + str(i)
                        archfile = archfile_tmp_count + "/" + archName
                        chan_widths.append(chan_width)
                        seg_vec.append(copy.deepcopy(init_seg))
                        froms_vec.append(copy.deepcopy(init_gsbArchFroms))
                        archTrees.append(copy.deepcopy(archTree))
                        archfiles.append(archfile)
                        if os.path.exists(archfile_tmp_count):
                            #raise SeekerError("archfile count " + str(Count) + " dir is already exist")
                            os.system("rm -rf " + archfile_tmp_count)
                            os.system("mkdir " + archfile_tmp_count)
                        else:
                            os.system("mkdir " + archfile_tmp_count)
                        modifyArch_fixLayout(archTree)
                        writeArch(archTree["root"].getroot(), archfile)
                        modifyArch_autoLayout(archTree)

                    result = []
                    pool = multiprocessing.Pool(10)
                    for ia in range(10):
                        workdir = arch_tmp + "/" + str(ia)
                        archfile = archfiles[ia]
                        #print(archfile)
                        result.append(pool.apply_async(func=arch_test,args=(caller, workdir, archfile, archName, "stereovision3.blif", chan_widths[ia], False,)))
                    pool.close()
                    pool.join()
                    result = [res.get() for res in result]
                    print(chan_widths)
                    print(result)
                    if result.count(True) == 0:
                        continue

                    for i in range(10):
                        if result[i] == True:
                            break

                    archfile_count = caller.task_dir + "/" + caller.run_dir[-1] + "/optimizeArchs/" + archName + "/" + str(Count)
                    archfile = archfile_count + "/" + archName
                    if os.path.exists(archfile_count):
                        #raise SeekerError("archfile count " + str(Count) + " dir is already exist")
                        os.system("rm -rf " + archfile_count)
                        os.system("mkdir " + archfile_count)
                    else:
                        os.system("mkdir " + archfile_count)
                    #os.system("cp " + archfiles[i] +  " " + archfile_count)
                    chan_width = chan_widths[i]
                    archTree = copy.deepcopy(archTrees[i])
                    writeArch(archTree["root"].getroot(), archfile)
                    init_seg = copy.deepcopy(seg_vec[i])
                    init_gsbArchFroms = copy.deepcopy(froms_vec[i])
                    break
                '''
                logger.info( "\n\tCount : " + str(Count))
                origName_map = {}
                (chan_width, origName_map) = newSegmentation_V3(init_seg, T, chan_width, origName_map)
                newGsbArchFroms(init_gsbArchFroms, init_seg, T, chan_width, origName_map)
                modifyArch_V3(init_seg, init_gsbArchFroms, archTree)
                modifyArch_addMedium(archTree)
                (gsb_mux_fanin, imux_mux_fanin) = generateTwoStageMux(archTree)
                #writeArch(archTree["root"].getroot(), "./tt/test.xml" + str(try_count))

                logger.info( "\n\tCount : " + str(Count))
                while not verify_fanin_ok(gsb_mux_fanin, imux_mux_fanin, init_seg, init_gsbArchFroms[2].values()[0], area_pair, logger):
                    init_seg = copy.deepcopy(_prev_segs)
                    init_gsbArchFroms = copy.deepcopy(_prev_froms)
                    chan_width = _prev_chan_width
                    (chan_width, origName_map) = newSegmentation_V3(init_seg, T, chan_width, origName_map)
                    newGsbArchFroms(init_gsbArchFroms, init_seg, T, chan_width, origName_map)
                    modifyArch_V3(init_seg, init_gsbArchFroms, archTree)
                    modifyArch_addMedium(archTree)
                    (gsb_mux_fanin, imux_mux_fanin) = generateTwoStageMux(archTree)
                    #writeArch(archTree["root"].getroot(), "./tt/test.xml" + str(try_count))
                    #try_count += 1
                #T = T_end
                #writeArch(archTree["root"].getroot(), "./test.xml")
                #break
                
                logger.info( "\tCurrent segs :")
                for s in init_seg:
                    s.show(logger)

                # run the vtr to evaluate new cost
                #originTree = copy.deepcopy(archTree)
                #clearWorkDir(caller, True)
                archfile_count = caller.task_dir + "/" + caller.run_dir[-1] + "/optimizeArchs/" + archName + "/" + str(Count)
                archfile = archfile_count + "/" + archName
                if os.path.exists(archfile_count):
                    #raise SeekerError("archfile count " + str(Count) + " dir is already exist")
                    os.system("rm -rf " + archfile_count)
                    os.system("mkdir " + archfile_count)
                else:
                    os.system("mkdir " + archfile_count)
                writeArch(archTree["root"].getroot(), archfile)
                #writeArch(archTree["root"].getroot(), "./test.xml")
                #T = T_end
                #break
                '''
                logger.info( "\n\tCount : " + str(Count))
                logger.info( "\tCurrent segs :")
                for s in init_seg:
                    s.show(logger)
                print( "\nCount : " + str(Count))
                pool = multiprocessing.Pool(processes = caller.processes)
                for circuit in caller.circuits:
                    workdir = archfile_count + "/" + circuit
                    pool.apply_async(func=run_vpr_task,args=(caller, workdir, archfile, archName, circuit, chan_width, False,))
                pool.close()
                pool.join()
                new_cost, new_mean_delay, new_mean_area, new_mean_area_delay = evaluateCost(archfile_count, caller, baseInfo, logger, False)
                #modifyArch_V2(init_seg, originTree, caller.task_dir + "/" + caller.run_dir[-1] + "/optimizeArchs/" + archName + "/" + archName)
                #new_cost, new_mean_delay, new_mean_area, new_mean_area_delay = evaluateCost_test(optWorkDir, T)
                if new_cost == None and new_mean_delay == None and new_mean_area == None and new_mean_area_delay == None:
                    logger.info("\tThe " + str(innerCount) + " Inner iteration (unroutable) ")
                    # keep the origin segment distribution
                    init_seg = copy.deepcopy(_prev_segs)
                    init_gsbArchFroms = copy.deepcopy(_prev_froms)
                    chan_width = _prev_chan_width
                    Count += 1
                    continue  # 如果有布不通的直接保持原样，跳到下一次迭代
                if new_cost < best_cost :
                    best_segs = copy.deepcopy(init_seg)
                    best_arch_count = Count
                    best_chan_width = chan_width
                    best_cost = new_cost
                    best_mean_delay = new_mean_delay
                    best_mean_area = new_mean_area
                    best_mean_area_delay = new_mean_area_delay

                
                
                df = new_cost - cost
                accept_state = "Rejected"
                # cost larger
                if df >= 0 :
                    r = random.random()
                    if math.exp(-df/(k * T)) <= r:
                        # keep the origin segment distribution
                        init_seg = copy.deepcopy(_prev_segs)
                        init_gsbArchFroms = copy.deepcopy(_prev_froms)
                        chan_width = _prev_chan_width
                    else:
                        # accept the new segment distribution
                        cost = new_cost
                        mean_delay = new_mean_delay
                        mean_area = new_mean_area
                        mean_area_delay = new_mean_area_delay
                        accept_rate += 1
                        accept_state = "Accepted"
                        
                else:
                # cost smaller,  accept the new segment distribution
                    cost = new_cost
                    mean_delay = new_mean_delay
                    mean_area = new_mean_area
                    mean_area_delay = new_mean_area_delay
                    accept_rate += 1
                    accept_state = "Accepted"


                loop_end_time = datetime.datetime.now()
                if (loop_end_time-loop_start_time).seconds > 600 :
                    time =  str(round((loop_end_time-loop_start_time).seconds/60.0,2)) + "min" 
                else :
                    time = str((loop_end_time-loop_start_time).seconds) + "s"
                logger.info("\tThe " + str(innerCount) + " Inner iteration (" + accept_state + "):      cost: " + str(cost) + "   time :(" + time + ")     mean delay (" + str(mean_delay) + "%)")
                logger.info("\t\tmean area (" + str(mean_area) +"%)"  + "   mean area-delay (" + str(mean_area_delay) + "%)")

                statusfile = open(logdir + "/SA_para.txt", "w")
                statusfile.write("T:" + str(T))
                statusfile.write("\ninnerCount:" + str(innerCount))
                statusfile.write("\nouterCount:" + str(outerCount))
                statusfile.write("\nCount:" + str(Count))
                statusfile.write("\ncost:" + str(cost))
                statusfile.write("\nmean_delay:" + str(mean_delay))
                statusfile.write("\nmean_area:" + str(mean_area))
                statusfile.write("\nmean_area_delay:" + str(mean_area_delay))
                statusfile.write("\naccept_rate:" + str(accept_rate))
                statusfile.write("\naccept_state:" + str(accept_state))
                statusfile.write("\nchan_width:" + str(chan_width))

                statusfile.write("\nbest_cost:" + str(best_cost))
                statusfile.write("\nbest_mean_delay:" + str(best_mean_delay))
                statusfile.write("\nbest_mean_area:" + str(best_mean_area))
                statusfile.write("\nbest_mean_area_delay:" + str(best_mean_area_delay))
                statusfile.write("\nbest_arch_Count:" + str(best_arch_count))
                statusfile.write("\nbest_chan_width:" + str(best_chan_width))
                statusfile.close()
                #archive(optWorkDir, optArchiveDir, Count, caller.circuits)

                innerCount += 1
                Count += 1
                
            accept_rate = accept_rate * 1.0 / maxIter
            T = Update_t(T, alpha, accept_rate)
            outerCount += 1
            logger.info(str(outerCount) +  " Outer iteration :     T (" + str(T) + ")  cost (" + str(cost) + ")     accept_rate: (" + str(accept_rate) + ")"  )

        logger.info("\n\n The result of SA algorithm for : " + archName + " in routing chan_width " + str(chan_width))    
        logger.info("SA quit in segs : ")
        for s in init_seg:
            s.show(logger)
        logger.info("SA quit in cost : " + str(cost) )
        logger.info("SA quit in mean delay : " + str(mean_delay) + "%")
        logger.info("SA quit in mean area : " + str(mean_area) + "%")
        logger.info("SA quit in mean area : " + str(mean_area_delay) + "%")
        logger.info("\n\nBest Segs during SA : ")
        for s in best_segs:
            s.show(logger)
        logger.info("Best Cost during SA: " + str(best_cost) )
        logger.info("Best mean delay during SA: " + str(best_mean_delay)  + "%")
        logger.info("Best mean area during SA: " + str(best_mean_area)  + "%")
        logger.info("Best mean area-delay during SA: " + str(best_mean_area_delay)  + "%")
                
            
    SA_end_time = datetime.datetime.now()
    if (SA_end_time-SA_start_time).seconds > 600 :
        time =  str((SA_end_time-SA_start_time).days) + " day " + str(round((SA_end_time-SA_start_time).seconds/60.0,2)) + " min" 
    else :
        time = str((SA_end_time-SA_start_time).seconds) + "s"
    logger.info("\nSA running time : " + time)
                  

