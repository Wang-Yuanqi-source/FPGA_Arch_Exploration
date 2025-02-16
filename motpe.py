import pdb
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
from Generate_two_stage import From_inf, generateTwoStageMux, readArch2, writeArch2, findSeg, verify_fanin_ok, compute_area, countViolations

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
from xml.dom import minidom

import optuna

from Seeker_GSB import *

# Random arch
def genArch(variables):
    # Constants
    PbTotalNum = 8
    OxbarTotalNum = 16
    IMUXTotalNum0 = 16
    IMUXTotalNum1 = 48
    OpinTypes = ["o", "q", ]
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
    varConnNums = list(variables[(4 * maxSegLen):(4 * maxSegLen + (2 * maxSegLen + 2) * (maxSegLen + numAddition))])
    varConnNumsIMUX  = varConnNums[0:(maxSegLen + numAddition)]
    varConnReuseIMUX = varConnNums[(maxSegLen + numAddition):2 * (maxSegLen + numAddition)]
    varConnNumsGSB   = varConnNums[2 * (maxSegLen + numAddition):(maxSegLen + 2) * (maxSegLen + numAddition)]
    varConnReuseGSB  = varConnNums[(maxSegLen + 2) * (maxSegLen + numAddition):(2 * maxSegLen + 2) * (maxSegLen + numAddition)]

    # New Segments
    # -> Basic parameters
    tile_length = 30
    segRmetal = 7.862 * tile_length
    segCmetal = round(0.215 * tile_length / 2, 5) / pow(10, 15)
    segDrivers = getSegmentsSet()
    # -> Limits of segment quantities
    numSegmentSteps = list(map(lambda x: x * 2, [length for length in range(1, maxSegLen + 1)]))
    minSegmentSteps = [2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    maxSegmentSteps = [12, 12, 8, 8, 4, 4, 2, 2, 1, 1, 1, 1, 0, 0, 0, 0]
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
        connection.num_foreach = int(round(scaleSegmentRelations[segment.length - 1] * connection.total_froms * varConnNumsIMUX[(segment.length - 1)]))
        connection.pin_types = ""
        connection.reuse = 1 if segment.length <= 6 else 0
        # connection.reuse = 1 if varConnReuseIMUX[(segment.length - 1)] > 0.2 else 0
        connection.switchpoint = 0
        if connection.num_foreach > 0: 
            relationsIMUX.append(connection)
    # -> -> From opins, plb
    connection = From_inf()
    connection.type = "pb"
    connection.name = "plb"
    connection.total_froms = PbTotalNum
    connection.num_foreach = int(round(0.25 * connection.total_froms)) if varConnNumsIMUX[(maxSegLen - 1) + 1] > 0.5 else 0
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
    connection.num_foreach = int(round(0.125 * connection.total_froms)) if varConnNumsIMUX[(maxSegLen - 1) + 2] > 0.5 else 0
    # connection.num_foreach = int(round(scaleOtherTypeRelations[1] * connection.total_froms * varConnNumsIMUX[(maxSegLen - 1) + 2]))
    connection.pin_types = ""
    connection.reuse = 1
    # connection.reuse = 1 if varConnReuseIMUX[(maxSegLen - 1) + 2] > 0.2 else 0
    connection.switchpoint = 0
    if connection.num_foreach > 0: 
        relationsIMUX.append(connection)
    # -> -> From ipins, reuse = 1
    connection = From_inf()
    connection.type = "imux"
    connection.name = "plb"
    connection.total_froms = IMUXTotalNum0 * 0
    connection.num_foreach = int(round(scaleOtherTypeRelations[2] * connection.total_froms * varConnNumsIMUX[(maxSegLen - 1) + 3]))
    # connection.pin_types = " ".join(randomPick(IpinTypes, IpinTypeProbs, random.randint(0, len(IpinTypes))))
    connection.pin_types = "i x"
    connection.reuse = 1 if varConnReuseIMUX[(maxSegLen - 1) + 3] > 0.2 else 0
    connection.switchpoint = 0
    if connection.num_foreach > 0 and len(connection.pin_types) > 0: 
        relationsIMUX.append(connection)
    # -> -> From ipins, reuse = 0
    connection = From_inf()
    connection.type = "imux"
    connection.name = "plb"
    connection.total_froms = IMUXTotalNum1
    connection.num_foreach = 1 if varConnNumsIMUX[(maxSegLen - 1) + 4] > 0.5 else 0
    # connection.num_foreach = int(round(scaleOtherTypeRelations[3] * connection.total_froms * varConnNumsIMUX[(maxSegLen - 1) + 4]))
    connection.pin_types = "Ia Ib Ic Id Ie If Ig Ih"
    connection.reuse = 0
    # connection.reuse = 1 if varConnReuseIMUX[(maxSegLen - 1) + 4] > 0.2 else 0
    connection.switchpoint = 0
    if connection.num_foreach > 0 and len(connection.pin_types) > 0: 
        relationsIMUX.append(connection)
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
            connection.num_foreach = int(round(scaleSegmentRelations[segment.length - 1] * connection.total_froms * varConnNumsGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (seg2.length - 1)]))
            connection.pin_types = ""
            connection.reuse = 1 if seg1.length <= 6 and seg2.length <= 6 else 0
            # connection.reuse = 1 if varConnReuseGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (seg2.length - 1)] > (0.2 + seg1.length / float(maxSegLen)) else 0
            connection.switchpoint = 0
            if connection.num_foreach > 0: 
                relation.append(connection)
        # -> -> From opins, plb
        connection = From_inf()
        connection.type = "pb"
        connection.name = "plb"
        connection.total_froms = PbTotalNum
        connection.num_foreach = int(round(0.25 * connection.total_froms)) if varConnNumsGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 1] > 0.5 else 0
        # connection.num_foreach = int(round(scaleOtherTypeRelations[0] * connection.total_froms * varConnNumsGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 1]))
        connection.pin_types = " ".join(randomPick(OpinTypes, OpinTypeProbs, random.randint(0, len(OpinTypes))))
        connection.reuse = 1 if seg1.length <= 6 else 0
        # connection.reuse = 1 if varConnReuseGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 1] > (0.4 + seg1.length / float(maxSegLen)) else 0
        connection.switchpoint = 0
        if connection.num_foreach > 0 and len(connection.pin_types) > 0: 
            relation.append(connection)
        # -> -> From opins, oxbar
        connection = From_inf()
        connection.type = "omux"
        connection.name = "oxbar"
        connection.total_froms = OxbarTotalNum
        connection.num_foreach = int(round(0.125 * connection.total_froms)) if varConnNumsGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 2] > 0.5 else 0
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
        connection.name = "plb"
        connection.total_froms = IMUXTotalNum0 * 0
        connection.num_foreach = int(round(scaleOtherTypeRelations[2] * connection.total_froms * varConnNumsGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 3]))
        # connection.pin_types = " ".join(randomPick(IpinTypes, IpinTypeProbs, random.randint(0, len(IpinTypes))))
        connection.pin_types = "i x"
        connection.reuse = 1 if varConnReuseGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 3] > (0.4 + seg1.length / float(maxSegLen)) else 0
        connection.switchpoint = 0
        if connection.num_foreach > 0 and len(connection.pin_types) > 0: 
            relation.append(connection)
        # -> -> From ipins, reuse = 0
        connection = From_inf()
        connection.type = "imux"
        connection.name = "plb"
        connection.total_froms = IMUXTotalNum1 * 0
        connection.num_foreach = int(round(scaleOtherTypeRelations[3] * connection.total_froms * varConnNumsGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 4]))
        connection.pin_types = "Ia Ib Ic Id Ie If Ig Ih"
        connection.reuse = 1 if varConnReuseGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 4] > (0.4 + seg1.length / float(maxSegLen)) else 0
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

    # Print Info
    # print(segments)
    # print()
    # for elem in relations: 
    #     print(elem)
    # print()
    # print("Channel Width:", chanWidth)

    return segments, relations, chanWidth

# Random arch
def genArch2(variables):
    # Constants
    PbTotalNum = 8
    OxbarTotalNum = 16
    IMUXTotalNum0 = 16
    IMUXTotalNum1 = 48
    OpinTypes = ["o", "q", ]
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
    varConnNums = list(variables[(4 * maxSegLen):(4 * maxSegLen + (2 * maxSegLen + 2) * (maxSegLen + numAddition))])
    varConnNumsIMUX  = varConnNums[0:(maxSegLen + numAddition)]
    varConnReuseIMUX = varConnNums[(maxSegLen + numAddition):2 * (maxSegLen + numAddition)]
    varConnNumsGSB   = varConnNums[2 * (maxSegLen + numAddition):(maxSegLen + 2) * (maxSegLen + numAddition)]
    varConnReuseGSB  = varConnNums[(maxSegLen + 2) * (maxSegLen + numAddition):(2 * maxSegLen + 2) * (maxSegLen + numAddition)]

    # New Segments
    # -> Basic parameters
    tile_length = 30
    segRmetal = 7.862 * tile_length
    segCmetal = round(0.215 * tile_length / 2, 5) / pow(10, 15)
    segDrivers = getSegmentsSet()
    # -> Limits of segment quantities
    numSegmentSteps = list(map(lambda x: x * 2, [length for length in range(1, maxSegLen + 1)]))
    minSegmentSteps = [8, 2, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    maxSegmentSteps = [16, 10, 8, 12, 4, 4, 2, 2, 1, 1, 1, 1, 0, 0, 0, 0]
    # maxSegmentSteps = [10, 5, 5, 5, 3, 3, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1]
    scaleSegmentRelations   = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, ]
    scaleOtherTypeRelations = [0.5, 0.5, 0.5, 0.5]
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
        connection.num_foreach = int(round(scaleSegmentRelations[segment.length - 1] * connection.total_froms * varConnNumsIMUX[(segment.length - 1)]))
        connection.pin_types = ""
        connection.reuse = 1 if segment.length <= 6 else 0
        # connection.reuse = 1 if varConnReuseIMUX[(segment.length - 1)] > 0.2 else 0
        connection.switchpoint = 0
        if connection.num_foreach > 0: 
            relationsIMUX.append(connection)
    # -> -> From opins, plb
    connection = From_inf()
    connection.type = "pb"
    connection.name = "plb"
    connection.total_froms = PbTotalNum
    connection.num_foreach = int(round(0.25 * connection.total_froms)) if varConnNumsIMUX[(maxSegLen - 1) + 1] > 0.5 else 0
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
    connection.num_foreach = int(round(0.125 * connection.total_froms)) if varConnNumsIMUX[(maxSegLen - 1) + 2] > 0.5 else 0
    # connection.num_foreach = int(round(scaleOtherTypeRelations[1] * connection.total_froms * varConnNumsIMUX[(maxSegLen - 1) + 2]))
    connection.pin_types = ""
    connection.reuse = 1
    # connection.reuse = 1 if varConnReuseIMUX[(maxSegLen - 1) + 2] > 0.2 else 0
    connection.switchpoint = 0
    if connection.num_foreach > 0: 
        relationsIMUX.append(connection)
    # -> -> From ipins, reuse = 1
    connection = From_inf()
    connection.type = "imux"
    connection.name = "plb"
    connection.total_froms = IMUXTotalNum0 * 0
    connection.num_foreach = int(round(scaleOtherTypeRelations[2] * connection.total_froms * varConnNumsIMUX[(maxSegLen - 1) + 3]))
    # connection.pin_types = " ".join(randomPick(IpinTypes, IpinTypeProbs, random.randint(0, len(IpinTypes))))
    connection.pin_types = "i x"
    connection.reuse = 1 if varConnReuseIMUX[(maxSegLen - 1) + 3] > 0.2 else 0
    connection.switchpoint = 0
    if connection.num_foreach > 0 and len(connection.pin_types) > 0: 
        relationsIMUX.append(connection)
    # -> -> From ipins, reuse = 0
    connection = From_inf()
    connection.type = "imux"
    connection.name = "plb"
    connection.total_froms = IMUXTotalNum1
    connection.num_foreach = 1 if varConnNumsIMUX[(maxSegLen - 1) + 4] > 0.5 else 0
    # connection.num_foreach = int(round(scaleOtherTypeRelations[3] * connection.total_froms * varConnNumsIMUX[(maxSegLen - 1) + 4]))
    connection.pin_types = "Ia Ib Ic Id Ie If Ig Ih"
    connection.reuse = 0
    # connection.reuse = 1 if varConnReuseIMUX[(maxSegLen - 1) + 4] > 0.2 else 0
    connection.switchpoint = 0
    if connection.num_foreach > 0 and len(connection.pin_types) > 0: 
        relationsIMUX.append(connection)
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
            connection.num_foreach = int(round(scaleSegmentRelations[segment.length - 1] * connection.total_froms * varConnNumsGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (seg2.length - 1)]))
            connection.pin_types = ""
            connection.reuse = 1 if seg1.length <= 6 and seg2.length <= 6 else 0
            # connection.reuse = 1 if varConnReuseGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (seg2.length - 1)] > (0.2 + seg1.length / float(maxSegLen)) else 0
            connection.switchpoint = 0
            if connection.num_foreach > 0: 
                relation.append(connection)
        # -> -> From opins, plb
        connection = From_inf()
        connection.type = "pb"
        connection.name = "plb"
        connection.total_froms = PbTotalNum
        connection.num_foreach = int(round(0.25 * connection.total_froms)) if varConnNumsGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 1] > 0.5 else 0
        # connection.num_foreach = int(round(scaleOtherTypeRelations[0] * connection.total_froms * varConnNumsGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 1]))
        connection.pin_types = " ".join(randomPick(OpinTypes, OpinTypeProbs, random.randint(0, len(OpinTypes))))
        connection.reuse = 1 if seg1.length <= 6 else 0
        # connection.reuse = 1 if varConnReuseGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 1] > (0.4 + seg1.length / float(maxSegLen)) else 0
        connection.switchpoint = 0
        if connection.num_foreach > 0 and len(connection.pin_types) > 0: 
            relation.append(connection)
        # -> -> From opins, oxbar
        connection = From_inf()
        connection.type = "omux"
        connection.name = "oxbar"
        connection.total_froms = OxbarTotalNum
        connection.num_foreach = int(round(0.125 * connection.total_froms)) if varConnNumsGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 2] > 0.5 else 0
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
        connection.name = "plb"
        connection.total_froms = IMUXTotalNum0 * 0
        connection.num_foreach = int(round(scaleOtherTypeRelations[2] * connection.total_froms * varConnNumsGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 3]))
        # connection.pin_types = " ".join(randomPick(IpinTypes, IpinTypeProbs, random.randint(0, len(IpinTypes))))
        connection.pin_types = "i x"
        connection.reuse = 1 if varConnReuseGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 3] > (0.4 + seg1.length / float(maxSegLen)) else 0
        connection.switchpoint = 0
        if connection.num_foreach > 0 and len(connection.pin_types) > 0: 
            relation.append(connection)
        # -> -> From ipins, reuse = 0
        connection = From_inf()
        connection.type = "imux"
        connection.name = "plb"
        connection.total_froms = IMUXTotalNum1 * 0
        connection.num_foreach = int(round(scaleOtherTypeRelations[3] * connection.total_froms * varConnNumsGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 4]))
        connection.pin_types = "Ia Ib Ic Id Ie If Ig Ih"
        connection.reuse = 1 if varConnReuseGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 4] > (0.4 + seg1.length / float(maxSegLen)) else 0
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

    # Print Info
    # print(segments)
    # print()
    # for elem in relations: 
    #     print(elem)
    # print()
    # print("Channel Width:", chanWidth)

    return segments, relations, chanWidth

# Random arch
def genArch3(variables):
    # Constants
    PbTotalNum = 8
    OxbarTotalNum = 16
    IMUXTotalNum0 = 16
    IMUXTotalNum1 = 48
    OpinTypes = ["o", "q", ]
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
    varConnNums = list(variables[(4 * maxSegLen):(4 * maxSegLen + (2 * maxSegLen + 2) * (maxSegLen + numAddition))])
    varConnNumsIMUX  = varConnNums[0:(maxSegLen + numAddition)]
    varConnReuseIMUX = varConnNums[(maxSegLen + numAddition):2 * (maxSegLen + numAddition)]
    varConnNumsGSB   = varConnNums[2 * (maxSegLen + numAddition):(maxSegLen + 2) * (maxSegLen + numAddition)]
    varConnReuseGSB  = varConnNums[(maxSegLen + 2) * (maxSegLen + numAddition):(2 * maxSegLen + 2) * (maxSegLen + numAddition)]

    # New Segments
    # -> Basic parameters
    tile_length = 30
    segRmetal = 7.862 * tile_length
    segCmetal = round(0.215 * tile_length / 2, 5) / pow(10, 15)
    segDrivers = getSegmentsSet()
    # -> Limits of segment quantities
    numSegmentSteps = list(map(lambda x: x * 2, [length for length in range(1, maxSegLen + 1)]))
    # minSegmentSteps = [5, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # maxSegmentSteps = [15, 12, 8, 8, 5, 5, 3, 3, 2, 2, 2, 2, 0, 0, 0, 0]
    minSegmentSteps = [2, 4, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    maxSegmentSteps = [12, 16, 6, 4, 3, 3, 3, 3, 2, 2, 2, 2, 0, 0, 0, 0]
    scaleSegmentRelations   = [0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, ]
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
        connection.num_foreach = int(round(scaleSegmentRelations[segment.length - 1] * connection.total_froms * varConnNumsIMUX[(segment.length - 1)]))
        connection.pin_types = ""
        connection.reuse = 1 if segment.length <= 6 else 0
        # connection.reuse = 1 if varConnReuseIMUX[(segment.length - 1)] > 0.2 else 0
        connection.switchpoint = 0
        if connection.num_foreach > 0: 
            relationsIMUX.append(connection)
    # -> -> From opins, plb
    connection = From_inf()
    connection.type = "pb"
    connection.name = "plb"
    connection.total_froms = PbTotalNum
    connection.num_foreach = int(round(0.25 * connection.total_froms)) if varConnNumsIMUX[(maxSegLen - 1) + 1] > 0.5 else 0
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
    connection.num_foreach = int(round(0.125 * connection.total_froms)) if varConnNumsIMUX[(maxSegLen - 1) + 2] > 0.5 else 0
    # connection.num_foreach = int(round(scaleOtherTypeRelations[1] * connection.total_froms * varConnNumsIMUX[(maxSegLen - 1) + 2]))
    connection.pin_types = ""
    connection.reuse = 1
    # connection.reuse = 1 if varConnReuseIMUX[(maxSegLen - 1) + 2] > 0.2 else 0
    connection.switchpoint = 0
    if connection.num_foreach > 0: 
        relationsIMUX.append(connection)
    # -> -> From ipins, reuse = 1
    connection = From_inf()
    connection.type = "imux"
    connection.name = "plb"
    connection.total_froms = IMUXTotalNum0 * 0
    connection.num_foreach = int(round(scaleOtherTypeRelations[2] * connection.total_froms * varConnNumsIMUX[(maxSegLen - 1) + 3]))
    # connection.pin_types = " ".join(randomPick(IpinTypes, IpinTypeProbs, random.randint(0, len(IpinTypes))))
    connection.pin_types = "i x"
    connection.reuse = 1 if varConnReuseIMUX[(maxSegLen - 1) + 3] > 0.2 else 0
    connection.switchpoint = 0
    if connection.num_foreach > 0 and len(connection.pin_types) > 0: 
        relationsIMUX.append(connection)
    # -> -> From ipins, reuse = 0
    connection = From_inf()
    connection.type = "imux"
    connection.name = "plb"
    connection.total_froms = IMUXTotalNum1
    connection.num_foreach = 1 if varConnNumsIMUX[(maxSegLen - 1) + 4] > 0.5 else 0
    # connection.num_foreach = int(round(scaleOtherTypeRelations[3] * connection.total_froms * varConnNumsIMUX[(maxSegLen - 1) + 4]))
    connection.pin_types = "Ia Ib Ic Id Ie If Ig Ih"
    connection.reuse = 0
    # connection.reuse = 1 if varConnReuseIMUX[(maxSegLen - 1) + 4] > 0.2 else 0
    connection.switchpoint = 0
    if connection.num_foreach > 0 and len(connection.pin_types) > 0: 
        relationsIMUX.append(connection)
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
            connection.num_foreach = int(round(scaleSegmentRelations[segment.length - 1] * connection.total_froms * varConnNumsGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (seg2.length - 1)]))
            connection.pin_types = ""
            connection.reuse = 1 if seg1.length <= 6 and seg2.length <= 6 else 0
            # connection.reuse = 1 if varConnReuseGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (seg2.length - 1)] > (0.2 + seg1.length / float(maxSegLen)) else 0
            connection.switchpoint = 0
            if connection.num_foreach > 0: 
                relation.append(connection)
        # -> -> From opins, plb
        connection = From_inf()
        connection.type = "pb"
        connection.name = "plb"
        connection.total_froms = PbTotalNum
        connection.num_foreach = int(round(0.25 * connection.total_froms)) if varConnNumsGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 1] > 0.5 else 0
        # connection.num_foreach = int(round(scaleOtherTypeRelations[0] * connection.total_froms * varConnNumsGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 1]))
        connection.pin_types = " ".join(randomPick(OpinTypes, OpinTypeProbs, random.randint(0, len(OpinTypes))))
        connection.reuse = 1 if seg1.length <= 6 else 0
        # connection.reuse = 1 if varConnReuseGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 1] > (0.4 + seg1.length / float(maxSegLen)) else 0
        connection.switchpoint = 0
        if connection.num_foreach > 0 and len(connection.pin_types) > 0: 
            relation.append(connection)
        # -> -> From opins, oxbar
        connection = From_inf()
        connection.type = "omux"
        connection.name = "oxbar"
        connection.total_froms = OxbarTotalNum
        connection.num_foreach = int(round(0.125 * connection.total_froms)) if varConnNumsGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 2] > 0.5 else 0
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
        connection.name = "plb"
        connection.total_froms = IMUXTotalNum0 * 0
        connection.num_foreach = int(round(scaleOtherTypeRelations[2] * connection.total_froms * varConnNumsGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 3]))
        # connection.pin_types = " ".join(randomPick(IpinTypes, IpinTypeProbs, random.randint(0, len(IpinTypes))))
        connection.pin_types = "i x"
        connection.reuse = 1 if varConnReuseGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 3] > (0.4 + seg1.length / float(maxSegLen)) else 0
        connection.switchpoint = 0
        if connection.num_foreach > 0 and len(connection.pin_types) > 0: 
            relation.append(connection)
        # -> -> From ipins, reuse = 0
        connection = From_inf()
        connection.type = "imux"
        connection.name = "plb"
        connection.total_froms = IMUXTotalNum1 * 0
        connection.num_foreach = int(round(scaleOtherTypeRelations[3] * connection.total_froms * varConnNumsGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 4]))
        connection.pin_types = "Ia Ib Ic Id Ie If Ig Ih"
        connection.reuse = 1 if varConnReuseGSB[(seg1.length - 1) * (maxSegLen + numAddition) + (maxSegLen - 1) + 4] > (0.4 + seg1.length / float(maxSegLen)) else 0
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

    # Print Info
    # print(segments)
    # print()
    # for elem in relations: 
    #     print(elem)
    # print()
    # print("Channel Width:", chanWidth)

    return segments, relations, chanWidth

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

if __name__ == "__main__": 
    # analyze the argv 
    caller = Caller.Caller(sys.argv)
    # read the arch
    archs = readArch(caller)
    # time
    startTime = datetime.datetime.now()
    # for area evaluate
    size_map = mux_trans_sizes()
    areaDict = {}
    areaDict["gsb_mux"] = {}
    areaDict["imux_mux"] = {}
    for i in range(1, 13):
        areaDict[str(i)] = {}
    for k in areaDict.keys():
        for i in range(30):
            areaDict[k][i] = compute_area(i, size_map[k])
    print("area_dict:")
    print(areaDict)
    areaPair = [0, areaDict]
    # area constraints 
    isAreaCons = True if caller.area_cons == 1 else False
    # read basic arch
    archName = list(archs.keys())[0]
    archTree = archs[archName]
    # logger
    logger = logging.getLogger('main')
    logdir = caller.task_dir + "/" + caller.run_dir[-1] + "/optimizeArchs/" + archName
    logfile = logdir + "/logfile.log"
    logger_init(logger, logdir, logfile)
    # get baseline info
    baseWorkdir = caller.task_dir + "/" + caller.run_dir[-1] + "/optimizeArchs/" + archName + "/baseline"
    archfile = caller.vtr_flow_dir + "/" + caller.arch_dir + "/" + archName
    if os.path.exists(baseWorkdir):
        logger.error("Base work dir is already exist")
        raise SeekerError("Base work dir is already exist")
    else:
        os.system("mkdir " + baseWorkdir)
    baseInfo = baselineInfo_cbsb()
    logger.info("Base Info: ")
    logger.info(baseInfo)
    # init the work dir
    optWorkDir = caller.task_dir + "/" + caller.run_dir[-1] + "/optimizeArchs/" + archName + "/workdir"
    optArchiveDir = caller.task_dir + "/" + caller.run_dir[-1] + "/optimizeArchs/" + archName + "/archive"
    if os.path.exists(optWorkDir):
        logger.error("Opt Work dir is already exist")
        raise SeekerError("Opt Work dir is already exist")
    else:
        os.system("mkdir " + optWorkDir)
    # analyze basic arch
    initSeg = getArchSegmentation(archTree["segOrigin"])
    initRelations = getGsbArchFroms(archTree["root"])
    initChanWidth = 158
    (gsbMUXFanin, imuxMUXFanin) = generateTwoStageMux(archTree)
    initOkay = verify_fanin_ok(gsbMUXFanin, imuxMUXFanin, initSeg, list(initRelations[2].values())[0], areaPair, logger, False)
    # evaluate the baseline
    archfileStart = caller.task_dir + "/" + caller.run_dir[-1] + "/optimizeArchs/" + archName + "/startpoint"
    archfile = archfileStart + "/" + archName
    if os.path.exists(archfileStart):
        logger.error("archfile start dir is already exist")
        raise SeekerError("archfile start dir is already exist")
    else:
        os.system("mkdir " + archfileStart)
    writeArch(archTree["root"].getroot(), archfile)
    def evaluate(archfileStart, archfile, archName, chanWidth, info): 
        pool = multiprocessing.Pool(processes = caller.processes)
        for circuit in caller.circuits:
            workdir = archfileStart + "/" + circuit
            pool.apply_async(func=run_vpr_task, args=(caller, workdir, archfile, archName, circuit, chanWidth, False, 10800))
        pool.close()
        pool.join()
        cost, meanDelay, meanArea, meanAreaDelay = evaluateCost(archfileStart, caller, info, logger, False)
        return cost, meanDelay, meanArea, meanAreaDelay
    # print("BEGIN: Initial Testing")
    # cost, meanDelay, meanArea, meanAreaDelay = evaluate(archfileStart, archfile, archName, initChanWidth, baseInfo)
    # print(cost, meanDelay, meanArea, meanAreaDelay)
    # print("END: Initial Testing")

    # TPE optimization
    maxSegLen   = 16
    numAddition = 4 
    numVars = 4 * maxSegLen + (2 * maxSegLen + 2) * (maxSegLen + numAddition)
    archCount = 0
    def objective(trial): 
        variables = []
        for idx in range(numVars): 
            variables.append(trial.suggest_float("x{}".format(idx), 0.0, 1.0))
        BaseCost = 20 * 2
        global archCount
        segments, relations, chanWidth = genArch(variables)
        # segments, relations, chanWidth = genArch3(variables)
        # segments, relations, chanWidth = genArch2(variables)
        modifyArch_V3(segments, relations, archTree)
        modifyArch_addMedium(archTree)
        (gsbMUXFanin, imuxMUXFanin) = generateTwoStageMux(archTree)
        # violations
        violations = countViolations(gsbMUXFanin, imuxMUXFanin, segments, list(relations[2].values())[0], areaPair, logger, False)
        if violations > 0: 
            # return 20 * violations
            return [BaseCost + violations, BaseCost + violations]
        # violations
        connectivity = calcConnectivity(segments, relations)
        if connectivity < 0.65: 
            return [BaseCost, BaseCost]
        # if chanWidth < 80:  
        if chanWidth < 130 or chanWidth > 210: 
            return [BaseCost, BaseCost]
        # write arch
        print("Channel width:", chanWidth)
        archfileCount = caller.task_dir + "/" + caller.run_dir[-1] + "/optimizeArchs/" + archName + "/" + str(archCount)
        archfile = archfileCount + "/" + archName
        if os.path.exists(archfileCount):
            #raise SeekerError("archfile count " + str(archCount) + " dir is already exist")
            os.system("rm -rf " + archfileCount)
            os.system("mkdir " + archfileCount)
        else:
            os.system("mkdir " + archfileCount)
        writeArch(archTree["root"].getroot(), archfile)
        # test validity 1
        tmparchfile = archfileCount + "/tmptest/" + archName
        if not os.path.exists(archfileCount + "/tmptest"):
            os.system("mkdir " + archfileCount + "/tmptest")
        else: 
            os.system("rm -rf " + archfileCount + "/tmptest")
            os.system("mkdir " + archfileCount + "/tmptest")
        writeArch(archTree["root"].getroot(), tmparchfile)
        print("Testing tmp arch: ", archfileCount + "/tmptest")
        testResult = arch_test(caller, archfileCount + "/tmptest", tmparchfile, archName, "stereovision3.blif", chanWidth, False)
        os.system("rm -rf " + archfileCount + "/tmptest")
        if not testResult: 
            return [BaseCost, BaseCost]
        logger.info( "\tSegments :" + str(archCount))
        for s in segments:
            s.show(logger)
        logger.info( "\tRelations IMUX :" + str(archCount))
        for key, value in relations[2].items(): 
            logger.info( "\t\t :" + key)
            for r in value: 
                r.show(logger)
        logger.info( "\tRelations GSB :" + str(archCount))
        for key, value in relations[0].items(): 
            logger.info( "\t\t :" + key)
            for r in value: 
                r.show(logger)
        # run benchmarks
        archCount += 1
        pool = multiprocessing.Pool(processes = caller.processes)
        for circuit in caller.circuits:
            workdir = archfileCount + "/" + circuit
            pool.apply_async(func=run_vpr_task, args=(caller, workdir, archfile, archName, circuit, chanWidth, False, 7200))
        pool.close()
        pool.join()
        # cost, meanDelay, meanArea, meanAreaDelay = evaluateCost(archfileCount, caller, baseInfo, logger, False)
        cost, meanDelay, meanArea, meanAreaDelay = evaluateCostMultiObj(archfileCount, caller, baseInfo, logger, False)
        for circuit in caller.circuits:
            workdir = archfileCount + "/" + circuit
            os.system("rm -rf " + workdir)
        logger.info("\tThe " + str(archCount) + " Inner iteration: cost: " + str(cost) + "; mean delay (" + str(meanDelay) + "%)")
        logger.info("\t\tmean area (" + str(meanArea) +"%)"  + "   mean area-delay (" + str(meanAreaDelay) + "%)")
        return [cost + 1.0 + meanDelay / 100.0, cost + 1.0 + meanArea / 100.0] 
        
    study = optuna.create_study(sampler = optuna.samplers.TPESampler(), directions=["minimize", "minimize"])
    study.optimize(objective, n_trials=2 ** 16, show_progress_bar=True)
    
    # maxSegLen   = 16
    # numAddition = 4 
    # variables = [random.random() for _ in range(4 * maxSegLen + (2 * maxSegLen + 2) * (maxSegLen + numAddition))]
    # print(variables)
    # segments, relations, chanWidth = genArch(variables)
    # modifyArch_V3(segments, relations, archTree)
    # modifyArch_addMedium(archTree)
    # (faninGSB, faninGSB) = generateTwoStageMux(archTree)
    # minSegmentSteps = [2, 4, 2, 1, 0, 0, 2, 0, 0, 1, 0, 0, 0, 0, 0, 0]
    # maxSegmentSteps = [8, 10, 6, 3, 2, 2, 4, 1, 1, 3, 0, 0, 0, 0, 0, 0]
