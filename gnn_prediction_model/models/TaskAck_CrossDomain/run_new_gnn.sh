#!/bin/bash

learning_rates=(0.001 0.0008)

decays=(0.001)

neurons=(256)

batches=(32 64)

num_layers=(2 3)

conv_types=('SAGE')

for lr in "${learning_rates[@]}"; do
    for decay in "${decays[@]}"; do
			for neuron in "${neurons[@]}"; do
				for batch in "${batches[@]}";do
					for num_layer in "${num_layers[@]}"; do
						for conv_type in "${conv_types[@]}"; do
							# 构建bsub提交命令
							nohup_cmd="nohup bsub -I python GAT_inst_new.py --lr $lr --decay $decay --neurons $neuron --batch $batch --num_layers $num_layer --conv_type $conv_type > \"${job_name}.out\" 2> \"${job_name}.err\" &"
                            echo "$nohup_cmd"
							eval $nohup_cmd
						done
					done
				done
        done
    done
done

echo "All jobs have been submitted."
