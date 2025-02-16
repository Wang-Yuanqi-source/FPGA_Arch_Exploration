#!/bin/bash

export PYTHONPATH=`pwd`

parallel=30
step=1

# run mongod
mongo_dir="workdir/mongo_db_vib"
workdir="workdir"
vpr_dir="Your_VPR_Path"
mkdir -p $mongo_dir ; rm -rf $mongo_dir/*
bsub -R "select[hname!=asicskl03]" "mongod --dbpath $mongo_dir --port 1234 > /dev/null"
while [[ `bjobs` == "" ]]; do sleep 1s ; done
while [[ `bjobs -w | grep mongod | awk '{print $6}'` == "-" ]]; do sleep 1s ; done
mongo_exec_host=`bjobs -w | grep mongod | awk '{print $6}'`
echo $mongo_exec_host

# run hyperopt.py
opt_linenumber=`cat -n Seeker_bayes_seg.py  | grep mongo+ssh | head -n 1 | awk '{print $1}'`
sed -i "${opt_linenumber}c \ \ \ \ connect_string = \"mongo+ssh://$mongo_exec_host:1234/foo_db/jobs\"" Seeker_bayes_seg.py

result_linenumber=`cat -n get_result.py  | grep mongo+ssh | head -n 1 | awk '{print $1}'`
sed -i "${result_linenumber}c \ \ \ \ connect_string = \"mongo+ssh://$mongo_exec_host:1234/foo_db/jobs\"" get_result.py
bsub -R "select[hname!=asicskl03]" "python3 Seeker_bayes_seg.py -base_arch_file alkaidT_vib.xml -base_csv_file result_new_para.csv -parallel_number $parallel -exec_file $vpr_dir -blif_dir /home/wllpro/llwang/yqwang/parellel_editing_alkaidT/blif_files -blif_names_file blif_list -same_trial_limit 1 > log.txt 2>&1" # log


# run hyperopt-mongo-worker
for (( i = 0; i < $parallel; i++ ))
do
    t_dir="$workdir/vib_new$i" ; echo $t_dir
    mkdir -p $t_dir ; rm -rf $t_dir/*
    cp get_info.sh $t_dir # cp run_vpr.sh $t_dir ; cp initial_csv.sh $t_dir ; 
    chmod +x ./get_info.sh
    bsub -R "select[hname!=asicskl03]" "hyperopt-mongo-worker --mongo=$mongo_exec_host:1234/foo_db --poll-interval=0.1 --workdir=$t_dir/ --reserve-timeout=360000 --no-subprocesses > $t_dir/log 2>&1" # /dev/null 2>&1"
    # hyperopt-mongo-worker --mongo=$mongo_exec_host:1234/foo_db --poll-interval=0.1 --workdir=$t_dir/ --reserve-timeout=36000 --no-subprocesses
    sleep 0.5s
done
