from xml.etree import ElementTree as ET
from torch_geometric.data import Data
from extract_clb import *
import pandas as pd
import torch
from get_switch import load_switch_dict
from get_segment import *
from get_utilis import *

def process_tile_to_nodes_dict(file_path, vib_name, position):
    """
    解析 XML 文件并处理节点字典，为每个节点添加 vib_position 特征，并为节点名字、inputs 和 outputs 添加基于 position 的前缀。
    """
    # 加载和解析 XML 文件

    tree = ET.parse(file_path)
    root = tree.getroot()

    switch_data_dict = load_switch_dict('switch_info.csv')
    segment_dict = create_segment_data_dict(file_path)

    nodes_dict = {}

    extract_clb_nodes(file_path, nodes_dict)

    # vib_xpath = f"vib_arch/vib[@name='{vib_name}']/multistage_muxs"
    vib_xpath = f"vib_arch/vib[@name='vib0']/multistage_muxs"
    multistage_muxs = root.find(vib_xpath)

    if multistage_muxs is None:
        raise ValueError(f"No 'multistage_muxs' element found under 'vib name={vib_name}'.")
    else:
        # 处理找到的 multistage_muxs
        add_mux_node(multistage_muxs, nodes_dict, switch_data_dict, segment_dict)

    # 处理节点字典，添加 vib_position 并修改名字和 inputs/outputs
    updated_nodes_dict = {}
    prefix = f"{position}_"  # 基于 position 生成前缀

    # for node_name, node_data in nodes_dict.items():
    #     # 给节点名字加上前缀
    #     new_node_name = prefix + node_name

    #     # 添加 vib_position 特征
    #     node_data['vib_position'] = position

    #     # 更新 inputs，给每个 input 加上前缀
    #     if 'inputs' in node_data:
    #         node_data['inputs'] = [prefix + inp for inp in node_data['inputs']]

    #     # 更新 outputs，给每个 output 加上前缀
    #     if 'outputs' in node_data:
    #         node_data['outputs'] = [prefix + out for out in node_data['outputs']]

    #     # 把更新后的节点数据加入新的字典
    #     updated_nodes_dict[new_node_name] = node_data

    global_feature = get_global(segment_dict, nodes_dict)

    directlist = root.find(f"directlist")
    add_directlist(nodes_dict, directlist)

    return nodes_dict, global_feature


def process_xml_to_data(file_path, label, node_labels):
    # 解析 XML 文件
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # # 定位到 architecture/vib_layout/fixed_layout 节点
    # fixed_layout = root.find("vib_layout/fixed_layout")
    # if fixed_layout is None:
    #     raise ValueError("No 'fixed_layout' element found under 'vib_layout'.")
    # print(file_path)
    
    # # 查找所有 <row> 标签
    # rows = fixed_layout.findall("row")
    # cols = fixed_layout.findall("col")
    
    # if not rows and not cols:
    #     raise ValueError("No 'row' or 'col' elements found under 'fixed_layout'.")

    # # 如果没有找到 <row>，则查找 <col>，并处理 starty 为 startx
    # if not rows:
    #     max_starty = 50
    #     vib_types = [None] * max_starty
        
    #     for col in cols:
    #         # 获取 <col> 标签中的 type 和 startx 属性
    #         vib_type = col.get("type")
    #         startx = col.get("startx")
            
    #         if vib_type is None or startx is None:
    #             raise ValueError(f"Invalid col element: {ET.tostring(col, encoding='unicode')}")
            
    #         # 检查是否为 "W-1"，并将其转换为 49
    #         if startx == "W-1":
    #             startx = 49
    #         else:
    #             startx = int(startx)  # 将 startx 转换为整数

    #         # 检查数组中的位置是否已经有值
    #         if vib_types[startx] is not None:
    #             raise ValueError(f"Conflict detected: startx {startx} already assigned to '{vib_types[startx]}', "
    #                              f"cannot reassign to '{vib_type}'.")

    #         # 将 vib_type 放入 vib_types 数组中的 startx 位置
    #         vib_types[startx] = vib_type
    # else:
    #     # 原始处理 <row> 标签的逻辑
    #     max_starty = 50
    #     vib_types = [None] * (max_starty)

    #     for row in rows:
    #         # 获取 <row> 标签中的 type 和 starty 属性
    #         vib_type = row.get("type")
    #         starty = row.get("starty")

    #         if vib_type is None or starty is None:
    #             raise ValueError(f"Invalid row element: {ET.tostring(row, encoding='unicode')}")

    #         # 检查是否为 "H-1"，并将其转换为 49
    #         if starty == "H-1":
    #             starty = 49
    #         else:
    #             starty = int(starty)  # 转换 starty 为整数

    #         # 检查数组中的位置是否已经有值
    #         if vib_types[starty] is not None:
    #             raise ValueError(f"Conflict detected: starty {starty} already assigned to '{vib_types[starty]}', "
    #                              f"cannot reassign to '{vib_type}'.")

    #         # 将 vib_type 放入 vib_types 数组中的 starty 位置
    #         vib_types[starty] = vib_type

    # # 检查是否有跳过的 starty 值
    # for i in range(len(vib_types)):
    #     if i > 0 and vib_types[i] is None and vib_types[i-1] is not None:
    #         raise ValueError(f"Missing vib_type for start {i}, but previous value at start {i-1} exists.")

    nodes_dict = {}
    global_features = []

    # for i in range(2, len(vib_types), 5):
    #     # 检查 vib_types[i] 是否为空，如果为空则用 vib_types[i-1] 代替
    #     if vib_types[i] is None and i > 0:
    #         vib_types[i] = vib_types[i - 1]
        
    #     # 如果 vib_types[i] 依然为空，可能是因为 i-1 也为空，可以继续处理或抛出异常
    #     if vib_types[i] is None:
    #         raise ValueError(f"vib_types[{i}] is still None after fallback to vib_types[{i-1}].")
        
    #     # 调用 process_tile_to_nodes_dict 函数并更新节点信息和全局特性
    #     node_dict, global_feature = process_tile_to_nodes_dict(file_path, vib_types[i], i//5)
    #     nodes_dict.update(node_dict)
    #     global_features.extend(global_feature)

    node_dict, global_feature = process_tile_to_nodes_dict(file_path, 0, 0)
    nodes_dict.update(node_dict)
    global_features.extend(global_feature)
    
    # print(nodes_dict)
    data = process_dict_to_data(nodes_dict, global_features, label, node_labels)

    return data



def process_dict_to_data(nodes_dict, global_features, label, node_labels):

    nodes_dict['startpoint'] = {
        'type': 'startpoint',
        'inputs': [],
        'outputs': [],
        'vib_position':-1
    }

    nodes_dict['endpoint'] = {
        'type': 'endpoint',
        'inputs': [],
        'outputs': [],
        'vib_position':-1
    }


    for name, attrs in nodes_dict.items():
    # 排除 startpoint 和 end_point
        if name in ['startpoint', 'endpoint']:
            continue

        # 如果当前节点的 inputs 为空
        if not attrs.get('inputs', []):
            # 将当前节点的名字加入 startpoint 的 outputs
            nodes_dict['startpoint'].setdefault('outputs', []).append(name)
            # 将 startpoint 加入当前节点的 inputs
            attrs.setdefault('inputs', []).append('startpoint')

        # 如果当前节点的 outputs 为空
        if not attrs.get('outputs', []):
            # 将 end_point 加入当前节点的 outputs
            attrs.setdefault('outputs', []).append('endpoint')
            # 将当前节点的名字加入 end_point 的 inputs
            nodes_dict['endpoint'].setdefault('inputs', []).append(name)

    start_nodes = []
    end_nodes = []

    # 直接从nodes_dict提取边信息
    for node, attrs in nodes_dict.items():
        for output_node in attrs.get('outputs', []):
            start_nodes.append(node)
            end_nodes.append(output_node)

    # 将节点名称映射到连续的整数索引
    node_to_idx = {node: idx for idx, node in enumerate(nodes_dict.keys())}

    # print("End Nodes:", end_nodes)
    # print("Node to Index Keys:", node_to_idx)


    # 转换节点名称为索引
    start_nodes_idx = [node_to_idx[node] for node in start_nodes]
    end_nodes_idx = [node_to_idx[node] for node in end_nodes]

    # 创建edge_index张量
    edge_index = torch.tensor([start_nodes_idx, end_nodes_idx], dtype=torch.long)

    one_hot_encoding(nodes_dict)

    type_list = ['startpoint', 'endpoint', 'clb.I0', 'clb.I1', 'clb.I2'
                 ,'clb.I3', 'clb.I4', 'clb.I5', 'clb.I6', 'clb.I7', 'clb.I8', 'clb.I9',
                 'clb.I10', 'clb.I11', 'clb.cin', 'clb.reset', 'clb.O', 'clb.cout', 'clb.clk',
                 'fle.in', 'fle.out', 'fle.clk', 'fle.reset', 'fle.cin', 'fle.cout', 'ff.D'
                 ,'ff.Q', 'ff.C', 'ff.R', 'ble5.in', 'ble5.out', 'ble5.reset', 'ble5.clk', 'lut5.out',
                 'lut5.in', 'mux', 'dff.D', 'dff.Q', 'dff.C', 'segment_in', 'segment_out']

    feature_names = ['delay']
    position_features = ['from_x', 'from_y', 'to_x', 'to_y']
    seg_features = ['l0', 'l1', 'l2', 'l3', 'l4', 'l5', 'l6', 'l7', 'l8', 'l9', 'l10', 'l11', 'l12', 'l13', 'l14', 'l15', 'l16']
    vib_position_features = ['v0', 'v1', 'v2', 'v3', 'v4', 'v5', 'v6', 'v7', 'v8', 'v9', 'v-1']
    freq_features = ['freq']

    feature_names.extend(type_list)
    feature_names.extend(seg_features)
    feature_names.extend(position_features)
    # feature_names.extend(vib_position_features)
    feature_names.extend(freq_features)

    features_list = []
    labels = [0] * len(nodes_dict)

    for node, attrs in nodes_dict.items():
        node_features = []
        for feature in feature_names:
            if feature in position_features:
                node_features.append(attrs.get(feature, 0) / 2)
            elif feature == 'delay':
                node_features.append(attrs.get(feature, 0) * 10**11)
            elif feature in seg_features:
                node_features.append(attrs.get(feature, 0))
            # elif feature in vib_position_features:
            #     node_features.append(attrs.get(feature, 0))
            elif feature in type_list:
                node_features.append(attrs.get(feature, 0))
            elif feature in freq_features:
                node_features.append(attrs.get(feature, 0) * 10)
            else:
                raise ValueError(f"Unknown feature: {feature}")
        features_list.append(node_features)
        labels[node_to_idx[node]] = node_labels.get(node, 0)

    # print(features_list)

    # 转换特征列表为张量
    features_tensor = torch.tensor(features_list, dtype=torch.float)

    # 将标签转换为张量
    labels_tensor = torch.tensor(labels, dtype=torch.int)

    global_features.append(label)
    # 将全局特征转换为张量
    global_features_tensor = torch.tensor(global_features, dtype=torch.float)

    # 使用字典组织特征
    data = Data(x=features_tensor, edge_index=edge_index, y=labels_tensor, other_attrs=global_features_tensor)

    return data


# file_path = "jq13_55.xml"  # Replace with the actual file path
# nodes_dict = process_xml_to_nodes_dict(file_path)
# nodes_dict = add_one_hot_encoding(nodes_dict)
# # print(nodes_dict)
# process_dict_to_graph(nodes_dict, 0.5)
