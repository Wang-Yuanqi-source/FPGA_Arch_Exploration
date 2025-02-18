#同构保留，异构可能换成单列的直连
import sys
from xml.etree import ElementTree as ET

def get_global(segment_dict, nodes_dict):
    global_feature = []

    # 遍历 segment_dict 的键值 1 到 16
    for i in range(1, 17):  # 键值为 1 到 16
        str_key = str(i)  # 将键转换为字符串格式
        if str_key in segment_dict:
            # 如果键存在，取其 freq 作为特征
            global_feature.append(segment_dict[str_key]['freq'])
        else:
            # 如果不存在，特征为 0
            global_feature.append(0)

    # 统计 nodes_dict 中 type 为 mux 的节点数量
    mux_count = 0
    mux_types = ['mux', 'plb.mux', 'ble.mux']  # 假设 'mux' 类型的列表
    for node_name, node_data in nodes_dict.items():
        if node_data.get('type') in mux_types:
            mux_count += 1

    # 将 mux_count 除以 10
    mux_feature = mux_count / 10.0

    # 将 mux_feature 添加到 global_feature 列表中
    global_feature.append(mux_feature)

    return global_feature


def calculate_chan_width_from_xml(root):
    group = root.findall("vib_arch/vib[@name='vib0']/seg_group")
    # 查找所有 track_num 标签并将其值转换为 int
    track_nums = [int(elem.attrib.get('track_nums', '0')) for elem in group]
    # print(track_nums)
    # 计算 track_num 的总和
    total_track_nums_sum = sum(track_nums)

    return 2 * total_track_nums_sum

def create_segment_data_dict(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    chan_width = calculate_chan_width_from_xml(root)

    segementlist = root.find('segmentlist')

    # Initialize a dictionary to hold switch data
    segment_dict = {}

    for segment in segementlist:
        freq = float(float(segment.get('freq'))/float(chan_width))
        length = int(segment.get('length'))
        bend_element = segment.find('bend')
        if bend_element is None:
            route1 = length
            route2 = 0
            direct = 0
        else:
            bend_pattern = bend_element.text.strip().split()
            # print(bend_pattern)
            if 'D' in bend_pattern:
                index_d = bend_pattern.index('D')
                route1 = index_d + 1  # 正确计数D的位置
                route2 = route1 - length
                # print(route1, route2)
                direct = 1
            elif 'U' in bend_pattern:
                index_u = bend_pattern.index('U')
                route1 = index_u + 1  # 正确计数U的位置
                route2 = length - route1
                # print(route1, route2)
                direct = -1
        segment_dict[segment.get('length')] = {'route1': route1, 'route2': route2, 'direct': direct, 'freq': freq}
    return segment_dict

def get_position(segment_dict, length, direct, in_out):
    route1 = segment_dict[length]['route1']
    route2 = segment_dict[length]['route2']

    if in_out == 'out':
        if direct == 'E':
            return route1,route2
        elif direct == 'W':
            return -route1,-route2
        elif direct == 'S':
            return route2, -route1
        elif direct == 'N':
            return -route2, route1
        else:
            return "out direct type not supported"
    elif in_out =='in':
        if direct == 'E':
            return -route2,-route1
        elif direct == 'W':
            return route2, route1
        elif direct == 'S':
            return -route1, route2
        elif direct == 'N':
            return route1, -route2
        else:
            return "in direct type not supported"
    else:
        return "in_out type not supported"

def get_connect_direct(segment_dict, length, direct, in_out):
    bend_type = segment_dict[length]['direct']
    directions = ['E', 'S', 'W', 'N']

    if in_out == 'out':
        return directions[(directions.index(direct) + bend_type) % 4]
    elif in_out =='in':
        return directions[(directions.index(direct) - bend_type) % 4]

# file_path = "D://Desktop//vtr//sha//jq13_55.xml"
# segment_data_dict = create_segment_data_dict(file_path)
# print(segment_data_dict)
# from_x, from_y = get_position(segment_data_dict, "8", "S", 'in')
# print(from_x, from_y)
# to_x, to_y = get_position(segment_data_dict, "5", "E", 'out')
# print(to_x, to_y)