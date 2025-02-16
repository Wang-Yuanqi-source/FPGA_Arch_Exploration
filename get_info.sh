#!/bin/bash

arch_name=$1
blif_name=$2
csv_file=$3
log_file="vpr_stdout.log"

bles=`grep 6-LUT $arch_name/$blif_name/$log_file | awk -F ' ' '{print $NF}'`
FPGA_size=`grep "FPGA sized to" $arch_name/$blif_name/$log_file | grep grid | awk -F ' ' '{print $4,"x",$4}'`
Device_Util=`grep "Device Utilization" $arch_name/$blif_name/$log_file | head -n 1 | awk -F ' ' '{print $3}'`
io_Util=`grep "Block Util" $arch_name/$blif_name/$log_file | grep "Type: io" | head -n 1 | awk -F ' ' '{print $3}'`
clb_Util=`grep "Block Util" $arch_name/$blif_name/$log_file | grep "Type: plb" | head -n 1 | awk -F ' ' '{print $3}'`
num_nets=`grep "Netlist num_nets" $arch_name/$blif_name/$log_file | awk -F ' ' '{print $3}'`
clbs=`grep "blocks of type: plb" $arch_name/$blif_name/$log_file | grep Netlist | awk -F ' ' '{print $2}'`
Total_Wirelength=`grep "Total wirelength" $arch_name/$blif_name/$log_file | awk -F ' ' '{print $3}' | awk -F ',' '{print $1}'`
Total_logic_block_area=`grep "Total logic block area" $arch_name/$blif_name/$log_file | awk -F ' ' '{print $NF}'`
Total_used_logic_block_area=`grep "Total used logic block area" $arch_name/$blif_name/$log_file | awk -F ' ' '{print $NF}'`
Total_routing_area=`grep "Total routing area" $arch_name/$blif_name/$log_file | awk -F ' ' '{print $4}' | awk -F ',' '{print $1}'`
per_logic_tile=`grep "Total routing area" $arch_name/$blif_name/$log_file | awk -F ' ' '{print $NF}'`
Crit_Path=`grep "Final critical path" $arch_name/$blif_name/$log_file | awk -F ' ' '{print $7}'`
echo "Crit_Path" $Crit_Path
echo $blif_name,$bles,$FPGA_size,$Device_Util,$io_Util,$clb_Util,$num_nets,$clbs,$Total_Wirelength,$Total_logic_block_area,$Total_used_logic_block_area,$Total_routing_area,$per_logic_tile,$Crit_Path >> $csv_file
