# import xml.etree.ElementTree as ET
# from hyperopt import hp, space_eval, STATUS_OK, STATUS_FAIL
# from hyperopt.mongoexp import MongoTrials
# # from hyper_opt_parallel import gen_new_arch, get_args, get_rval, gen_space
# from Seeker_bayes_seg import *
# import pandas as pd
# from bson.json_util import dumps
# import matplotlib.pyplot as plt 

# def sort_trials_concern_key(elem):
#     return float(elem['geom imp'])
# def get_failed_arch(trials, archTree):
#     fail_arch_var = []
#     i = 0
#     os.system('mkdir arch_failed')
#     print(os.getcwd())
#     archfile = os.getcwd() + '/arch_failed'
    
#     for trial in trials.trials:
#         if trial['result']['status'] == STATUS_FAIL:
#             if 'results' in trial['result']:
#                 i = i + 1
#                 fail_arch_var.append(trial["misc"]["vals"])
#                 vars_dic = {}
#                 arch_var = []
#                 for (k, v) in trial['misc']['vals'].items():
#                     k = int(k[3:])
#                     vars_dic[k] = v[0]
#                 for var in sorted(vars_dic.items(), key = lambda x: x[0]):
#                     arch_var.append(var[1])
#                 segments, relations, chanWidth, typeToNum = genArch(arch_var)
#                 modifyArch_V3(segments, relations, archTree)
#                 modifyArch_addMedium(archTree)
#                 (gsbMUXFanin, imuxMUXFanin) = generateTwoStageMux_v200(archTree)
#                 modifyMUXSize(archTree, gsbMUXFanin, imuxMUXFanin, typeToNum)
#                 new_arch_name = 'test'+str(i) + '.xml'
#                 writeArch(archTree["root"].getroot(), './arch_failed/' + new_arch_name)

# def get_best_arch(trials, archTree):
#     fail_arch_var = []
#     i = 0
#     vars_dic = {}
#     work_dir = 'best_arch'
#     os.system('mkdir best_arch')
#     print(os.getcwd())
#     archfile = os.getcwd() + '/best_arch'
#     best_trail = trials.best_trial
#     arch_var = []
#     trial_var = best_trail['misc']['vals']
#     for (k, v) in trial_var.items():
#         k = int(k[3:])
#         vars_dic[k] = v[0]
#     for var in sorted(vars_dic.items(), key = lambda x: x[0]):
#         arch_var.append(var[1])
#     segments, relations, chanWidth, typeToNum = genArch(arch_var)
#     modifyArch_V3(segments, relations, archTree)
#     modifyArch_addMedium(archTree)
#     (gsbMUXFanin, imuxMUXFanin) = generateTwoStageMux_v200(archTree)
#     modifyMUXSize(archTree, gsbMUXFanin, imuxMUXFanin, typeToNum)
#     new_arch_name = 'searched.xml'
#     writeArch(archTree["root"].getroot(), './best_arch/' + new_arch_name)
#     print("generate searched arch done")


# def show_trial_info(trials, arch_name):

#     for trial in trials.trials:
#         if (trial['result']['status'] == 'ok') and (trial['result']['arch_name'] == arch_name) and (float(trial['result']['loss']) < -0.1):
#             result_df = pd.DataFrame.from_dict(trial['result']['results'])
#             print(trial['result']['loss'])
#             print(result_df)


# def statistic_runner_con(trials):

#     print('total:', len(trials.trials))
#     why_num = {}

#     trials_OK = []
#     nTrial_OK =0
#     nTrial_FAIL = 0; nTrial_FAIL_Why = 0; nTrial_FAIL_run = 0
#     for trial in trials.trials:
#         if trial['result']['status'] == STATUS_OK:
#             trials_OK.append(trial)
#             nTrial_OK += 1
#         elif trial['result']['status'] == STATUS_FAIL:
#             nTrial_FAIL += 1
#             if 'why' in trial['result']:
#                 if trial['result']['why'] in why_num:
#                     why_num[trial['result']['why']] += 1
#                 else:
#                     why_num[trial['result']['why']] = 0
#                 nTrial_FAIL_Why += 1
#             if 'results' in trial['result']:
#                 nTrial_FAIL_run += 1
#         vals = trial["misc"]["vals"]
#         rval = {}
#         for k, v in list(vals.items()):
#             if v:
#                 rval[k] = v[0]
#         # print(space_eval(space, rval))
#         # print(trial['result']['why'])
#     print('STATUS_OK:', int(nTrial_OK * 1.5))
#     print('STATUS_FAIL:', int(nTrial_FAIL * 1.5))
#     print('STATUS_FAIL_Why:', int(nTrial_FAIL_Why * 1.5))
#     print('nTrial_FAIL_run:', int(nTrial_FAIL_run * 1.5))
#     print(why_num)
    
# def statistic_best_archs(trials):

#     print('total:', len(trials.trials))
#     why_num = {}
#     archs_to_improve = {}
#     archs_to_passNum = {}
#     archs_to_res = {}
#     archs_to_archname = {}

#     trials_OK = []
#     nTrial_OK =0
#     nTrial_FAIL = 0; nTrial_FAIL_Why = 0; nTrial_FAIL_run = 0
#     for trial in trials.trials:
#         if (trial['result']['status'] == 'ok'):
#             archs_to_improve[trial['result']['arch_name']] = trial['result']['geom imp']
#             archs_to_passNum[trial['result']['arch_name']] = trial['result']['bench_PASS_number']
            
#             archs_to_res[trial['result']['arch_name']] = pd.DataFrame.from_dict(trial['result']['results'])
#         else:
#             if (trial['result'].get('why') is not None):
#                 print(trial['result']['why'])
#             nTrial_FAIL = nTrial_FAIL + 1
#     arch_ls = list(archs_to_improve.items())
#     arch_ls.sort(key= lambda x: x[1], reverse = False)

#     print('OK number:', len(arch_ls))
#     print('FAIL number:', nTrial_FAIL)
    
#     for arch_impove in arch_ls[0:200]:
#         print(arch_impove)
#         print(archs_to_passNum[arch_impove[0]])
#         print(archs_to_res[arch_impove[0]])
#         # print(space_eval(space, rval))
#         # print(trial['result']['why'])

# if __name__ == "__main__":

#     #args = get_args()
#     #base_arch_file = args.base_arch_file
#     #base_csv_file = args.base_csv_file
#     #new_arch_name = args.new_arch_name
#     #parallel_number = args.parallel_number
#     #base_arch_tree = {}

#     #with open(base_arch_file) as base_arch_f:
#         #base_arch_tree['root'] = ET.parse(base_arch_f)
#         #base_arch_tree['segOrigin'] = getOriginSeg(base_arch_tree["root"])
#     #with open(base_csv_file, 'r') as base_csv_f:
#         #base_result = pd.read_csv(base_csv_f, index_col=0)

    connect_string = "mongo+ssh://asicskl01:1234/foo_db/jobs"
#     trials = MongoTrials(connect_string)
    
#     statistic_best_archs(trials)
    
#     #for trial in trials.trials:
#         #if (trial['result']['status'] == 'ok'):
#             #print(trial['result']['geom imp'])
#             #print("\t")

#     # get_failed_arch(trials, base_arch_tree)

#     # print(trials.trials[0])
#     #statistic_runner_con(trials)
#     # print(trials.trials[0])
#     # print('sFull28_8.xml')
#     #show_trial_info(trials, 'sFullRe47_10.xml')
#     # if trials.best_trial['result']['bench_PASS_number'] > 20:
#     #for trial in trials.trials:
#         #if trial['result']['status'] == STATUS_OK:
#             #print(trial['result']['loss'])
#             #print(trial['result']['geom imp'])
#             #print(trial['result']['bench_PASS_number'])
#             #print(trial['result']['arch_name'])
#             #result_df = pd.DataFrame.from_dict(trial['result']['results'])
#             #print(result_df)
#             #print("\n \n")
#     # print(trials.best_trial)
#     # print(sorted(trials.argmin.items(), key=lambda v:v[0]))

#     # dict_test = trials.argmin
#     # new_dict = []
#     # for i in range(696):
#     #     new_dict.append( dict_test['var'+str(i)] )
#     # segments, relations, chanWidth, typeToNum = genArch(new_dict)
#     # modifyArch_V3(segments, relations, base_arch_tree)
#     # modifyArch_addMedium(base_arch_tree)
#     # (gsbMUXFanin, imuxMUXFanin) = generateTwoStageMux_v200(base_arch_tree)
#     # modifyMUXSize(base_arch_tree, gsbMUXFanin, imuxMUXFanin, typeToNum)
#     # new_arch_name = 'searched.xml'
#     # writeArch(base_arch_tree["root"].getroot(), './best_arch/' + new_arch_name)

#     # get_best_arch(trials, base_arch_tree)
#     # print(trials.best_trial['result']['parms'])
#     # result_df.to_csv(new_arch_name + '.csv')

#     # maxSegLen   = 16
#     # numAddition = 4 
#     # space = [hp.uniform("var" + str(idx), 0.0, 1.0) for idx in range(maxSegLen + (2 * maxSegLen + 2) * (maxSegLen + numAddition))]
#     # print(space_eval(space, trials.argmin))
#     # segments, relations, chanWidth, typeToNum = genArch(space_eval(space, trials.argmin))
#     # modifyArch_V3(segments, relations, base_arch_tree)
#     # modifyArch_addMedium(base_arch_tree)
#     # (gsbMUXFanin, imuxMUXFanin) = generateTwoStageMux_v200(base_arch_tree)
#     # modifyMUXSize(base_arch_tree, gsbMUXFanin, imuxMUXFanin, typeToNum)
#     # new_arch_name = 'searched.xml'
#     # writeArch(base_arch_tree["root"].getroot(), './best_arch/' + new_arch_name)

    
#     # trials_OK = [
#     #     t
#     #     for t in trials
#     #     if t["result"]["status"] == STATUS_OK
#     # ]
#     # print(len(trials_OK))
#     # print(trials_OK[0]['result']['loss'])
#     # x = []
#     # y = []
#     # print(len(trials_OK))
#     # for i in range(len(trials_OK)):
#     #     x.append(i)
#     #     y.append(float(trials_OK[i]['result']['loss']-15.13842497) / 15.13842497 * 100)
        
#     # plt.scatter(x, y, zorder=5)
#     # plt.plot(x, y, zorder=5)
#     # plt.xlabel('Count')
#     # plt.ylabel('Delay (%)')
#     # plt.axhline(y=0, linestyle='--', c='r', zorder=10)
#     # # plt.axhline(y=-3.057934867318393, linestyle='--', c='r', zorder=10)
#     # plt.savefig('count_anneal.jpg', dpi=600, bbox_inches = 'tight')


#     # trials_no_repeat = []
#     # for t in trials_OK:
#     #     params = get_rval(t)
#     #     if params not in trials_no_repeat:
#     #         trials_no_repeat.append(params)
#     # print('trials_OK:', len(trials_OK))
#     # print('trials_no_repeat:', len(trials_no_repeat))

#     # counter = 0
#     # for t in trials.trials:
#     #     if t["result"]["status"] == STATUS_OK and float(t['result']['geom imp']) < -0.023:
#     #         print((t['result']['geom imp']), counter, end=' ')
#     #     counter += 1

#     # trials_concern = []
#     # for trial in trials.trials:
#     #     trial_tmp_dict = {}
#     #     if trial['result']['status'] == STATUS_OK and trial['result']['bench_PASS_number'] == 18:
#     #         trial_tmp_dict['bench_PASS_number'] = trial['result']['bench_PASS_number']
#     #         trial_tmp_dict['geom imp'] = trial['result']['geom imp']
#     #         trial_tmp_dict['result'] = dumps(trial['result']['results'])
#     #         vals = trial["misc"]["vals"]
#     #         rval = {}
#     #         for k, v in list(vals.items()):
#     #             if v:
#     #                 rval[k] = v[0]
#     #         trial_tmp_dict['params'] = space_eval(space, rval)
#     #         if trial_tmp_dict not in trials_concern:
#     #             trials_concern.append(trial_tmp_dict)

#     # nNumb48 = nNumb56 = nNumb64 = nNumb72 = nNumb80 = nNumb88 = nNumb96 = 0
#     # nMUX6 = nMUX7 = nMUX8 = nMUX9 = 0
#     # trials_concern.sort(key=sort_trials_concern_key)
#     # for t in trials_concern[:300]:
#     #     print(t['params']['number'], t['geom imp'], t['params']['l1_l2']['size'], end=' ')
#     #     print()
#     #     if t['params']['l1_l2']['size'] == 6: nMUX6 += 1
#     #     if t['params']['l1_l2']['size'] == 7: nMUX7 += 1
#     #     if t['params']['l1_l2']['size'] == 8: nMUX8 += 1
#     #     if t['params']['l1_l2']['size'] == 9: nMUX9 += 1
        
#     #     if t['params']['number'] == 48: nNumb48 += 1
#     #     if t['params']['number'] == 56: nNumb56 += 1
#     #     if t['params']['number'] == 64: nNumb64 += 1
#     #     if t['params']['number'] == 72: nNumb72 += 1
#     #     if t['params']['number'] == 80: nNumb80 += 1
#     #     if t['params']['number'] == 88: nNumb88 += 1
#     #     if t['params']['number'] == 96: nNumb96 += 1
#     # print(nMUX6, nMUX7, nMUX8, nMUX9, end=' ')
#     # print()
#     # print(nNumb48, nNumb56, nNumb64, nNumb72, nNumb80, nNumb88, nNumb96, end=' ')
#     # print()

#     # for t in trials_concern:
#     #     if t['params']['number'] == 96:
#     #         print(t['params']['number'], t['geom imp'], t['params']['l1_l2']['size'], end=' ')
#     #         print()


import xml.etree.ElementTree as ET
from hyperopt import hp, space_eval, STATUS_OK, STATUS_FAIL
from hyperopt.mongoexp import MongoTrials
# from hyper_opt_parallel import gen_new_arch, get_args, get_rval, gen_space
from Seeker_bayes_seg import *
import pandas as pd
from bson.json_util import dumps
import matplotlib.pyplot as plt 

def sort_trials_concern_key(elem):
    return float(elem['geom imp'])
def get_failed_arch(trials, archTree):
    fail_arch_var = []
    i = 0
    os.system('mkdir arch_failed')
    print(os.getcwd())
    archfile = os.getcwd() + '/arch_failed'
    
    for trial in trials.trials:
        if trial['result']['status'] == STATUS_FAIL:
            if 'results' in trial['result']:
                i = i + 1
                fail_arch_var.append(trial["misc"]["vals"])
                vars_dic = {}
                arch_var = []
                for (k, v) in trial['misc']['vals'].items():
                    k = int(k[3:])
                    vars_dic[k] = v[0]
                for var in sorted(vars_dic.items(), key = lambda x: x[0]):
                    arch_var.append(var[1])
                segments, relations, chanWidth, typeToNum = genArch(arch_var)
                modifyArch_V3(segments, relations, archTree)
                modifyArch_addMedium(archTree)
                (gsbMUXFanin, imuxMUXFanin) = generateTwoStageMux_v200(archTree)
                modifyMUXSize(archTree, gsbMUXFanin, imuxMUXFanin, typeToNum)
                new_arch_name = 'test'+str(i) + '.xml'
                writeArch(archTree["root"].getroot(), './arch_failed/' + new_arch_name)

def get_best_arch(trials, archTree):
    fail_arch_var = []
    i = 0
    vars_dic = {}
    work_dir = 'best_arch'
    os.system('mkdir best_arch')
    print(os.getcwd())
    archfile = os.getcwd() + '/best_arch'
    best_trail = trials.best_trial
    arch_var = []
    trial_var = best_trail['misc']['vals']
    for (k, v) in trial_var.items():
        k = int(k[3:])
        vars_dic[k] = v[0]
    for var in sorted(vars_dic.items(), key = lambda x: x[0]):
        arch_var.append(var[1])
    segments, relations, chanWidth, typeToNum = genArch(arch_var)
    modifyArch_V3(segments, relations, archTree)
    modifyArch_addMedium(archTree)
    (gsbMUXFanin, imuxMUXFanin) = generateTwoStageMux_v200(archTree)
    modifyMUXSize(archTree, gsbMUXFanin, imuxMUXFanin, typeToNum)
    new_arch_name = 'searched.xml'
    writeArch(archTree["root"].getroot(), './best_arch/' + new_arch_name)
    print("generate searched arch done")


def show_trial_info(trials, arch_name):

    for trial in trials.trials:
        if (trial['result']['status'] == 'ok') and (trial['result']['arch_name'] == arch_name) and (float(trial['result']['loss']) < -0.1):
            result_df = pd.DataFrame.from_dict(trial['result']['results'])
            print(trial['result']['loss'])
            print(result_df)


def statistic_runner_con(trials):

    print('total:', len(trials.trials))
    why_num = {}

    trials_OK = []
    nTrial_OK =0
    nTrial_FAIL = 0; nTrial_FAIL_Why = 0; nTrial_FAIL_run = 0
    for trial in trials.trials:
        if trial['result']['status'] == STATUS_OK:
            trials_OK.append(trial)
            nTrial_OK += 1
        elif trial['result']['status'] == STATUS_FAIL:
            nTrial_FAIL += 1
            if 'why' in trial['result']:
                if trial['result']['why'] in why_num:
                    why_num[trial['result']['why']] += 1
                else:
                    why_num[trial['result']['why']] = 0
                nTrial_FAIL_Why += 1
            if 'results' in trial['result']:
                nTrial_FAIL_run += 1
        vals = trial["misc"]["vals"]
        rval = {}
        for k, v in list(vals.items()):
            if v:
                rval[k] = v[0]
        # print(space_eval(space, rval))
        # print(trial['result']['why'])
    print('STATUS_OK:', int(nTrial_OK * 1.5))
    print('STATUS_FAIL:', int(nTrial_FAIL * 1.5))
    print('STATUS_FAIL_Why:', int(nTrial_FAIL_Why * 1.5))
    print('nTrial_FAIL_run:', int(nTrial_FAIL_run * 1.5))
    print(why_num)
    
def statistic_best_archs(trials):

    print('total:', len(trials.trials))
    why_num = {}
    archs_to_improve = {}
    archs_to_improve_delay = {}
    archs_to_improve_area = {}
    archs_to_passNum = {}
    archs_to_res = {}
    archs_to_archname = {}

    trials_OK = []
    nTrial_OK =0
    nTrial_FAIL = 0; nTrial_FAIL_Why = 0; nTrial_FAIL_run = 0
    for trial in trials.trials:
        if (trial['result']['status'] == 'ok'):
            archs_to_improve[trial['result']['arch_name']] = trial['result']['loss']
            archs_to_improve_delay[trial['result']['arch_name']] = trial['result']['delay imp']
            archs_to_improve_area[trial['result']['arch_name']] = trial['result']['area imp']
            archs_to_passNum[trial['result']['arch_name']] = trial['result']['bench_PASS_number']
            
            archs_to_res[trial['result']['arch_name']] = pd.DataFrame.from_dict(trial['result']['results'])
        else:
            if (trial['result'].get('why') is not None):
                print(trial['result']['why'])
            nTrial_FAIL = nTrial_FAIL + 1
    arch_ls = list(archs_to_improve_delay.items())
    arch_ls.sort(key= lambda x: x[1], reverse = False)

    print('OK number:', len(arch_ls))
    print('FAIL number:', nTrial_FAIL)
    
    for arch_impove in arch_ls[0:200]:
        print(arch_impove)
        print(archs_to_passNum[arch_impove[0]])
        print(archs_to_res[arch_impove[0]])
        # print(space_eval(space, rval))
        # print(trial['result']['why'])

if __name__ == "__main__":

    #args = get_args()
    #base_arch_file = args.base_arch_file
    #base_csv_file = args.base_csv_file
    #new_arch_name = args.new_arch_name
    #parallel_number = args.parallel_number
    #base_arch_tree = {}

    #with open(base_arch_file) as base_arch_f:
        #base_arch_tree['root'] = ET.parse(base_arch_f)
        #base_arch_tree['segOrigin'] = getOriginSeg(base_arch_tree["root"])
    #with open(base_csv_file, 'r') as base_csv_f:
        #base_result = pd.read_csv(base_csv_f, index_col=0)

    connect_string = "mongo+ssh://asicskl28:1234/foo_db/jobs"
    trials = MongoTrials(connect_string)
    
    statistic_best_archs(trials)
    
    #for trial in trials.trials:
        #if (trial['result']['status'] == 'ok'):
            #print(trial['result']['geom imp'])
            #print("\t")

    # get_failed_arch(trials, base_arch_tree)

    # print(trials.trials[0])
    #statistic_runner_con(trials)
    # print(trials.trials[0])
    # print('sFull28_8.xml')
    #show_trial_info(trials, 'sFullRe47_10.xml')
    # if trials.best_trial['result']['bench_PASS_number'] > 20:
    #for trial in trials.trials:
        #if trial['result']['status'] == STATUS_OK:
            #print(trial['result']['loss'])
            #print(trial['result']['geom imp'])
            #print(trial['result']['bench_PASS_number'])
            #print(trial['result']['arch_name'])
            #result_df = pd.DataFrame.from_dict(trial['result']['results'])
            #print(result_df)
            #print("\n \n")
    # print(trials.best_trial)
    # print(sorted(trials.argmin.items(), key=lambda v:v[0]))

    # dict_test = trials.argmin
    # new_dict = []
    # for i in range(696):
    #     new_dict.append( dict_test['var'+str(i)] )
    # segments, relations, chanWidth, typeToNum = genArch(new_dict)
    # modifyArch_V3(segments, relations, base_arch_tree)
    # modifyArch_addMedium(base_arch_tree)
    # (gsbMUXFanin, imuxMUXFanin) = generateTwoStageMux_v200(base_arch_tree)
    # modifyMUXSize(base_arch_tree, gsbMUXFanin, imuxMUXFanin, typeToNum)
    # new_arch_name = 'searched.xml'
    # writeArch(base_arch_tree["root"].getroot(), './best_arch/' + new_arch_name)

    # get_best_arch(trials, base_arch_tree)
    # print(trials.best_trial['result']['parms'])
    # result_df.to_csv(new_arch_name + '.csv')

    # maxSegLen   = 16
    # numAddition = 4 
    # space = [hp.uniform("var" + str(idx), 0.0, 1.0) for idx in range(maxSegLen + (2 * maxSegLen + 2) * (maxSegLen + numAddition))]
    # print(space_eval(space, trials.argmin))
    # segments, relations, chanWidth, typeToNum = genArch(space_eval(space, trials.argmin))
    # modifyArch_V3(segments, relations, base_arch_tree)
    # modifyArch_addMedium(base_arch_tree)
    # (gsbMUXFanin, imuxMUXFanin) = generateTwoStageMux_v200(base_arch_tree)
    # modifyMUXSize(base_arch_tree, gsbMUXFanin, imuxMUXFanin, typeToNum)
    # new_arch_name = 'searched.xml'
    # writeArch(base_arch_tree["root"].getroot(), './best_arch/' + new_arch_name)

    
    # trials_OK = [
    #     t
    #     for t in trials
    #     if t["result"]["status"] == STATUS_OK
    # ]
    # print(len(trials_OK))
    # print(trials_OK[0]['result']['loss'])
    # x = []
    # y = []
    # print(len(trials_OK))
    # for i in range(len(trials_OK)):
    #     x.append(i)
    #     y.append(float(trials_OK[i]['result']['loss']-15.13842497) / 15.13842497 * 100)
        
    # plt.scatter(x, y, zorder=5)
    # plt.plot(x, y, zorder=5)
    # plt.xlabel('Count')
    # plt.ylabel('Delay (%)')
    # plt.axhline(y=0, linestyle='--', c='r', zorder=10)
    # # plt.axhline(y=-3.057934867318393, linestyle='--', c='r', zorder=10)
    # plt.savefig('count_anneal.jpg', dpi=600, bbox_inches = 'tight')


    # trials_no_repeat = []
    # for t in trials_OK:
    #     params = get_rval(t)
    #     if params not in trials_no_repeat:
    #         trials_no_repeat.append(params)
    # print('trials_OK:', len(trials_OK))
    # print('trials_no_repeat:', len(trials_no_repeat))

    # counter = 0
    # for t in trials.trials:
    #     if t["result"]["status"] == STATUS_OK and float(t['result']['geom imp']) < -0.023:
    #         print((t['result']['geom imp']), counter, end=' ')
    #     counter += 1

    # trials_concern = []
    # for trial in trials.trials:
    #     trial_tmp_dict = {}
    #     if trial['result']['status'] == STATUS_OK and trial['result']['bench_PASS_number'] == 18:
    #         trial_tmp_dict['bench_PASS_number'] = trial['result']['bench_PASS_number']
    #         trial_tmp_dict['geom imp'] = trial['result']['geom imp']
    #         trial_tmp_dict['result'] = dumps(trial['result']['results'])
    #         vals = trial["misc"]["vals"]
    #         rval = {}
    #         for k, v in list(vals.items()):
    #             if v:
    #                 rval[k] = v[0]
    #         trial_tmp_dict['params'] = space_eval(space, rval)
    #         if trial_tmp_dict not in trials_concern:
    #             trials_concern.append(trial_tmp_dict)

    # nNumb48 = nNumb56 = nNumb64 = nNumb72 = nNumb80 = nNumb88 = nNumb96 = 0
    # nMUX6 = nMUX7 = nMUX8 = nMUX9 = 0
    # trials_concern.sort(key=sort_trials_concern_key)
    # for t in trials_concern[:300]:
    #     print(t['params']['number'], t['geom imp'], t['params']['l1_l2']['size'], end=' ')
    #     print()
    #     if t['params']['l1_l2']['size'] == 6: nMUX6 += 1
    #     if t['params']['l1_l2']['size'] == 7: nMUX7 += 1
    #     if t['params']['l1_l2']['size'] == 8: nMUX8 += 1
    #     if t['params']['l1_l2']['size'] == 9: nMUX9 += 1
        
    #     if t['params']['number'] == 48: nNumb48 += 1
    #     if t['params']['number'] == 56: nNumb56 += 1
    #     if t['params']['number'] == 64: nNumb64 += 1
    #     if t['params']['number'] == 72: nNumb72 += 1
    #     if t['params']['number'] == 80: nNumb80 += 1
    #     if t['params']['number'] == 88: nNumb88 += 1
    #     if t['params']['number'] == 96: nNumb96 += 1
    # print(nMUX6, nMUX7, nMUX8, nMUX9, end=' ')
    # print()
    # print(nNumb48, nNumb56, nNumb64, nNumb72, nNumb80, nNumb88, nNumb96, end=' ')
    # print()

    # for t in trials_concern:
    #     if t['params']['number'] == 96:
    #         print(t['params']['number'], t['geom imp'], t['params']['l1_l2']['size'], end=' ')
    #         print()
