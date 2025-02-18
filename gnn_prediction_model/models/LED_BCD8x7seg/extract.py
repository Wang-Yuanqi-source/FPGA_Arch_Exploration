import os
import re
import csv

def extract_info_from_log(log_file_path):
    """从日志文件中提取信息"""
    with open(log_file_path, 'r', encoding='latin-1') as file:
        log_content = file.read()

    # 提取信息
    bles = re.search(r'6-LUT.*?(\d+)', log_content).group(1) if re.search(r'6-LUT.*?(\d+)', log_content) else "N/A"
    fpga_size = re.search(r'FPGA sized to.*?(\d+)\s*x\s*(\d+)', log_content)
    fpga_size = f"{fpga_size.group(1)}x{fpga_size.group(2)}" if fpga_size else "N/A"
    device_util = re.search(r'Device Utilization.*?(\d+\.\d+)', log_content).group(1) if re.search(r'Device Utilization.*?(\d+\.\d+)', log_content) else "N/A"
    io_util = re.search(r'Block Util.*?Type: io.*?(\d+\.\d+)', log_content).group(1) if re.search(r'Block Util.*?Type: io.*?(\d+\.\d+)', log_content) else "N/A"
    clb_util = re.search(r'Block Util.*?Type: plb.*?(\d+\.\d+)', log_content).group(1) if re.search(r'Block Util.*?Type: plb.*?(\d+\.\d+)', log_content) else "N/A"
    num_nets = re.search(r'Netlist num_nets.*?(\d+)', log_content).group(1) if re.search(r'Netlist num_nets.*?(\d+)', log_content) else "N/A"
    clbs = re.search(r'blocks of type: plb.*?Netlist.*?(\d+)', log_content).group(1) if re.search(r'blocks of type: plb.*?Netlist.*?(\d+)', log_content) else "N/A"
    total_wirelength = re.search(r'Total wirelength.*?(\d+,?\d+)', log_content).group(1).replace(',', '') if re.search(r'Total wirelength.*?(\d+,?\d+)', log_content) else "N/A"
    total_logic_block_area = re.search(r'Total logic block area.*?(\d+\.\d+)', log_content).group(1) if re.search(r'Total logic block area.*?(\d+\.\d+)', log_content) else "N/A"
    total_used_logic_block_area = re.search(r'Total used logic block area.*?(\d+\.\d+)', log_content).group(1) if re.search(r'Total used logic block area.*?(\d+\.\d+)', log_content) else "N/A"
    total_routing_area = re.search(r'Total routing area:\s*([\d\.e\+\-]+)', log_content).group(1) if re.search(r'Total routing area:\s*([\d\.e\+\-]+)', log_content) else "N/A"
    per_logic_tile = re.search(r'Total routing area.*?(\d+\.\d+)', log_content).group(1) if re.search(r'Total routing area.*?(\d+\.\d+)', log_content) else "N/A"
    crit_path = re.search(r'Final critical path.*?(\d+\.\d+)', log_content).group(1) if re.search(r'Final critical path.*?(\d+\.\d+)', log_content) else "N/A"

    # 返回提取的信息
    return {
        "bles": bles,
        "fpga_size": fpga_size,
        "device_util": device_util,
        "io_util": io_util,
        "clb_util": clb_util,
        "num_nets": num_nets,
        "clbs": clbs,
        "total_wirelength": total_wirelength,
        "total_logic_block_area": total_logic_block_area,
        "total_used_logic_block_area": total_used_logic_block_area,
        "total_routing_area": total_routing_area,
        "per_logic_tile": per_logic_tile,
        "crit_path": crit_path
    }

def write_to_csv(csv_file_path, architecture_name, extracted_info):
    """将提取的信息写入 CSV 文件"""
    file_exists = os.path.isfile(csv_file_path)
    with open(csv_file_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # 如果文件不存在，写入表头
        if not file_exists:
            writer.writerow([
                "Architecture",
                "6-LUTs",
                "FPGA Size",
                "Device Utilization",
                "IO Utilization",
                "CLB Utilization",
                "Number of Nets",
                "CLBs",
                "Total Wirelength",
                "Total Logic Block Area",
                "Total Used Logic Block Area",
                "Total Routing Area",
                "Per Logic Tile",
                "Critical Path"
            ])
        # 写入当前架构的信息
        writer.writerow([
            architecture_name,
            extracted_info["bles"],
            extracted_info["fpga_size"],
            extracted_info["device_util"],
            extracted_info["io_util"],
            extracted_info["clb_util"],
            extracted_info["num_nets"],
            extracted_info["clbs"],
            extracted_info["total_wirelength"],
            extracted_info["total_logic_block_area"],
            extracted_info["total_used_logic_block_area"],
            extracted_info["total_routing_area"],
            extracted_info["per_logic_tile"],
            extracted_info["crit_path"]
        ])

def process_workdir(workdir):
    """遍历 workdir 文件夹，处理每个电路设计和架构"""
    for circuit_design in os.listdir(workdir):
        circuit_design_path = os.path.join(workdir, circuit_design)
        if os.path.isdir(circuit_design_path):
            # 创建以电路设计命名的 CSV 文件
            csv_file_path = os.path.join(workdir, f"{circuit_design}.csv")
            for architecture in os.listdir(circuit_design_path):
                architecture_path = os.path.join(circuit_design_path, architecture)
                if os.path.isdir(architecture_path):
                    log_file_path = os.path.join(architecture_path, "vpr_stdout.log")
                    if os.path.isfile(log_file_path):
                        # 提取日志文件信息
                        extracted_info = extract_info_from_log(log_file_path)
                        # 将信息写入 CSV 文件
                        write_to_csv(csv_file_path, architecture, extracted_info)
                        print(f"Processed {circuit_design}/{architecture}")
                    else:
                        print(f"Log file not found in {circuit_design}/{architecture}")
                else:
                    print(f"Skipping non-directory: {architecture}")
        else:
            print(f"Skipping non-directory: {circuit_design}")

# 主程序
if __name__ == "__main__":
    workdir = "./"  # 替换为实际的 workdir 路径
    process_workdir(workdir)
    print("处理完成！")