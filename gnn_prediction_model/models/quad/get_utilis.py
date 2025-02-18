from xml.etree import ElementTree as ET
from get_switch import query_tdel
from get_segment import get_position
import re
import pandas as pd

def normal_delay(delay):
    return delay

def get_seg_direct(input_str: str) -> str:
    if '.' in input_str:
        parts = input_str.split('.')
        if len(parts) > 1 and len(parts[1]) > 0:
            return parts[1][0]  # 获取 '.' 后部分的第一个字母
        else:
            raise ValueError(f"No valid character found after '.' in input: {input_str}")
    else:
        raise ValueError(f"No '.' found in input: {input_str}")

def get_seg_length(input_str: str) -> str:
    match = re.search(r'l(\d+)\.', input_str)
    if match:
        return match.group(1)  # 返回匹配到的数字
    else:
        raise ValueError(f"No valid format found in input: {input_str}")

def get_seg_freq(segment_dict, length) -> float:
    return segment_dict[length]['freq']

def identify_to_type(input_str: str) -> str:
    if input_str.startswith("clb.I") and len(input_str) > len("clb.I"):
        return input_str[:len("clb.I") + 1]
    elif input_str.startswith("l"):
        return "segment_out"
    else:
        raise TypeError(f"Unknown type for input: {input_str}")

def identify_from_type(input_str: str) -> str:
    if input_str.startswith("clb.") and len(input_str) > len("clb."):
        return input_str[:len("clb.") + 1]
    elif input_str.startswith("l"):
        return "segment_in"
    elif input_str.startswith("mux") or input_str.startswith("omux"):
        return "mux"
    else:
        raise TypeError(f"Unknown type for input: {input_str}")

# Function to add nodes from 'mux' tags
def add_mux_node(root, nodes_dict, switch_dict, segment_dict):
    first_stage = root.find("first_stage")
    if first_stage is None:
        raise ValueError("No 'first_stage' element found under 'multistage_muxs'.")

    # Iterate through each 'mux' in 'first_stage'
    for mux in first_stage.iter("mux"):
        # Extract the 'name' attribute
        mux_name = mux.get("name")
        
        from_text = mux.find("from")
        from_elements = []

        # If the 'from' element exists, split its content by spaces
        if from_text is not None and from_text.text is not None:
            # Split by spaces and store in the array
            from_elements = from_text.text.strip().split()
        
        if mux_name and mux_name not in nodes_dict:
            nodes_dict[mux_name] = {
                'name': mux_name,
                'type': 'mux',
                'delay': query_tdel(switch_dict, 'only_mux',len(from_elements)),
                'inputs': from_elements,
                'outputs': [],
                'inform_distance': 0,
                'level': 'clb',
                'to_x': 0,
                'to_y': 0
            }
        else:
            nodes_dict[mux_name]['inputs'].extend(from_elements)
            nodes_dict[mux_name]['delay'] = query_tdel(switch_dict, 'only_mux',len(nodes_dict[mux_name]['inputs']))
        
        for element in from_elements:
            if element not in nodes_dict:
                add_from_node(element, nodes_dict, segment_dict)
            nodes_dict[element]['outputs'].append(mux_name)
    
    second_stage = root.find("second_stage")
    if second_stage is None:
        raise ValueError("No 'second_stage' element found under 'multistage_muxs'.")

    # Iterate through each 'mux' in 'second_stage'
    for mux in second_stage.iter("mux"):
        # Extract the 'name' attribute
        mux_name = mux.get("name")
        to_text = mux.find("to")
        from_text = mux.find("from")
        from_elements = []

        # If the 'from' element exists, split its content by spaces
        if from_text is not None and from_text.text is not None:
            # Split by spaces and store in the array
            from_elements = from_text.text.strip().split()
            from_elements = add_from_suffix(from_elements)
        
        type = identify_to_type(to_text.text)

        if type == 'segment_out':
            direct = get_seg_direct(to_text.text)
            length = get_seg_length(to_text.text)
            to_x, to_y = get_position(segment_dict, length, direct, 'out')
            delay = query_tdel(switch_dict, length, len(from_elements))
            name = to_text.text + '_to'
            freq = get_seg_freq(segment_dict, length)
            if name not in nodes_dict:
                nodes_dict[name] = {
                    'name': name,
                    'type': type,
                    'delay': delay,
                    'inputs': from_elements,
                    'outputs': [],
                    'inform_distance': length,
                    'direct': direct,
                    'level': 'seg',
                    'to_x': to_x,
                    'to_y': to_y,
                    'freq': freq
                }
            else:
                nodes_dict[name]['inputs'].extend(from_elements)
                nodes_dict[name]['delay'] = query_tdel(switch_dict, 'ipin_cblock', len(nodes_dict[name]['inputs']))
        
        else:
            name = to_text.text
            delay = query_tdel(switch_dict, 'ipin_cblock',len(from_elements))
            if name not in nodes_dict:
                nodes_dict[name] = {
                    'name': name,
                    'type': type,
                    'delay': delay,
                    'inputs': from_elements,
                    'outputs': [],
                    'inform_distance': 0,
                    'level': 'clb'
                }
            else:
                nodes_dict[name]['inputs'].extend(from_elements)
                nodes_dict[name]['delay'] = query_tdel(switch_dict, 'ipin_cblock', len(nodes_dict[name]['inputs']))
                
        for from_node in from_elements:
            add_from_node(from_node, nodes_dict, segment_dict)
            nodes_dict[from_node]['outputs'].append(name)
    
def add_from_suffix(from_elements):
    # 创建一个新的列表来存储处理后的 from_node
    updated_from_elements = []
    
    for from_node in from_elements:
        # 判断 from_node 是否为 'segment_input' 类型
        if identify_from_type(from_node) == 'segment_in':
            # 如果满足条件，则加上 '_from' 后缀
            updated_from_elements.append(from_node + '_from')
        else:
            # 不满足条件的保持原样
            updated_from_elements.append(from_node)
    
    return updated_from_elements

def add_from_node(element, nodes_dict, segment_dict):
    type = identify_from_type(element)
    name = element
    if type == 'clb.o' or type == 'clb.q':
        if name in nodes_dict:
            return
        else:
            nodes_dict[name] = {
            'name': name,
            'type': type,
            'delay': 0,
            'inputs': [],
            'outputs': [],
            'inform_distance': 0,
            'level': 'clb'
        }
    elif type == 'segment_in':
        if name in nodes_dict:
            return
        else:
            direct = get_seg_direct(name)
            length = get_seg_length(name)
            from_x, from_y = get_position(segment_dict, length, direct, 'in')
            freq = get_seg_freq(segment_dict, length)
            nodes_dict[name] = {
            'name': name,
            'type': type,
            'delay': 0,
            'inputs': [],
            'outputs': [],
            'inform_distance': length,
            'level': 'seg',
            'direct': direct,
            'from_x': from_x,
            'from_y': from_y,
            'freq': freq
        }
    
    elif type == 'mux':
        if name in nodes_dict:
            return
        else:
            nodes_dict[name] = {
            'name': name,
            'type': type,
            'delay': 0,
            'inputs': [],
            'outputs': [],
            'inform_distance': 0,
            'level': 'mux'
        }
            
    else:
        raise ValueError('Unknown node type: ' + type)
        

# 添加种类特征
def one_hot_encoding(node_dict):
    type_list = ['segment_out', 'startpoint', 'endpoint', 'clb.I0', 'clb.I1', 'clb.I2'
                ,'clb.I3', 'clb.I4', 'clb.I5', 'clb.I6', 'clb.I7', 'clb.I8', 'clb.I9',
                'clb.I10', 'clb.I11', 'clb.cin', 'clb.reset', 'clb.O', 'clb.cout', 'clb.clk',
                'fle.in', 'fle.out', 'fle.clk', 'fle.reset', 'fle.cin', 'fle.cout', 'ff.D'
                ,'ff.Q', 'ff.C', 'ff.R', 'ble5.in', 'ble5.out', 'ble5.reset', 'ble5.clk', 'lut5.out',
                'lut5.in', 'mux', 'dff.D', 'dff.Q', 'dff.C', 'segment_in', 'segment_out']

    for name, attributes in node_dict.items():
        # 遍历 type_list 中的每个类型
        for type_name in type_list:
            # 检查节点的 'type' 是否与当前类型相匹配
            if attributes['type'] == type_name:
                attributes[type_name] = 1
            else:
                attributes[type_name] = 0
        if attributes['type'] not in type_list:
            print(f"Error: Node '{name}' has an unknown type: {attributes['type']}")
            raise ValueError(f"Node '{name}' has an unrecognized type '{attributes['type']}'")

    seg_features = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16']
    # vib_position_features = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-1']
    for name, attributes in node_dict.items():

        if 'inform_distance' not in attributes:
            attributes['inform_distance'] = '0'  # 如果不存在，设为 '0'
        else:
            attributes['inform_distance'] = str(attributes['inform_distance'])

        # 检查节点的 'inform_distance' 是否在 seg_features 中
        if attributes['inform_distance'] not in seg_features:
            print(f"Error: Node '{name}' has an unknown inform_distance: {attributes['inform_distance']}")
            raise ValueError(f"Node '{name}' has an unrecognized inform_distance '{attributes['inform_distance']}'")

        # 遍历 seg_features 中的每个类型，并在前面加 'l'
        for seg in seg_features:
            prefixed_seg = 'l' + seg  # 加上前缀 'l'
            if attributes['inform_distance'] == seg:
                attributes[prefixed_seg] = 1
            else:
                attributes[prefixed_seg] = 0  
        
        # if str(attributes['vib_position']) not in vib_position_features:
        #     print(f"Error: Node '{name}' has an unknown vib_position: {attributes['vib_position']}")
        #     raise ValueError(f"Node '{name}' has an unrecognized vib_position '{attributes['vib_position']}'")

        # # 遍历 vib_position_features 中的每个类型，并在前面加 'l'
        # for vib in vib_position_features:
        #     prefixed_vib = 'v' + vib  # 加上前缀 'l'
        #     if str(attributes['vib_position']) == vib:
        #         attributes[prefixed_vib] = 1
        #     else:
        #         attributes[prefixed_vib] = 0  
    


    return node_dict

def add_directlist(node_dict, directlist):
    for direct in directlist.findall('direct'):
        # 获取 from_pin 和 to_pin
        from_pin = direct.get('from_pin')
        to_pin = direct.get('to_pin')

        # 检查 from_pin 是否需要 clean
        if '[' in from_pin and ':' in from_pin:
            from_pin_clean = from_pin.split('[')[0] + '[' + from_pin.split('[')[1].split(':')[0] + ']'
        else:
            from_pin_clean = from_pin  # 如果不符合格式，直接使用原始值

        # 检查 to_pin 是否需要 clean
        if '[' in to_pin and ':' in to_pin:
            to_pin_clean = to_pin.split('[')[0] + '[' + to_pin.split('[')[1].split(':')[0] + ']'
        else:
            to_pin_clean = to_pin  # 如果不符合格式，直接使用原始值

        # 更新 node_dict
        if from_pin_clean not in node_dict:
            node_dict[from_pin_clean] = {'outputs': [], 'inputs': []}
        if to_pin_clean not in node_dict:
            node_dict[to_pin_clean] = {'outputs': [], 'inputs': []}

        node_dict[from_pin_clean]['outputs'].append(to_pin_clean)
        node_dict[to_pin_clean]['inputs'].append(from_pin_clean)

    return node_dict