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
        result[(k+offset) % 4] += 1
    return result


def random_pick(itemList, probs):
    x = random.uniform(0,1)
    c_prob = 0.0
    for item, prob in zip(itemList, probs):
        c_prob += prob
        if x < c_prob: 
            break
    return item

def assignNumforeach_imux(num_foreach, offset = 4):
    result = [0, 0, 0, 0, 0]
    for k in range(int(num_foreach * 4)):
        result[(k + offset) % 5] += 1
    return result

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
                for k in range(min(1,omux_each_mux[j])):
                    from_details = "OG_" + str(assign_from[1][(assign_from[0] + k)% seg_from.total_froms])
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
                print(assign_from[0])
                from_details = ""
                for k in range(imux_from.num_foreach):
                    from_details = from_details + " " + from_candidate[(assign_from[0] + k) % (imux_from.total_froms * 4)]
                from_details = from_details.strip()
                if from_details == "":
                    continue

                stagemuxfrom = TwoStageMuxFrom_inf(type_str, name_str, from_details, imux_from.switchpoint)
                if second_mux in StageMuxFroms:
                    StageMuxFroms[second_mux].append(stagemuxfrom)
                else:
                    StageMuxFroms[second_mux] = [stagemuxfrom]
                
                assign_from[0] = ( assign_from[0] + imux_from.num_foreach ) % (imux_from.total_froms * 4)


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
            for i_m in range(5):
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
 
def assignTwoStageMux_gsb_HalfBent(segs, gsb, to_mux_nums, gsb_mux_fanin, gsbElem, bentSegs):
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
                #print(first_mux)
                if first_mux:
                    del(first_mux[(i_dir + 2) % 4])
                SecondStageMuxFroms_firstStage[second_mux] = first_mux
        

    #print(SecondStageMuxFroms_noStage)
    gsb_two_stage = ET.SubElement(gsbElem, "multistage_muxs")
    first_stage = ET.SubElement(gsb_two_stage, "first_stage")
    first_stage.set("switch_name", "only_mux")
    second_stage = ET.SubElement(gsb_two_stage, "second_stage")

    firstStageMuxFroms = sorted(firstStageMuxFroms.items(),
                                key = lambda x: int( re.search(r'mux-(.*)-(.*)', x[0], re.M | re.I).group(1) )
                                )
    
    lenNameMap = {}
    nameLenMap = segs
    for segName, segLen in segs.items():
        lenNameMap[segLen] = segName
 
    lenNumMap = {}
    for length, bentinfo in bentSegs.items():
        if to_mux_nums[lenNameMap[length]] * length * 2 != bentinfo.normal_num + bentinfo.bent_num:
            raise ArchError("num normal + bent not equal to all normal!")
        lenNumMap[length] = (bentinfo.normal_num / length / 2, bentinfo.bent_num / length / 2)

    for (k, v) in firstStageMuxFroms:
        mux_from = ET.SubElement(first_stage, "mux")
        mux_from.set("name", k)
        fanin = 0
        #print("\tmux_name" + k)
        for vv in v:
            #vv.show()
            if vv.type == "seg" and lenNumMap[nameLenMap[vv.name]][1] != 0:
                fromSeg_name = vv.name
                fromSeg_len = nameLenMap[fromSeg_name]
                normal_num = lenNumMap[fromSeg_len][0]
                bent_num = lenNumMap[fromSeg_len][1]
                from_details = vv.from_details.split(" ")
                normal_details = []
                bent_details = []
                for from_detail in from_details:
                    index = int(from_detail[1:])
                    if index >= normal_num:
                        bent_details.append(from_detail[0] + str(index - normal_num))
                    else:
                        normal_details.append(from_detail)
                
                if len(normal_details) > 0:
                    tsn = TwoStageMuxFrom_inf("seg", vv.name, " ".join(normal_details))
                    tsn.to_arch(mux_from)
                if len(bent_details) > 0:
                    tsb = TwoStageMuxFrom_inf("seg", vv.name + "_bent", " ".join(bent_details))
                    tsb.to_arch(mux_from)
            else:
                vv.to_arch(mux_from)
            fanin += vv.count_detail_nums()
        gsb_mux_fanin["first"][k] = fanin
    
    for k, v in SecondStageMuxFroms_firstStage.items():
        mux_from = ET.SubElement(second_stage, "mux")
        normal_num = lenNumMap[nameLenMap[k[1]]][0]
        index = int(k[2][1:])
        if index >= normal_num:
            mux_from.set("name", k[0][0:2] + str(index - normal_num))
            mux_from.set("to_seg_name", k[1] + "_bent")
            real_to_track = k[2][0] + str(index - normal_num)
            mux_from.set("to_track", real_to_track)
        else:
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
                if vv.type == "seg" and lenNumMap[nameLenMap[vv.name]][1] != 0:
                    fromSeg_name = vv.name
                    fromSeg_len = nameLenMap[fromSeg_name]
                    normal_num = lenNumMap[fromSeg_len][0]
                    bent_num = lenNumMap[fromSeg_len][1]
                    from_details = vv.from_details.split(" ")
                    normal_details = []
                    bent_details = []
                    for from_detail in from_details:
                        index = int(from_detail[1:])
                        if index >= normal_num:
                            bent_details.append(from_detail[0] + str(index - normal_num))
                        else:
                            normal_details.append(from_detail)
                
                    if len(normal_details) > 0:
                        tsn = TwoStageMuxFrom_inf("seg", vv.name, " ".join(normal_details))
                        tsn.to_arch(mux_from)
                    if len(bent_details) > 0:
                        tsb = TwoStageMuxFrom_inf("seg", vv.name + "_bent", " ".join(bent_details))
                        tsb.to_arch(mux_from)
                else:
                    vv.to_arch(mux_from)
                fanin += vv.count_detail_nums()
        gsb_mux_fanin["second"][fanin_key] = fanin    

def assignTwoStageMux_imux_HalfBent(segs, imux_froms, imux_mux_fanin, imuxElem, bentSegs):
    firstStageMuxFroms = {}
    SecondStageMuxFroms_firstStage = {}
    SecondStageMuxFroms_noStage = {}
    #offset_second = 0
    from_type_offset = {}

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
            for i_m in range(5):
                mux_name = "mux-" + str((i_b % 4 * 20 + i_b // 4 * 5 + i_m + i_p % 2 * 10 + i_p * 20) % 80 + 1)
                first_mux.append(mux_name)
                
            SecondStageMuxFroms_firstStage[second_mux] = first_mux

    #print(SecondStageMuxFroms_noStage)
    imux_two_stage = ET.SubElement(imuxElem, "multistage_muxs")
    first_stage = ET.SubElement(imux_two_stage, "first_stage")
    first_stage.set("switch_name", "imux_mux")
    second_stage = ET.SubElement(imux_two_stage, "second_stage")
    
    firstStageMuxFroms = sorted(firstStageMuxFroms.items(),
                                key = lambda x: int( re.search(r'mux-(.*)', x[0], re.M | re.I).group(1) )
                                )

    lenNameMap = {}
    nameLenMap = segs
    for segName, segLen in segs.items():
        lenNameMap[segLen] = segName

    lenNumMap = {}
    for length, bentinfo in bentSegs.items():
        #gsb先跑，已经验过是否相等
        lenNumMap[length] = (bentinfo.normal_num / length / 2, bentinfo.bent_num / length / 2)

    for (k, v) in firstStageMuxFroms:
        mux_from = ET.SubElement(first_stage, "mux")
        mux_from.set("name", k)
        fanin = 0
        #print("\tmux_name" + k)
        for vv in v:
            #vv.show()
            if vv.type == "seg" and lenNumMap[nameLenMap[vv.name]][1] != 0:
                fromSeg_name = vv.name
                fromSeg_len = nameLenMap[fromSeg_name]
                normal_num = lenNumMap[fromSeg_len][0]
                bent_num = lenNumMap[fromSeg_len][1]
                from_details = vv.from_details.split(" ")
                normal_details = []
                bent_details = []
                for from_detail in from_details:
                    index = int(from_detail[1:])
                    if index >= normal_num:
                        bent_details.append(from_detail[0] + str(index - normal_num))
                    else:
                        normal_details.append(from_detail)
                
                if len(normal_details) > 0:
                    tsn = TwoStageMuxFrom_inf("seg", vv.name, " ".join(normal_details))
                    tsn.to_arch(mux_from)
                if len(bent_details) > 0:
                    tsb = TwoStageMuxFrom_inf("seg", vv.name + "_bent", " ".join(bent_details))
                    tsb.to_arch(mux_from)
            else:
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
                if vv.type == "seg" and lenNumMap[fromSeg_len][1] != 0:
                    fromSeg_name = vv.name
                    fromSeg_len = nameLenMap[fromSeg_name]
                    normal_num = lenNumMap[fromSeg_len][0]
                    bent_num = lenNumMap[fromSeg_len][1]
                    from_details = vv.from_details.split(" ")
                    normal_details = []
                    bent_details = []
                    for from_detail in from_details:
                        index = int(from_detail[1:])
                        if index >= normal_num:
                            bent_details.append(from_detail[0] + str(index - normal_num))
                        else:
                            normal_details.append(from_detail)
                
                    if len(normal_details) > 0:
                        tsn = TwoStageMuxFrom_inf("seg", vv.name, " ".join(normal_details))
                        tsn.to_arch(mux_from)
                    if len(bent_details) > 0:
                        tsb = TwoStageMuxFrom_inf("seg", vv.name + "_bent", " ".join(bent_details))
                        tsb.to_arch(mux_from)
                else:
                    vv.to_arch(mux_from)
                fanin += vv.count_detail_nums()
        imux_mux_fanin["second"][k[0]] = fanin

# 生成Bent线和普通线一起分配的多级mux（一般是各分各的）
def generateTwoStageMux_HalfBent(archTree, bentSegs):
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

    imux_mux_fanin = {}
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

    assignTwoStageMux_gsb_HalfBent(segs, gsb, to_mux_nums, gsb_mux_fanin, gsbElem, bentSegs)
    assignTwoStageMux_imux_HalfBent(segs, imux_froms, imux_mux_fanin, imuxElem, bentSegs)
    return (gsb_mux_fanin, imux_mux_fanin)

##################################################################################
#####
#####  if you wanna run the seeker.py :
#####       example : python Seeker.py -o ./ -j 20 -t hard_wire_test
#####                 and set the (optimize_arch_add) in config.txt
#####
#################################################################################

if __name__ == "__main__":
    archTree = readArch2("./V200_Explore.xml")
    generateTwoStageMux(archTree)
    if os.path.exists("./test2.xml"):
        os.remove("./test2.xml")
    writeArch2(archTree["root"].getroot(), "./test2.xml")
    #print(archTree["root"].getroot())
