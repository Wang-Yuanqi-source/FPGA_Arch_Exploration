import json
from collections import Counter

def count_node_names(file_name):
    # 构建文件路径
    json_file_path = file_name
    
    # 读取 JSON 文件
    with open(json_file_path, 'r') as f:
        nodes_info = json.load(f)
    
    # 初始化计数器
    name_counter = Counter()
    
    # 遍历节点信息
    for node in nodes_info:
        index = node['index']
        
        # 生成 name
        if node['type'] in ['CHANX', 'CHANY']:
            name = f"{index}_out"
        else:
            name = f"{index}"
        
        # 更新计数
        name_counter[name] += 1

    return name_counter

# file_name = "trial_999"
# node_counts = count_node_names(file_name)
# print(node_counts)
