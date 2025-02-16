# -*- coding: utf-8 -*-

import os.path
import sys
import re
import random
import math
import copy
import datetime

from optparse import OptionParser
import multiprocessing

from functools import reduce

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
from xml.dom import minidom
from itertools import permutations

class ArchError(Exception):
    pass

def prettify2(elem):
    """
        Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8').decode("utf-8")
    rough_string = re.sub(">\s*<", "><", rough_string)
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="\t", encoding="utf-8")

def readArch2(archfile):
    archTree = {}
    archTree["root"] = ET.parse(archfile)
    return archTree

def writeArch2(elem, outfile):
    f = open(outfile, "wb+")
    f.write(prettify2(elem))
    f.close()
class Seg_inf():
    def __init__(self, segElem = None):
        if segElem != None:
            self.name = segElem.get("name")
            self.length = segElem.get("length")
            self.freq = segElem.get("freq")
            self.total_froms = None
            self.switchpoint = 0
        else:
            self.name = None
            self.length = None
            self.freq = 0
            self.total_froms = None
class From_inf():
    def __init__(self, fromElem = None):
        if fromElem != None:
            self.type = fromElem.get("type")
            self.name = fromElem.get("name")
            self.num_foreach = int(fromElem.get("num_foreach", 1))
            if fromElem.get("total_froms") == None:
                print(self.type)
                print(self.name)
                print(str(self.num_foreach))
            self.total_froms = int(fromElem.get("total_froms"))
            self.pin_types = fromElem.get("pin_types", "")
            self.reuse = int(fromElem.get("reuse", 1))
            self.switchpoint = int(fromElem.get("switchpoint", 0))

        else:
            self.type = None
            self.name = None
            self.num_foreach = 0
            self.total_froms = 0
            self.pin_types = ""
            self.reuse = 1
            self.switchpoint = 0

    def __eq__(self, _from):
        if self.type == _from.type and \
           self.name == _from.name and \
           self.num_foreach == _from.num_foreach and \
           self.total_froms == _from.total_froms and \
           self.pin_types == _from.pin_types and \
           self.reuse == _from.reuse and \
           self.switchpoint == _from.switchpoint :
           return True
        
        return False

    def show(self, logger=None):
        if logger == None:
            print("\t\tfrom_type: " + self.type + "; " + "from_name: " + self.name + "; " + "num_foreach: " + str(self.num_foreach) + "; " + "total_froms: " + str(self.total_froms) + "; " + "reuse: " + str(self.reuse) + "; " + "pin_types:" + self.pin_types + "; " + "switchpoint:" + str(self.switchpoint))
        else:
            logger.info("\t\tfrom_type: " + self.type + "; " + "from_name: " + self.name + "; " + "num_foreach: " + str(self.num_foreach) + "; " + "total_froms: " + str(self.total_froms) + "; " + "reuse: " + str(self.reuse) + "; " + "pin_types:" + self.pin_types + "; " + "switchpoint:" + str(self.switchpoint))


class TwoStageMuxFrom_inf():
    def __init__(self, _type, _name, _from_details, _switchpoint = 0):
        self.type = _type
        self.name = _name
        self.from_details = _from_details
        self.switchpoint = _switchpoint

    def show(self):
        print("\t\tfrom_type=" + self.type + "\t" + "from_name=" + self.name + "\t"
              "from_details=" + self.from_details + "\t" + "switchpoint=" + str(self.switchpoint))
    
    def to_arch(self, mux_from_arch):
        a_from = ET.SubElement(mux_from_arch, "from")
        a_from.set("type", self.type)
        a_from.set("name", self.name)
        a_from.set("from_detail", self.from_details)
        a_from.set("switchpoint", str(self.switchpoint))

    def count_detail_nums(self):
        return len(self.from_details.split(" "))
        

def assignNumforeach_gsb(num_foreach, offset):
    result = [0, 0, 0, 0]
    for k in range(num_foreach):
        result[(k + offset) % 4] += 1
    return result


def random_pick(itemList, probs):
    x = random.uniform(0,1)
    c_prob = 0.0
    for item, prob in zip(itemList, probs):
        c_prob += prob
        if x < c_prob: 
            break
    return item

def assignNumforeach_imux(num_foreach, offset):
    result = [0 for i in range(8)]
    for k in range(int(num_foreach)):
        result[(k + offset) % 8] += 1
    return result
def assignNumforeach_gsb_v200(num_foreach, offset):
    result = [0 for i in range(4)]
    for k in range(int(num_foreach)):
        result[(k + offset) % 4] += 1
    offset = (int(num_foreach) + offset) % 4
    return result, offset

def assign_firstStageMux_from(segs, seg_from, mux_nums, offset, assign_from, assignNumforeachOffset,
                                to_track_to_first_mux, StageMuxFroms, length_reuse_threshold, first_mux_assign):
    ind2dir = ["W", "N", "E", "S"]
    type_str = seg_from.type
    name_str = seg_from.name
    if type_str == "seg":
        if True:
            for i in range(mux_nums):
                for j in range(4):
                    mux_name = "mux-" + str(offset + i) + "-" + str(j)
                    dir_str = ind2dir[j]
                    from_details = ""
                    for k in range(seg_from.num_foreach):
                        from_details = from_details + " " + dir_str + str(assign_from[1][(assign_from[0] + k) % seg_from.total_froms])  
                    
                    if first_mux_assign:
                        to_track_to_first_mux[i].append(mux_name)

                    from_details = from_details.strip()
                    if from_details == "":
                        continue

                    stagemuxfrom = TwoStageMuxFrom_inf(
                        type_str, name_str, from_details, seg_from.switchpoint)
                    if mux_name in StageMuxFroms:
                        StageMuxFroms[mux_name].append(stagemuxfrom)
                    else:
                        StageMuxFroms[mux_name] = [stagemuxfrom]  
                    
                assign_from[0] = (assign_from[0] + seg_from.num_foreach) % seg_from.total_froms

    elif type_str == "omux":
        for i in range(mux_nums):
            omux_each_mux = assignNumforeach_gsb(seg_from.num_foreach, assignNumforeachOffset)
            for j in range(4):
                mux_name = "mux-" + str(offset + i) + "-" + str(j)
                from_details = ""
                for k in range(min(1,omux_each_mux[j])):
                    from_details = 'OG_' + str(assign_from[1][(assign_from[0] + k)% seg_from.total_froms])
                assign_from[0] = (assign_from[0] + omux_each_mux[j]) % seg_from.total_froms
                        
                if first_mux_assign:
                    to_track_to_first_mux[i].append(mux_name)

                from_details = from_details.strip()
                if from_details == "":
                    continue

                stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_details)
                if mux_name in StageMuxFroms:
                    StageMuxFroms[mux_name].append(stagemuxfrom)
                else:
                    StageMuxFroms[mux_name] = [stagemuxfrom]
                        
    elif type_str == "pb":
        for i in range(mux_nums):
            pb_each_mux = assignNumforeach_gsb(seg_from.num_foreach, assignNumforeachOffset)
            for j in range(4):
                mux_name = "mux-" + str(offset + i) + "-" + str(j)
                from_details = ""
                for k in range(pb_each_mux[j]):
                    from_details = from_details + " " + str(assign_from[1][(assign_from[0] + k)% seg_from.total_froms])
                assign_from[0] = (assign_from[0] + pb_each_mux[j]) % seg_from.total_froms
                        
                if first_mux_assign:
                   to_track_to_first_mux[i].append(mux_name)

                from_details = from_details.strip()
                if from_details == "":
                    continue

                stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_details)
                if mux_name in StageMuxFroms:
                    StageMuxFroms[mux_name].append(stagemuxfrom)
                else:
                    StageMuxFroms[mux_name] = [stagemuxfrom]
                        

def assign_firstStageMux_from_v200(segs, seg_from, mux_nums, seg_from_assign, offset, assign_from, assignNumforeachOffset,
                                to_track_to_first_mux, StageMuxFroms, length_reuse_threshold, first_mux_assign, segs_times):
    ind2dir = ["W", "N", "E", "S"]
    type_str = "seg"
    name_str = seg_from.name
    
    if type_str == "seg":
        if True:
            # print(name_str + ':' + str(seg_from_assign))
            # print(seg_from_assign)
            # print(offset)
            for i in range(mux_nums):
                # four direction, one group (four muxes) all in one direction
                for j in range(4):

                    # one group contains four muxes, assign by segs_times
                    for k in range(4):

                        mux_name = "mux_" + str(i *16 + j * 4 + k)
                        dir_str = ind2dir[j]
                        from_details = ""
                        for l in range(seg_from_assign[k]):
                            from_details = from_details + " " + dir_str + str(assign_from[1][(assign_from[0] + l) % seg_from.total_froms])  
                        assign_from[0] = (assign_from[0] + seg_from_assign[k]) % seg_from.total_froms
                    
                        # if first_mux_assign:
                        #     to_track_to_first_mux[i].append(mux_name)

                        from_details = from_details.strip()
                        if from_details == "":
                            continue

                        stagemuxfrom = TwoStageMuxFrom_inf(
                            type_str, name_str, from_details, 0)
                        if mux_name in StageMuxFroms:
                            StageMuxFroms[mux_name].append(stagemuxfrom)
                        else:
                            StageMuxFroms[mux_name] = [stagemuxfrom]  
                    
                    
def assign_firstStageMux_pin_from_v200(segs, pin_froms, mux_nums, seg_from_assign, offset_first, assign_from, assignNumforeachOffset_first,
                                to_track_to_first_mux, StageMuxFroms, length_reuse_threshold, first_mux_assign, segs_times):
    if len(pin_froms) > 1:
        for i in range(mux_nums):
            pin_from = pin_froms[i % len(pin_froms)]
            type_str = pin_from.type
            name_str = pin_from.name
            mux_name = "mux_" + str(i)

            if (type_str == 'pb'):
                from_detail = pin_from.pin_types + ":" + str(assign_from[pin_from.pin_types])
                assign_from[pin_from.pin_types] = (assign_from[pin_from.pin_types] + 1) % 8
                stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_detail)
                if mux_name in StageMuxFroms:
                    StageMuxFroms[mux_name].append(stagemuxfrom)
                else:
                    StageMuxFroms[mux_name] = [stagemuxfrom]

            elif (type_str == 'cas'):
                from_detail = "SW_CAS" + str(assign_from["SW_CAS"])
                assign_from["SW_CAS"] = (assign_from["SW_CAS"] + 1) % 8
                stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_detail)
                if mux_name in StageMuxFroms:
                    StageMuxFroms[mux_name].append(stagemuxfrom)
                else:
                    StageMuxFroms[mux_name] = [stagemuxfrom]


        
    # elif type_str == "omux":
    #     for i in range(mux_nums):
    #         omux_each_mux = assignNumforeach_gsb(seg_from.num_foreach, assignNumforeachOffset)
    #         for j in range(4):
    #             mux_name = "mux-" + str(offset + i) + "-" + str(j)
    #             from_details = ""
    #             for k in range(min(1,omux_each_mux[j])):
    #                 from_details = 'OG_' + str(assign_from[1][(assign_from[0] + k)% seg_from.total_froms])
    #             assign_from[0] = (assign_from[0] + omux_each_mux[j]) % seg_from.total_froms
                        
    #             if first_mux_assign:
    #                 to_track_to_first_mux[i].append(mux_name)

    #             from_details = from_details.strip()
    #             if from_details == "":
    #                 continue

    #             stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_details)
    #             if mux_name in StageMuxFroms:
    #                 StageMuxFroms[mux_name].append(stagemuxfrom)
    #             else:
    #                 StageMuxFroms[mux_name] = [stagemuxfrom]
                        
    # elif type_str == "pb":
    #     for i in range(mux_nums):
    #         pb_each_mux = assignNumforeach_gsb(seg_from.num_foreach, assignNumforeachOffset)
    #         for j in range(4):
    #             mux_name = "mux-" + str(offset + i) + "-" + str(j)
    #             from_details = ""
    #             for k in range(pb_each_mux[j]):
    #                 from_details = from_details + " " + str(assign_from[1][(assign_from[0] + k)% seg_from.total_froms])
    #             assign_from[0] = (assign_from[0] + pb_each_mux[j]) % seg_from.total_froms
                        
    #             if first_mux_assign:
    #                to_track_to_first_mux[i].append(mux_name)

    #             from_details = from_details.strip()
    #             if from_details == "":
    #                 continue

    #             stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_details)
    #             if mux_name in StageMuxFroms:
    #                 StageMuxFroms[mux_name].append(stagemuxfrom)
    #             else:
    #                 StageMuxFroms[mux_name] = [stagemuxfrom]

def assign_secondStageMux_from(segs, seg_from, mux_nums, assign_from, assignNumforeachOffset,
                                to_seg_name, StageMuxFroms, length_reuse_threshold, first_mux_assign):
    ind2dir = ["W", "N", "E", "S"]
    type_str = seg_from.type
    name_str = seg_from.name
    if type_str == "seg":
        if True:
            for i in range(mux_nums):
                #from_index_offset = assign_from[0] * 4
                #print(assign_from[1])
                #print(assign_from[0] % seg_from.total_froms)
                #print((assign_from[0] + seg_from.num_foreach) % seg_from.total_froms + 1)
                index_tmp = assign_from[1]*2
                start = assign_from[0] % seg_from.total_froms
                end = (assign_from[0] + seg_from.num_foreach) % seg_from.total_froms + 1
                if start < end:
                    index_candi = index_tmp[start:end]
                else:
                    index_candi = index_tmp[start:end + seg_from.total_froms]

                #index_candi = assign_from[1][assign_from[0] % seg_from.total_froms : (assign_from[0] + seg_from.num_foreach) % seg_from.total_froms + 1]
                
                for j in range(4):
                    mux_name = ind2dir[j] + "-b" + str(i)
                    to_track = ind2dir[j] + str(i)
                    second_mux = (mux_name, to_seg_name, to_track)
                    #dir_str = ind2dir[j]
                    dir_str_vec = ind2dir[j] + ind2dir[(j + 1) % 4] + ind2dir[(j - 1) % 4] + ind2dir[(j + 2) % 4]
                    #from_candidate = map(lambda x, y: str(x) + str(y), dir_str_vec, assign_from[1])
                    #print(index_candi)
                    from_candidate = reduce(lambda x, y: [str(x) + str(y) for x in dir_str_vec for y in index_candi ], dir_str_vec)
                    #print(from_candidate)
                    from_details = ""
                    for k in range(seg_from.num_foreach):
                        from_details = from_details + " " + from_candidate[k % len(from_candidate)]
                    from_details = from_details.strip()
                    if from_details == "":
                        continue

                    stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_details, seg_from.switchpoint)
                    if second_mux in StageMuxFroms:
                        StageMuxFroms[second_mux].append(stagemuxfrom)
                    else:
                        StageMuxFroms[second_mux] = [stagemuxfrom]

                #from_index_offset = (from_index_offset + seg_from.num_foreach) % len(from_candidate)
                #print(assign_from[0])
                #assign_from[0] = int((assign_from[0] + math.ceil(seg_from.num_foreach / 4)) % seg_from.total_froms)
                assign_from[0] = (assign_from[0] + seg_from.num_foreach) % seg_from.total_froms
                #print(assign_from[0])


    elif type_str == "omux":
        for i in range(mux_nums):
            omux_each_mux = assignNumforeach_gsb(seg_from.num_foreach, assignNumforeachOffset)
            for j in range(4):
                mux_name = ind2dir[j] + "-b" + str(i)
                to_track = ind2dir[j] + str(i)
                second_mux = (mux_name, to_seg_name, to_track)
                from_details = ""
                for k in range(omux_each_mux[j]):
                    from_details = from_details + " " + str(assign_from[1][(assign_from[0] + k)% seg_from.total_froms])
                assign_from[0] = (assign_from[0] + omux_each_mux[j]) % seg_from.total_froms
                        
                from_details = from_details.strip()
                if from_details == "":
                    continue

                stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_details)
                if second_mux in StageMuxFroms:
                    StageMuxFroms[second_mux].append(stagemuxfrom)
                else:
                    StageMuxFroms[second_mux] = [stagemuxfrom]

    elif type_str == "pb":
        for i in range(mux_nums):
            pb_each_mux = assignNumforeach_gsb(seg_from.num_foreach, assignNumforeachOffset)
            for j in range(4):
                mux_name = ind2dir[j] + "-b" + str(i)
                to_track = ind2dir[j] + str(i)
                second_mux = (mux_name, to_seg_name, to_track)
                from_details = ""
                for k in range(pb_each_mux[j]):
                    from_details = from_details + " " + str(assign_from[1][(assign_from[0] + k)% seg_from.total_froms])
                assign_from[0] = (assign_from[0] + pb_each_mux[j]) % seg_from.total_froms
                        
                from_details = from_details.strip()
                if from_details == "":
                    continue

                stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_details)
                if second_mux in StageMuxFroms:
                    StageMuxFroms[second_mux].append(stagemuxfrom)
                else:
                    StageMuxFroms[second_mux] = [stagemuxfrom]
                   

# assign connection of two stage mux in gsb
def assignTwoStageMux_gsb(segs, gsb, to_mux_nums, gsb_mux_fanin, gsbElem):
    ind2dir = ["W", "N", "E", "S"]
    firstStageMuxFroms = {}
    SecondStageMuxFroms_firstStage = {}
    SecondStageMuxFroms_noStage = {}
    length_reuse_threshold = 6
    offset_first = 0
    #offset_second = 0
    from_type_offset = {}
    for to_seg_name, mux_nums in to_mux_nums.items():
        seg_froms = gsb[to_seg_name]

        to_track_to_first_mux = []
        for i in range(mux_nums):
            to_track_to_first_mux.append([])
        first_mux_assign = True
        assignNumforeachOffset_first = 0
        assignNumforeachOffset_second = 0
        for seg_from in seg_froms:
            #seg_from.show()
            type_str = seg_from.type
            
            from_index = []
            if type_str == "pb":
                pin_types = seg_from.pin_types.split(" ")
                for idx in range(8):
                    for i_pin in range(len(pin_types)):
                        from_index.append(pin_types[i_pin] + ":" + str(idx))
            else:
                from_index = list(range(seg_from.total_froms))

            #first stage mux
            assign_from = [0, from_index]
            if seg_from.name in from_type_offset:
                assign_from = [from_type_offset[seg_from.name], from_index]

            if seg_from.reuse:
                assign_firstStageMux_from(segs, seg_from, mux_nums, offset_first, assign_from, assignNumforeachOffset_first,
                                        to_track_to_first_mux, firstStageMuxFroms, length_reuse_threshold, first_mux_assign)
                if type_str == "pb" or type_str == "omux":
                    assignNumforeachOffset_first = (assignNumforeachOffset_first + seg_from.num_foreach) % 4
            else:
                #print(SecondStageMuxFroms_noStage)
                #print(assign_from[0])
                assign_secondStageMux_from(segs, seg_from, mux_nums, assign_from, assignNumforeachOffset_second,
                                           to_seg_name, SecondStageMuxFroms_noStage, length_reuse_threshold, first_mux_assign)
                if type_str == "pb" or type_str == "omux":
                    assignNumforeachOffset_second = (assignNumforeachOffset_second + seg_from.num_foreach) % 4
            
            first_mux_assign = False

            #if type_str == "seg":
            from_type_offset[seg_from.name] = assign_from[0]

            #print(from_seg_offset)
        offset_first += mux_nums


        #second stage mux
        for i_t in range(mux_nums):
            for i_dir in range(4):
                mux_name = ind2dir[i_dir] + "-b" + str(i_t)
                to_track = ind2dir[i_dir] + str(i_t)
                second_mux = (mux_name, to_seg_name, to_track)
                first_mux = copy.deepcopy(to_track_to_first_mux[i_t])
                if first_mux:
                    del(first_mux[(i_dir + 2) % 4])
                first_mux.append('mux-' + str((i_t + 1) % (20)) + '-' + str(i_dir))
                SecondStageMuxFroms_firstStage[second_mux] = first_mux
        

    #print(SecondStageMuxFroms_noStage)
    gsb_two_stage = ET.SubElement(gsbElem, "multistage_muxs")
    first_stage = ET.SubElement(gsb_two_stage, "first_stage")
    first_stage.set("switch_name", "only_mux")
    second_stage = ET.SubElement(gsb_two_stage, "second_stage")

    firstStageMuxFroms = sorted(firstStageMuxFroms.items(),
                                key = lambda x: int( re.search(r'mux-(.*)-(.*)', x[0], re.M | re.I).group(1) )
                                )
    
    for (k, v) in firstStageMuxFroms:
        mux_from = ET.SubElement(first_stage, "mux")
        mux_from.set("name", k)
        fanin = 0
        #print("\tmux_name" + k)
        for vv in v:
            #vv.show()
            vv.to_arch(mux_from)
            fanin += vv.count_detail_nums()
        gsb_mux_fanin["first"][k] = fanin
    
    for k, v in SecondStageMuxFroms_firstStage.items():
        mux_from = ET.SubElement(second_stage, "mux")
        mux_from.set("name", k[0])
        mux_from.set("to_seg_name", k[1])
        mux_from.set("to_track", k[2])

        fanin = 0
        fanin_key = k[1] + ":" + k[2]

        if v:
            a_from = ET.SubElement(mux_from, "from")
            a_from.set("mux_name", " ".join(v))
            fanin += len(v)


        if k in SecondStageMuxFroms_noStage:
            v2 = SecondStageMuxFroms_noStage[k]
            #print(v2)
            for vv in v2:
                #vv.show()
                vv.to_arch(mux_from)
                fanin += vv.count_detail_nums()
        gsb_mux_fanin["second"][fanin_key] = (fanin, str(segs[k[1]]))


# assign connection of two stage mux in gsb
def assignTwoStageMux_gsb_v200(segs, gsb, to_mux_nums, gsb_mux_fanin, gsbElem, segs_freq, segElems, pin_froms):
    # segs_freq is the dic whose key is the seg_name and the value is the fraction of each seg to the total seg num
    ind2dir = ["W", "N", "E", "S"]
    firstStageMuxFroms = {}
    SecondStageMuxFroms_firstStage = {}
    CasStageMUXFroms_firstStage = {}
    SecondStageMuxFroms_noStage = {}
    length_reuse_threshold = 6
    offset_first = 0
    #offset_second = 0
    from_type_offset = {}
    segs_times = {}
    seg_check = 0
    min_times = 16
    min_seg = []
    a = [0, 1, 2, 3]
    dir_type_comb = list(permutations(a, 4))
    # print(dir_type_comb)

    # assign the times that each seg appears 
    for seg_name in segs_freq.keys():
        seg_times = int(12 * segs_freq[seg_name])
        segs_times[seg_name] = seg_times
        seg_check = seg_check + segs_times[seg_name]
        if (min_times == seg_times):
            min_seg.append(seg_name)
        if (min_times > seg_times):
            min_times = seg_times
            min_seg = [seg_name]

    ind = 0
    while(seg_check != 12):
        seg_name = min_seg[ind]
        segs_times[seg_name] = segs_times[seg_name] + 1
        seg_check = seg_check + 1
        ind = (ind + 1) % len(min_seg)
    for to_seg_name, mux_nums in to_mux_nums.items():
        seg_froms = gsb[to_seg_name]

        to_track_to_first_mux = []
        for i in range(mux_nums):
            to_track_to_first_mux.append([])
        first_mux_assign = True
        assignNumforeachOffset_first = 0
        assignNumforeachOffset_second = 0

    seg_froms = gsb['l1']

    # assign the seg drives
    offset_first = 0
    is_first = 1
    for seg in segElems:
            #seg_from.show()
        from_index = []
        from_index = list(range(seg.total_froms))

        # first stage mux
        assign_from = [0, from_index]
        if seg.name in from_type_offset:
            assign_from = [from_type_offset[seg.name], from_index]
        if 1:
            seg_from_assign, offset_first = assignNumforeach_gsb_v200(segs_times[seg.name], offset_first)
            # print(seg_from.name)
            assign_firstStageMux_from_v200(segs, seg, 8, seg_from_assign, offset_first, assign_from, assignNumforeachOffset_first,
                                to_track_to_first_mux, firstStageMuxFroms, length_reuse_threshold, first_mux_assign, segs_times)
            # if type_str == "pb" or type_str == "omux":
            #     assignNumforeachOffset_first = (assignNumforeachOffset_first + seg_from.num_foreach) % 4
        else:
                #print(SecondStageMuxFroms_noStage)
                #print(assign_from[0])
            assign_secondStageMux_from(segs, seg, mux_nums, assign_from, assignNumforeachOffset_second,
                                    to_seg_name, SecondStageMuxFroms_noStage, length_reuse_threshold, first_mux_assign)
            is_first = 0
            # if type_str == "pb" or type_str == "omux":
            #     assignNumforeachOffset_second = (assignNumforeachOffset_second + seg_from.num_foreach) % 4
            

            #if type_str == "seg":
        from_type_offset[seg.name] = assign_from[0]
    
            #print(from_seg_offset)
    # assign the plb, omux drives
    assign_from = {}
    if len(pin_froms) > 0:
        for pin_from in pin_froms:
            if pin_from.type == "pb":
                assign_from[pin_from.pin_types] = 0
            elif pin_from.type == "omux":
                assign_from["OG"] = 0
            elif pin_from.type == "cas":
                assign_from["SW_CAS"] = 0
        pin_from = pin_froms[0]
        print("gsb fb from:")
        pin_from.show()
        if pin_from.reuse:
            assign_firstStageMux_pin_from_v200(segs, pin_froms, 128, seg_from_assign, offset_first, assign_from, assignNumforeachOffset_first,
                                to_track_to_first_mux, firstStageMuxFroms, length_reuse_threshold, first_mux_assign, segs_times)




    mux_type_dir = {}
    type_offset_dir = {}
    for i in range(128):
        dir_type = ind2dir[i % 16 // 4]
        type_ind = i % 4
        mux_type = dir_type + str(type_ind)
        if (mux_type) not in mux_type_dir:
            mux_type_dir[mux_type] = [i]
            type_offset_dir[mux_type] = 0
        else:
            mux_type_dir[mux_type].append(i)


        # second stage mux
    SecondStageMuxFroms_noStage_seg = {}
    mux_th = 0
    is_first = 1
    for to_seg_name, mux_nums in to_mux_nums.items():
        for i_t in range(mux_nums):
            for i_dir in range(4):
                mux_name = ind2dir[i_dir] + "-b" + str(i_t)
                to_track = ind2dir[i_dir] + str(i_t)
                second_mux = (mux_name, to_seg_name, to_track)
                if (i_t > mux_nums * 2 // 3) and (is_first == 1):
                    drive_for_neighbor = []
                    from_detail = ""
                    for j in range(4):
                        if i_dir != j:
                            from_detail = from_detail + ' ' + ind2dir[j] + str(i_t)
                    drive_for_neighbor.append(TwoStageMuxFrom_inf("seg", to_seg_name, from_detail))
                    from_detail = "OG_1ST_" + str((i_t + i_dir) % 4) + " OG_1ST_" + str((i_t + i_dir) % 4 + 4) + " OG_1ST_" + str((i_t + i_dir) % 4 + 8)
                    drive_for_neighbor.append(TwoStageMuxFrom_inf("omux", "oxbar", from_detail))
                    SecondStageMuxFroms_noStage_seg[second_mux] = drive_for_neighbor
                else:
                    first_mux = []
                    dir_type = dir_type_comb[mux_th % 24]
                    # if (mux_th == 0):
                    #     print(dir_type[1])
                    for im_dir in range(4):
                        mux_type = ind2dir[im_dir] + str(dir_type[im_dir])
                        # if first_mux:
                        #     del(first_mux[(i_dir + 2) % 4])
                        offset = type_offset_dir[mux_type] % len(mux_type_dir[mux_type])
                        type_offset_dir[mux_type] += 1
                        first_mux.append('mux_' + str(mux_type_dir[mux_type][offset]))
                    # if (mux_th == 0):
                    #     print(first_mux)
                    mux_th += 1
                    SecondStageMuxFroms_firstStage[second_mux] = first_mux
        is_first = 0
        
    # generate the cascade mux

    for i in range(8):
        mux_name = "SW_CAS" + str(i)
        cas_mux = (mux_name)
        first_mux = []
        for i_b in range(4):
            mux_th = 16 * i + i_b * 4 + (i + i_b) % 4
            first_mux.append("mux_" + str(mux_th))
        CasStageMUXFroms_firstStage[mux_name] = first_mux

    #print(SecondStageMuxFroms_noStage)
    gsb_two_stage = ET.SubElement(gsbElem, "multistage_muxs")
    first_stage = ET.SubElement(gsb_two_stage, "first_stage")
    first_stage.set("switch_name", "only_mux")
    second_stage = ET.SubElement(gsb_two_stage, "second_stage")
    cas_stage = ET.SubElement(gsb_two_stage, "cas_stage")
    cas_stage.set("switch_name", "only_mux")

    # firstStageMuxFroms = sorted(firstStageMuxFroms.items(),
    #                             key = lambda x: int( re.search(r'mux-(.*)-(.*)', x[0], re.M | re.I).group(1) )
    #                             )
    
    for k, v in firstStageMuxFroms.items():
        mux_from = ET.SubElement(first_stage, "mux")
        mux_from.set("name", k)
        fanin = 0
        #print("\tmux_name" + k)
        for vv in v:
            #vv.show()
            vv.to_arch(mux_from)
            fanin += vv.count_detail_nums()
        gsb_mux_fanin["first"][k] = fanin
    
    for k, v in SecondStageMuxFroms_firstStage.items():
        mux_from = ET.SubElement(second_stage, "mux")
        mux_from.set("name", k[0])
        mux_from.set("to_seg_name", k[1])
        mux_from.set("to_track", k[2])

        fanin = 0
        fanin_key = k[1] + ":" + k[2]

        if v:
            a_from = ET.SubElement(mux_from, "from")
            a_from.set("mux_name", " ".join(v))
            fanin += len(v)


        if k in SecondStageMuxFroms_noStage:
            v2 = SecondStageMuxFroms_noStage[k]
            #print(v2)
            for vv in v2:
                #vv.show()
                vv.to_arch(mux_from)
                fanin += vv.count_detail_nums()
        gsb_mux_fanin["second"][fanin_key] = (fanin, str(segs[k[1]]))

    for k, v in SecondStageMuxFroms_noStage_seg.items():
        mux_from = ET.SubElement(second_stage, "mux")
        mux_from.set("name", k[0])
        mux_from.set("to_seg_name", k[1])
        mux_from.set("to_track", k[2])

        if v:
            for vv in v:
                vv.to_arch(mux_from)

    for k, v in CasStageMUXFroms_firstStage.items():
        mux_from = ET.SubElement(cas_stage, "mux")
        mux_from.set("name", k)

        if v:
            a_from = ET.SubElement(mux_from, "from")
            a_from.set("mux_name", " ".join(v))
            fanin += len(v)


def assign_firstStageMux_from_imux(segs, imux_from, assign_from, offset, assignNumforeachOffset, StageMuxFroms):
    ind2dir = ["W", "N", "E", "S"]
    type_str = imux_from.type
    name_str = imux_from.name
    if type_str == "seg":
        for i in range(4):
            seg_from_assign = assignNumforeach_imux(imux_from.num_foreach, offset)
            #if i == 0:
            #    print(seg_from_assign)
            five_from = []
            for j in range(1,5):
                #mux_name = "mux-" + str(j + i * 20)
                dir_str = ind2dir[j-1]
                from_details = ""
                for k in range(imux_from.num_foreach):
                    if k < seg_from_assign[j]:
                        from_details = from_details + " " + dir_str + str(assign_from[1][(assign_from[0] + k) % imux_from.total_froms])
                    else:
                        five_from.append(dir_str + str(assign_from[1][(assign_from[0] + k) % imux_from.total_froms]))
                from_details = from_details.strip()
                if from_details == "":
                    continue

                stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_details, imux_from.switchpoint)
                
                for i2 in range(0, 4):
                    mux_name = "mux-" + str(j + 5 * i2 + i * 20)
                    if mux_name in StageMuxFroms:
                        StageMuxFroms[mux_name].append(stagemuxfrom)
                    else:
                        StageMuxFroms[mux_name] = [stagemuxfrom]
                
            #mux_name = "mux-" + str(5 + i * 20)
            from_details = " ".join(five_from)
            if from_details == "":
                continue
            stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_details, imux_from.switchpoint)
            for i2 in range(0, 4):
                same_mux_name = "mux-" + str( 5 + i2 * 5 + i * 20)
                if same_mux_name in StageMuxFroms:
                    StageMuxFroms[same_mux_name].append(stagemuxfrom)
                else:
                    StageMuxFroms[same_mux_name] = [stagemuxfrom]

            assign_from[0] = (assign_from[0] + imux_from.num_foreach) % imux_from.total_froms

    elif type_str == "omux":
        for i in range(16):
            omux_each_mux = assignNumforeach_imux(imux_from.num_foreach/4.0, assignNumforeachOffset)
            for j in range(1,6):
                mux_name = "mux-" + str(j + i * 5)
                from_details = ""
                for k in range(min(1,omux_each_mux[j-1])):
                    from_details = "OG_" + str(assign_from[1][(assign_from[0] + k) % imux_from.total_froms])
                assign_from[0] = (assign_from[0] + omux_each_mux[j-1]) % imux_from.total_froms
                from_details = from_details.strip()
                if from_details == "":
                    continue

                stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_details)
                if mux_name in StageMuxFroms:
                    StageMuxFroms[mux_name].append(stagemuxfrom)
                else:
                    StageMuxFroms[mux_name] = [stagemuxfrom]

    elif type_str == "pb":
        for i in range(16):
            pb_each_mux = assignNumforeach_imux(imux_from.num_foreach/4.0, assignNumforeachOffset)
            for j in range(1,6):
                mux_name = "mux-" + str(j + i * 5)
                from_details = ""
                for k in range(pb_each_mux[j-1]):
                    from_details = from_details + " " + str(assign_from[1][(assign_from[0] + k) % imux_from.total_froms])
                assign_from[0] = (assign_from[0] + pb_each_mux[j-1]) % imux_from.total_froms
                from_details = from_details.strip()
                if from_details == "":
                    continue

                stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_details)
                if mux_name in StageMuxFroms:
                    StageMuxFroms[mux_name].append(stagemuxfrom)
                else:
                    StageMuxFroms[mux_name] = [stagemuxfrom]

    elif type_str == "imux":
        for i in range(16):
            imux_each_mux = assignNumforeach_imux(imux_from.num_foreach/4.0, assignNumforeachOffset)
            for j in range(1,6):
                mux_name = "mux-" + str(j + i * 5)
                from_details = ""
                for k in range(imux_each_mux[j-1]):
                    from_details = from_details + " " + str(assign_from[1][(assign_from[0] + k) % imux_from.total_froms])
                assign_from[0] = (assign_from[0] + imux_each_mux[j-1]) % imux_from.total_froms
                from_details = from_details.strip()
                if from_details == "":
                    continue

                stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_details)
                if mux_name in StageMuxFroms:
                    StageMuxFroms[mux_name].append(stagemuxfrom)
                else:
                    StageMuxFroms[mux_name] = [stagemuxfrom]

def assign_firstStageMux_from_imux_v200(segs, imux_from, assign_from, offset, assignNumforeachOffset, StageMuxFroms):
    ind2dir = ["E", "W", "S", "N"]
    pb_type = ["o", "q", "mux_o"]
    assign_from_pb = {"o": 0, "q": 0, "mux_o": 0}
    type_str = imux_from.type
    name_str = imux_from.name
    group_num = 8
    group_size = 8
    mux_size = 8
    dir_seq = []
    dir_seq.append('10010110011010011100001100111100')
    dir_seq.append('03232232123233230333322212222333')
    dir_seq.append('10320123103201231032012310320123')
    ind_seq = []
    # print(name_str)
    if type_str == "seg":
        for i in range(group_num):
            seg_from_assign = assignNumforeach_imux(imux_from.num_foreach, offset)
            # print(seg_from_assign)
            #if i == 0:
            #    print(seg_from_assign)
            for j in range(group_size):
                #mux_name = "mux-" + str(j + i * 20)
                dir_ind = int(dir_seq[j % 3][(i * group_size + j) % 32])
                dir_str = ind2dir[dir_ind]
                from_details = ""
                ind_int = assign_from[0]
                for k in range(imux_from.num_foreach):
                    if k < seg_from_assign[j]:

                        ind_int = ind_int + imux_from.total_froms // 2 - ((imux_from.total_froms + 1) % 2) * ((j + i * group_size + 1) % 2)
                        if (k == 0):
                            assign_from[0] = ind_int
                        dir_ind = int(dir_seq[k % 3][(i * group_size + j) % 32])
                        dir_str = ind2dir[dir_ind]
                        from_details = from_details + " " + dir_str + str(ind_int % imux_from.total_froms)
                from_details = from_details.strip()
                if from_details == "":
                    continue

                stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_details, imux_from.switchpoint)
                
                mux_name = "mux-" + str(j + i * group_size)
                if mux_name in StageMuxFroms:
                    StageMuxFroms[mux_name].append(stagemuxfrom)
                else:
                    StageMuxFroms[mux_name] = [stagemuxfrom]

                # assign_from[0] = ind_int
                

    elif type_str == "omux":
        for i in range(group_num):
            omux_each_mux = assignNumforeach_imux(imux_from.num_foreach, offset)
            # print(omux_each_mux)
            for j in range(group_size):
                mux_name = "mux-" + str(j + i * group_size)
                from_details = ""
                for k in range(omux_each_mux[j]):
                    if k:
                        from_details = from_details + ' '
                    from_details = from_details + "OG_" + str(assign_from[1][(assign_from[0] + k) % imux_from.total_froms])
                assign_from[0] = (assign_from[0] + omux_each_mux[j-1]) % imux_from.total_froms
                from_details = from_details.strip()
                if from_details == "":
                    continue

                stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_details)
                if mux_name in StageMuxFroms:
                    StageMuxFroms[mux_name].append(stagemuxfrom)
                else:
                    StageMuxFroms[mux_name] = [stagemuxfrom]

    elif type_str == "glb":
        for i in range(group_num):
            glb_each_mux = assignNumforeach_imux(imux_from.num_foreach, offset)
            # print(glb_each_mux)
            for j in range(group_size):
                mux_name = "mux-" + str(j + i * group_size)
                from_details = ""
                for k in range(glb_each_mux[j]):
                    if k:
                        from_details = from_details + ' '
                    from_details = from_details + "GLB" + str(assign_from[1][(assign_from[0] + k) % imux_from.total_froms])
                assign_from[0] = (assign_from[0] + glb_each_mux[j-1]) % imux_from.total_froms
                from_details = from_details.strip()
                if from_details == "":
                    continue

                stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_details)
                if mux_name in StageMuxFroms:
                    StageMuxFroms[mux_name].append(stagemuxfrom)
                else:
                    StageMuxFroms[mux_name] = [stagemuxfrom]

    elif type_str == "pb":
        from_ind = 0
        for i in range(group_num):
            pb_each_mux = assignNumforeach_imux(imux_from.num_foreach, offset)
            # print(pb_each_mux)
            for j in range(group_size):
                mux_name = "mux-" + str(j + i * group_size)
                from_details = ""
                # print(pb_each_mux[j])
                for k in range(pb_each_mux[j]):
                    if k:
                        from_details = from_details + ' '
                    type_now = pb_type[(from_ind + k) % 3]
                    from_details = from_details + type_now + ':' + str(assign_from_pb[type_now])
                    assign_from_pb[type_now] = (assign_from_pb[type_now] + 1) % imux_from.total_froms
                    # print(from_details)
                from_ind = from_ind + pb_each_mux[j]
                from_details = from_details.strip()
                if from_details == "":
                    continue

                stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_details)
                if mux_name in StageMuxFroms:
                    StageMuxFroms[mux_name].append(stagemuxfrom)
                else:
                    StageMuxFroms[mux_name] = [stagemuxfrom]


def assign_secondStageMux_from_imux(segs, imux_from, assign_from, StageMuxFroms):
    ind2dir = ["W", "N", "E", "S"]
    type_str = imux_from.type
    name_str = imux_from.name
    if type_str == "seg":
        i_ports = ("Ia", "Ib", "Ic", "Id", "Ie", "If", "Ig", "Ih")
        for i_p in range(len(i_ports)):
            for i_b in range(8):
                mux_name = "b" + str(i_b) + "-" + i_ports[i_p]
                to_pin = i_ports[i_p] + ":" + str(i_b)
                if i_b == 6:
                    mux_name = "x-" + i_ports[i_p]
                    to_pin = "x:" + str(i_p)
                elif i_b == 7:
                    mux_name = "i-" + i_ports[i_p]
                    to_pin = "i:" + str(i_p)
                second_mux = (mux_name, to_pin)
                
                from_candidate = reduce(lambda x, y: [str(x) + str(y) for y in assign_from[1] for x in ind2dir], ind2dir)
                # print("second stage assign")
                # print(from_candidate)
                from_details = ""
                from_details = from_details + " " + from_candidate[(assign_from[0]) % (imux_from.total_froms * 4)]
                from_details = from_details.strip()
                if from_details == "":
                    continue

                stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_details, imux_from.switchpoint)
                if second_mux in StageMuxFroms:
                    StageMuxFroms[second_mux].append(stagemuxfrom)
                else:
                    StageMuxFroms[second_mux] = [stagemuxfrom]
                
                assign_from[0] = ( assign_from[0] + 1) % (imux_from.total_froms * 4)

    elif type_str == "omux" or type_str == "pb" or type_str == "imux":
        i_ports = ("Ia", "Ib", "Ic", "Id", "Ie", "If", "Ig", "Ih")
        for i_p in range(len(i_ports)):
            for i_b in range(8):
                mux_name = "b" + str(i_b) + "-" + i_ports[i_p]
                to_pin = i_ports[i_p] + ":" + str(i_b)
                if i_b == 6:
                    mux_name = "x-" + i_ports[i_p]
                    to_pin = "x:" + str(i_p)
                elif i_b == 7:
                    mux_name = "i-" + i_ports[i_p]
                    to_pin = "i:" + str(i_p)
                second_mux = (mux_name, to_pin)
                
                from_details = ""
                if type_str == "omux":
                    for k in range(min(1, imux_from.num_foreach)):
                        from_details = "OG_" + str(assign_from[1][(assign_from[0] + k) % imux_from.total_froms])
                else:
                    for k in range(imux_from.num_foreach):
                        from_details = from_details + " " + str(assign_from[1][(assign_from[0] + k) % imux_from.total_froms])
                    from_details = from_details.strip()
                if from_details == "":
                    continue

                stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_details)
                if second_mux in StageMuxFroms:
                    StageMuxFroms[second_mux].append(stagemuxfrom)
                else:
                    StageMuxFroms[second_mux] = [stagemuxfrom]
                
                assign_from[0] = (assign_from[0] + imux_from.num_foreach) % imux_from.total_froms

# assign connection of two stage mux in imux
def assignTwoStageMux_imux(segs, imux_froms, imux_mux_fanin, imuxElem):
    firstStageMuxFroms = {}
    SecondStageMuxFroms_firstStage = {}
    SecondStageMuxFroms_noStage = {}
    #offset_second = 0
    from_type_offset = {}
    mux_nums = 8

    assignNumforeachOffset_first = 0
    offset = 0
    for imux_from in imux_froms:
        #seg_from.show()
        type_str = imux_from.type
            
        from_index = []
        if type_str == "pb" or type_str == "imux":
            pin_types = imux_from.pin_types.split(" ")
            for idx in range(8):
                for i_pin in range(len(pin_types)):
                    from_index.append(pin_types[i_pin] + ":" + str(idx))
        else:
            from_index = list(range(imux_from.total_froms))

        #first stage mux
        assign_from = [0, from_index]
        if imux_from.name in from_type_offset:
            assign_from = [from_type_offset[imux_from.name], from_index]

        if imux_from.reuse:
            assign_firstStageMux_from_imux(segs, imux_from, assign_from, offset, assignNumforeachOffset_first, firstStageMuxFroms)
            if type_str == "pb" or type_str == "omux" or type_str == "imux":
                assignNumforeachOffset_first = (assignNumforeachOffset_first + imux_from.num_foreach) % 5
            if type_str == "seg":
                offset = (offset + imux_from.num_foreach * 4) % 5
        else:
            #print(SecondStageMuxFroms_noStage)
            assign_secondStageMux_from_imux(segs, imux_from, assign_from, SecondStageMuxFroms_noStage)
            
        
        #if type_str == "seg":
        from_type_offset[imux_from.name] = assign_from[0]

        #print(from_seg_offset)


    #second stage mux
    i_ports = ("Ia", "Ib", "Ic", "Id", "Ie", "If", "Ig", "Ih")
    for i_p in range(len(i_ports)):
        for i_b in range(6):
            mux_name = "b" + str(i_b) + "-" + i_ports[i_p]
            to_pin = i_ports[i_p] + ":" + str(i_b)
            if i_b == 6:
                mux_name = "x-" + i_ports[i_p]
                to_pin = "x:" + str(i_p)
            elif i_b == 7:
                mux_name = "i-" + i_ports[i_p]
                to_pin = "i:" + str(i_p)
            second_mux = (mux_name, to_pin)
            first_mux = []
            for i_m in range(8):
                mux_name = "mux-" + str((i_b % 4 * 20 + i_b // 4 * 5 + i_m + i_p % 2 * 10 + i_p * 20) % 80 + 1)
                first_mux.append(mux_name)
                
            SecondStageMuxFroms_firstStage[second_mux] = first_mux

    #print(SecondStageMuxFroms_noStage)
    imux_two_stage = ET.SubElement(imuxElem, "multistage_muxs")
    first_stage = ET.SubElement(imux_two_stage, "first_stage")
    first_stage.set("switch_name", "only_mux")
    second_stage = ET.SubElement(imux_two_stage, "second_stage")
    
    firstStageMuxFroms = sorted(firstStageMuxFroms.items(),
                                key = lambda x: int( re.search(r'mux-(.*)', x[0], re.M | re.I).group(1) )
                                )

    for (k, v) in firstStageMuxFroms:
        mux_from = ET.SubElement(first_stage, "mux")
        mux_from.set("name", k)
        fanin = 0
        #print("\tmux_name" + k)
        for vv in v:
            #vv.show()
            vv.to_arch(mux_from)
            fanin += vv.count_detail_nums()
        imux_mux_fanin["first"][k] = fanin
    
    for k, v in SecondStageMuxFroms_firstStage.items():
        mux_from = ET.SubElement(second_stage, "mux")
        mux_from.set("name", k[0])
        mux_from.set("to_pin", k[1])
        fanin = 0

        if v:
            a_from = ET.SubElement(mux_from, "from")
            a_from.set("mux_name", " ".join(v))
            fanin += len(v)

        if k in SecondStageMuxFroms_noStage:
            v2 = SecondStageMuxFroms_noStage[k]
            #print(v2)
            for vv in v2:
                #vv.show()
                vv.to_arch(mux_from)  
                fanin += vv.count_detail_nums()
        
        imux_mux_fanin["second"][k[0]] = fanin
    
# modify the arch in a new version

# assign connection of two stage mux in imux
def assignTwoStageMux_imux_v200(segs, imux_froms, imux_mux_fanin, imuxElem, segElems):
    firstStageMuxFroms = {}
    SecondStageMuxFroms_firstStage = {}
    SecondStageMuxFroms_noStage = {}
    #offset_second = 0
    from_type_offset = {}
    mux_nums = 8

    assignNumforeachOffset_first = 0
    offset = 0
    num_froms = 0
    num_seg_from = 0
    num_fb_from = 0
    num_seg_type = 0
    num_fb_type = 0

    for imux_from in imux_froms:
        if imux_from.type == "seg":
            num_seg_type = num_seg_type + 1
            num_seg_from = num_seg_from + imux_from.num_foreach
        else:
            num_fb_type = num_fb_type + 1
            num_fb_from = num_fb_from + imux_from.num_foreach

    num_from = len(imux_froms)
    num_check_seg = 0
    num_check_fb = 0
    for imux_from in imux_froms:
        #seg_from.show()
        if imux_from.type == "seg":
            imux_from.num_foreach = imux_from.num_foreach * 48 // num_seg_from
            num_check_seg = num_check_seg + imux_from.num_foreach
        else:
            imux_from.num_foreach = imux_from.num_foreach * 16 // num_fb_from
            num_check_fb = num_check_fb + imux_from.num_foreach

    if num_check_seg != 48:
        for i in range(48 - num_check_seg):
            imux_froms[i % num_seg_type].num_foreach = imux_froms[i % num_seg_type].num_foreach + 1
    
    
    if num_check_fb != 16:
        for i in range(16 - num_check_fb):
            imux_froms[i % num_fb_type + num_seg_type].num_foreach = imux_froms[i % num_fb_type + num_seg_type].num_foreach + 1


    for imux_from in imux_froms:
        from_index = []
        imux_from.show()
        type_str = imux_from.type
        if type_str == "pb" or type_str == "imux":
            pin_types = imux_from.pin_types.split(" ")
            for idx in range(8):
                for i_pin in range(len(pin_types)):
                    from_index.append(pin_types[i_pin] + ":" + str(idx))
        else:
            from_index = list(range(imux_from.total_froms))

        #first stage mux
        assign_from = [0, from_index]
        if imux_from.name in from_type_offset:
            assign_from = [from_type_offset[imux_from.name], from_index]

        if imux_from.reuse:
            assign_firstStageMux_from_imux_v200(segs, imux_from, assign_from, offset, assignNumforeachOffset_first, firstStageMuxFroms)
            # print("assign imux from done")
            # print(type_str)
            # print(offset)
            offset = (offset + imux_from.num_foreach) % 8
            # print(offset)
        else:
            #print(SecondStageMuxFroms_noStage)
            assign_secondStageMux_from_imux(segs, imux_from, assign_from, SecondStageMuxFroms_noStage)
            
        
        #if type_str == "seg":
        from_type_offset[imux_from.name] = assign_from[0]

        #print(from_seg_offset)


    #second stage mux
    i_ports = ("Ia", "Ib", "Ic", "Id", "Ie", "If", "Ig", "Ih")
    for i_p in range(len(i_ports)):
        for i_b in range(8):
            mux_name = "b" + str(i_b) + "-" + i_ports[i_p]
            to_pin = i_ports[i_p] + ":" + str(i_b)
            if i_b == 6:
                mux_name = "x-" + i_ports[i_p]
                to_pin = "x:" + str(i_p)
            elif i_b == 7:
                mux_name = "i-" + i_ports[i_p]
                to_pin = "i:" + str(i_p)
            second_mux = (mux_name, to_pin)
            first_mux = []
            for i_m in range(8):
                if (i_p != i_m):
                    mux_name = "mux-" + str(i_m + i_b * 8)
                    first_mux.append(mux_name)
                
            SecondStageMuxFroms_firstStage[second_mux] = first_mux

    #print(SecondStageMuxFroms_noStage)
    imux_two_stage = ET.SubElement(imuxElem, "multistage_muxs")
    first_stage = ET.SubElement(imux_two_stage, "first_stage")
    first_stage.set("switch_name", "only_mux")
    second_stage = ET.SubElement(imux_two_stage, "second_stage")
    glb_stage = ET.SubElement(imux_two_stage, "glb_stage")
    glb_stage.set("switch_name", "only_mux")
    
    firstStageMuxFroms = sorted(firstStageMuxFroms.items(),
                                key = lambda x: int( re.search(r'mux-(.*)', x[0], re.M | re.I).group(1) )
                                )
    
    # glb_stage
    ind2dir = ["W", "N", "E", "S"]
    assign_from = {}
    GlbStageMuxFroms = {}
    seg_num = {}
    for seg in segElems:
        if (seg.name[0] == 'l') and (seg.name not in seg_num):
            seg_num[seg.name] = seg.total_froms
    for i in range(16):
        mux_name = "GLB" + str(i)
        mux_from = []
        for i_f in range(4):
            if i_f < 2:
                type_from = "seg"
                name_from = list(segs.keys())[(((i + i_f) % 3 == 0) + ((i + i_f) % 6 == 0)) % len(segs.keys())]
                if name_from not in assign_from:
                    assign_from[name_from] = 0
                from_detail = ind2dir[(i + i_f) % 4] + str(assign_from[name_from])
                assign_from[name_from] = (assign_from[name_from] + 1) % seg_num[name_from]
                mux_from.append(TwoStageMuxFrom_inf(type_from, name_from, from_detail))

            else:
                type_from = "cas"
                name_from = "cas"
                if name_from not in assign_from:
                    assign_from[name_from] = 0
                from_detail = "SW_CAS" + str(assign_from[name_from])
                assign_from[name_from] = (assign_from[name_from] + 1) % 8
                mux_from.append(TwoStageMuxFrom_inf(type_from, name_from, from_detail))

        GlbStageMuxFroms[mux_name] = mux_from


    for (k, v) in firstStageMuxFroms:
        mux_from = ET.SubElement(first_stage, "mux")
        mux_from.set("name", k)
        fanin = 0
        #print("\tmux_name" + k)
        for vv in v:
            #vv.show()
            vv.to_arch(mux_from)
            fanin += vv.count_detail_nums()
        imux_mux_fanin["first"][k] = fanin
    
    for k, v in SecondStageMuxFroms_firstStage.items():
        mux_from = ET.SubElement(second_stage, "mux")
        mux_from.set("name", k[0])
        mux_from.set("to_pin", k[1])
        fanin = 0

        if v:
            a_from = ET.SubElement(mux_from, "from")
            a_from.set("mux_name", " ".join(v))
            fanin += len(v)

        if k in SecondStageMuxFroms_noStage:
            v2 = SecondStageMuxFroms_noStage[k]
            #print(v2)
            for vv in v2:
                #vv.show()
                vv.to_arch(mux_from)  
                fanin += vv.count_detail_nums()
        
        imux_mux_fanin["second"][k[0]] = fanin

    for k, v in GlbStageMuxFroms.items():
        mux_from = ET.SubElement(glb_stage, "mux")
        mux_from.set("name", k)
        fanin = 0
        #print("\tmux_name" + k)
        for vv in v:
            #vv.show()
            vv.to_arch(mux_from)
            fanin += vv.count_detail_nums()
        imux_mux_fanin["first"][k] = fanin
    
# modify the arch in a new version

def generateTwoStageMux_v200(archTree):
    gsb_arch = archTree["root"].getroot().find("gsb_arch")

    gsbElem = gsb_arch.find("gsb")
    imuxElem = gsb_arch.find("imux")
    segsElem = archTree["root"].getroot().find("segmentlist")
    gsb = {}
    to_mux_nums = {}
    imux = {}
    segs = {}
    segs_numfreq = {}
    seg_num = 0
    segElems = []

    if imuxElem.find("multistage_muxs") != None:
        imuxElem.remove(imuxElem.find("multistage_muxs"))
    if gsbElem.find("multistage_muxs") != None:
        gsbElem.remove(gsbElem.find("multistage_muxs"))
    for seg in segsElem:
        seg_info = Seg_inf(seg)
        if (seg.get('name')[0] == 'l'):
            seg_name = seg.get("name")
            seg_length = int(seg.get("length"))
            segs[seg_name] = seg_length
            segs_numfreq[seg_name] = int(float(seg.get("freq")) / 2 / seg_length)
            seg_info.total_froms = int(float(seg.get("freq")) / 2 / seg_length)
            # print(str(seg_name) + ' ' + str(segs_numfreq[seg_name]))
            seg_num = seg_num + segs_numfreq[seg_name]
            segElems.append(seg_info) 
        # print(seg_info.total_from)
    for seg_name in segs_numfreq.keys():
        segs_numfreq[seg_name] = segs_numfreq[seg_name] / seg_num
        # print(segs_numfreq[seg_name])
    
    gsb_mux_fanin = {}
    gsb_mux_fanin["first"] = {}
    gsb_mux_fanin["second"] = {}

    pin_froms = []
    for seg_group in gsbElem:
        to_seg_name = seg_group.get("name")
        if (to_seg_name == "l1"):
            for fromElem in seg_group:
                if fromElem.get("type") != "seg":
                    if fromElem.get("type") == "pb":
                        # divide the pb from description into seperate From_inf acccording to its pin_types
                        from_details = fromElem.get("pin_types").split()
                        for pin_type in from_details:
                            pin_from = From_inf(fromElem)
                            pin_from.pin_types = pin_type
                            pin_froms.append(pin_from)
                    else:
                        pin_froms.append(From_inf(fromElem))
        seg_froms = []
        for fromElem in seg_group:
            seg_froms.append(From_inf(fromElem))

        gsb[to_seg_name] = seg_froms
        to_mux_nums[to_seg_name] = int(seg_group.get("track_nums"))
        #gsb_mux_fanin[to_seg_name] = {}
    # pin_froms is the feedback drive of l1 produced by bayes variables

    imux_mux_fanin ={}
    imux_mux_fanin["first"] = {}
    imux_mux_fanin["second"] = {}
    for lut_group in imuxElem:
        lut_name = lut_group.get("name")
        imux_froms = []
        for fromElem in lut_group:
            imux_froms.append(From_inf(fromElem))
        imux[lut_name] = imux_froms
    if len(imux) > 1:
        raise ArchError("too many lut_group in imux, only one lut_group is ok")
    assignTwoStageMux_gsb_v200(segs, gsb, to_mux_nums, gsb_mux_fanin, gsbElem, segs_numfreq, segElems, pin_froms)
    assignTwoStageMux_imux_v200(segs, imux_froms,imux_mux_fanin, imuxElem, segElems)
    return (gsb_mux_fanin, imux_mux_fanin)
def generateTwoStageMux(archTree):
    gsb_arch = archTree["root"].getroot().find("gsb_arch")

    gsbElem = gsb_arch.find("gsb")
    imuxElem = gsb_arch.find("imux")
    segsElem = archTree["root"].getroot().find("segmentlist")
    gsb = {}
    to_mux_nums = {}
    imux = {}
    segs = {}

    if imuxElem.find("multistage_muxs") != None:
        imuxElem.remove(imuxElem.find("multistage_muxs"))
    if gsbElem.find("multistage_muxs") != None:
        gsbElem.remove(gsbElem.find("multistage_muxs"))

    for seg in segsElem:
        seg_name = seg.get("name")
        seg_length = int(seg.get("length"))
        segs[seg_name] = seg_length
    
    gsb_mux_fanin = {}
    gsb_mux_fanin["first"] = {}
    gsb_mux_fanin["second"] = {}
    for seg_group in gsbElem:
        to_seg_name = seg_group.get("name")
        seg_froms = []
        for fromElem in seg_group:
            seg_froms.append(From_inf(fromElem))
        gsb[to_seg_name] = seg_froms
        to_mux_nums[to_seg_name] = int(seg_group.get("track_nums"))

        #gsb_mux_fanin[to_seg_name] = {}
        
    imux_mux_fanin ={}
    imux_mux_fanin["first"] = {}
    imux_mux_fanin["second"] = {}
    for lut_group in imuxElem:
        lut_name = lut_group.get("name")
        imux_froms = []
        for fromElem in lut_group:
            imux_froms.append(From_inf(fromElem))
        imux[lut_name] = imux_froms
    if len(imux) > 1:
        raise ArchError("too many lut_group in imux, only one lut_group is ok")

    assignTwoStageMux_gsb(segs, gsb, to_mux_nums, gsb_mux_fanin, gsbElem)
    assignTwoStageMux_imux(segs, imux_froms,imux_mux_fanin, imuxElem)
    return (gsb_mux_fanin, imux_mux_fanin)
  
def compute_area(fanin, mux_trans_size):
    trans_sram_bit = 4
    pass_trans_area = mux_trans_size #???

    pass_trans = 0
    sram_trans = 0

    if fanin <= 1 :
        return 0
    elif fanin == 2:
        pass_trans = 2 * pass_trans_area
        sram_trans = 1 * trans_sram_bit
    elif fanin <=4:
        pass_trans = fanin * pass_trans_area
        sram_trans = fanin * trans_sram_bit
    else:
        num_second_stage_trans = int(math.floor(float(math.sqrt(float(fanin))) + 0.00001))
        pass_trans = (fanin + num_second_stage_trans) * pass_trans_area
        sram_trans = (math.ceil(float(fanin) / num_second_stage_trans - 0.00001) + num_second_stage_trans) * trans_sram_bit
        if num_second_stage_trans == 2:
            sram_trans -= 1 * trans_sram_bit
    
    return sram_trans + pass_trans

def findSeg(segs, seg_name):
    for seg in segs:
        if seg.name == seg_name:
            return seg
    return None

def verify_fanin_ok(gsb_mux_fanin, imux_mux_fanin, segs, imux_froms, area_pair, logger, is_area_cons = True):
    fanin_num_driver = {}
    #gsb_first
    gsb_first_fanin = gsb_mux_fanin["first"]
    fanin_num_driver["gsb_mux"] = {}
    for mux_name, fanin in gsb_first_fanin.items():
        if fanin not in fanin_num_driver["gsb_mux"]:
            fanin_num_driver["gsb_mux"][fanin] = 1 
        else:
            fanin_num_driver["gsb_mux"][fanin] += 1

        if is_area_cons:
            if fanin > 6 or fanin < 4:
                #logger.info("error gsb first fanin")
                return False
        else:
            if fanin > 10 or fanin < 4:
                #logger.info("error gsb first fanin")
                return False

    #gsb_second
    gsb_second_fanin = gsb_mux_fanin["second"]
    for mux_name, fanin_pair in gsb_second_fanin.items():
        fanin = fanin_pair[0]
        driver_name = fanin_pair[1]
        if driver_name not in fanin_num_driver:
            fanin_num_driver[driver_name] = {}

        seg_name = mux_name.split(":")[0]

        if fanin not in fanin_num_driver[driver_name]:
            fanin_num_driver[driver_name][fanin] = 1 
        else:
            fanin_num_driver[driver_name][fanin] += 1

        is_shortSeg = True
        for seg in segs:
            if seg.name == seg_name and seg.length > 6:
                is_shortSeg = False
                break
        
        if is_shortSeg:
            if is_area_cons:
                if fanin > 5 or fanin < 4:
                    #logger.info("error gsb second(short) fanin")
                    return False
            else:
                if fanin > 10 or fanin < 4:
                    #logger.info("error gsb second(short) fanin")
                    return False
        else:
            if fanin > 16 or fanin < 6:
                #logger.info("error gsb second(long) fanin")
                return False
    
    #imux_first
    imux_first_fanin = imux_mux_fanin["first"]
    fanin_num_driver["imux_mux"] = {}
    for mux_name, fanin in imux_first_fanin.items():
        if fanin not in fanin_num_driver["imux_mux"]:
            fanin_num_driver["imux_mux"][fanin] = 1
        else:
            fanin_num_driver["imux_mux"][fanin] += 1

        if is_area_cons:
            if fanin > 7 or fanin < 4:
                #logger.info("error imux first fanin")
                return False
        else:
            if fanin > 10 or fanin < 4:
                #logger.info("error imux first fanin")
                return False

    #imux_second
    imux_second_fanin = imux_mux_fanin["second"]
    for mux_name, fanin in imux_second_fanin.items():
        if fanin not in fanin_num_driver["imux_mux"]:
            fanin_num_driver["imux_mux"][fanin] = 1
        else:
            fanin_num_driver["imux_mux"][fanin] += 1
        
        if is_area_cons:
            if fanin > 8 or fanin < 5:
                #logger.info("error imux second fanin")
                return False
        else:
            if fanin > 12 or fanin < 5:
                #logger.info("error imux second fanin")
                return False
    
    count = 0
    for imux_from in imux_froms:
        if imux_from.type == "seg":
            seg = findSeg(segs, imux_from.name)
            if seg.length <= 6:
                count += 1 
    if count < 2:
        #logger.info("error imux from too small")
        return False

    if is_area_cons:
        standard_area = area_pair[0]
        area_dict = area_pair[1]
        new_area = 0
        for driver_name, fanin_num in fanin_num_driver.items():
            for k,v in fanin_num.items():
                new_area += area_dict[driver_name][k] * v
        if new_area > standard_area * 1.1:
            if standard_area == 0:
                area_pair[0] = new_area
            else:
                #logger.info("error area")
                return False

    #logger.info("\n\n")
    '''logger.info("\t***********verify_fanin_ok***************")
    logger.info("\tfanin" + "\t" + "mux_num")
    for k,v in fanin_num.items():
        logger.info("\t" + str(k) + "\t" + str(v))
    #logger.info("\n")'''
    return True

def countViolations(gsb_mux_fanin, imux_mux_fanin, segs, imux_froms, area_pair, is_area_cons = True):

    violation = 0

    fanin_num_driver = {}
    #gsb_first
    gsb_first_fanin = gsb_mux_fanin["first"]
    fanin_num_driver["gsb_mux"] = {}
    for mux_name, fanin in gsb_first_fanin.items():
        if fanin not in fanin_num_driver["gsb_mux"]:
            fanin_num_driver["gsb_mux"][fanin] = 1 
        else:
            fanin_num_driver["gsb_mux"][fanin] += 1

        if is_area_cons:
            if fanin > 10 or fanin < 4:
                #logger.info("error gsb first fanin")
                violation += 1
        else:
            if fanin > 10 or fanin < 4:
                #logger.info("error gsb first fanin")
                violation += 1
    # print('after gsb_first'+ str(violation))

    #gsb_second
    gsb_second_fanin = gsb_mux_fanin["second"]
    for mux_name, fanin_pair in gsb_second_fanin.items():
        fanin = fanin_pair[0]
        driver_name = fanin_pair[1]
        if driver_name not in fanin_num_driver:
            fanin_num_driver[driver_name] = {}

        seg_name = mux_name.split(":")[0]

        if fanin not in fanin_num_driver[driver_name]:
            fanin_num_driver[driver_name][fanin] = 1 
        else:
            fanin_num_driver[driver_name][fanin] += 1

        is_shortSeg = True
        for seg in segs:
            if seg.name == seg_name and seg.length > 6:
                is_shortSeg = False
                break
        
        if is_shortSeg:
            if is_area_cons:
                if fanin > 5 or fanin < 4:
                    #logger.info("error gsb second(short) fanin")
                    violation += 1
            else:
                if fanin > 10 or fanin < 4:
                    #logger.info("error gsb second(short) fanin")
                    violation += 1
        else:
            if fanin > 16 or fanin < 6:
                #logger.info("error gsb second(long) fanin")
                violation += 1
    
    # print('after gsb_second'+ str(violation))
    #imux_first
    imux_first_fanin = imux_mux_fanin["first"]
    fanin_num_driver["imux_mux"] = {}
    for mux_name, fanin in imux_first_fanin.items():
        if fanin not in fanin_num_driver["imux_mux"]:
            fanin_num_driver["imux_mux"][fanin] = 1
        else:
            fanin_num_driver["imux_mux"][fanin] += 1

        if is_area_cons:
            if fanin > 7 or fanin < 4:
                #logger.info("error imux first fanin")
                violation += 1
        else:
            if fanin > 10 or fanin < 4:
                #logger.info("error imux first fanin")
                violation += 1

    # print('after imux_first'+ str(violation))
    #imux_second
    imux_second_fanin = imux_mux_fanin["second"]
    for mux_name, fanin in imux_second_fanin.items():
        if fanin not in fanin_num_driver["imux_mux"]:
            fanin_num_driver["imux_mux"][fanin] = 1
        else:
            fanin_num_driver["imux_mux"][fanin] += 1
        
        if is_area_cons:
            if fanin > 8 or fanin < 5:
                #logger.info("error imux second fanin")
                violation += 1
        else:
            if fanin > 12 or fanin < 5:
                #logger.info("error imux second fanin")
                violation += 1
    
    # print('after imux_second'+ str(violation))
    count = 0
    for imux_from in imux_froms:
        if imux_from.type == "seg":
            seg = findSeg(segs, imux_from.name)
            if seg.length <= 6:
                count += 1 
    if count < 2:
        #logger.info("error imux from too small")
        violation += 1
    # print('after imux_segfrom'+ str(violation))

    if is_area_cons:
        standard_area = area_pair[0]
        area_dict = area_pair[1]
        new_area = 0
        for driver_name, fanin_num in fanin_num_driver.items():
            for k,v in fanin_num.items():
                new_area += area_dict[driver_name][k] * v
        if new_area > standard_area * 1.1:
            if standard_area == 0:
                area_pair[0] = new_area
            else:
                #logger.info("error area")
                violation += 1
    # print('after area check'+ str(violation))

    # #logger.info("\n\n")
    # logger.info("\t***********verify_fanin_ok***************")
    # logger.info("\tfanin" + "\t" + "mux_num")
    # for k,v in fanin_num.items():
    #     logger.info("\t" + str(k) + "\t" + str(v))
    # #logger.info("\n")
    return violation

class bendInfo():
    switch_type = ["U", "D"]

    def __init__(self, _len, _normal_num, _bent_num, _seg, _bent_seg):
        self.length = _len
        self.normal_num = _normal_num
        self.normal_seg = _seg
        self.bent_num = _bent_num
        self.bent_seg = _bent_seg
        self.is_shortSeg = False if _len > 6 else True
    
    def setNormalNum(self, _normal_num, _seg):
        self.normal_num = _normal_num
        self.normal_seg = _seg

    def setBent(self, _bent_num, _bent_seg):
        self.bent_num = _bent_num
        self.bent_seg = _bent_seg


def modifyEachMUXSize(mux, mux_name, drive_num, driveMaxNum):

    if (drive_num < 4)or(drive_num == 5)or(drive_num == 7):
        drive_info = mux.findall('from')[0]
        from_detail = drive_info.get('from_detail')
        from_details = from_detail.split(' ')
        new_from_detail = from_details[0]
        while new_from_detail in from_details:
            new_from_detail = random_pick(['E','S','N','W'],[0.25] * 4) + str(random_pick([i for i in range(driveMaxNum)],[1/driveMaxNum] * driveMaxNum))
        new_drive = TwoStageMuxFrom_inf(drive_info.get('type'), drive_info.get('name'), new_from_detail)
        new_drive.to_arch(mux)
        return (drive_num + 1)
    elif (drive_num > 8):
        while (drive_num > 8):
            drive_info = mux.findall('from')[0]
            from_detail = drive_info.get('from_detail')
            from_details = from_detail.split(' ')
            if len(from_details) > 1:
                from_details.pop()
                drive_info.set('from_detail', ' '.join(from_details))
            else:
                mux.remove(mux.findall('from')[0])
            drive_num = drive_num - 1

        return 8


def modifyMUXSize(archTree, gsbFanin, imuxFanin, type_to_maxNum):
    
    gsb_arch = archTree["root"].getroot().find("gsb_arch")
    gsbMUX = gsb_arch.find("gsb").find("multistage_muxs")
    imuxMUX = gsb_arch.find("imux").find("multistage_muxs")
    gsb1 = gsbMUX.find("first_stage")
    imux1 = imuxMUX.find("first_stage")
    for (k, v) in gsbFanin["first"].items():
        if (v == 4) or (v == 6) or (v == 8):
            continue
        for mux in gsb1.findall('mux'):
            if mux.get('name') == k:
                drive_info = mux.findall('from')[0]
                from_type = drive_info.get('name')
                driveMaxNum = type_to_maxNum[from_type] if from_type in type_to_maxNum.keys() else  4
                new_fanin = modifyEachMUXSize(mux, k, v, driveMaxNum)
                gsbFanin['first'][k] = new_fanin
                
    for (k, v) in imuxFanin["first"].items():
        if (v == 4) or (v == 6) or (v == 8):
            continue
        for mux in imux1.findall('mux'):
            if mux.get('name') == k:
                drive_info = mux.findall('from')[0]
                from_type = drive_info.get('name')
                driveMaxNum = type_to_maxNum[from_type] if from_type in type_to_maxNum.keys() else  4
                new_fanin = modifyEachMUXSize(mux, k, v, driveMaxNum)
                imuxFanin['first'][k] = new_fanin
 


##################################################################################
#####
#####  if you wanna run the seeker.py :
#####       example : python Seeker.py -o ./ -j 20 -t hard_wire_test
#####                 and set the (optimize_arch_add) in config.txt
#####
#################################################################################

if __name__ == "__main__":
    archTree = readArch2("./V200_baseline_v3.xml")
    generateTwoStageMux_v200(archTree)
    if os.path.exists("./test2.xml"):
        os.remove("./test2.xml")
    writeArch2(archTree["root"].getroot(), "./test2.xml")
    #print(archTree["root"].getroot())
