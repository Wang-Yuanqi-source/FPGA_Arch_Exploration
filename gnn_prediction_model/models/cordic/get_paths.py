import os
import json
import xml.etree.cElementTree as ET

def extract_routing_from_timing_report(timing_report):
    routing_info = {}
    with open(timing_report, 'r') as file:
        lines = file.readlines()
        medium_nodes = []
        chany_nodes = []
        chanx_nodes = []
        ipin_nodes = []
        critical_path_num = 0
        for line in lines:
            if "Point" in line:
                critical_path_num += 1
            if critical_path_num > 1:
                break
            if "MEDIUM" in line:
                words = line.split()
                word = words[1].split(":")[1]
                medium_nodes.append(word)
            if "CHANY" in line:
                words = line.split()
                word = words[1].split(":")[1]
                chany_nodes.append(word)
            if "CHANX" in line:
                words = line.split()
                word = words[1].split(":")[1]
                chanx_nodes.append(word)
            if "IPIN" in line:
                words = line.split()
                word = words[1].split(":")[1]
                ipin_nodes.append(word)
        
        routing_info["MEDIUM"] = medium_nodes
        routing_info["CHANX"] = chanx_nodes
        routing_info["CHANY"] = chany_nodes
        routing_info["IPIN"] = ipin_nodes

    return routing_info

def extract_from_route(route_report, routing_info):
    nodes = []
    with open(route_report, 'r') as file:
        lines = file.readlines()
        for k, values in routing_info.items():
            for v in values:
                for line in lines:
                    words = line.split()
                    if len(words) > 0 and words[0] == "Node:" and words[1] == v:
                        node = {}
                        if k == "MEDIUM":
                            coord = words[3]
                            x = coord.split(",")[1]
                            y = coord.split(",")[2]
                            y = y[:-1]
                            coord = "(" + x + "," + y +")"
                            node = {'type': "MEDIUM", 'coor': coord, 'index': words[5]}
                            nodes.append(node)
                            break
                        if k == "IPIN":
                            coord = words[3]
                            x = coord.split(",")[1]
                            y = coord.split(",")[2]
                            y = y[:-1]
                            coord = "(" + x + "," + y +")"
                            node = {'type': "IPIN", 'coor': coord, 'index': words[6]}
                            nodes.append(node)
                            break
                        if k == "CHANY":
                            index = int(words[-3])
                            if index % 2 == 0:
                                coord = words[3]
                                x = coord.split(",")[1]
                                y = coord.split(",")[2]
                                y = y[:-1]
                                y = str(int(y) - 1)
                            else:
                                coord = words[-5]
                                x = coord.split(",")[-2]
                                if "(" in x:
                                    x = x[1:]
                                y = coord.split(",")[-1]
                                y = y[:-1]
                            coord = "(" + x + "," + y +")"
                            node = {'type': "CHANY", 'coor': coord, 'index': words[-3]}
                            nodes.append(node)
                            break
                        if k == "CHANX":
                            index = int(words[-3])
                            if index % 2 == 0:
                                coord = words[3]
                                x = coord.split(",")[1]
                                x = str(int(x) - 1)
                                y = coord.split(",")[2]
                                y = y[:-1]
                            else:
                                coord = words[-5]
                                x = coord.split(",")[-2]
                                if "(" in x:
                                    x = x[1:]
                                y = coord.split(",")[-1]
                                y = y[:-1]
                            coord = "(" + x + "," + y +")"
                            node = {'type': "CHANX", 'coor': coord, 'index': words[-3]}
                            nodes.append(node)
                            break
    return nodes

def modify(arch_file, nodes_info):
    archtree = ET.parse(arch_file)
    segmentlist = archtree.getroot().find("segmentlist")
    vib_layout = archtree.getroot().find("vib_layout")
    vib_arch = archtree.getroot().find("vib_arch")
    segments = []

    for segment in segmentlist.findall("segment"):
        freq = segment.get("freq")
        name = segment.get("name")
        length = segment.get("length")
        if float(freq) > 0:
            segments.append({'name': name, 'freq': freq, 'length': length})

    for node in nodes_info:
        if node['type'] == 'CHANX':
            index = int(node['index'])
            dir = ""
            to_name = ""
            if index % 2 == 0:
                dir = "E"
            else:
                dir = "W"

            count = 0
            for segment in segments:
                count += int(segment['freq'])
                if count > index:
                    if index % 2 == 0:
                        new_index = int((int(segment['freq']) - (count - index) + 1) / 2)
                    else:
                        new_index = int((int((int(segment['freq']) - (count - index) + 1) / 2) - 1) / int(segment['length'])) * int(segment['length'])
                    to_name = to_name + segment['name'] + "." + dir + str(new_index)
                    break
            
            node['index'] = to_name
        if node['type'] == 'CHANY':
            index = int(node['index'])
            dir = ""
            to_name = ""
            if index % 2 == 0:
                dir = "N"
            else:
                dir = "S"

            count = 0
            for segment in segments:
                count += int(segment['freq'])
                if count > index:
                    if index % 2 == 0:
                        new_index = int((int(segment['freq']) - (count - index) + 1) / 2)
                    else:
                        new_index = int((int((int(segment['freq']) - (count - index) + 1) / 2) - 1) / int(segment['length'])) * int(segment['length'])
                    to_name = to_name + segment['name'] + "." + dir + str(new_index)
                    break
            
            node['index'] = to_name

        # rows = vib_layout.find("fixed_layout").findall("row")
        # cols = vib_layout.find("fixed_layout").findall("col")
        # coordx = node['coor'].split(",")[0][1:]
        # coordy = node['coor'].split(",")[1][:-1]
        # if rows:
        #     for row in rows:
        #         if row.get("starty") == coordy:
        #             vib_type = row.get("type")
        #             node['vib_type'] = vib_type
        #             break
        #     node['node_position'] = int(int(coordy) / 5)
        #     node['row_or_col'] = "row"
        # elif cols:
        #     for i in range(int(int(coordx) / 5) * 5, int(int(coordx) / 5) * 5 + 5):
        #         for col in cols:
        #             if col.get("startx") == str(i) and col.get("type")[0:8] == "vib_clb_":
        #                 vib_type = col.get("type")
        #                 node['vib_type'] = vib_type
        #                 break
        #     node['node_position'] = int(int(coordx) / 5)
        #     node['row_or_col'] = "col"

        if node['type'] == 'MEDIUM':
            for vib in vib_arch.findall("vib"):
                # if vib.get("name") == node['vib_type']:
                first_stage = vib.find("multistage_muxs").find("first_stage")
                index = int(node['index'])
                muxes = first_stage.findall("mux")
                for i in range(0, len(muxes)):
                    if i == index:
                        node['index'] =  muxes[i].get("name")
                        break
                break

def extract_critial_info(timing_report, route_report, arch_file):
    routing_info = extract_routing_from_timing_report(timing_report)
    nodes_info = extract_from_route(route_report, routing_info)
    modify(arch_file, nodes_info)
    return nodes_info

def process_designs(log_dir, arch_dir, path_dir):
    # 遍历 log_dir 下的所有子文件夹（design）
    for design in os.listdir(log_dir):
        design_path = os.path.join(log_dir, design)
        if os.path.isdir(design_path):
            # 在 path_dir 下创建同名文件夹
            design_output_dir = os.path.join(path_dir, design)
            os.makedirs(design_output_dir, exist_ok=True)

            # 遍历 design 下的所有子文件夹（arch）
            for arch in os.listdir(design_path):
                arch_path = os.path.join(design_path, arch)
                if os.path.isdir(arch_path):
                    # 构造文件路径
                    timing_report = os.path.join(arch_path, 'report_timing.setup.rpt')
                    route_report = os.path.join(arch_path, f'{design}.route')
                    arch_file = os.path.join(arch_dir, f'{arch}.xml')

                    # 检查文件是否存在
                    if os.path.exists(timing_report) and os.path.exists(route_report) and os.path.exists(arch_file):
                        # 提取关键路径信息
                        nodes_info = extract_critial_info(timing_report, route_report, arch_file)

                        # 保存结果到 path_dir/design/arch.json
                        output_file = os.path.join(design_output_dir, f'{arch}.json')
                        with open(output_file, 'w') as f:
                            json.dump(nodes_info, f, indent=4)
                        print(f'Processed: {design}/{arch}')
                    else:
                        print(f'Skipped {design}/{arch}: Missing files.')
                else:
                    print(f'Skipping non-directory: {arch}')
        else:
            print(f'Skipping non-directory: {design}')

if __name__ == '__main__':
    log_dir = '/home/wllpro/llwang/yfdai/HRAE_company/raw_dataset_results' 
    arch_dir = '/home/wllpro/llwang/yfdai/HRAE_company/raw_dataset_archs'
    path_dir = '/home/wllpro/llwang/yfdai/HRAE_company/raw_crit_paths'

    process_designs(log_dir, arch_dir, path_dir)
    print("处理完成！")