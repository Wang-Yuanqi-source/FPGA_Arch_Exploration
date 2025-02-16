import pdb
import os.path
import sys
import re
import random
import math
import copy
import datetime
import logging
import argparse
from functools import partial
import pandas as pd
import numpy as np
import subprocess
import time

from random import randint

from scipy import stats
from optparse import OptionParser
import multiprocessing
from collections import Counter

import Caller
import Regex
from Generate_two_stage import From_inf, generateTwoStageMux, readArch2, writeArch2, findSeg, verify_fanin_ok, compute_area, countViolations, modifyMUXSize

from Generate_two_stage_v200 import generateTwoStageMux_v200
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
from xml.dom import minidom

from hyperopt import hp, fmin, mix, tpe, rand, space_eval, STATUS_OK, STATUS_FAIL
from hyperopt.mongoexp import MongoTrials, Trials

from Seeker_GSB import *
from Convert_gsb2vib_openFPGA import *

def get_arith_avg(dataframe, index_name):
    return dataframe[index_name].mean()

def get_geom_avg(dataframe, index_name):
    return stats.gmean(dataframe[index_name].dropna())

def xml_indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            xml_indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

# Random arch
def genArch_seg(variables):
    # Constants
    PbTotalNum = 8
    OxbarTotalNum = 8
    GLBTotalNum = 16
    IMUXTotalNum0 = 16
    IMUXTotalNum1 = 48
    OpinTypes = ["o", "q", "mux_o"]
    OpinTypeProbs = [1 / 3.0, 1 / 3.0, 1 / 3.0]
    IpinTypes = ["i", "x"]
    IpinTypeProbs = [0.5, 0.5]
    # Variable definitions
    maxSegLen   = 16
    numAddition = 4 # opin = 2, imux = 2, 
    varSegNums  = list(variables[0:maxSegLen])
    varBendProb = list(variables[maxSegLen:(2 * maxSegLen)])
    varBendPos  = list(variables[(2 * maxSegLen):(3 * maxSegLen)])
    varBendType = list(variables[(3 * maxSegLen):(4 * maxSegLen)])

    # New Segments
    # -> Basic parameters
    tile_length = 30
    segRmetal = 7.862 * tile_length
    segCmetal = round(0.215 * tile_length / 2, 5) / pow(10, 15)
    segDrivers = getSegmentsSet()
    # -> Limits of segment quantities
    numSegmentSteps = list(map(lambda x: x * 2, [length for length in range(1, maxSegLen + 1)]))
    minSegmentSteps = [5, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    maxSegmentSteps = [15, 12, 8, 8, 5, 5, 0, 3, 0, 2, 0, 2, 0, 0, 0, 0]
    # maxSegmentSteps = [10, 5, 5, 5, 3, 3, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1]
    scaleSegmentRelations   = [0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, ]
    scaleOtherTypeRelations = [0.25, 0.25, 0.25, 0.25]
    # -> Segment quantity offsets
    segNumOffset = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
    for idx in range(len(varSegNums)): 
        varSegNums[idx] = max(0.0, (varSegNums[idx] - segNumOffset[idx]) / (1.0 - segNumOffset[idx])) 
    # -> Switch types
    # maxrate = 100.0
    # switch_type = ["U", "D", "-"]
    # switch_type_prob_short = [0.25, 0.25, 0.5]
    # switch_type_prob_long = [0.1, 0.1, 0.8]
    # -> Go!
    # new_chan_width = chan_width
    # prev_seg = copy.deepcopy(segs)
    # -> -> Validity
    valid = True
    # -> -> Generate segments
    # -> -> -> Numbers of segments
    segNums = []
    for idx in range(0, len(varSegNums)):
        portion = varSegNums[idx]
        segNums.append(round(minSegmentSteps[idx] + (maxSegmentSteps[idx] - minSegmentSteps[idx]) * portion) * numSegmentSteps[idx])
    totalSegNum = float(sum(segNums))
    type_to_num = {}
    for i in range(len(segNums)):
        if segNums[i] != 0:
            segType = 'l' + str(i + 1)
            type_to_num[segType] = segNums[i] // numSegmentSteps[i]
    segments = []
    for length in range(1, maxSegLen + 1):
        segment = bendSegmentation()
        segment.length = length
        segment.Rmetal = str(segRmetal)
        segment.Cmetal = str(segCmetal)
        segment.driver = str(length)
        segment.driver_para = (str(segDrivers[length]['Tdel']), str(
            segDrivers[length]['mux_trans_size']), str(segDrivers[length]['buf_size']))
        segment.is_shortSeg = False if length > 6 else True
        segment.freq = segNums[length - 1]
        segment.net_idx = length
        segment.name = "l" + str(length)
        segment.bend_list = []
        if length > 1: 
            segment.bend_list = ['-'] * (length - 1)
            if varBendProb[length - 1] > 0.5 and length > 2: 
                position = int(round((length - 2) * varBendPos[length - 1])) if length <= 6 else int(round((length/2 - 1) * varBendPos[length - 1]))
                bendType = "U" if varBendType[length - 1] > 0.5 else "D"
                segment.bend_list[position] = bendType
        segments.append(segment)
    tmplist = []
    for segment in segments: 
        if segment.freq > 0.0: 
            tmplist.append(segment)
            # print("Segment Quantity:", segment.length, ":", round(segment.freq))
    segments = tmplist
    # -> -> -> Validate the segments, such as check_circle(bend_list), 
    for segment in segments: 
        if len(segment.bend_list) > 0: 
            valid = valid and not check_circle(segment.bend_list)
    # print("Validity (after segment generation):", valid)
    # print("Generated segments: ")
    # list(map(lambda x: x.show(), segments))
    # -> -> -> Channel width
    chanWidth = int(totalSegNum)
    # print("Channel width: ", chanWidth)

    # New Driving Relations
    # -> Utilities
    def randomPick(itemList, probs, number):
        result = set()
        assert len(itemList) >= number, "Cannot randomly pick " + str(number) + " items in a list of " + str(len(itemList)) + " items. "
        while len(result) < number:  
            x = random.uniform(0, 1)
            c_prob = 0.0
            for item, prob in zip(itemList, probs):
                c_prob += prob
                if x < c_prob: 
                    break
            result.add(item)
        return list(result)
    # -> IMUX driving relations
    relationsIMUX = []
    # -> -> From segments
    for segment in segments:
        connection = From_inf()
        connection.type = "seg"
        connection.name = segment.name
        connection.total_froms = int(segNums[segment.length - 1] / segment.length / 2)
        connection.num_foreach = connection.total_froms
        connection.pin_types = ""
        connection.reuse = 1 if segment.length <= 6 else 0
        # connection.reuse = 1 if varConnReuseIMUX[(segment.length - 1)] > 0.2 else 0
        connection.switchpoint = 0
        if connection.num_foreach > 0: 
            relationsIMUX.append(connection)
    # -> -> From opins, clb
    connection = From_inf()
    connection.type = "pb"
    connection.name = "clb"
    connection.total_froms = PbTotalNum
    connection.num_foreach = int(round(0.25 * connection.total_froms))
    # connection.num_foreach = int(round(scaleOtherTypeRelations[0] * connection.total_froms * varConnNumsIMUX[(maxSegLen - 1) + 1]))
    connection.pin_types = " ".join(randomPick(OpinTypes, OpinTypeProbs, random.randint(0, len(OpinTypes))))
    connection.reuse = 1
    # connection.reuse = 1 if varConnReuseIMUX[(maxSegLen - 1) + 1] > 0.2 else 0
    connection.switchpoint = 0
    if connection.num_foreach > 0 and len(connection.pin_types) > 0: 
        relationsIMUX.append(connection)
    # -> -> From opins, oxbar
    connection = From_inf()
    connection.type = "omux"
    connection.name = "oxbar"
    connection.total_froms = OxbarTotalNum
    connection.num_foreach = int(round(0.125 * connection.total_froms))
    # connection.num_foreach = int(round(scaleOtherTypeRelations[1] * connection.total_froms * varConnNumsIMUX[(maxSegLen - 1) + 2]))
    connection.pin_types = ""
    connection.reuse = 1
    # connection.reuse = 1 if varConnReuseIMUX[(maxSegLen - 1) + 2] > 0.2 else 0
    connection.switchpoint = 0
    if connection.num_foreach > 0: 
        relationsIMUX.append(connection)

    
    # -> -> From glb
    connection = From_inf()
    connection.type = "glb"
    connection.name = "glb"
    connection.total_froms = OxbarTotalNum
    connection.num_foreach = int(round(0.125 * connection.total_froms))
    # connection.num_foreach = int(round(scaleOtherTypeRelations[1] * connection.total_froms * varConnNumsIMUX[(maxSegLen - 1) + 2]))
    connection.pin_types = ""
    connection.reuse = 1
    # connection.reuse = 1 if varConnReuseIMUX[(maxSegLen - 1) + 2] > 0.2 else 0
    connection.switchpoint = 0
    if connection.num_foreach > 0: 
        relationsIMUX.append(connection)
    # -> -> From ipins, reuse = 1

    # connection = From_inf()
    # connection.type = "imux"
    # connection.name = "clb"
    # connection.total_froms = IMUXTotalNum0 * 0
    # connection.num_foreach = int(round(scaleOtherTypeRelations[2] * connection.total_froms * varConnNumsIMUX[(maxSegLen - 1) + 3]))
    # # connection.pin_types = " ".join(randomPick(IpinTypes, IpinTypeProbs, random.randint(0, len(IpinTypes))))
    # connection.pin_types = "i x"
    # connection.reuse = 1 if varConnReuseIMUX[(maxSegLen - 1) + 3] > 0.2 else 0
    # connection.switchpoint = 0
    # if connection.num_foreach > 0 and len(connection.pin_types) > 0: 
    #     relationsIMUX.append(connection)
    # # -> -> From ipins, reuse = 0
    # connection = From_inf()
    # connection.type = "imux"
    # connection.name = "clb"
    # connection.total_froms = IMUXTotalNum1
    # connection.num_foreach = 1 if varConnNumsIMUX[(maxSegLen - 1) + 4] > 0.5 else 0
    # # connection.num_foreach = int(round(scaleOtherTypeRelations[3] * connection.total_froms * varConnNumsIMUX[(maxSegLen - 1) + 4]))
    # connection.pin_types = "Ia Ib Ic Id Ie If Ig Ih"
    # connection.reuse = 0
    # # connection.reuse = 1 if varConnReuseIMUX[(maxSegLen - 1) + 4] > 0.2 else 0
    # connection.switchpoint = 0
    # if connection.num_foreach > 0 and len(connection.pin_types) > 0: 
    #     relationsIMUX.append(connection)
    # -> -> Finally
    relationsIMUX = {"Ia Ic Ie Ig": relationsIMUX, }

    # -> ToMUXNum
    numSegs = {}
    for segment in segments: 
        numSegs[segment.name] = int(segment.freq / segment.length / 2)

    # -> GSB driving relations
    relationsGSB = {}
    for seg1 in segments: 
        # -> -> From segments
        relation = []
        for seg2 in segments: 
            connection = From_inf()
            connection.type = "seg"
            connection.name = seg2.name
            connection.total_froms = int(segNums[seg2.length - 1] / seg2.length / 2)
            connection.num_foreach = connection.total_froms
            connection.pin_types = ""
            connection.reuse = 1 if seg1.length <= 6 and seg2.length <= 6 else 0
            # connection.reuse = 1 if varConnReuseGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (seg2.length - 1)] > (0.2 + seg1.length / float(maxSegLen)) else 0
            connection.switchpoint = 0
            if connection.num_foreach > 0: 
                relation.append(connection)
        # -> -> From opins, clb
        connection = From_inf()
        connection.type = "pb"
        connection.name = "clb"
        connection.total_froms = PbTotalNum
        connection.num_foreach = int(round(0.25 * connection.total_froms))
        # connection.num_foreach = int(round(scaleOtherTypeRelations[0] * connection.total_froms * varConnNumsGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 1]))
        connection.pin_types = " ".join(randomPick(OpinTypes, OpinTypeProbs, random.randint(0, len(OpinTypes))))
        connection.reuse = 1 if seg1.length <= 6 else 0
        # connection.reuse = 1 if varConnReuseGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 1] > (0.4 + seg1.length / float(maxSegLen)) else 0
        connection.switchpoint = 0
        if connection.num_foreach > 0 and len(connection.pin_types) > 0: 
            relation.append(connection)
        # -> -> From opins, oxbar
        connection = From_inf()
        connection.type = "cas"
        connection.name = "cas"
        connection.total_froms = OxbarTotalNum
        connection.num_foreach = int(round(0.125 * connection.total_froms))
        # connection.num_foreach = int(round(scaleOtherTypeRelations[1] * connection.total_froms * varConnNumsGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 2]))
        connection.pin_types = ""
        connection.reuse = 1 if seg1.length <= 6 else 0
        # connection.reuse = 1 if varConnReuseGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 2] > (0.4 + seg1.length / float(maxSegLen)) else 0
        connection.switchpoint = 0
        if connection.num_foreach > 0: 
            relation.append(connection)
        # -> -> From ipins, reuse = 1
        connection = From_inf()
        connection.type = "imux"
        connection.name = "clb"
        connection.total_froms = IMUXTotalNum0 * 0
        connection.num_foreach = int(round(0.125 * connection.total_froms))
        # connection.pin_types = " ".join(randomPick(IpinTypes, IpinTypeProbs, random.randint(0, len(IpinTypes))))
        connection.pin_types = "i x"
        connection.reuse = 1
        connection.switchpoint = 0
        if connection.num_foreach > 0 and len(connection.pin_types) > 0: 
            relation.append(connection)
        # -> -> From ipins, reuse = 0
        connection = From_inf()
        connection.type = "imux"
        connection.name = "clb"
        connection.total_froms = IMUXTotalNum1 * 0
        connection.num_foreach = int(round(0.125 * connection.total_froms))
        connection.pin_types = "Ia Ib Ic Id Ie If Ig Ih"
        connection.reuse = 1
        connection.switchpoint = 0
        if connection.num_foreach > 0 and len(connection.pin_types) > 0: 
            relation.append(connection)
        relationsGSB[seg1.name] = relation
        
    # print("Generated relationsIMUX: ")
    # list(map(lambda x: x.show(), relationsIMUX["Ia Ic Ie Ig"]))
    # print("Generated relationsGSB: ")
    # list(map(lambda x: map(lambda y: y.show(), x), relationsGSB.values()))
    # -> numForeach, muxNums
    others = {'num_foreach': 12, 'mux_nums': 16}

    relations = [relationsGSB, numSegs, relationsIMUX, others]

    # print(segments)
    # print()
    # for elem in relations: 
    #     print(elem)
    # print()
    # print("Channel Width:", chanWidth)

    return segments, relations, chanWidth, type_to_num

def calcConnectivity(segments, relations): 
    relationsIMUX, relationsGSB = relations[2], relations[0]
    countSegs = len(segments)
    countDiv = 1 + len(relationsGSB)
    countIMUX = len(relationsIMUX)
    countGSB = 0
    for key, value in relationsGSB.items(): 
        countGSB += len(value)
    average = float(countIMUX + countGSB) / countDiv

    return average / countSegs

def get_rval(trial):
    vals = trial["misc"]["vals"]
    rval = {}
    for k, v in list(vals.items()):
        if v:
            rval[k] = v[0]
    return rval

def writeArch(elem, outfile):
    f = open(outfile, "wb+")
    f.write(prettify(elem))
    f.close()
    
def objective(variables, space, archTree, base_result, new_arch_name, exec_file, blif_dir, blif_names, connect_string, same_trial_limit):
    
    # print(variables)
    
    size_map = mux_trans_sizes()
    areaDict = {}
    areaDict["gsb_mux"] = {}
    areaDict["imux_mux"] = {}
    for i in range(1, 13):
        areaDict[str(i)] = {}
    for k in areaDict.keys():
        for i in range(30):
            areaDict[k][i] = compute_area(i, size_map[k])
    areaPair = [0, areaDict]

    segments, relations, chanWidth, typeToNum = genArch_seg(variables)
    # segments, relations, chanWidth = genArch3(variables)
    # segments, relations, chanWidth = genArch2(variables)
    modifyArch_V3_bent(segments, relations, archTree)
    modifyArch_addMedium(archTree)
    (gsbMUXFanin, imuxMUXFanin) = generateTwoStageMux_v200(archTree)
    
    archfileTmp = new_arch_name + 'Tmp.xml'
    archfile = new_arch_name + '.xml'
    modifyMUXSize(archTree, gsbMUXFanin, imuxMUXFanin, typeToNum)
    writeArch(archTree["root"].getroot(), archfileTmp)
    convert_vib2openFPGAvib(archfileTmp, archfile)
    # print('generate done')
    # violations
    # violations = countViolations(gsbMUXFanin, imuxMUXFanin, segments, list(relations[2].values())[0], areaPair, False)
    # if violations > 0: 
    #     # return 20 * violations
    #     return {
    #         'why': 'violations',
    #         'status': STATUS_FAIL,
    #     }
    # print('pass prune 1')
    # violations
    connectivity = calcConnectivity(segments, relations)
    if connectivity < 0.65:
        return {
            'why': 'connectivity',
            'status': STATUS_FAIL,
        }
    print('pass prune 2')
    # if chanWidth < 80:  
    if chanWidth < 80 or chanWidth > 200: 
        return {
            'why': 'chanWidth',
            'status': STATUS_FAIL,
        }
    print('pass prune 3')
    # write arch


    tmp_trials = MongoTrials(connect_string)
    counter = 0
    for t in tmp_trials:
        if t['result']['status'] == STATUS_OK:
            if variables == space_eval(space, get_rval(t)):
                counter += 1
    if counter >= same_trial_limit:
        return {
            'why': 'exceed trial limit',
            'status': STATUS_FAIL
        }
    
    # delay_ratio = {}
    # # run benchmarks
    # # base_geom_avg_delay = get_geom_avg(base_result, 'Crit Path')
    # base_delay = base_result['Crit Path'].dropna()
    # with open(new_arch_name + '.csv', 'w') as csv_file:
    #     csv_file.write(',bles,FPGA size,Device Util,io Util,clb Util,num nets,clbs,Total Wirelength,Total logic block area, Total used logic block area,Total routing area,per logic tile routing area,Crit Path\n')
    # subprocess.run(['mkdir', '-p', new_arch_name])
    # for blif_name in blif_names:
    #     if pd.isna( base_result['Crit Path'][blif_name] ):
    #         continue
    #     else:
    #         subprocess.run(['mkdir', '-p', new_arch_name+'/'+blif_name])
    #         subprocess.run(['timeout','300m',exec_file, '../../'+new_arch_name+'.xml', blif_dir+'/'+blif_name+'.blif',  '--route_chan_width', str(chanWidth), '--full_stats', 'on', '--clock_modeling', 'ideal', '--device', 'ultimate', '--max_router_iterations', '400', '--target_ext_pin_util', 'clb:1.00,1.00', '--skip_sync_clustering_and_routing_results', 'on', '--constant_net_method', 'route', '--write_placement_delay_lookup', '../placement_delay_lookup.bin'], cwd = new_arch_name+'/'+blif_name)
    #         break
    # for blif_name in blif_names:
    #     if pd.isna( base_result['Crit Path'][blif_name] ):
    #         continue
    #     else:
    #         subprocess.run(['mkdir', '-p', new_arch_name+'/'+blif_name])
    #         #netfile = blif_dir + 'net/' + blif_name + '.net'
    #         #subprocess.run(['cp', netfile, new_arch_name+'/'+blif_name])
    #         subprocess.run(['timeout','300m',exec_file, '../../'+new_arch_name+'.xml', blif_dir+'/'+blif_name+'.blif',  '--route_chan_width', str(chanWidth), '--full_stats', 'on', '--clock_modeling', 'ideal', '--device', 'ultimate', '--max_router_iterations', '400', '--target_ext_pin_util', 'clb:1.00,1.00', '--skip_sync_clustering_and_routing_results', 'on', '--constant_net_method', 'route', '--read_placement_delay_lookup', '../placement_delay_lookup.bin'], cwd = new_arch_name+'/'+blif_name)
    #         subprocess.run(['./get_info.sh', new_arch_name, blif_name, new_arch_name + '.csv'])
    #         with open(new_arch_name + '.csv', 'r') as csv_file:
    #             new_result = pd.read_csv(csv_file, index_col=0)
    #             new_delay = new_result['Crit Path'].dropna()
    #             if blif_name in new_delay:
    #                 delay_ratio[blif_name] = (new_delay[blif_name] - base_delay[blif_name]) /  base_delay[blif_name]
    #                 logging.info(blif_name + ':' + str(delay_ratio[blif_name]))
    #         bench_PASS_number = new_result['Crit Path'].count()
    #         if bench_PASS_number < new_result.shape[0] - 1:
    #         # if bench_PASS_number < 1:
    #             subprocess.run(['rm', '-rf', new_arch_name])
    #             return {
    #                 # 'loss': base_geom_avg_delay * 1.3,
    #                 # 'status': STATUS_OK,
    #                 'status': STATUS_FAIL,
    #                 'bench_PASS_number': bench_PASS_number,
    #                 'results': new_result.to_dict()
    #             }
    # # save the arch file
    
    # dir_path = os.getcwd()
    # logging.info(delay_ratio)
    # t_ind = re.findall('[^/]+(?!.*/)', dir_path)[0]
    # file_list = []
    # logging.info(os.popen("ls ./").readlines())
    # for file in os.popen("ls ./").readlines():
    #     file = file.strip()
    #     logging.info(file[-3:])
    #     if (file[-3:] == 'xml') and (file != new_arch_name + '.xml'):
    #         file_list.append(file)
    # # if len(file_list) > 0:
    # #     cur_file = file_list[-1][0:-4]
    # #     cur_ind = cur_file.split('_')[-1]
    # #     # logging.info('current max xml index: ' + cur_ind)
    # # else:
    # #     cur_ind = 0
    # cur_ind = len(file_list)
    # record_name = t_ind + '_' + str(int(cur_ind) + 1) + '.xml'
    # subprocess.run(['mv', archfile, record_name])
    # # logging.info('the name of file to make is ' + t_ind + '_' + str(int(cur_ind) + 1) )


    # with open(new_arch_name + '.csv', 'r') as csv_file:
    #     new_result = pd.read_csv(csv_file, index_col=0)
    # bench_PASS_number = new_result['Crit Path'].count()
    # new_geom_avg_delay = get_geom_avg(new_result, 'Crit Path')
    # # Impro = f"{(new_geom_avg_delay - base_geom_avg_delay) / base_geom_avg_delay: .2%}"
    # avg_impro_ratio = np.array(list(delay_ratio.values())).mean()
    # # Impro = (new_geom_avg_delay - base_geom_avg_delay) / base_geom_avg_delay
    # return {
    #     'loss': avg_impro_ratio,
    #     'status': STATUS_OK,
    #     'bench_PASS_number': bench_PASS_number,
    #     'geom imp': avg_impro_ratio,
    #     'results': new_result.to_dict(),
    #     'arch_name': record_name
    # }

    delay_ratio = {}
    area_ratio = {}
    delay_area_product_ratio = {}
    # run benchmarks
    base_geom_avg_delay = get_geom_avg(base_result, 'Crit Path')
    base_delay = base_result['Crit Path'].dropna()
    base_area = base_result['Total routing area'].dropna()
    with open(new_arch_name + '.csv', 'w') as csv_file:
        csv_file.write(',bles,FPGA size,Device Util,io Util,clb Util,num nets,clbs,Total Wirelength,Total logic block area, Total used logic block area,Total routing area,per logic tile routing area,Crit Path\n')
    subprocess.run(['mkdir', '-p', new_arch_name])
    # for blif_name in blif_names:
    #     if pd.isna( base_result['Crit Path'][blif_name] ):
    #         continue
    #     else:
    #         subprocess.run(['mkdir', '-p', new_arch_name+'/'+blif_name])
    #         subprocess.run(['timeout','300m',exec_file, '../../'+new_arch_name+'.xml', blif_dir+'/'+blif_name+'.blif',  '--route_chan_width', str(chanWidth), '--full_stats', 'on', '--clock_modeling', 'ideal', '--device', 'ultimate', '--max_router_iterations', '400', '--target_ext_pin_util', 'clb:1.00,1.00', '--skip_sync_clustering_and_routing_results', 'on', '--timing_report_detail', 'detailed','--constant_net_method', 'route', '--write_placement_delay_lookup', '../placement_delay_lookup.xml'], cwd = new_arch_name+'/'+blif_name)
    #         break
    for blif_name in blif_names:
        if pd.isna( base_result['Crit Path'][blif_name] ):
            continue
        else:
            subprocess.run(['mkdir', '-p', new_arch_name+'/'+blif_name])
            #netfile = blif_dir + 'net/' + blif_name + '.net'
            #subprocess.run(['cp', netfile, new_arch_name+'/'+blif_name])
            subprocess.run(['timeout','300m',exec_file, '../../'+new_arch_name+'.xml', blif_dir+'/'+blif_name+'.blif',  '--route_chan_width', str(chanWidth), '--full_stats', 'on', '--clock_modeling', 'ideal', '--device', 'ultimate', '--max_router_iterations', '400', '--target_ext_pin_util', 'clb:1.00,1.00', '--skip_sync_clustering_and_routing_results', 'on', '--constant_net_method', 'route', '--place_delay_model', 'simple', '--timing_report_detail', 'detailed'], cwd = new_arch_name+'/'+blif_name)
            subprocess.run(['./get_info.sh', new_arch_name, blif_name, new_arch_name + '.csv'])
            with open(new_arch_name + '.csv', 'r') as csv_file:
                new_result = pd.read_csv(csv_file, index_col=0)
                new_delay = new_result['Crit Path'].dropna()
                new_area = new_result['Total routing area'].dropna()
                if blif_name in new_delay:
                    delay_ratio[blif_name] = (new_delay[blif_name] - base_delay[blif_name]) / base_delay[blif_name]
                    area_ratio[blif_name] = (new_area[blif_name] - base_area[blif_name]) / base_area[blif_name]
                    delay_area_product_ratio[blif_name] = (new_delay[blif_name] * new_area[blif_name] - base_delay[blif_name] * base_area[blif_name]) /  (base_delay[blif_name] * base_area[blif_name])
                    logging.info(blif_name + ': ' + "delay_imp:" + str(delay_ratio[blif_name]) + " area_imp:" + str(area_ratio[blif_name]) + " delay_area_product_imp:" + str(delay_area_product_ratio[blif_name]))
            bench_PASS_number = new_result['Crit Path'].count()
            if bench_PASS_number < new_result.shape[0]:
            # if bench_PASS_number < 1:
                subprocess.run(['rm', '-rf', new_arch_name])
                
                dir_path = os.getcwd()
                logging.info(delay_ratio)
                t_ind = re.findall('[^/]+(?!.*/)', dir_path)[0]
                file_list = []
                logging.info(os.popen("ls ./").readlines())
                for file in os.popen("ls ./").readlines():
                    file = file.strip()
                    logging.info(file[-3:])
                    if (file[-3:] == 'xml') and (file != new_arch_name + '.xml'):
                        file_list.append(file)
                # if len(file_list) > 0:
                #     cur_file = file_list[-1][0:-4]
                #     cur_ind = cur_file.split('_')[-1]
                #     # logging.info('current max xml index: ' + cur_ind)
                # else:
                #     cur_ind = 0
                cur_ind = len(file_list)
                record_name = t_ind + '_' + str(int(cur_ind) + 1) + '_failed.xml'
                subprocess.run(['mv', archfile, record_name])
                # save the arch file
                return {
                    # 'loss': base_geom_avg_delay * 1.3,
                    # 'status': STATUS_OK,
                    'why': 'low benchmark pass ratio',
                    'status': STATUS_FAIL,
                    'bench_PASS_number': bench_PASS_number,
                    'results': new_result.to_dict()
                    
                }
    
    dir_path = os.getcwd()
    logging.info(delay_ratio)
    t_ind = re.findall('[^/]+(?!.*/)', dir_path)[0]
    file_list = []
    logging.info(os.popen("ls ./").readlines())
    for file in os.popen("ls ./").readlines():
        file = file.strip()
        logging.info(file[-3:])
        if (file[-3:] == 'xml') and (file != new_arch_name + '.xml'):
            file_list.append(file)
    # if len(file_list) > 0:
    #     cur_file = file_list[-1][0:-4]
    #     cur_ind = cur_file.split('_')[-1]
    #     # logging.info('current max xml index: ' + cur_ind)
    # else:
    #     cur_ind = 0
    cur_ind = len(file_list)
    record_name = t_ind + '_' + str(int(cur_ind) + 1) + '.xml'
    subprocess.run(['mv', archfile, record_name])
    # logging.info('the name of file to make is ' + t_ind + '_' + str(int(cur_ind) + 1) )


    with open(new_arch_name + '.csv', 'r') as csv_file:
        new_result = pd.read_csv(csv_file, index_col=0)
    bench_PASS_number = new_result['Crit Path'].count()
    new_geom_avg_delay = get_geom_avg(new_result, 'Crit Path')
    # Impro = f"{(new_geom_avg_delay - base_geom_avg_delay) / base_geom_avg_delay: .2%}"
    avg_delay_ratio = np.array(list(delay_ratio.values())).mean()
    avg_area_ratio = np.array(list(area_ratio.values())).mean()
    area_dalay_product_avg_ratio = np.array(list(delay_area_product_ratio.values())).mean()
    Impro = (new_geom_avg_delay - base_geom_avg_delay) / base_geom_avg_delay
    return {
        'loss': area_dalay_product_avg_ratio,
        'status': STATUS_OK,
        'bench_PASS_number': bench_PASS_number,
        'delay imp': avg_delay_ratio,
        'area imp': avg_area_ratio,
        'results': new_result.to_dict(),
        'arch_name': record_name
    }

def get_args():
    default = '(default: %(default)s)'
    parser = argparse.ArgumentParser()
    parser.add_argument("-base_arch_file", type=str, required=True, help="baseline arch file")
    parser.add_argument("-base_csv_file", type=str, required=False, default="V200_baseline_v2.csv", help=f"baseline csv file, {default}")
    parser.add_argument("-new_arch_name", type=str, required=False, default="vpr_arch_wo_crossbar", help=f"new arch name, {default}")
    parser.add_argument("-parallel_number", type=int, required=False, default=1, help=f"parallel number, {default}")
    parser.add_argument("-exec_file", type=str, required=False, help="executable file")
    parser.add_argument("-blif_dir", type=str, required=False, help="blif file directory")
    parser.add_argument("-blif_names_file", type=str, required=False, default="blif_list", help=f"blif names file, {default}")
    parser.add_argument("-same_trial_limit", type=int, required=False, default=1, help=f"exact same trials limit, {default}")

    return parser.parse_args()


if __name__ == "__main__":

    logger = logging.getLogger('main')
    logdir = '.'
    logfile = logdir + "/logfile.log"
    logger_init(logger, logdir, logfile)

    args = get_args()
    base_arch_file = args.base_arch_file
    base_csv_file = args.base_csv_file
    new_arch_name = args.new_arch_name
    parallel_number = args.parallel_number
    same_trial_limit = args.same_trial_limit

    exec_file = args.exec_file
    blif_dir = args.blif_dir
    blif_names_file = args.blif_names_file

    base_arch_tree = {}
    with open(base_arch_file, 'r',encoding='utf-8') as base_arch_f:
         base_arch_tree['root'] = ET.parse(base_arch_f)
         base_arch_tree['segOrigin'] = getOriginSeg(base_arch_tree["root"])
    with open(base_csv_file, 'r') as base_csv_f:
        base_result = pd.read_csv(base_csv_f, index_col=0)
    with open(blif_names_file, 'r') as blif_names_f:
        blif_names = [line.strip() for line in blif_names_f.readlines()]

    maxSegLen   = 16
    numAddition = 4 
    space = [hp.uniform("var" + str(idx), 0.0, 1.0) for idx in range(maxSegLen * 4)]

    connect_string = "mongo+ssh://asicskl01:1234/foo_db/jobs"
    trials = MongoTrials(connect_string)

    fmin(
        # partial(objective, space=space, trials=trials, base_arch_tree=base_arch_tree, new_arch_name=new_arch_name),
        partial(objective, space=space, archTree = base_arch_tree, base_result=base_result, new_arch_name=new_arch_name, exec_file=exec_file, blif_dir=blif_dir, blif_names=blif_names, connect_string=connect_string, same_trial_limit=same_trial_limit),
        space=space,
        # algo=tpe.suggest,
        algo=partial(mix.suggest, p_suggest=[(0.1, rand.suggest), (0.9, tpe.suggest)]),
        # algo=partial(tpe.suggest, n_startup_jobs=1, n_EI_candidates=4),
        # max_evals=1,
        trials=trials,
        # connect_string = connect_string,
        # return_argmin=True,
        max_queue_len=parallel_number
    )
