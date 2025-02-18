#!/bin/bash

# 需要保留的 .pth 文件列表（绝对路径）
keep_files=(
    "/home/wllpro/llwang/yfdai/HRAE_company/models/boxcar/best_0.001_0.001_256_SAGE_2_32_0.9444_epoch_281.pth"
    "/home/wllpro/llwang/yfdai/HRAE_company/models/cordic/best_0.001_0.001_256_SAGE_3_32_0.8980_epoch_238.pth"
    "/home/wllpro/llwang/yfdai/HRAE_company/models/cordictanh/best_0.0008_0.001_256_SAGE_3_64_0.7962_epoch_2.pth"
    "/home/wllpro/llwang/yfdai/HRAE_company/models/Divide/best_0.001_0.001_256_SAGE_3_32_0.9500_epoch_212.pth"
    "/home/wllpro/llwang/yfdai/HRAE_company/models/GrayCounter/best_0.0008_0.001_256_SAGE_2_32_0.9861_epoch_282.pth"
    "/home/wllpro/llwang/yfdai/HRAE_company/models/LCDmodule/best_0.001_0.001_256_SAGE_3_32_0.8753_epoch_117.pth"
    "/home/wllpro/llwang/yfdai/HRAE_company/models/LED_BCD8x7seg/best_0.001_0.001_256_SAGE_3_32_0.9078_epoch_101.pth"
    "/home/wllpro/llwang/yfdai/HRAE_company/models/Murax/best_0.0008_0.001_256_SAGE_2_64_0.8952_epoch_294.pth"
    "/home/wllpro/llwang/yfdai/HRAE_company/models/music/best_0.0008_0.001_256_SAGE_2_32_0.9076_epoch_133.pth"
    "/home/wllpro/llwang/yfdai/HRAE_company/models/picorv32/best_0.001_0.001_256_SAGE_3_32_0.8196_epoch_155.pth"
    "/home/wllpro/llwang/yfdai/HRAE_company/models/pong/best_0.001_0.001_256_SAGE_3_32_0.6838_epoch_199.pth"
    "/home/wllpro/llwang/yfdai/HRAE_company/models/PushButton_Debouncer/best_0.001_0.001_256_SAGE_3_32_0.8698_epoch_210.pth"
    "/home/wllpro/llwang/yfdai/HRAE_company/models/PWM/best_0.001_0.001_256_SAGE_3_32_0.8091_epoch_71.pth"
    "/home/wllpro/llwang/yfdai/HRAE_company/models/quad/best_0.001_0.001_256_SAGE_3_32_0.7845_epoch_224.pth"
    "/home/wllpro/llwang/yfdai/HRAE_company/models/RCServo/best_0.0008_0.001_256_SAGE_3_32_0.9095_epoch_283.pth"
    "/home/wllpro/llwang/yfdai/HRAE_company/models/seqcordic/best_0.0008_0.001_256_SAGE_3_32_0.9304_epoch_249.pth"
    "/home/wllpro/llwang/yfdai/HRAE_company/models/seqpolar/best_0.0008_0.001_256_SAGE_2_64_0.9380_epoch_296.pth"
    "/home/wllpro/llwang/yfdai/HRAE_company/models/simplfir/best_0.001_0.001_256_SAGE_2_64_0.8389_epoch_295.pth"
    "/home/wllpro/llwang/yfdai/HRAE_company/models/topolar/best_0.0008_0.001_256_SAGE_3_32_0.8743_epoch_125.pth"
)

# 创建关联数组用于快速查找
declare -A keep_dict
for file in "${keep_files[@]}"; do
    # 标准化路径（替换多余斜杠）
    normalized_file=$(echo "$file" | sed 's#//*#/#g')
    keep_dict["$normalized_file"]=1
done

# 是否启用“模拟运行”（不实际删除文件）
dry_run=false  # 设为 true 只显示操作，不实际删除

# 遍历当前目录及所有子目录中的 .pth 文件
find . -type f -name "*.pth" | while read -r file; do
    # 转换为绝对路径并标准化
    abs_file=$(realpath "$file" | sed 's#//*#/#g')

    # 检查是否在保留列表中
    if [[ -z "${keep_dict[$abs_file]}" ]]; then
        if [ "$dry_run" = true ]; then
            echo "[Dry Run] Would delete: $abs_file"
        else
            echo "Deleting: $abs_file"
            rm -- "$abs_file"
        fi
    else
        echo "Keeping: $abs_file"
    fi
done