#!/bin/bash

# 定义输出 CSV 文件路径
output_csv="/home/wllpro/llwang/yfdai/HRAE_company/models/best_models_summary.csv"

# 写入 CSV 文件的表头
echo "Folder,MaxTestR,BestFile" > "$output_csv"

# 遍历 /home/wllpro/llwang/yfdai/HRAE_company/models/ 下的所有子文件夹
for folder in /home/wllpro/llwang/yfdai/HRAE_company/models/*/; do
  if [ -d "$folder" ]; then
    max_testr=0
    best_file=""

    # 遍历子文件夹中的所有 .pth 文件
    for file in "$folder"/*.pth; do
      # 从文件名中提取 testr 的值
      testr=$(basename "$file" .pth | grep -oP '[0-9\.]+(?=_epoch_)')

      # 比较并找出最大的 testr 值
      if [[ $(echo "$testr > $max_testr" | bc) -ne 0 ]]; then
        max_testr=$testr
        best_file="$file"
      fi
    done

    # 将每个子文件夹的最大 testr 值和对应的文件名写入 CSV 文件
    echo "\"$folder\",\"$max_testr\",\"$best_file\"" >> "$output_csv"
  fi
done

echo "CSV 文件已生成：$output_csv"