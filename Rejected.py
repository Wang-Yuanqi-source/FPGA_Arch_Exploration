# -*- coding: utf-8 -*-
import re
import os.path
import matplotlib.pyplot as plt
from Reporter_GSB import compare

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

def readArch(archfile):
    archTree = {}
    archTree["root"] = ET.parse(archfile)
    return archTree


class seg_inf():
    def __init__(self, _len, _pattern, _num):
        self.len = _len
        self.num = _num
        self.pattern = _pattern

    def show(self):
        print("\t\tnum: " + self.num + "; ")


if __name__ == "__main__":
    logfile = "./[ssh qjd@192.168.64.111] (2020-11-02_164147).log"
    f = open(logfile)
    lines = f.readlines()
    countFound = False
    count_list = []
    count_delay_map = {}
    for line in lines:
        if countFound:
            iteration_match = re.match(re.compile(".*Inner iteration \(([()a-zA-Z]*)\)"), line)
            if iteration_match:
                if iteration_match.group(1) == "Rejected":
                    count_list.append(int(count))
                countFound = False
        else:
            count_match = re.match(re.compile(".*Count : (.*)"), line)
            if count_match:
                countFound = True
                count = count_match.group(1)
                #print(count)
    print(count_list)

    for count in count_list:
        task_dir = "./"
        baseline_dir = task_dir + "/baseline"
        modified_dir = "../" + str(count)
        compare_pair = [[baseline_dir, modified_dir]]
        #print(os.getcwd())
        count_delay_map[count] = compare(compare_pair, task_dir)
    #count seg and gsb
    #current_dir = os.getcwd()
    thres = 10.0
    counts = sorted(count_delay_map.keys())
    print(counts)
    out_f = open("seg_inf_up_delay.txt", "w+")
    #counts = [1, 2]
    #count_list.clear()
    #count_list={1:-10.0, 2:-11.0}
    for count in counts:
        if count_delay_map[count] > thres:
            archfile = "./" + str(count) + "/k6_frac_N10_mem32K_40nm_gsb24.xml"
            archTree = readArch(archfile)

            #seg inf
            seg_nums = {}
            gsb_arch = archTree["root"].getroot().find("gsb_arch")
            gsbElem = gsb_arch.find("gsb")
            for seg_group in gsbElem:
                seg_name = seg_group.get("name")
                if seg_name == None:
                    continue
                seg_nums[seg_name] = int(seg_group.get("track_nums"))

            seg_inf_map = {}
            segsElem = archTree["root"].getroot().find("segmentlist")
            for seg in segsElem:
                seg_name = seg.get("name")
                if seg_name in ["imux_medium", "gsb_medium", "omux_medium"]:
                    continue
                seg_length = int(seg.get("length"))
                
                bendElem = seg.find("bend")
                if bendElem != None:
                    seg_bend_list = bendElem.text
                else:
                    seg_bend_list = "-" * (seg_length - 1)

                seg_num = seg_nums[seg_name]

                seg_inf_map[seg_name] = seg_inf(seg_length, seg_bend_list, seg_num)

            out_f.write("==================== count:" + str(count) + " ************************************\n")
            out_f.write('{0:<10}  {1:<10}  {2:<10}'.format("length", "pattern", "num") + "\n")
            seg_infs = sorted(seg_inf_map.values(), key=lambda x:x.len)
            for seg in seg_infs:
                out_f.write('{0:<10}  {1:<10}  {2:<10}'.format(seg.len, seg.pattern, seg.num) + "\n")
            out_f.write("\n")

            #imux from
            imuxs = []
            omux_tag = False
            imux_tag = False
            pb_tag = False
            imuxElem = gsb_arch.find("imux")
            group = imuxElem.find("group")
            for imuxFroms in group:
                if imuxFroms.get("type") == "seg":
                    imuxs.append(imuxFroms.get("name"))
                elif imuxFroms.get("type") == "omux":
                    omux_tag = True
                elif imuxFroms.get("type") == "imux":
                    imux_tag = True
                elif imuxFroms.get("type") == "pb":
                    pb_tag = True
            
            out_f.write('{0:<10}'.format("imux:"))
            for imux in imuxs:
                seg = seg_inf_map[imux]
                out_f.write('{0:<10}'.format(str(seg.len) + "(" + seg.pattern + ")"))
            if imux_tag:
                out_f.write('{0:<10}'.format("imux"))
            if omux_tag:
                out_f.write('{0:<10}'.format("omux"))
            if pb_tag:
                out_f.write('{0:<10}'.format("pb"))
            out_f.write("\n\n")

            #gsb from
            gsbElem = gsb_arch.find("gsb")
            seg_names = [x[0] for x in sorted(seg_inf_map.items(), key=lambda x:x[1].len)]
            seg_groups = [0] * len(seg_names)
            #print(seg_names)
            for segGroup in gsbElem:
                seg_name = segGroup.get("name")
                if seg_name == None:
                    continue
                index = seg_names.index(seg_name)
                seg_groups[index] = segGroup

            for segGroup in seg_groups:
                seg_name = segGroup.get("name")
                if seg_name == None:
                    continue

                gsbs = []
                omux_tag = False
                pb_tag = False
                for gsbFroms in segGroup:
                    if gsbFroms.get("type") == "seg":
                        gsbs.append(gsbFroms.get("name"))
                    elif gsbFroms.get("type") == "omux":
                        omux_tag = True
                    elif gsbFroms.get("type") == "pb":
                        pb_tag = True

                seg = seg_inf_map[seg_name]
                out_f.write('{0:<15}'.format(str(seg.len) + "(" + seg.pattern + "):"))
                for gsb in gsbs:
                    seg = seg_inf_map[gsb]
                    out_f.write('{0:<15}'.format(str(seg.len) + "(" + seg.pattern + ")"))
                if omux_tag:
                    out_f.write('{0:<15}'.format("omux"))
                if pb_tag:
                    out_f.write('{0:<15}'.format("pb"))
                out_f.write("\n")
            out_f.write("\n")

            

            




                
                    
    




        


    
