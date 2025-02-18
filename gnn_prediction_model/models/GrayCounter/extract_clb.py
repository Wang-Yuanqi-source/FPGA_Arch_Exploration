#修改成pb_type=clb
#先只用clb的数据看结果



import xml.etree.ElementTree as ET
from itertools import chain  

def construct_nodes_dict(root, root_name, nodes_dict, level):
    for node_type in ['input', 'output', 'clock']:
        for element in root.findall(f"./{node_type}"):
            num_pins = int(element.get('num_pins'))
            name_prefix = element.get('name')  # Expected to be something like 'Ia'

            if num_pins == 1:
                node_name = f"{root_name}.{name_prefix}"
                nodes_dict[node_name] = {
                    'name': node_name,
                    'type': level + '.' + name_prefix,
                    'level':level,
                    'delay': 0,
                    'inputs': [],
                    'outputs': [],
                    'inform_distance': 0
                }
            else:
                # Create nodes based on num_pins
                for i in range(num_pins):
                    node_name = f"{root_name}.{name_prefix}[{i}]"
                    nodes_dict[node_name] = {
                        'name': node_name,
                        'type': level + '.' + name_prefix,
                        'level':level,
                        'delay': 0,
                        'inputs': [],
                        'outputs': [],
                        'inform_distance': 0
                    }

    return nodes_dict

def complete_connections(nodes_dict,inputs,outputs):
    for input_name in inputs:
        nodes_dict[input_name]['outputs'].extend(outputs)
    for output_name in outputs:
        nodes_dict[output_name]['inputs'].extend(inputs)


def extract_clb_nodes(xml_file, nodes_dict):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    pb_type_name='clb'
    pb_types = root.findall(".//pb_type[@name='" + pb_type_name + "']")

    # 创建一个新的XML树，仅包含找到的pb_type
    new_root = ET.Element("complexblocks")
    for pb in pb_types:
        new_root.append(pb)

    # 最外层clb
    construct_nodes_dict(new_root.find(".//pb_type[@name='" + 'clb' + "']"), 'clb', nodes_dict, 'clb')

    # 建立8个fle
    fle_root = new_root.find(".//pb_type[@name='" + 'fle' + "']")
    fle_num = int(fle_root.get('num_pb'))
    for i in range(fle_num):
        fle_name = f"fle[{i}]"
        construct_nodes_dict(fle_root, fle_name, nodes_dict, 'fle')
        n1_lut5_root = fle_root.find(".//mode[@name='" + 'n1_lut5' + "']")
        ble5_root = n1_lut5_root.find(".//pb_type[@name='" + 'ble5' + "']")
        ble5_name = fle_name + f".ble5"
        construct_nodes_dict(ble5_root, ble5_name, nodes_dict, 'ble5')
        lut5_root = ble5_root.find(".//pb_type[@name='" + 'lut5' + "']")
        lut5_name = ble5_name + f".lut5"
        construct_nodes_dict(lut5_root, lut5_name, nodes_dict, 'lut5')
        for i in range(5):
            nodes_dict[lut5_name+f'.in[{i}]']['outputs'].append(lut5_name+f'.out')
            nodes_dict[lut5_name+f'.out']['inputs'].append(lut5_name+f'.in[0]')
            nodes_dict[lut5_name+f'.out']['delay'] = 2.25042e-10
        
        #这里默认配置为dff
        ff_root = ble5_root.find(".//pb_type[@name='ff']")
        ff_name = ble5_name + f".ff"
        construct_nodes_dict(ff_root, ff_name, nodes_dict, 'ff')
        if ff_root is not None:
            # 在 pb_type name="ff" 下查找 mode name="dff"
            dff_mode = ff_root.find(".//mode[@name='dff']")
            if dff_mode is not None:
                # 在 mode name="dff" 下查找 pb_type name="dff"
                dff_root = dff_mode.find(".//pb_type[@name='dff']")
        dff_name = ble5_name + f".dff"
        construct_nodes_dict(dff_root, dff_name, nodes_dict, 'dff')
        nodes_dict[dff_name+f'.D']['delay']=7.85e-11
        nodes_dict[dff_name+f'.Q']['delay']=4.47e-11

        nodes_dict[dff_name+f'.Q']['outputs'].append(ff_name+f'.Q')
        nodes_dict[ff_name+f'.Q']['inputs'].append(dff_name+f'.Q')
        nodes_dict[ff_name+f'.D']['outputs'].append(dff_name+f'.D')
        nodes_dict[dff_name+f'.D']['inputs'].append(ff_name+f'.D')
        nodes_dict[ff_name+f'.C']['outputs'].append(dff_name+f'.C')
        nodes_dict[dff_name+f'.C']['inputs'].append(ff_name+f'.C')

        for i in range(5):
            nodes_dict[ble5_name+f'.in[{i}]']['outputs'].append(lut5_name+f'.in[{i}]')
            nodes_dict[lut5_name+f'.in[{i}]']['inputs'].append(ble5_name+f'.in[{i}]')
        nodes_dict[ble5_name+f'.clk']['outputs'].append(ff_name+f'.C')
        nodes_dict[ff_name+f'.C']['inputs'].append(ble5_name+f'.clk')
        nodes_dict[ble5_name+f'.reset']['outputs'].append(ff_name+f'.R')
        nodes_dict[ff_name+f'.R']['inputs'].append(ble5_name+f'.reset')
        nodes_dict[lut5_name+f'.out']['outputs'].append(ff_name+f'.D')
        nodes_dict[ff_name+f'.D']['inputs'].append(lut5_name+f'.out')
        nodes_dict[lut5_name+f'.out']['outputs'].append(ble5_name+f'.out')
        nodes_dict[ble5_name+f'.out']['inputs'].append(lut5_name+f'.out')
        nodes_dict[ff_name+f'.Q']['outputs'].append(ble5_name+f'.out')
        nodes_dict[ble5_name+f'.out']['inputs'].append(ff_name+f'.Q')

        for i in range(5):
            nodes_dict[fle_name+f'.in[{i}]']['outputs'].append(ble5_name+f'.in[{i}]')
            nodes_dict[ble5_name+f'.in[{i}]']['inputs'].append(fle_name+f'.in[{i}]')
        nodes_dict[ble5_name+f'.out']['outputs'].append(fle_name+f'.out[0]')
        nodes_dict[fle_name+f'.out[0]']['inputs'].append(ble5_name+f'.out')
        nodes_dict[fle_name+f'.clk']['outputs'].append(ble5_name+f'.clk')
        nodes_dict[ble5_name+f'.clk']['inputs'].append(fle_name+f'.clk')

    for i in range(5):
        nodes_dict[f'clb.I0[{i}]']['outputs'].append(f'fle[0].in[{i}]')
        nodes_dict[f'fle[0].in[{i}]']['inputs'].append(f'clb.I0[{i}]')
        nodes_dict[f'clb.I1[{i}]']['outputs'].append(f'fle[1].in[{i}]')
        nodes_dict[f'fle[1].in[{i}]']['inputs'].append(f'clb.I1[{i}]')
        nodes_dict[f'clb.I2[{i}]']['outputs'].append(f'fle[2].in[{i}]')
        nodes_dict[f'fle[2].in[{i}]']['inputs'].append(f'clb.I2[{i}]')
        nodes_dict[f'clb.I3[{i}]']['outputs'].append(f'fle[3].in[{i}]')
        nodes_dict[f'fle[3].in[{i}]']['inputs'].append(f'clb.I3[{i}]')
        nodes_dict[f'clb.I4[{i}]']['outputs'].append(f'fle[4].in[{i}]')
        nodes_dict[f'fle[4].in[{i}]']['inputs'].append(f'clb.I4[{i}]')
        nodes_dict[f'clb.I5[{i}]']['outputs'].append(f'fle[5].in[{i}]')
        nodes_dict[f'fle[5].in[{i}]']['inputs'].append(f'clb.I5[{i}]')
        nodes_dict[f'clb.I6[{i}]']['outputs'].append(f'fle[6].in[{i}]')
        nodes_dict[f'fle[6].in[{i}]']['inputs'].append(f'clb.I6[{i}]')
        nodes_dict[f'clb.I7[{i}]']['outputs'].append(f'fle[7].in[{i}]')
        nodes_dict[f'fle[7].in[{i}]']['inputs'].append(f'clb.I7[{i}]')
        nodes_dict[f'clb.I8[{i}]']['outputs'].append(f'fle[8].in[{i}]')
        nodes_dict[f'fle[8].in[{i}]']['inputs'].append(f'clb.I8[{i}]')
        nodes_dict[f'clb.I9[{i}]']['outputs'].append(f'fle[9].in[{i}]')
        nodes_dict[f'fle[9].in[{i}]']['inputs'].append(f'clb.I9[{i}]')
        nodes_dict[f'clb.I10[{i}]']['outputs'].append(f'fle[10].in[{i}]')
        nodes_dict[f'fle[10].in[{i}]']['inputs'].append(f'clb.I10[{i}]')
        nodes_dict[f'clb.I11[{i}]']['outputs'].append(f'fle[11].in[{i}]')
        nodes_dict[f'fle[11].in[{i}]']['inputs'].append(f'clb.I11[{i}]')

    for i in range(12):
        nodes_dict[f'clb.clk[0]']['outputs'].append(f'fle[{i}].clk')
        nodes_dict[f'fle[{i}].clk']['inputs'].append(f'clb.clk[0]')
        nodes_dict[f'fle[{i}].clk']['delay']=1.6946600000000003e-10

        nodes_dict[f'clb.reset']['outputs'].append(f'fle[{i}].reset')
        nodes_dict[f'fle[{i}].reset']['inputs'].append(f'clb.reset')
        nodes_dict[f'fle[{i}].reset']['delay']=2.46196e-10

    nodes_dict[f'fle[11].out[1]']['outputs'].append(f'clb.O[23]')
    nodes_dict[f'clb.O[23]']['inputs'].append(f'fle[11].out[1]')
    nodes_dict[f'fle[11].out[0]']['outputs'].append(f'clb.O[22]')
    nodes_dict[f'clb.O[22]']['inputs'].append(f'fle[11].out[0]')
    nodes_dict[f'fle[10].out[1]']['outputs'].append(f'clb.O[21]')
    nodes_dict[f'clb.O[21]']['inputs'].append(f'fle[10].out[1]')
    nodes_dict[f'fle[10].out[0]']['outputs'].append(f'clb.O[20]')
    nodes_dict[f'clb.O[20]']['inputs'].append(f'fle[10].out[0]')
    nodes_dict[f'fle[9].out[1]']['outputs'].append(f'clb.O[19]')
    nodes_dict[f'clb.O[19]']['inputs'].append(f'fle[9].out[1]')
    nodes_dict[f'fle[9].out[0]']['outputs'].append(f'clb.O[18]')
    nodes_dict[f'clb.O[18]']['inputs'].append(f'fle[9].out[0]')
    nodes_dict[f'fle[8].out[1]']['outputs'].append(f'clb.O[17]')
    nodes_dict[f'clb.O[17]']['inputs'].append(f'fle[8].out[1]')
    nodes_dict[f'fle[8].out[0]']['outputs'].append(f'clb.O[16]')
    nodes_dict[f'clb.O[16]']['inputs'].append(f'fle[8].out[0]')
    nodes_dict[f'fle[7].out[1]']['outputs'].append(f'clb.O[15]')
    nodes_dict[f'clb.O[15]']['inputs'].append(f'fle[7].out[1]')
    nodes_dict[f'fle[7].out[0]']['outputs'].append(f'clb.O[14]')
    nodes_dict[f'clb.O[14]']['inputs'].append(f'fle[7].out[0]')
    nodes_dict[f'fle[6].out[1]']['outputs'].append(f'clb.O[13]')
    nodes_dict[f'clb.O[13]']['inputs'].append(f'fle[6].out[1]')
    nodes_dict[f'fle[6].out[0]']['outputs'].append(f'clb.O[12]')
    nodes_dict[f'clb.O[12]']['inputs'].append(f'fle[6].out[0]')

    nodes_dict[f'fle[5].out[1]']['outputs'].append(f'clb.O[11]')
    nodes_dict[f'clb.O[11]']['inputs'].append(f'fle[5].out[1]')
    nodes_dict[f'fle[5].out[0]']['outputs'].append(f'clb.O[10]')
    nodes_dict[f'clb.O[10]']['inputs'].append(f'fle[5].out[0]')
    nodes_dict[f'fle[4].out[1]']['outputs'].append(f'clb.O[9]')
    nodes_dict[f'clb.O[9]']['inputs'].append(f'fle[4].out[1]')
    nodes_dict[f'fle[4].out[0]']['outputs'].append(f'clb.O[8]')
    nodes_dict[f'clb.O[8]']['inputs'].append(f'fle[4].out[0]')
    nodes_dict[f'fle[3].out[1]']['outputs'].append(f'clb.O[7]')
    nodes_dict[f'clb.O[7]']['inputs'].append(f'fle[3].out[1]')
    nodes_dict[f'fle[3].out[0]']['outputs'].append(f'clb.O[6]')
    nodes_dict[f'clb.O[6]']['inputs'].append(f'fle[3].out[0]')
    nodes_dict[f'fle[2].out[1]']['outputs'].append(f'clb.O[5]')
    nodes_dict[f'clb.O[5]']['inputs'].append(f'fle[2].out[1]')
    nodes_dict[f'fle[2].out[0]']['outputs'].append(f'clb.O[4]')
    nodes_dict[f'clb.O[4]']['inputs'].append(f'fle[2].out[0]')
    nodes_dict[f'fle[1].out[1]']['outputs'].append(f'clb.O[3]')
    nodes_dict[f'clb.O[3]']['inputs'].append(f'fle[1].out[1]')
    nodes_dict[f'fle[1].out[0]']['outputs'].append(f'clb.O[2]')
    nodes_dict[f'clb.O[2]']['inputs'].append(f'fle[1].out[0]')
    nodes_dict[f'fle[0].out[1]']['outputs'].append(f'clb.O[1]')
    nodes_dict[f'clb.O[1]']['inputs'].append(f'fle[0].out[1]')
    nodes_dict[f'fle[0].out[0]']['outputs'].append(f'clb.O[0]')
    nodes_dict[f'clb.O[0]']['inputs'].append(f'fle[0].out[0]')

    nodes_dict[f'clb.cin']['outputs'].append(f'fle[0].cin')
    nodes_dict[f'fle[0].cin']['inputs'].append(f'clb.cin')
    nodes_dict[f'fle[0].cin']['delay']=0.16e-9

    nodes_dict[f'clb.cout']['inputs'].append(f'fle[11].cout')
    nodes_dict[f'fle[11].cout']['outputs'].append(f'clb.cout')

    for i in range(11):
        nodes_dict[f'fle[{i}].cout']['outputs'].append(f'fle[{i+1}].cin')
        nodes_dict[f'fle[{i+1}].cin']['inputs'].append(f'fle[{i}].cout')

    #     #physical
    #     fabric_root = fle_root.find(".//pb_type[@name='" + 'fabric' + "']")
    #     fabric_name = fle_name + f".fabric"
    #     construct_nodes_dict(fabric_root, fabric_name, nodes_dict, 'fabric')

    #     frac_root = fabric_root.find(".//pb_type[@name='" + 'frac_logic' + "']")
    #     frac_name = fabric_name + f".frac"
    #     construct_nodes_dict(frac_root, frac_name, nodes_dict, 'frac_logic')
        
    #     frac_lut5_root = frac_root.find(".//pb_type[@name='" + 'frac_lut5_arith' + "']")
    #     frac_lut5_name = frac_name + f".frac_lut5"
    #     construct_nodes_dict(frac_lut5_root, frac_lut5_name, nodes_dict, 'frac_lut5_arith')

    #     #添加延时信息
    #     for i in range(5):
    #         nodes_dict[frac_lut5_name+f'.in[{i}]']['outputs'].append(frac_lut5_name+f'.lut4_out[0]')
    #         nodes_dict[frac_lut5_name+f'.in[{i}]']['outputs'].append(frac_lut5_name+f'.lut4_out[1]')
    #         nodes_dict[frac_lut5_name+f'.in[{i}]']['outputs'].append(frac_lut5_name+f'.lut5_out')
    #         nodes_dict[frac_lut5_name+f'.lut4_out[0]']['inputs'].append(frac_lut5_name+f'.in[{i}]')
    #         nodes_dict[frac_lut5_name+f'.lut4_out[1]']['inputs'].append(frac_lut5_name+f'.in[{i}]')
    #         nodes_dict[frac_lut5_name+f'.lut5_out']['inputs'].append(frac_lut5_name+f'.in[{i}]')
    #     nodes_dict[frac_lut5_name+f'.lut4_out[0]']['delay'] = 1.67286e-10
    #     nodes_dict[frac_lut5_name+f'.lut4_out[1]']['delay'] = 1.67286e-10
    #     nodes_dict[frac_lut5_name+f'.lut5_out']['delay'] = 2.25042e-10

    #     #添加连接信息
    #     for i in range(5):
    #         nodes_dict[frac_name+f'.in[{i}]']['outputs'] = frac_lut5_name+f'.in[{i}]'
    #         nodes_dict[frac_lut5_name+f'.in[{i}]']['inputs'] = frac_name+f'.in[{i}]'
    #     nodes_dict[frac_name+f'.out[1]']['inputs'] = frac_lut5_name+f'.lut4_out[1]'
    #     nodes_dict[frac_lut5_name+f'.lut4_out[1]']['outputs'] = frac_name+f'.out[1]'

    #     nodes_dict[frac_name+f'.out[0]']['inputs'] = frac_lut5_name+f'.lut4_out[0]'
    #     nodes_dict[frac_lut5_name+f'.lut4_out[0]']['outputs'] = frac_name+f'.out[0]'
    #     nodes_dict[frac_name+f'.out[0]']['inputs'].append(frac_lut5_name+f'.lut5_out')
    #     nodes_dict[frac_lut5_name+f'.lut5_out']['outputs'] = frac_name+f'.out[0]'

    #     ff_root = fabric_root.find(".//pb_type[@name='" + 'ff' + "']")
    #     ff_num = int(ff_root.get('num_pb'))
    #     for i in range(ff_num):
    #         ff_name = fabric_name + f".ff[{i}]"
    #         construct_nodes_dict(ff_root, ff_name, nodes_dict, 'ff')
    #         nodes_dict[ff_name+'.C']['delay'] = 7.85e-11
    #         nodes_dict[ff_name+'.Q']['delay'] = 4.47e-11
    #         nodes_dict[ff_name+'.Q']['inputs'].append(ff_name+'.C')
    #         nodes_dict[ff_name+'.C']['outputs'].append(ff_name+'.Q')

    #     adder_root = fabric_root.find(".//pb_type[@name='" + 'adder' + "']")
    #     adder_name = fabric_name + f".adder"
    #     construct_nodes_dict(adder_root, adder_name, nodes_dict, 'adder')
    #     nodes_dict[adder_name+'.sumout']['inputs'].append(adder_name+'.a')
    #     nodes_dict[adder_name+'.sumout']['inputs'].append(adder_name+'.b')
    #     nodes_dict[adder_name+'.sumout']['inputs'].append(adder_name+'.cin')
    #     nodes_dict[adder_name+'.a']['outputs'].append(adder_name+'.sumout')
    #     nodes_dict[adder_name+'.b']['outputs'].append(adder_name+'.sumout')
    #     nodes_dict[adder_name+'.cin']['outputs'].append(adder_name+'.sumout')
    #     nodes_dict[adder_name+'.cout']['inputs'].append(adder_name+'.a')
    #     nodes_dict[adder_name+'.cout']['inputs'].append(adder_name+'.b')
    #     nodes_dict[adder_name+'.cout']['inputs'].append(adder_name+'.cin')
    #     nodes_dict[adder_name+'.a']['outputs'].append(adder_name+'.cout')
    #     nodes_dict[adder_name+'.b']['outputs'].append(adder_name+'.cout')
    #     nodes_dict[adder_name+'.cin']['outputs'].append(adder_name+'.cout')
    #     nodes_dict[adder_name+'.sumout']['delay'] = 0.3e-9
    #     nodes_dict[adder_name+'.cout']['delay'] = 0.3e-9

    #     #连接信息
    #     for i in range(5):
    #         nodes_dict[fabric_name+f'.in[{i}]']['outputs'].append(frac_name+f'.in[{i}]')
    #         nodes_dict[frac_name+f'.in[{i}]']['inputs'].append(fabric_name+f'.in[{i}]')
    #     nodes_dict[fabric_name+f'.cin']['outputs'].append(adder_name+'.cin')
    #     nodes_dict[adder_name+'.cin']['inputs'].append(fabric_name+f'.cin')
    #     nodes_dict[adder_name+'.cout']['outputs'].append(frac_name+f'.cout')
    #     nodes_dict[frac_name+f'.cout']['inputs'].append(adder_name+'.cout')

    #     nodes_dict[fabric_name+f'.clk']['outputs'].append(frac_name+f'.ff[0].C')
    #     nodes_dict[frac_name+f'.ff[0].C']['inputs'].append(fabric_name+f'.clk')
    #     nodes_dict[fabric_name+f'.clk']['outputs'].append(frac_name+f'.ff[1].C')
    #     nodes_dict[frac_name+f'.ff[1].C']['inputs'].append(fabric_name+f'.clk')

    #     nodes_dict[fabric_name+f'.reset']['outputs'].append(frac_name+f'.ff[0].R')
    #     nodes_dict[frac_name+f'.ff[0].R']['inputs'].append(fabric_name+f'.reset')
    #     nodes_dict[fabric_name+f'.reset']['outputs'].append(frac_name+f'.ff[1].R')
    #     nodes_dict[frac_name+f'.ff[1].R']['inputs'].append(fabric_name+f'.reset')

    #     nodes_dict[frac_name+f'.out[0]']['outputs'].append(adder_name+f'.a')
    #     nodes_dict[adder_name+f'.a']['inputs'].append(frac_name+f'.out[0]')
    #     nodes_dict[frac_name+f'.out[1]']['outputs'].append(adder_name+f'.b')
    #     nodes_dict[adder_name+f'.b']['inputs'].append(frac_name+f'.out[1]')

    #     nodes_dict[frac_name+f'.out[0]']['outputs'].append(frac_name+f'.ff[0].D')
    #     nodes_dict[frac_name+f'.ff[0].D']['inputs'].append(frac_name+f'.out[0]')
    #     nodes_dict[frac_name+f'.ff[0].D']['delay'] = 1.9756000000000001e-10

    #     nodes_dict[frac_name+f'.out[1]']['outputs'].append(frac_name+f'.ff[1].D')
    #     nodes_dict[frac_name+f'.ff[1].D']['inputs'].append(frac_name+f'.out[1]')
    #     nodes_dict[adder_name+f'.sumout']['outputs'].append(frac_name+f'.ff[1].D')
    #     nodes_dict[frac_name+f'.ff[1].D']['inputs'].append(adder_name+f'.sumout')
    #     nodes_dict[frac_name+f'.ff[1].D']['delay'] = 1.9756000000000001e-10

    #     nodes_dict[frac_name+f'.ff[0].Q']['outputs'].append(fabric_name+f'.out[0]')
    #     nodes_dict[fabric_name+f'.out[0]']['inputs'].append(frac_name+f'.ff[0].Q')
    #     nodes_dict[frac_name+f'.out[0]']['outputs'].append(fabric_name+f'.out[0]')
    #     nodes_dict[fabric_name+f'.out[0]']['inputs'].append(frac_name+f'.out[0]')
    #     nodes_dict[fabric_name+f'.out[0]']['delay'] = 1.5475400000000002e-10

    #     nodes_dict[frac_name+f'.ff[1].Q']['outputs'].append(fabric_name+f'.out[1]')
    #     nodes_dict[fabric_name+f'.out[1]']['inputs'].append(frac_name+f'.ff[1].Q')
    #     nodes_dict[frac_name+f'.out[1]']['outputs'].append(fabric_name+f'.out[1]')
    #     nodes_dict[fabric_name+f'.out[1]']['inputs'].append(frac_name+f'.out[1]')
    #     nodes_dict[adder_name+f'.sumout']['outputs'].append(fabric_name+f'.out[1]')
    #     nodes_dict[fabric_name+f'.out[1]']['inputs'].append(adder_name+f'.sumout')
    #     nodes_dict[fabric_name+f'.out[1]']['delay'] = 1.5475400000000002e-10

        

    # #fle --clb
    # #connect all clb input nodes' outputs to fle input nodes
    # for i in range(6):
    #     nodes_dict[f'clb.Ia[{i}]']['outputs'].append(f'fle[0].in[{i}]')
    #     nodes_dict[f'clb.Ib[{i}]']['outputs'].append(f'fle[1].in[{i}]')
    #     nodes_dict[f'clb.Ic[{i}]']['outputs'].append(f'fle[2].in[{i}]')
    #     nodes_dict[f'clb.Id[{i}]']['outputs'].append(f'fle[3].in[{i}]')
    #     nodes_dict[f'clb.Ie[{i}]']['outputs'].append(f'fle[4].in[{i}]')
    #     nodes_dict[f'clb.If[{i}]']['outputs'].append(f'fle[5].in[{i}]')
    #     nodes_dict[f'clb.Ig[{i}]']['outputs'].append(f'fle[6].in[{i}]')
    #     nodes_dict[f'clb.Ih[{i}]']['outputs'].append(f'fle[7].in[{i}]')

    #     nodes_dict[f'fle[0].in[{i}]']['inputs'].append(f'clb.Ia[{i}]')
    #     nodes_dict[f'fle[1].in[{i}]']['inputs'].append(f'clb.Ib[{i}]')
    #     nodes_dict[f'fle[2].in[{i}]']['inputs'].append(f'clb.Ic[{i}]')
    #     nodes_dict[f'fle[3].in[{i}]']['inputs'].append(f'clb.Id[{i}]')
    #     nodes_dict[f'fle[4].in[{i}]']['inputs'].append(f'clb.Ie[{i}]')
    #     nodes_dict[f'fle[5].in[{i}]']['inputs'].append(f'clb.If[{i}]')
    #     nodes_dict[f'fle[6].in[{i}]']['inputs'].append(f'clb.Ig[{i}]')
    #     nodes_dict[f'fle[7].in[{i}]']['inputs'].append(f'clb.Ih[{i}]')

    # #connect all clb outputs    
    # for i in range(8):
    #     nodes_dict[f'clb.o[{i}]']['inputs'].append(f'fle[{i}].out[0]')
    #     nodes_dict[f'fle[{i}].out[0]']['outputs'].append(f'clb.o[{i}]')
    #     nodes_dict[f'clb.q[{i}]']['inputs'].append(f'fle[{i}].out[1]')
    #     nodes_dict[f'fle[{i}].out[1]']['outputs'].append(f'clb.q[{i}]')

    return nodes_dict

if __name__ == '__main__':
    nodes_dict = {}
    nodes_dict = extract_clb_nodes('D://Users//戴芸菲//Desktop//布通性模型//homo_example.xml')
    print(nodes_dict)
