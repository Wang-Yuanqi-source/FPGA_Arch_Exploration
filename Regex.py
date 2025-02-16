# -*- coding: utf-8 -*-

import re

def regex_task(r_type):
    if r_type == "circuit":
        return (re.compile("circuit_list_add=(.*)"))
    elif r_type == "arch":
        return (re.compile("arch_list_add=(.*)"))
    elif r_type == "vpr_params":
        return (re.compile("vpr_params=(.*)"))
    elif r_type == "circuits_dir":
        return (re.compile("circuits_dir=(.*)"))
    elif r_type == "archs_dir":
        return (re.compile("archs_dir=(.*)"))
    elif r_type == "status":
        return (re.compile("VPR suceeded"))
    elif r_type == "pack":
        return (re.compile(" --pack "))
    elif r_type == "place":
        return (re.compile(" --place "))
    elif r_type == "route":
        return (re.compile(" --route "))
    elif r_type == "route_chan_width":
        return (re.compile(" --route_chan_width "))
    elif r_type == "compare_pair":
        return (re.compile("compare_pair_add=(.*),(.*)"))
    elif r_type == "analyze_single":
        return (re.compile("analyze_add=(.*),(.*),(.*)"))
    elif r_type == "analyze_all":
        return (re.compile("analyze_add=(.*),(.*)"))
    elif r_type == "optimize_arch":
        return (re.compile("optimize_arch_add=(.*)"))
    elif r_type == "is_mutable_chan_width":
        return (re.compile("is_mutable_chan_width=true"))


def regex_reporter(r_type):
    if r_type == "logic_area":
        return re.compile(".*?Total logic block area \(Warning, need to add pitch of routing to blocks with height > 3\): (.*)")
    elif r_type == "routing_area":
        return re.compile("	Total routing area: (.*?), per logic tile")
    elif r_type == "delay":
        return re.compile("Final critical path: (.*?) ns")
    elif r_type == "chan_width":
        return re.compile("Circuit successfully routed with a channel width factor of ([0-9]+).")
    elif r_type == "routable":
        return re.compile("Circuit is unroutable with a channel width factor")
    elif r_type == "max_channel":
        return re.compile("\s+([0-9]+)\s+([0-9]+)\s+(.*?)\s+300")
    elif r_type == "channel":
        return re.compile("Best routing used a channel width factor of ([0-9]+).")
    elif r_type == "routing_area_bidir":
        return re.compile(".*?Assuming no buffer sharing \(pessimistic\). Total: (.*?), per logic tile: (.*?)")


def regex_analyzer(r_type):
    if r_type == "net":
        return re.compile("Net ([0-9]*) .*")
    elif r_type == "net_global":
        return re.compile("Net ([0-9]*) .*: global net .*")
    elif r_type == "node_source":
        return re.compile("Node:\s*([0-9]*)\s*SOURCE\s*\(([0-9]*),([0-9]*)\).*Delay: ([\.0-9]*).*")
    elif r_type == "node_sink":
        return re.compile("Node:\s*([0-9]*)\s*SINK\s*\(([0-9]*),([0-9]*)\)\s*Delay: ([\.0-9]*).*")
    elif r_type == "node_Opin":
        return re.compile("Node:\s*([0-9]*)\s*OPIN\s*\(([0-9]*),([0-9]*)\).*")
    elif r_type == "node_Ipin":
        return re.compile("Node:\s*([0-9]*)\s*IPIN\s*\(([0-9]*),([0-9]*)\).*")
    elif r_type == "from_node":
        return re.compile("From node.*From Type : (.*) To Type : (.*)")
    elif r_type == "path_opin":
        return re.compile("\tPath OPIN node :.*OPIN side : (.*) Location : \(([0-9]+), ([0-9]+)\)")
    elif r_type == "path_inpin":
        return re.compile("\tPath IPIN node :.*IPIN node: (.*) Location : \(([0-9]+), ([0-9]+)\)")
    elif r_type == "bend":
        return re.compile("Total bends: ([0-9]+)")
    elif r_type == "hard_points":
        return re.compile("Total used hard points: ([0-9]+)  bend_hard_points: ([0-9]+)")
    elif r_type == "switch_points":
        return re.compile("Total used switch points: ([0-9]+) bend_switch_points: ([0-9]+) radio: ([0-9\.]+)")


def regex_routingDelay(r_type):
    if r_type == "begin":
        return re.compile("#Path 1")
    elif r_type == "end":
        return re.compile("slack \(VIOLATED\).*")
    elif r_type == "routingDelay":
        return re.compile(".*\(inter-block routing\)\s+([0-9.]*)\s+([0-9.]*)")
