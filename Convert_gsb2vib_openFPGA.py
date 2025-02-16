import xml.etree.cElementTree as ET
import random
from xml.dom import minidom
import re
from random import randint

CLB_OPIN_NAME = "O"
CLB_IPIN_NAME = ["I0", "I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8", "I9", "I10", "I11"]
CLB_OPIN_NUM = 24
CLB_IPIN_NUM_PER_PORT = 5

IO_LEFTL_OUTPUT_NAME = "io_leftL.a2f_o"
IO_LEFTL_OUTPUT_NUM = 7
IO_LEFTL_INPUT_NAME = "io_leftL.f2a_i"
IO_LEFTL_INPUT_NAME_LCLK = "io_leftL.lclk"
IO_LEFTL_INPUT_NAME_LRESET = "io_leftL.lreset"
IO_LEFTL_INPUT_NUM = 14

IO_RIGHTL_OUTPUT_NAME = "io_rightL.a2f_o"
IO_RIGHTL_OUTPUT_NUM = 6
IO_RIGHTL_INPUT_NAME = "io_rightL.f2a_i"
IO_RIGHTL_INPUT_NAME_LCLK = "io_rightL.lclk"
IO_RIGHTL_INPUT_NAME_LRESET = "io_rightL.lreset"
IO_RIGHTL_INPUT_NUM = 6

IO_TOPL_OUTPUT_NAME = "io_topL.a2f_o"
IO_TOP_DSPL_OUTPUT_NAME = "io_top_dspL.a2f_o"
IO_TOP_RAML_OUTPUT_NAME = "io_top_ramL.a2f_o"
IO_TOPL_OUTPUT_NUM = 24
IO_TOPL_INPUT_NAME = "io_topL.f2a_i"
IO_TOP_DSPL_INPUT_NAME = "io_top_dspL.f2a_i"
IO_TOP_RAML_INPUT_NAME = "io_top_ramL.f2a_i"
IO_TOPL_INPUT_NAME_LCLK = "io_topL.lclk"
IO_TOP_DSPL_INPUT_NAME_LCLK = "io_top_dspL.lclk"
IO_TOP_RAML_INPUT_NAME_LCLK = "io_top_ramL.lclk"
IO_TOPL_INPUT_NAME_LRESET = "io_topL.lreset"
IO_TOP_DSPL_INPUT_NAME_LRESET = "io_top_dspL.lreset"
IO_TOP_RAML_INPUT_NAME_LRESET = "io_top_ramL.lreset"
IO_TOPL_INPUT_NUM = 7

IO_BOTTOML_OUTPUT_NAME = "io_bottomL.a2f_o"
IO_BOTTOM_DSPL_OUTPUT_NAME = "io_bottom_dspL.a2f_o"
IO_BOTTOM_RAML_OUTPUT_NAME = "io_bottom_ramL.a2f_o"
IO_BOTTOML_OUTPUT_NUM = 4
IO_BOTTOML_INPUT_NAME = "io_bottomL.f2a_i"
IO_BOTTOM_DSPL_INPUT_NAME = "io_bottom_dspL.f2a_i"
IO_BOTTOM_RAML_INPUT_NAME = "io_bottom_ramL.f2a_i"
IO_BOTTOML_INPUT_NAME_LCLK = "io_bottomL.lclk"
IO_BOTTOM_DSPL_INPUT_NAME_LCLK = "io_bottom_dspL.lclk"
IO_BOTTOM_RAML_INPUT_NAME_LCLK = "io_bottom_ramL.lclk"
IO_BOTTOML_INPUT_NAME_LRESET = "io_bottomL.lreset"
IO_BOTTOM_DSPL_INPUT_NAME_LRESET = "io_bottom_dspL.lreset"
IO_BOTTOM_RAML_INPUT_NAME_LRESET = "io_bottom_ramL.lreset"
IO_BOTTOML_INPUT_NUM = 8

DSP_INPUT_PINS_UP = ["dsp.a[0]", "dsp.a[1]", "dsp.a[2]", "dsp.a[3]", "dsp.a[4]", "dsp.a[5]", "dsp.a[6]", "dsp.a[7]", "dsp.a[8]", "dsp.a[9]", "dsp.a[10]", "dsp.a[11]",
                     "dsp.b[0]", "dsp.b[1]", "dsp.b[2]", "dsp.b[3]", "dsp.b[4]", "dsp.b[5]", "dsp.b[6]", "dsp.b[7]", "dsp.b[8]", "dsp.b[9]", "dsp.lclk[0]", "dsp.lreset[0]",
                     "dsp.a[24]", "dsp.a[25]", "dsp.a[26]", "dsp.a[27]", "dsp.a[28]", "dsp.a[29]", "dsp.a[30]", "dsp.a[31]", "dsp.a[32]", "dsp.a[33]", "dsp.a[34]", "dsp.a[35]",
                     "dsp.b[20]", "dsp.b[21]", "dsp.b[22]", "dsp.b[23]", "dsp.b[24]", "dsp.b[25]", "dsp.b[26]", "dsp.b[27]", "dsp.b[28]", "dsp.b[29]"]

DSP_OUTPUT_PINS_UP = ["dsp.q_o[0]", "dsp.q_o[1]", "dsp.q_o[2]", "dsp.q_o[3]", "dsp.q_o[4]", "dsp.q_o[5]", "dsp.q_o[6]", "dsp.q_o[7]", "dsp.q_o[8]", "dsp.q_o[9]", "dsp.q_o[10]", "dsp.q_o[11]",
                      "dsp.q_o[12]", "dsp.q_o[13]", "dsp.q_o[14]", "dsp.q_o[15]", "dsp.q_o[16]", "dsp.q_o[17]", "dsp.q_o[18]", "dsp.q_o[19]", "dsp.q_o[20]", "dsp.q_o[21]", "dsp.q_o[22]", "dsp.q_o[23]"]

DSP_INPUT_PINS_DOWN = ["dsp.a[36]", "dsp.a[37]", "dsp.a[38]", "dsp.a[39]", "dsp.a[40]", "dsp.a[41]", "dsp.a[42]", "dsp.a[43]", "dsp.a[44]", "dsp.a[45]", "dsp.a[46]", "dsp.a[47]",
                       "dsp.b[30]", "dsp.b[31]", "dsp.b[32]", "dsp.b[33]", "dsp.b[34]", "dsp.b[35]", "dsp.b[36]", "dsp.b[37]", "dsp.b[38]", "dsp.b[39]",
                       "dsp.a[12]", "dsp.a[13]", "dsp.a[14]", "dsp.a[15]", "dsp.a[16]", "dsp.a[17]", "dsp.a[18]", "dsp.a[19]", "dsp.a[20]", "dsp.a[21]", "dsp.a[22]", "dsp.a[23]",
                       "dsp.b[10]", "dsp.b[11]", "dsp.b[12]", "dsp.b[13]", "dsp.b[14]", "dsp.b[15]", "dsp.b[16]", "dsp.b[17]", "dsp.b[18]", "dsp.b[19]"]

DSP_OUTPUT_PINS_DOWN = ["dsp.q_o[24]", "dsp.q_o[25]", "dsp.q_o[26]", "dsp.q_o[27]", "dsp.q_o[28]", "dsp.q_o[29]", "dsp.q_o[30]", "dsp.q_o[31]", "dsp.q_o[32]", "dsp.q_o[33]", "dsp.q_o[34]", "dsp.q_o[35]",
                        "dsp.q_o[36]", "dsp.q_o[37]", "dsp.q_o[38]", "dsp.q_o[39]", "dsp.q_o[40]", "dsp.q_o[41]", "dsp.q_o[42]", "dsp.q_o[43]"]

RAM9K_INPUT_PINS_UP = ["ram9k.raddr_i[0]", "ram9k.raddr_i[1]", "ram9k.raddr_i[2]", "ram9k.raddr_i[3]", "ram9k.raddr_i[4]", "ram9k.raddr_i[5]",
                       "ram9k.waddr_i[0]", "ram9k.waddr_i[1]", "ram9k.waddr_i[2]", "ram9k.waddr_i[3]", "ram9k.waddr_i[4]", "ram9k.waddr_i[5]",
                       "ram9k.data_i[0]", "ram9k.data_i[1]", "ram9k.data_i[2]", "ram9k.data_i[3]", "ram9k.data_i[4]", "ram9k.data_i[5]", "ram9k.data_i[6]", "ram9k.data_i[7]", "ram9k.data_i[8]",
                       "ram9k.data_i[18]", "ram9k.data_i[19]", "ram9k.data_i[20]", "ram9k.data_i[21]", "ram9k.data_i[22]", "ram9k.data_i[23]", "ram9k.data_i[24]", "ram9k.data_i[25]", "ram9k.data_i[26]",
                       "ram9k.bwen_ni[0]", "ram9k.bwen_ni[1]", "ram9k.bwen_ni[2]", "ram9k.bwen_ni[3]", "ram9k.bwen_ni[4]", "ram9k.bwen_ni[5]", "ram9k.bwen_ni[6]", "ram9k.bwen_ni[7]", "ram9k.bwen_ni[8]",
                       "ram9k.bwen_ni[18]", "ram9k.bwen_ni[19]", "ram9k.bwen_ni[20]", "ram9k.bwen_ni[21]", "ram9k.bwen_ni[22]", "ram9k.bwen_ni[23]", "ram9k.bwen_ni[24]", "ram9k.bwen_ni[25]", "ram9k.bwen_ni[26]",
                       "ram9k.lclk[0]", "ram9k.lreset[0]"]

RAM9K_OUTPUT_PINS_UP = ["ram9k.q_o[0]", "ram9k.q_o[1]", "ram9k.q_o[2]", "ram9k.q_o[3]", "ram9k.q_o[4]", "ram9k.q_o[5]", "ram9k.q_o[6]", "ram9k.q_o[7]", "ram9k.q_o[8]", "ram9k.q_o[9]", "ram9k.q_o[10]", "ram9k.q_o[11]",
                        "ram9k.q_o[12]", "ram9k.q_o[13]", "ram9k.q_o[14]", "ram9k.q_o[15]", "ram9k.q_o[16]", "ram9k.q_o[17]", "ram9k.q_o[18]", "ram9k.q_o[19]", "ram9k.q_o[20]", "ram9k.q_o[21]", "ram9k.q_o[22]", "ram9k.q_o[23]"]

RAM9K_INPUT_PINS_DOWN = ["ram9k.raddr_i[6]", "ram9k.raddr_i[7]", "ram9k.raddr_i[8]", "ram9k.raddr_i[9]", "ram9k.raddr_i[10]",
                         "ram9k.waddr_i[6]", "ram9k.waddr_i[7]", "ram9k.waddr_i[8]", "ram9k.waddr_i[9]", "ram9k.waddr_i[10]",
                         "ram9k.data_i[27]", "ram9k.data_i[28]", "ram9k.data_i[29]", "ram9k.data_i[30]", "ram9k.data_i[31]", "ram9k.data_i[32]", "ram9k.data_i[33]", "ram9k.data_i[34]", "ram9k.data_i[35]",
                         "ram9k.data_i[9]", "ram9k.data_i[10]", "ram9k.data_i[11]", "ram9k.data_i[12]", "ram9k.data_i[13]", "ram9k.data_i[14]", "ram9k.data_i[15]", "ram9k.data_i[16]", "ram9k.data_i[17]",
                         "ram9k.bwen_ni[27]", "ram9k.bwen_ni[28]", "ram9k.bwen_ni[29]", "ram9k.bwen_ni[30]", "ram9k.bwen_ni[31]", "ram9k.bwen_ni[32]", "ram9k.bwen_ni[33]", "ram9k.bwen_ni[34]", "ram9k.bwen_ni[35]",
                         "ram9k.bwen_ni[9]", "ram9k.bwen_ni[10]", "ram9k.bwen_ni[11]", "ram9k.bwen_ni[12]", "ram9k.bwen_ni[13]", "ram9k.bwen_ni[14]", "ram9k.bwen_ni[15]", "ram9k.bwen_ni[16]", "ram9k.bwen_ni[17]",
                         "ram9k.wen_ni[0]", "ram9k.ren_ni[0]"]

RAM9K_OUTPUT_PINS_DOWN = ["ram9k.q_o[24]", "ram9k.q_o[25]", "ram9k.q_o[26]", "ram9k.q_o[27]", "ram9k.q_o[28]", "ram9k.q_o[29]", "ram9k.q_o[30]", "ram9k.q_o[31]", "ram9k.q_o[32]", "ram9k.q_o[33]", "ram9k.q_o[34]", "ram9k.q_o[35]"]
LAYOUT_NAME = "ultimate"
# remove the imux into the gsb tag, and modify the mux name in the original imux tag to aviod repeating
def swap_tags(imuxElem, gsbElem):
    imux_1st_stage = imuxElem.find("./multistage_muxs/first_stage")
    gsb_1st_stage = gsbElem.find("./multistage_muxs/first_stage")
    gsb_1st_stage.set("switch_name", "only_mux")

    for mux in imux_1st_stage.findall("mux"):
        gsb_1st_stage.append(mux)
        imux_1st_stage.remove(mux)

    imux_2nd_stage = imuxElem.find("./multistage_muxs/second_stage")
    gsb_2nd_stage = gsbElem.find("./multistage_muxs/second_stage")

    for mux in imux_2nd_stage.findall("mux"):
        gsb_2nd_stage.append(mux)
        imux_2nd_stage.remove(mux)

#add the omux description in the gsb tag
def add_omuxes(archtree, omuxElem, gsbElem):
    gsb_1st_stage = gsbElem.find("./multistage_muxs/first_stage")
    omux_1st_stage = omuxElem.find("./multistage_muxs/first_stage")
    omux_2nd_stage = omuxElem.find("./multistage_muxs/second_stage")

    for mux in omux_1st_stage.findall("mux"):
        gsb_1st_stage.append(mux)
    for mux in omux_2nd_stage.findall("mux"):
        gsb_1st_stage.append(mux)

    archtree.remove(omuxElem)

def prettify(elem):
    """
        Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8').decode("utf-8")
    rough_string = re.sub(">\s*<", "><", rough_string)
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="\t", encoding="utf-8")

#ouput the arch file
def writeArch(elem, outfile):
    f = open(outfile, "wb+")
    f.write(prettify(elem))
    f.close()

def remove_glb_cas(imuxElem, gsbElem):
    glb_stage = imuxElem.find("./multistage_muxs/glb_stage")
    cas_stage = gsbElem.find("./multistage_muxs/cas_stage")
    gsbElem.find("./multistage_muxs").remove(cas_stage)
    imuxElem.find("./multistage_muxs").remove(glb_stage)

def remove_glb_cas_in_mux(gsbElem):
    gsb_1st_stage = gsbElem.find("./multistage_muxs/first_stage")
    #gsb_2nd_stage = gsbElem.find("./multistage_muxs/second_stage")

    for mux in gsb_1st_stage.findall("mux"):
        for mux_from in mux.findall("from"):
            if mux_from.get("type") == "glb" or mux_from.get("type") == "cas":
                mux.remove(mux_from)

#remove the from description in the seg_group
def remove_from(gsbElem):
    gsbElem.set("arch_gsb_switch", "only_mux")
    for group_tag in gsbElem.findall("seg_group"):
        for from_tag in group_tag.findall("from"):
            group_tag.remove(from_tag)

def change_omux_pins(omuxElem, imuxElem, gsbElem):
    omux_1st_stage = omuxElem.find("./multistage_muxs/first_stage")
    omux_2nd_stage = omuxElem.find("./multistage_muxs/second_stage")

    imux_1st_stage = imuxElem.find("./multistage_muxs/first_stage")
    imux_2nd_stage = imuxElem.find("./multistage_muxs/second_stage")

    gsb_1st_stage = gsbElem.find("./multistage_muxs/first_stage")
    gsb_2nd_stage = gsbElem.find("./multistage_muxs/second_stage")

    for mux in omux_1st_stage.findall("mux"):
        for mux_from in mux.findall("from"):
            if mux_from.get("type") != None and mux_from.get("type") == "pb":
                name_list = mux_from.get("from_detail").split(":")
                if name_list[0] == "o":
                    name_list[0] = CLB_OPIN_NAME
                    mux_from.set("from_detail", ":".join(name_list))
                elif name_list[0] == "q":
                    name_list[0] = CLB_OPIN_NAME
                    name_list[1] = str(int(name_list[1]) + 8)
                    mux_from.set("from_detail", ":".join(name_list))
                elif name_list[0] == "mux_o":
                    name_list[0] = CLB_OPIN_NAME
                    name_list[1] = str(int(name_list[1]) + 16)
                    mux_from.set("from_detail", ":".join(name_list))
                else:
                    print("Wrong opin for pb")

    for mux in omux_2nd_stage.findall("mux"):
        for mux_from in mux.findall("from"):
            if mux_from.get("type") != None and mux_from.get("type") == "pb":
                name_list = mux_from.get("from_detail").split(":")
                if name_list[0] == "o":
                    name_list[0] = CLB_OPIN_NAME
                    mux_from.set("from_detail", ":".join(name_list))
                elif name_list[0] == "q":
                    name_list[0] = CLB_OPIN_NAME
                    name_list[1] = str(int(name_list[1]) + 8)
                    mux_from.set("from_detail", ":".join(name_list))
                elif name_list[0] == "mux_o":
                    name_list[0] = CLB_OPIN_NAME
                    name_list[1] = str(int(name_list[1]) + 16)
                    mux_from.set("from_detail", ":".join(name_list))
                else:
                    print("Wrong opin for pb")

    for mux in imux_1st_stage.findall("mux"):
        for mux_from in mux.findall("from"):
            if mux_from.get("type") != None and mux_from.get("type") == "pb":
                name_list = mux_from.get("from_detail").split(":")
                if name_list[0] == "o":
                    name_list[0] = CLB_OPIN_NAME
                    mux_from.set("from_detail", ":".join(name_list))
                elif name_list[0] == "q":
                    name_list[0] = CLB_OPIN_NAME
                    name_list[1] = str(int(name_list[1]) + 8)
                    mux_from.set("from_detail", ":".join(name_list))
                elif name_list[0] == "mux_o":
                    name_list[0] = CLB_OPIN_NAME
                    name_list[1] = str(int(name_list[1]) + 16)
                    mux_from.set("from_detail", ":".join(name_list))
                else:
                    print("Wrong opin for pb")

    for mux in imux_2nd_stage.findall("mux"):
        for mux_from in mux.findall("from"):
            if mux_from.get("type") != None and mux_from.get("type") == "pb":
                name_list = mux_from.get("from_detail").split(":")
                if name_list[0] == "o":
                    name_list[0] = CLB_OPIN_NAME
                    mux_from.set("from_detail", ":".join(name_list))
                elif name_list[0] == "q":
                    name_list[0] = CLB_OPIN_NAME
                    name_list[1] = str(int(name_list[1]) + 8)
                    mux_from.set("from_detail", ":".join(name_list))
                elif name_list[0] == "mux_o":
                    name_list[0] = CLB_OPIN_NAME
                    name_list[1] = str(int(name_list[1]) + 16)
                    mux_from.set("from_detail", ":".join(name_list))
                else:
                    print("Wrong opin for pb")   

    for mux in gsb_1st_stage.findall("mux"):
        for mux_from in mux.findall("from"):
            if mux_from.get("type") != None and mux_from.get("type") == "pb":
                name_list = mux_from.get("from_detail").split(":")
                if name_list[0] == "o":
                    name_list[0] = CLB_OPIN_NAME
                    mux_from.set("from_detail", ":".join(name_list))
                elif name_list[0] == "q":
                    name_list[0] = CLB_OPIN_NAME
                    name_list[1] = str(int(name_list[1]) + 8)
                    mux_from.set("from_detail", ":".join(name_list))
                elif name_list[0] == "mux_o":
                    name_list[0] = CLB_OPIN_NAME
                    name_list[1] = str(int(name_list[1]) + 16)
                    mux_from.set("from_detail", ":".join(name_list))
                else:
                    print("Wrong opin for pb")

    for mux in gsb_2nd_stage.findall("mux"):
        for mux_from in mux.findall("from"):
            if mux_from.get("type") != None and mux_from.get("type") == "pb":
                name_list = mux_from.get("from_detail").split(":")
                if name_list[0] == "o":
                    name_list[0] = CLB_OPIN_NAME
                    mux_from.set("from_detail", ":".join(name_list))
                elif name_list[0] == "q":
                    name_list[0] = CLB_OPIN_NAME
                    name_list[1] = str(int(name_list[1]) + 8)
                    mux_from.set("from_detail", ":".join(name_list))
                elif name_list[0] == "mux_o":
                    name_list[0] = CLB_OPIN_NAME
                    name_list[1] = str(int(name_list[1]) + 16)
                    mux_from.set("from_detail", ":".join(name_list))
                else:
                    print("Wrong opin for pb")

def rewrite_imux_2nd_stage(imuxElem):
    imux_1st_stage = imuxElem.find("./multistage_muxs/first_stage")
    imux_2nd_stage = imuxElem.find("./multistage_muxs/second_stage")

    first_stage_mux_name = []
    
    for mux in imux_1st_stage.findall("mux"):
        first_stage_mux_name.append(mux.get("name"))
    
    second_stage_mux_from_seg = []
    for mux in imux_2nd_stage.findall("mux"):
        for mux_from in mux.findall("from"):
            if mux_from.get("type"):
                second_stage_mux_from_seg.append(mux_from)
        imux_2nd_stage.remove(mux)

    group_num = CLB_IPIN_NUM_PER_PORT
    num_each_group = int(len(first_stage_mux_name) / group_num)
    sub_group_num = CLB_IPIN_NAME

    count = 0
    for iiport in range(0, len(CLB_IPIN_NAME)):
        iport = CLB_IPIN_NAME[iiport]
        for ipin in range(0, 5):
            mux_name = "b" + str(ipin) + "-" + iport
            to_pin = iport + ":" + str(ipin)
            from_mux = []
            for ifrom in range(num_each_group * ipin, num_each_group * ipin + num_each_group):                
                from_mux.append(first_stage_mux_name[ifrom])
            index = CLB_IPIN_NAME.index(iport)
            from_mux.pop(index)

            new_mux = ET.SubElement(imux_2nd_stage, "mux")            

            new_mux.set("name", mux_name)
            new_mux.set("to_pin", to_pin)

            mux_from_new = ET.SubElement(new_mux, "from")

            mux_from_new.set("mux_name", " ".join(from_mux))
            #new_mux.append(mux_from_new)
            if count < len(second_stage_mux_from_seg):
                new_mux.append(second_stage_mux_from_seg[count])

            #imux_2nd_stage.append(new_mux)
            count = count + 1

    extra_1st_mux_num = len(first_stage_mux_name) % group_num

    c = 0
    for mux_in_1st_stage in imux_1st_stage.findall("mux"):
        if c >= len(first_stage_mux_name) - extra_1st_mux_num:
            imux_1st_stage.remove(mux_in_1st_stage)
        c = c + 1
    

def modify_rules(gsbElem):
    gsbElem.tag = "vib"
    gsbElem.set("name", "vib0")
    gsbElem.set("pbtype_name", "clb")
    seg_group = gsbElem.get("gsb_seg_group")
    gsbElem.set("vib_seg_group", seg_group)
    arch_switch = gsbElem.get("arch_gsb_switch")
    gsbElem.set("arch_vib_switch", arch_switch)
    gsbElem.attrib.pop("gsb_seg_group")
    gsbElem.attrib.pop("arch_gsb_switch")

    gsb_1st_stage = gsbElem.find("./multistage_muxs/first_stage")
    gsb_2nd_stage = gsbElem.find("./multistage_muxs/second_stage")

    # Modify first stage
    for mux in gsb_1st_stage.findall("mux"):
        mux_from = []
        for i_mux_from in mux.findall("from"):
            mux_from.append(i_mux_from)
            mux.remove(i_mux_from)

        froms = []
        for i_from in mux_from:
            if i_from.get("type") != None:
                if i_from.get("type") == "pb":
                    i_name = i_from.get("name")
                    i_from_detail = i_from.get("from_detail").split(" ")
                    i_port_pin = []
                    for ii_from_detail in i_from_detail:
                        if ii_from_detail != "":
                            i_port_pin = ii_from_detail.split(":")
                            froms.append(i_name + "." + i_port_pin[0] + "[" + i_port_pin[1] + "]")

                elif i_from.get("type") == "seg":
                    i_name = i_from.get("name")
                    i_from_detail = i_from.get("from_detail").split(" ")
                    
                    for ii_from_detail in i_from_detail:
                        if ii_from_detail != "":
                            froms.append(i_name + "." + ii_from_detail)

                elif i_from.get("type") == "omux":
                    i_from_detail = i_from.get("from_detail").split(" ")
                    for ii_from_detail in i_from_detail:
                        if ii_from_detail != "":
                            froms.append(ii_from_detail)
                else:
                    print("Wrong from type")
            else:
                if i_from.get("mux_name") != None:
                    name_list = i_from.get("mux_name").split(" ")
                    for i_name_list in name_list:
                        if i_name_list != "":
                            froms.append(i_name_list)
                   
                else:
                    print("Wrong from type!\n")
        new_from = ET.SubElement(mux, "from")
        new_from_str = ""
        for i_froms in froms:
            new_from_str = new_from_str + str(i_froms) + str(" ")
        new_from_str = new_from_str[:-1]
        new_from.text = new_from_str

    # Modify second stage
    for mux in gsb_2nd_stage.findall("mux"):
        mux_from = []
        for i_mux_from in mux.findall("from"):
            mux_from.append(i_mux_from)
            mux.remove(i_mux_from)

        # Process to_pin/to_seg
        new_to = ET.SubElement(mux, "to")
        if mux.get("to_seg_name") != None:
            to_seg_name = mux.get("to_seg_name")
            to_track = mux.get("to_track")
            new_to.text = to_seg_name + "." + to_track
            mux.attrib.pop("to_seg_name")
            mux.attrib.pop("to_track")
        elif mux.get("to_pin") != None:
            to_pin = mux.get("to_pin").split(":")
            new_to.text = "clb" + "."+ to_pin[0] + "[" + to_pin[1] + "]"
            mux.attrib.pop("to_pin")
        else:
            print("Wrong to type!\n")

        # Process from tag
        froms = []
        for i_from in mux_from:
            if i_from.get("type") != None:
                if i_from.get("type") == "pb":
                    i_name = i_from.get("name")
                    i_from_detail = i_from.get("from_detail").split(" ")
                    i_port_pin = []
                    for ii_from_detail in i_from_detail:
                        if ii_from_detail != "":
                            i_port_pin = ii_from_detail.split(":")
                            froms.append(i_name + "." + i_port_pin[0] + "[" + i_port_pin[1] + "]")

                elif i_from.get("type") == "seg":
                    i_name = i_from.get("name")
                    i_from_detail = i_from.get("from_detail").split(" ")
                    
                    for ii_from_detail in i_from_detail:
                        if ii_from_detail != "":
                            froms.append(i_name + "." + ii_from_detail)

                elif i_from.get("type") == "omux":
                    i_from_detail = i_from.get("from_detail").split(" ")
                    for ii_from_detail in i_from_detail:
                        if ii_from_detail != "":
                            froms.append(ii_from_detail)
                else:
                    print("Wrong from type")
            else:
                if i_from.get("mux_name") != None:
                    name_list = i_from.get("mux_name").split(" ")
                    for i_name_list in name_list:
                        if i_name_list != "":
                            froms.append(i_name_list)
                   
                else:
                    print("Wrong from type")
        new_from = ET.SubElement(mux, "from")
        new_from_str = ""
        for i_froms in froms:
            new_from_str = new_from_str + str(i_froms) + str(" ")
        new_from_str = new_from_str[:-1]
        new_from.text = new_from_str

def modify_seg(gsbElem):
    for i_seg_group in gsbElem.findall("seg_group"):
        i_name = i_seg_group.get("name")
        i_name = i_name[1:]
        i_track_nums = i_seg_group.get("track_nums")
        i_seg_group.set("track_nums", str(int(i_name) * int(i_track_nums)))

    gsb_1st_stage = gsbElem.find("./multistage_muxs/first_stage")
    gsb_2nd_stage = gsbElem.find("./multistage_muxs/second_stage")

    # Modify first stage
    for mux in gsb_1st_stage.findall("mux"):
        mux_from = []
        for i_mux_from in mux.findall("from"):
            mux_from.append(i_mux_from)
            
        for i_from in mux_from:
            if i_from.get("type") != None:
                
                if i_from.get("type") == "seg":
                    i_name = i_from.get("name")
                    i_name = i_name[1:]
                    i_from_detail = i_from.get("from_detail").split(" ")
                    
                    from_details = ""
                    for ii_from_detail in i_from_detail:
                        if ii_from_detail != "":
                            seg_dir = ii_from_detail[0]
                            seg_index = ii_from_detail[1:]
                            new_index = int(seg_index) * int(i_name) + int(i_name) - int(1)
                            from_details = from_details + seg_dir + str(new_index) + " "
                    
                    from_details = from_details[:-1]
                    i_from.set("from_detail", from_details)

    # Modify second stage
    for mux in gsb_2nd_stage.findall("mux"):
        to_seg_name = mux.get("to_seg_name")
        
        if to_seg_name != None:
            seg_length = to_seg_name[1:]
            to_track = mux.get("to_track")
            seg_dir = to_track[0]
            seg_index = to_track[1:]
            new_index = int(seg_index) * int(seg_length)
            mux.set("to_track", seg_dir + str(new_index))

        mux_from = []
        for i_mux_from in mux.findall("from"):
            mux_from.append(i_mux_from)
            
        for i_from in mux_from:
            if i_from.get("type") != None:
                
                if i_from.get("type") == "seg":
                    i_name = i_from.get("name")
                    i_name = i_name[1:]
                    i_from_detail = i_from.get("from_detail").split(" ")
                    
                    from_details = ""
                    for ii_from_detail in i_from_detail:
                        if ii_from_detail != "":
                            seg_dir = ii_from_detail[0]
                            seg_index = ii_from_detail[1:]
                            new_index = int(seg_index) * int(i_name) + int(i_name) - int(1)
                            from_details = from_details + seg_dir + str(new_index) + " "
                    
                    from_details = from_details[:-1]
                    i_from.set("from_detail", from_details)

def add_left_io_vib(arch_gsb):
    new_vib = ET.SubElement(arch_gsb, "vib")
    vib = arch_gsb.find("vib")
    new_vib.set("name", "vib1")
    new_vib.set("pbtype_name", "io_leftL")
    new_vib.set("vib_seg_group", vib.get("vib_seg_group"))
    new_vib.set("arch_vib_switch", vib.get("arch_vib_switch"))

    for i_seg_group in vib.findall("seg_group"):
        new_seg_group = ET.SubElement(new_vib, "seg_group")
        new_seg_group.set("name", i_seg_group.get("name"))
        new_seg_group.set("track_nums", i_seg_group.get("track_nums"))

    new_multistage_muxs = ET.SubElement(new_vib, "multistage_muxs")
    new_first_stage = ET.SubElement(new_multistage_muxs, "first_stage")
    new_second_stage = ET.SubElement(new_multistage_muxs, "second_stage")

    first_stage = vib.find("./multistage_muxs/first_stage")
    second_stage = vib.find("./multistage_muxs/second_stage")

    # Process first stage
    new_first_stage.set("switch_name", first_stage.get("switch_name"))
    empty_1st_stage_mux = []
    for mux in first_stage.findall("mux"):
        new_mux = ET.SubElement(new_first_stage, "mux")
        new_mux.set("name", mux.get("name"))
        for i_from in mux.findall("from"):
            new_from = ET.SubElement(new_mux, "from")
            i_froms = i_from.text.split(" ")

            new_from_str = ""
            for ii_from in i_froms:
                if ii_from[0:3] == "clb":
                    from_clb_text = ii_from.split(".O[")
                    from_clb_index = from_clb_text[1]
                    from_clb_index = from_clb_index[:-1]
                    index = int(from_clb_index)
                    new_index = index % IO_LEFTL_OUTPUT_NUM
                    ii_from = IO_LEFTL_OUTPUT_NAME + "[" + str(new_index) + "]"
                if len(ii_from.split(".")) > 1:
                    dir_index = ii_from.split(".")[1]
                    dir = dir_index[0]
                    if dir == "E":
                        ii_from = ""
                if ii_from != "":
                    new_from_str = new_from_str + ii_from + str(" ")
            new_from_str = new_from_str[:-1]
            new_from.text = new_from_str
        if new_mux.find("from").text == "":
            empty_1st_stage_mux.append(new_mux.get("name"))
            new_first_stage.remove(new_mux)
            
    # Process second stage
    #new_second_stage.set("switch_name", first_stage.get("switch_name"))
    for mux in second_stage.findall("mux"):
        new_mux = ET.SubElement(new_second_stage, "mux")
        new_mux.set("name", mux.get("name"))

        new_to = ET.SubElement(new_mux, "to")
        mux_to = mux.find("to").text
        new_to_text = mux_to
        if mux_to[0:3] == "clb":
            mux_to_token = mux_to.split(".")[1]
            mux_to_port = mux_to_token.split("[")[0]
            mux_to_pin = mux_to_token[-2]
            abso_pin_index = 0
            for i_port in range(len(CLB_IPIN_NAME)):
                if CLB_IPIN_NAME[i_port] == mux_to_port:
                    abso_pin_index = int(mux_to_pin) + i_port * CLB_IPIN_NUM_PER_PORT
            
            new_index = abso_pin_index % IO_LEFTL_INPUT_NUM
            new_to_text = IO_LEFTL_INPUT_NAME + "[" + str(new_index) + "]"
        new_to.text = new_to_text


        for i_from in mux.findall("from"):
            new_from = ET.SubElement(new_mux, "from")
            i_froms = i_from.text.split(" ")

            new_from_str = ""
            for ii_from in i_froms:
                if ii_from[0:3] == "clb":
                    from_clb_text = ii_from.split(".O[")
                    from_clb_index = from_clb_text[1]
                    from_clb_index = from_clb_index[:-1]
                    index = int(from_clb_index)
                    new_index = index % IO_LEFTL_OUTPUT_NUM
                    ii_from = IO_LEFTL_OUTPUT_NAME + "[" + str(new_index) + "]"
                if len(ii_from.split(".")) > 1:
                    dir_index = ii_from.split(".")[1]
                    dir = dir_index[0]
                    if dir == "E":
                        ii_from = ""
                
                for i_1st_stage_mux in empty_1st_stage_mux:
                    if ii_from == i_1st_stage_mux:
                        ii_from = ""

                if ii_from != "":
                    new_from_str = new_from_str + ii_from + str(" ")
            new_from_str = new_from_str[:-1]
            new_from.text = new_from_str

        if new_mux.get("name")[0] == "W":
            new_second_stage.remove(new_mux)

    mux_count = 0
    for mux in new_second_stage.findall("mux"):
        mux_name = mux.get("name")
        mux_to = mux.find("to").text.split(".")
        total_num = IO_LEFTL_OUTPUT_NUM + IO_LEFTL_INPUT_NUM
        if mux_to[0] == "io_leftL":
            count = mux_count
            for i_index in range(count, total_num, IO_LEFTL_INPUT_NUM):
                # for lclk
                new_mux = ET.SubElement(new_second_stage, "mux")
                new_mux.set("name", mux_name)
                new_mux_to = ET.SubElement(new_mux, "to")
                new_mux_to.text = IO_LEFTL_INPUT_NAME_LCLK + "[" + str(i_index) + "]"

                for i_from in mux.findall("from"):
                    new_mux_from = ET.SubElement(new_mux, "from")
                    new_mux_from.text = i_from.text

                # for lreset
                new_mux = ET.SubElement(new_second_stage, "mux")
                new_mux.set("name", mux_name)
                new_mux_to = ET.SubElement(new_mux, "to")
                new_mux_to.text = IO_LEFTL_INPUT_NAME_LRESET + "[" + str(i_index) + "]"

                for i_from in mux.findall("from"):
                    new_mux_from = ET.SubElement(new_mux, "from")
                    new_mux_from.text = i_from.text
            mux_count += 1





def add_right_io_vib(arch_gsb):
    new_vib = ET.SubElement(arch_gsb, "vib")
    vib = arch_gsb.find("vib")
    new_vib.set("name", "vib2")
    new_vib.set("pbtype_name", "io_rightL")
    new_vib.set("vib_seg_group", vib.get("vib_seg_group"))
    new_vib.set("arch_vib_switch", vib.get("arch_vib_switch"))

    for i_seg_group in vib.findall("seg_group"):
        new_seg_group = ET.SubElement(new_vib, "seg_group")
        new_seg_group.set("name", i_seg_group.get("name"))
        new_seg_group.set("track_nums", i_seg_group.get("track_nums"))

    new_multistage_muxs = ET.SubElement(new_vib, "multistage_muxs")
    new_first_stage = ET.SubElement(new_multistage_muxs, "first_stage")
    new_second_stage = ET.SubElement(new_multistage_muxs, "second_stage")

    first_stage = vib.find("./multistage_muxs/first_stage")
    second_stage = vib.find("./multistage_muxs/second_stage")

    # Process first stage
    new_first_stage.set("switch_name", first_stage.get("switch_name"))
    empty_1st_stage_mux = []
    for mux in first_stage.findall("mux"):
        new_mux = ET.SubElement(new_first_stage, "mux")
        new_mux.set("name", mux.get("name"))
        for i_from in mux.findall("from"):
            new_from = ET.SubElement(new_mux, "from")
            i_froms = i_from.text.split(" ")

            new_from_str = ""
            for ii_from in i_froms:
                if ii_from[0:3] == "clb":
                    from_clb_text = ii_from.split(".O[")
                    from_clb_index = from_clb_text[1]
                    from_clb_index = from_clb_index[:-1]
                    index = int(from_clb_index)
                    new_index = index % IO_RIGHTL_OUTPUT_NUM
                    ii_from = IO_RIGHTL_OUTPUT_NAME + "[" + str(new_index) + "]"
                if len(ii_from.split(".")) > 1:
                    dir_index = ii_from.split(".")[1]
                    dir = dir_index[0]
                    if dir == "W":
                        ii_from = ""
                if ii_from != "":
                    new_from_str = new_from_str + ii_from + str(" ")
                
            new_from_str = new_from_str[:-1]
            new_from.text = new_from_str
        if new_mux.find("from").text == "":
            empty_1st_stage_mux.append(new_mux.get("name"))
            new_first_stage.remove(new_mux)
            
    # Process second stage
    #new_second_stage.set("switch_name", first_stage.get("switch_name"))
    for mux in second_stage.findall("mux"):
        new_mux = ET.SubElement(new_second_stage, "mux")
        new_mux.set("name", mux.get("name"))

        new_to = ET.SubElement(new_mux, "to")
        mux_to = mux.find("to").text
        new_to_text = mux_to
        if mux_to[0:3] == "clb":
            mux_to_token = mux_to.split(".")[1]
            mux_to_port = mux_to_token.split("[")[0]
            mux_to_pin = mux_to_token[-2]
            abso_pin_index = 0
            for i_port in range(len(CLB_IPIN_NAME)):
                if CLB_IPIN_NAME[i_port] == mux_to_port:
                    abso_pin_index = int(mux_to_pin) + i_port * CLB_IPIN_NUM_PER_PORT
            
            new_index = abso_pin_index % IO_RIGHTL_INPUT_NUM
            new_to_text = IO_RIGHTL_INPUT_NAME + "[" + str(new_index) + "]"
        new_to.text = new_to_text

        for i_from in mux.findall("from"):
            new_from = ET.SubElement(new_mux, "from")
            i_froms = i_from.text.split(" ")

            new_from_str = ""
            for ii_from in i_froms:
                if ii_from[0:3] == "clb":
                    from_clb_text = ii_from.split(".O[")
                    from_clb_index = from_clb_text[1]
                    from_clb_index = from_clb_index[:-1]
                    index = int(from_clb_index)
                    new_index = index % IO_RIGHTL_OUTPUT_NUM
                    ii_from = IO_RIGHTL_OUTPUT_NAME + "[" + str(new_index) + "]"
                if len(ii_from.split(".")) > 1:
                    dir_index = ii_from.split(".")[1]
                    dir = dir_index[0]
                    if dir == "W":
                        ii_from = ""
                
                for i_1st_stage_mux in empty_1st_stage_mux:
                    if ii_from == i_1st_stage_mux:
                        ii_from = ""

                if ii_from != "":
                    new_from_str = new_from_str + ii_from + str(" ")
                
            new_from_str = new_from_str[:-1]
            new_from.text = new_from_str

        if new_mux.get("name")[0] == "E":
            new_second_stage.remove(new_mux)

        if new_to.text[0] == "l":
            new_str = ""
            froms = new_mux.find("from").text
            for i_from in froms.split(" "):
                if i_from[0] == "l":
                    new_str = new_str
                else:
                    new_str = new_str + i_from + str(" ")
            new_str = new_str[:-1]
            new_mux.find("from").text = new_str

    mux_count = 0
    for mux in new_second_stage.findall("mux"):
        mux_name = mux.get("name")
        mux_to = mux.find("to").text.split(".")
        total_num = IO_RIGHTL_OUTPUT_NUM + IO_RIGHTL_INPUT_NUM
        if mux_to[0] == "io_rightL":
            count = mux_count
            for i_index in range(count, total_num, IO_RIGHTL_INPUT_NUM):
                # for lclk
                new_mux = ET.SubElement(new_second_stage, "mux")
                new_mux.set("name", mux_name)
                new_mux_to = ET.SubElement(new_mux, "to")
                new_mux_to.text = IO_RIGHTL_INPUT_NAME_LCLK + "[" + str(i_index) + "]"

                for i_from in mux.findall("from"):
                    new_mux_from = ET.SubElement(new_mux, "from")
                    new_mux_from.text = i_from.text

                # for lreset
                new_mux = ET.SubElement(new_second_stage, "mux")
                new_mux.set("name", mux_name)
                new_mux_to = ET.SubElement(new_mux, "to")
                new_mux_to.text = IO_RIGHTL_INPUT_NAME_LRESET + "[" + str(i_index) + "]"

                for i_from in mux.findall("from"):
                    new_mux_from = ET.SubElement(new_mux, "from")
                    new_mux_from.text = i_from.text
            mux_count += 1

def add_top_io_vib(arch_gsb):
    new_vib = ET.SubElement(arch_gsb, "vib")
    vib = arch_gsb.find("vib")
    new_vib.set("name", "vib3")
    new_vib.set("pbtype_name", "io_topL")
    new_vib.set("vib_seg_group", vib.get("vib_seg_group"))
    new_vib.set("arch_vib_switch", vib.get("arch_vib_switch"))

    new_vib_ = ET.SubElement(arch_gsb, "vib")
    new_vib_.set("name", "vib10")
    new_vib_.set("pbtype_name", "io_top_dspL")
    new_vib_.set("vib_seg_group", vib.get("vib_seg_group"))
    new_vib_.set("arch_vib_switch", vib.get("arch_vib_switch"))

    new_vib__ = ET.SubElement(arch_gsb, "vib")
    new_vib__.set("name", "vib11")
    new_vib__.set("pbtype_name", "io_top_ramL")
    new_vib__.set("vib_seg_group", vib.get("vib_seg_group"))
    new_vib__.set("arch_vib_switch", vib.get("arch_vib_switch"))

    for i_seg_group in vib.findall("seg_group"):
        new_seg_group = ET.SubElement(new_vib, "seg_group")
        new_seg_group.set("name", i_seg_group.get("name"))
        new_seg_group.set("track_nums", i_seg_group.get("track_nums"))

        new_seg_group_ = ET.SubElement(new_vib_, "seg_group")
        new_seg_group_.set("name", i_seg_group.get("name"))
        new_seg_group_.set("track_nums", i_seg_group.get("track_nums"))

        new_seg_group__ = ET.SubElement(new_vib__, "seg_group")
        new_seg_group__.set("name", i_seg_group.get("name"))
        new_seg_group__.set("track_nums", i_seg_group.get("track_nums"))

    new_multistage_muxs = ET.SubElement(new_vib, "multistage_muxs")
    new_first_stage = ET.SubElement(new_multistage_muxs, "first_stage")
    new_second_stage = ET.SubElement(new_multistage_muxs, "second_stage")

    new_multistage_muxs_ = ET.SubElement(new_vib_, "multistage_muxs")
    new_first_stage_ = ET.SubElement(new_multistage_muxs_, "first_stage")
    new_second_stage_ = ET.SubElement(new_multistage_muxs_, "second_stage")

    new_multistage_muxs__ = ET.SubElement(new_vib__, "multistage_muxs")
    new_first_stage__ = ET.SubElement(new_multistage_muxs__, "first_stage")
    new_second_stage__ = ET.SubElement(new_multistage_muxs__, "second_stage")

    first_stage = vib.find("./multistage_muxs/first_stage")
    second_stage = vib.find("./multistage_muxs/second_stage")

    # Process first stage
    new_first_stage.set("switch_name", first_stage.get("switch_name"))
    new_first_stage_.set("switch_name", first_stage.get("switch_name"))
    new_first_stage__.set("switch_name", first_stage.get("switch_name"))
    empty_1st_stage_mux = []
    empty_1st_stage_mux_ = []
    empty_1st_stage_mux__ = []
    for mux in first_stage.findall("mux"):
        new_mux = ET.SubElement(new_first_stage, "mux")
        new_mux.set("name", mux.get("name"))
        new_mux_ = ET.SubElement(new_first_stage_, "mux")
        new_mux_.set("name", mux.get("name"))
        new_mux__ = ET.SubElement(new_first_stage__, "mux")
        new_mux__.set("name", mux.get("name"))
        for i_from in mux.findall("from"):
            new_from = ET.SubElement(new_mux, "from")
            new_from_ = ET.SubElement(new_mux_, "from")
            new_from__ = ET.SubElement(new_mux__, "from")
            i_froms = i_from.text.split(" ")

            new_from_str = ""
            new_from_str_ = ""
            new_from_str__ = ""
            for ii_from in i_froms:
                ii_from_ = ii_from
                ii_from__ = ii_from
                if ii_from[0:3] == "clb":
                    from_clb_text = ii_from.split(".O[")
                    from_clb_index = from_clb_text[1]
                    from_clb_index = from_clb_index[:-1]
                    index = int(from_clb_index)
                    new_index = index % IO_TOPL_OUTPUT_NUM
                    ii_from = IO_TOPL_OUTPUT_NAME + "[" + str(new_index) + "]"
                    ii_from_ = IO_TOP_DSPL_OUTPUT_NAME + "[" + str(new_index) + "]"
                    ii_from__ = IO_TOP_RAML_OUTPUT_NAME + "[" + str(new_index) + "]"
                if len(ii_from.split(".")) > 1:
                    dir_index = ii_from.split(".")[1]
                    dir = dir_index[0]
                    if dir == "S":
                        ii_from = ""
                        ii_from_ = ""
                        ii_from__ = ""
                if ii_from != "":
                    new_from_str = new_from_str + ii_from + str(" ")
                if ii_from_ != "":
                    new_from_str_ = new_from_str_ + ii_from_ + str(" ")
                if ii_from__ != "":
                    new_from_str__ = new_from_str__ + ii_from__ + str(" ")
                
            new_from_str = new_from_str[:-1]
            new_from_str_ = new_from_str_[:-1]
            new_from_str__ = new_from_str__[:-1]
            new_from.text = new_from_str
            new_from_.text = new_from_str_
            new_from__.text = new_from_str__
        if new_mux.find("from").text == "":
            empty_1st_stage_mux.append(new_mux.get("name"))
            new_first_stage.remove(new_mux)
        if new_mux_.find("from").text == "":
            empty_1st_stage_mux_.append(new_mux_.get("name"))
            new_first_stage_.remove(new_mux_)
        if new_mux__.find("from").text == "":
            empty_1st_stage_mux__.append(new_mux__.get("name"))
            new_first_stage__.remove(new_mux__)

            
    # Process second stage
    #new_second_stage.set("switch_name", first_stage.get("switch_name"))
    for mux in second_stage.findall("mux"):
        new_mux = ET.SubElement(new_second_stage, "mux")
        new_mux.set("name", mux.get("name"))
        new_mux_ = ET.SubElement(new_second_stage_, "mux")
        new_mux_.set("name", mux.get("name"))
        new_mux__ = ET.SubElement(new_second_stage__, "mux")
        new_mux__.set("name", mux.get("name"))

        new_to = ET.SubElement(new_mux, "to")
        new_to_ = ET.SubElement(new_mux_, "to")
        new_to__ = ET.SubElement(new_mux__, "to")
        mux_to = mux.find("to").text
        new_to_text = mux_to
        new_to_text_ = mux_to
        new_to_text__ = mux_to
        if mux_to[0:3] == "clb":
            mux_to_token = mux_to.split(".")[1]
            mux_to_port = mux_to_token.split("[")[0]
            mux_to_pin = mux_to_token[-2]
            abso_pin_index = 0
            for i_port in range(len(CLB_IPIN_NAME)):
                if CLB_IPIN_NAME[i_port] == mux_to_port:
                    abso_pin_index = int(mux_to_pin) + i_port * CLB_IPIN_NUM_PER_PORT
            
            new_index = abso_pin_index % IO_TOPL_INPUT_NUM
            new_to_text = IO_TOPL_INPUT_NAME + "[" + str(new_index) + "]"
            new_to_text_ = IO_TOP_DSPL_INPUT_NAME + "[" + str(new_index) + "]"
            new_to_text__ = IO_TOP_RAML_INPUT_NAME + "[" + str(new_index) + "]"
        new_to.text = new_to_text
        new_to_.text = new_to_text_
        new_to__.text = new_to_text__


        for i_from in mux.findall("from"):
            
            new_from = ET.SubElement(new_mux, "from")
            new_from_ = ET.SubElement(new_mux_, "from")
            new_from__ = ET.SubElement(new_mux__, "from")
            i_froms = i_from.text.split(" ")

            new_from_str = ""
            new_from_str_ = ""
            new_from_str__ = ""
            for ii_from in i_froms:
                ii_from_ = ii_from
                ii_from__ = ii_from
                if ii_from[0:3] == "clb":
                    from_clb_text = ii_from.split(".O[")
                    from_clb_index = from_clb_text[1]
                    from_clb_index = from_clb_index[:-1]
                    index = int(from_clb_index)
                    new_index = index % IO_TOPL_OUTPUT_NUM
                    ii_from = IO_TOPL_OUTPUT_NAME + "[" + str(new_index) + "]"
                    ii_from_ = IO_TOP_DSPL_OUTPUT_NAME + "[" + str(new_index) + "]"
                    ii_from__ = IO_TOP_RAML_OUTPUT_NAME + "[" + str(new_index) + "]"
                if len(ii_from.split(".")) > 1:
                    dir_index = ii_from.split(".")[1]
                    dir = dir_index[0]
                    if dir == "S":
                        ii_from = ""
                        ii_from_ = ""
                        ii_from__ = ""
                
                for i_1st_stage_mux in empty_1st_stage_mux:
                    if ii_from == i_1st_stage_mux:
                        ii_from = ""
                for i_1st_stage_mux_ in empty_1st_stage_mux_:
                    if ii_from_ == i_1st_stage_mux_:
                        ii_from_ = ""
                for i_1st_stage_mux__ in empty_1st_stage_mux__:
                    if ii_from__ == i_1st_stage_mux__:
                        ii_from__ = ""

                if ii_from != "":
                    new_from_str = new_from_str + ii_from + str(" ")
                if ii_from_ != "":
                    new_from_str_ = new_from_str_ + ii_from_ + str(" ")
                if ii_from__ != "":
                    new_from_str__ = new_from_str__ + ii_from__ + str(" ")
                
            new_from_str = new_from_str[:-1]
            new_from.text = new_from_str
            new_from_str_ = new_from_str_[:-1]
            new_from_.text = new_from_str_
            new_from_str__ = new_from_str__[:-1]
            new_from__.text = new_from_str__
        if new_mux.get("name")[0] == "N":
            new_second_stage.remove(new_mux)
        if new_mux_.get("name")[0] == "N":
            new_second_stage_.remove(new_mux_)
        if new_mux__.get("name")[0] == "N":
            new_second_stage__.remove(new_mux__)

        if new_to.text[0] == "l":
            new_str = ""
            froms = new_mux.find("from").text
            for i_from in froms.split(" "):
                if i_from[0] == "l":
                    new_str = new_str
                else:
                    new_str = new_str + i_from + str(" ")
            new_str = new_str[:-1]
            new_mux.find("from").text = new_str
        if new_to_.text[0] == "l":
            new_str_ = ""
            froms_ = new_mux_.find("from").text
            for i_from_ in froms_.split(" "):
                if i_from_[0] == "l":
                    new_str_ = new_str_
                else:
                    new_str_ = new_str_ + i_from_ + str(" ")
            new_str_ = new_str_[:-1]
            new_mux_.find("from").text = new_str_
        if new_to__.text[0] == "l":
            new_str__ = ""
            froms__ = new_mux__.find("from").text
            for i_from__ in froms__.split(" "):
                if i_from__[0] == "l":
                    new_str__ = new_str__
                else:
                    new_str__ = new_str__ + i_from__ + str(" ")
            new_str__ = new_str__[:-1]
            new_mux__.find("from").text = new_str__

    mux_count = 0
    for mux in new_second_stage.findall("mux"):
        mux_name = mux.get("name")
        mux_to = mux.find("to").text.split(".")
        total_num = IO_TOPL_OUTPUT_NUM + IO_TOPL_INPUT_NUM
        if mux_to[0] == "io_topL":
            count = mux_count
            for i_index in range(count, total_num, IO_TOPL_INPUT_NUM):
                # for lclk
                new_mux = ET.SubElement(new_second_stage, "mux")
                new_mux.set("name", mux_name)
                new_mux_to = ET.SubElement(new_mux, "to")
                new_mux_to.text = IO_TOPL_INPUT_NAME_LCLK + "[" + str(i_index) + "]"

                for i_from in mux.findall("from"):
                    new_mux_from = ET.SubElement(new_mux, "from")
                    new_mux_from.text = i_from.text

                # for lreset
                new_mux = ET.SubElement(new_second_stage, "mux")
                new_mux.set("name", mux_name)
                new_mux_to = ET.SubElement(new_mux, "to")
                new_mux_to.text = IO_TOPL_INPUT_NAME_LRESET + "[" + str(i_index) + "]"

                for i_from in mux.findall("from"):
                    new_mux_from = ET.SubElement(new_mux, "from")
                    new_mux_from.text = i_from.text
            mux_count += 1

    mux_count = 0
    for mux in new_second_stage_.findall("mux"):
        mux_name = mux.get("name")
        mux_to = mux.find("to").text.split(".")
        total_num = IO_TOPL_OUTPUT_NUM + IO_TOPL_INPUT_NUM
        if mux_to[0] == "io_top_dspL":
            count = mux_count
            for i_index in range(count, total_num, IO_TOPL_INPUT_NUM):
                # for lclk
                new_mux = ET.SubElement(new_second_stage_, "mux")
                new_mux.set("name", mux_name)
                new_mux_to = ET.SubElement(new_mux, "to")
                new_mux_to.text = IO_TOP_DSPL_INPUT_NAME_LCLK + "[" + str(i_index) + "]"

                for i_from in mux.findall("from"):
                    new_mux_from = ET.SubElement(new_mux, "from")
                    new_mux_from.text = i_from.text

                # for lreset
                new_mux = ET.SubElement(new_second_stage_, "mux")
                new_mux.set("name", mux_name)
                new_mux_to = ET.SubElement(new_mux, "to")
                new_mux_to.text = IO_TOP_DSPL_INPUT_NAME_LRESET + "[" + str(i_index) + "]"

                for i_from in mux.findall("from"):
                    new_mux_from = ET.SubElement(new_mux, "from")
                    new_mux_from.text = i_from.text
            mux_count += 1

    mux_count = 0
    for mux in new_second_stage__.findall("mux"):
        mux_name = mux.get("name")
        mux_to = mux.find("to").text.split(".")
        total_num = IO_TOPL_OUTPUT_NUM + IO_TOPL_INPUT_NUM
        if mux_to[0] == "io_top_ramL":
            count = mux_count
            for i_index in range(count, total_num, IO_TOPL_INPUT_NUM):
                # for lclk
                new_mux = ET.SubElement(new_second_stage__, "mux")
                new_mux.set("name", mux_name)
                new_mux_to = ET.SubElement(new_mux, "to")
                new_mux_to.text = IO_TOP_RAML_INPUT_NAME_LCLK + "[" + str(i_index) + "]"

                for i_from in mux.findall("from"):
                    new_mux_from = ET.SubElement(new_mux, "from")
                    new_mux_from.text = i_from.text

                # for lreset
                new_mux = ET.SubElement(new_second_stage__, "mux")
                new_mux.set("name", mux_name)
                new_mux_to = ET.SubElement(new_mux, "to")
                new_mux_to.text = IO_TOP_RAML_INPUT_NAME_LRESET + "[" + str(i_index) + "]"

                for i_from in mux.findall("from"):
                    new_mux_from = ET.SubElement(new_mux, "from")
                    new_mux_from.text = i_from.text
            mux_count += 1

def add_bottom_io_vib(arch_gsb):
    new_vib = ET.SubElement(arch_gsb, "vib")
    vib = arch_gsb.find("vib")
    new_vib.set("name", "vib4")
    new_vib.set("pbtype_name", "io_bottomL")
    new_vib.set("vib_seg_group", vib.get("vib_seg_group"))
    new_vib.set("arch_vib_switch", vib.get("arch_vib_switch"))

    new_vib_ = ET.SubElement(arch_gsb, "vib")
    new_vib_.set("name", "vib12")
    new_vib_.set("pbtype_name", "io_bottom_dspL")
    new_vib_.set("vib_seg_group", vib.get("vib_seg_group"))
    new_vib_.set("arch_vib_switch", vib.get("arch_vib_switch"))
    new_vib__ = ET.SubElement(arch_gsb, "vib")
    new_vib__.set("name", "vib13")
    new_vib__.set("pbtype_name", "io_bottom_ramL")
    new_vib__.set("vib_seg_group", vib.get("vib_seg_group"))
    new_vib__.set("arch_vib_switch", vib.get("arch_vib_switch"))

    for i_seg_group in vib.findall("seg_group"):
        new_seg_group = ET.SubElement(new_vib, "seg_group")
        new_seg_group.set("name", i_seg_group.get("name"))
        new_seg_group.set("track_nums", i_seg_group.get("track_nums"))

        new_seg_group_ = ET.SubElement(new_vib_, "seg_group")
        new_seg_group_.set("name", i_seg_group.get("name"))
        new_seg_group_.set("track_nums", i_seg_group.get("track_nums"))

        new_seg_group__ = ET.SubElement(new_vib__, "seg_group")
        new_seg_group__.set("name", i_seg_group.get("name"))
        new_seg_group__.set("track_nums", i_seg_group.get("track_nums"))

    new_multistage_muxs = ET.SubElement(new_vib, "multistage_muxs")
    new_multistage_muxs_ = ET.SubElement(new_vib_, "multistage_muxs")
    new_multistage_muxs__ = ET.SubElement(new_vib__, "multistage_muxs")
    new_first_stage = ET.SubElement(new_multistage_muxs, "first_stage")
    new_second_stage = ET.SubElement(new_multistage_muxs, "second_stage")
    new_first_stage_ = ET.SubElement(new_multistage_muxs_, "first_stage")
    new_second_stage_ = ET.SubElement(new_multistage_muxs_, "second_stage")
    new_first_stage__ = ET.SubElement(new_multistage_muxs__, "first_stage")
    new_second_stage__ = ET.SubElement(new_multistage_muxs__, "second_stage")

    first_stage = vib.find("./multistage_muxs/first_stage")
    second_stage = vib.find("./multistage_muxs/second_stage")

    # Process first stage
    new_first_stage.set("switch_name", first_stage.get("switch_name"))
    new_first_stage_.set("switch_name", first_stage.get("switch_name"))
    new_first_stage__.set("switch_name", first_stage.get("switch_name"))
    empty_1st_stage_mux = []
    empty_1st_stage_mux_ = []
    empty_1st_stage_mux__ = []
    for mux in first_stage.findall("mux"):
        new_mux = ET.SubElement(new_first_stage, "mux")
        new_mux.set("name", mux.get("name"))
        new_mux_ = ET.SubElement(new_first_stage_, "mux")
        new_mux_.set("name", mux.get("name"))
        new_mux__ = ET.SubElement(new_first_stage__, "mux")
        new_mux__.set("name", mux.get("name"))
        for i_from in mux.findall("from"):
            new_from = ET.SubElement(new_mux, "from")
            new_from_ = ET.SubElement(new_mux_, "from")
            new_from__ = ET.SubElement(new_mux__, "from")
            i_froms = i_from.text.split(" ")

            new_from_str = ""
            new_from_str_ = ""
            new_from_str__ = ""
            for ii_from in i_froms:
                ii_from_ = ii_from
                ii_from__ = ii_from
                if ii_from[0:3] == "clb":
                    from_clb_text = ii_from.split(".O[")
                    from_clb_index = from_clb_text[1]
                    from_clb_index = from_clb_index[:-1]
                    index = int(from_clb_index)
                    new_index = index % IO_BOTTOML_OUTPUT_NUM
                    ii_from = IO_BOTTOML_OUTPUT_NAME + "[" + str(new_index) + "]"
                    ii_from_ = IO_BOTTOM_DSPL_OUTPUT_NAME + "[" + str(new_index) + "]"
                    ii_from__ = IO_BOTTOM_RAML_OUTPUT_NAME + "[" + str(new_index) + "]"
                if len(ii_from.split(".")) > 1:
                    dir_index = ii_from.split(".")[1]
                    dir = dir_index[0]
                    if dir == "N":
                        ii_from = ""
                        ii_from_ = ""
                        ii_from__ = ""
                if ii_from != "":
                    new_from_str = new_from_str + ii_from + str(" ")
                if ii_from_ != "":
                    new_from_str_ = new_from_str_ + ii_from_ + str(" ")
                if ii_from__ != "":
                    new_from_str__ = new_from_str__ + ii_from__ + str(" ")
                
            new_from_str = new_from_str[:-1]
            new_from.text = new_from_str
            new_from_str_ = new_from_str_[:-1]
            new_from_.text = new_from_str_
            new_from_str__ = new_from_str__[:-1]
            new_from__.text = new_from_str__
        if new_mux.find("from").text == "":
            empty_1st_stage_mux.append(new_mux.get("name"))
            new_first_stage.remove(new_mux)
        if new_mux_.find("from").text == "":
            empty_1st_stage_mux_.append(new_mux_.get("name"))
            new_first_stage_.remove(new_mux_)
        if new_mux__.find("from").text == "":
            empty_1st_stage_mux__.append(new_mux__.get("name"))
            new_first_stage__.remove(new_mux__)

            
    # Process second stage
    #new_second_stage.set("switch_name", first_stage.get("switch_name"))
    for mux in second_stage.findall("mux"):
        new_mux = ET.SubElement(new_second_stage, "mux")
        new_mux.set("name", mux.get("name"))
        new_mux_ = ET.SubElement(new_second_stage_, "mux")
        new_mux_.set("name", mux.get("name"))
        new_mux__ = ET.SubElement(new_second_stage__, "mux")
        new_mux__.set("name", mux.get("name"))

        new_to = ET.SubElement(new_mux, "to")
        new_to_ = ET.SubElement(new_mux_, "to")
        new_to__ = ET.SubElement(new_mux__, "to")
        mux_to = mux.find("to").text
        new_to_text = mux_to
        new_to_text_ = mux_to
        new_to_text__ = mux_to
        if mux_to[0:3] == "clb":
            mux_to_token = mux_to.split(".")[1]
            mux_to_port = mux_to_token.split("[")[0]
            mux_to_pin = mux_to_token[-2]
            abso_pin_index = 0
            for i_port in range(len(CLB_IPIN_NAME)):
                if CLB_IPIN_NAME[i_port] == mux_to_port:
                    abso_pin_index = int(mux_to_pin) + i_port * CLB_IPIN_NUM_PER_PORT
            
            new_index = abso_pin_index % IO_BOTTOML_INPUT_NUM
            new_to_text = IO_BOTTOML_INPUT_NAME + "[" + str(new_index) + "]"
            new_to_text_ = IO_BOTTOM_DSPL_INPUT_NAME + "[" + str(new_index) + "]"
            new_to_text__ = IO_BOTTOM_RAML_INPUT_NAME + "[" + str(new_index) + "]"
        new_to.text = new_to_text
        new_to_.text = new_to_text_
        new_to__.text = new_to_text__


        for i_from in mux.findall("from"):
            new_from = ET.SubElement(new_mux, "from")
            new_from_ = ET.SubElement(new_mux_, "from")
            new_from__ = ET.SubElement(new_mux__, "from")
            i_froms = i_from.text.split(" ")

            new_from_str = ""
            new_from_str_ = ""
            new_from_str__ = ""
            for ii_from in i_froms:
                ii_from_ = ii_from
                ii_from__ = ii_from
                if ii_from[0:3] == "clb":
                    from_clb_text = ii_from.split(".O[")
                    from_clb_index = from_clb_text[1]
                    from_clb_index = from_clb_index[:-1]
                    index = int(from_clb_index)
                    new_index = index % IO_BOTTOML_OUTPUT_NUM
                    ii_from = IO_BOTTOML_OUTPUT_NAME + "[" + str(new_index) + "]"
                    ii_from_ = IO_BOTTOM_DSPL_OUTPUT_NAME + "[" + str(new_index) + "]"
                    ii_from__ = IO_BOTTOM_RAML_OUTPUT_NAME + "[" + str(new_index) + "]"
                if len(ii_from.split(".")) > 1:
                    dir_index = ii_from.split(".")[1]
                    dir = dir_index[0]
                    if dir == "N":
                        ii_from = ""
                        ii_from_ = ""
                        ii_from__ = ""
                
                for i_1st_stage_mux in empty_1st_stage_mux:
                    if ii_from == i_1st_stage_mux:
                        ii_from = ""
                for i_1st_stage_mux_ in empty_1st_stage_mux_:
                    if ii_from_ == i_1st_stage_mux_:
                        ii_from_ = ""
                for i_1st_stage_mux__ in empty_1st_stage_mux__:
                    if ii_from__ == i_1st_stage_mux__:
                        ii_from__ = ""

                if ii_from != "":
                    new_from_str = new_from_str + ii_from + str(" ")
                if ii_from_ != "":
                    new_from_str_ = new_from_str_ + ii_from_ + str(" ")
                if ii_from__ != "":
                    new_from_str__ = new_from_str__ + ii_from__ + str(" ")
                
            new_from_str = new_from_str[:-1]
            new_from.text = new_from_str
            new_from_str_ = new_from_str_[:-1]
            new_from_.text = new_from_str_
            new_from_str__ = new_from_str__[:-1]
            new_from__.text = new_from_str__

        if new_mux.get("name")[0] == "S":
            new_second_stage.remove(new_mux)
        if new_mux_.get("name")[0] == "S":
            new_second_stage_.remove(new_mux_)
        if new_mux__.get("name")[0] == "S":
            new_second_stage__.remove(new_mux__)

    mux_count = 0
    for mux in new_second_stage.findall("mux"):
        mux_name = mux.get("name")
        mux_to = mux.find("to").text.split(".")
        total_num = IO_BOTTOML_OUTPUT_NUM + IO_BOTTOML_INPUT_NUM
        if mux_to[0] == "io_bottomL":
            count = mux_count
            for i_index in range(count, total_num, IO_BOTTOML_INPUT_NUM):
                # for lclk
                new_mux = ET.SubElement(new_second_stage, "mux")
                new_mux.set("name", mux_name)
                new_mux_to = ET.SubElement(new_mux, "to")
                new_mux_to.text = IO_BOTTOML_INPUT_NAME_LCLK + "[" + str(i_index) + "]"

                for i_from in mux.findall("from"):
                    new_mux_from = ET.SubElement(new_mux, "from")
                    new_mux_from.text = i_from.text

                # for lreset
                new_mux = ET.SubElement(new_second_stage, "mux")
                new_mux.set("name", mux_name)
                new_mux_to = ET.SubElement(new_mux, "to")
                new_mux_to.text = IO_BOTTOML_INPUT_NAME_LRESET + "[" + str(i_index) + "]"

                for i_from in mux.findall("from"):
                    new_mux_from = ET.SubElement(new_mux, "from")
                    new_mux_from.text = i_from.text
            mux_count += 1

    mux_count = 0
    for mux in new_second_stage_.findall("mux"):
        mux_name = mux.get("name")
        mux_to = mux.find("to").text.split(".")
        total_num = IO_BOTTOML_OUTPUT_NUM + IO_BOTTOML_INPUT_NUM
        if mux_to[0] == "io_bottom_dspL":
            count = mux_count
            for i_index in range(count, total_num, IO_BOTTOML_INPUT_NUM):
                # for lclk
                new_mux = ET.SubElement(new_second_stage_, "mux")
                new_mux.set("name", mux_name)
                new_mux_to = ET.SubElement(new_mux, "to")
                new_mux_to.text = IO_BOTTOM_DSPL_INPUT_NAME_LCLK + "[" + str(i_index) + "]"

                for i_from in mux.findall("from"):
                    new_mux_from = ET.SubElement(new_mux, "from")
                    new_mux_from.text = i_from.text

                # for lreset
                new_mux = ET.SubElement(new_second_stage_, "mux")
                new_mux.set("name", mux_name)
                new_mux_to = ET.SubElement(new_mux, "to")
                new_mux_to.text = IO_BOTTOM_DSPL_INPUT_NAME_LRESET + "[" + str(i_index) + "]"

                for i_from in mux.findall("from"):
                    new_mux_from = ET.SubElement(new_mux, "from")
                    new_mux_from.text = i_from.text
            mux_count += 1

    mux_count = 0
    for mux in new_second_stage__.findall("mux"):
        mux_name = mux.get("name")
        mux_to = mux.find("to").text.split(".")
        total_num = IO_BOTTOML_OUTPUT_NUM + IO_BOTTOML_INPUT_NUM
        if mux_to[0] == "io_bottom_ramL":
            count = mux_count
            for i_index in range(count, total_num, IO_BOTTOML_INPUT_NUM):
                # for lclk
                new_mux = ET.SubElement(new_second_stage__, "mux")
                new_mux.set("name", mux_name)
                new_mux_to = ET.SubElement(new_mux, "to")
                new_mux_to.text = IO_BOTTOM_RAML_INPUT_NAME_LCLK + "[" + str(i_index) + "]"

                for i_from in mux.findall("from"):
                    new_mux_from = ET.SubElement(new_mux, "from")
                    new_mux_from.text = i_from.text

                # for lreset
                new_mux = ET.SubElement(new_second_stage__, "mux")
                new_mux.set("name", mux_name)
                new_mux_to = ET.SubElement(new_mux, "to")
                new_mux_to.text = IO_BOTTOM_RAML_INPUT_NAME_LRESET + "[" + str(i_index) + "]"

                for i_from in mux.findall("from"):
                    new_mux_from = ET.SubElement(new_mux, "from")
                    new_mux_from.text = i_from.text
            mux_count += 1

def add_empty_vib(arch_gsb):
    new_vib = ET.SubElement(arch_gsb, "vib")
    vib = arch_gsb.find("vib")
    new_vib.set("name", "vib5")
    new_vib.set("pbtype_name", "EMPTY")
    new_vib.set("vib_seg_group", vib.get("vib_seg_group"))
    new_vib.set("arch_vib_switch", vib.get("arch_vib_switch"))

    for i_seg_group in vib.findall("seg_group"):
        new_seg_group = ET.SubElement(new_vib, "seg_group")
        new_seg_group.set("name", i_seg_group.get("name"))
        new_seg_group.set("track_nums", i_seg_group.get("track_nums"))

    new_multistage_muxs = ET.SubElement(new_vib, "multistage_muxs")
    new_first_stage = ET.SubElement(new_multistage_muxs, "first_stage")
    new_second_stage = ET.SubElement(new_multistage_muxs, "second_stage")

    first_stage = vib.find("./multistage_muxs/first_stage")
    second_stage = vib.find("./multistage_muxs/second_stage")

    # Process first stage
    new_first_stage.set("switch_name", first_stage.get("switch_name"))
    for mux in first_stage.findall("mux"):
        if mux.get("name")[0:2] != "OG" and mux.get("name")[0:4] != "omux":
            new_mux = ET.SubElement(new_first_stage, "mux")
            new_mux.set("name", mux.get("name"))

            for i_from in mux.findall("from"):
                new_from = ET.SubElement(new_mux, "from")
                i_froms = i_from.text.split(" ")

                new_from_str = ""
                for ii_from in i_froms:
                    if ii_from[0:3] == "clb" or ii_from[0:2] == "OG" or ii_from[0:4] == "omux":
                        new_from_str = new_from_str + str("")
                    else:
                        new_from_str = new_from_str + ii_from + str(" ")
                new_from_str = new_from_str[:-1]
            
                new_from.text = new_from_str

    # Process second stage
    
    for mux in second_stage.findall("mux"):
        mux_to = mux.find("to").text
        if mux_to[0:3] != "clb":
            new_mux = ET.SubElement(new_second_stage, "mux")
            new_mux.set("name", mux.get("name"))

            
            new_to = ET.SubElement(new_mux, "to")
            new_to_text = mux_to
            
            new_to.text = new_to_text

            for i_from in mux.findall("from"):
                new_from = ET.SubElement(new_mux, "from")
                i_froms = i_from.text.split(" ")

                new_from_str = ""
                for ii_from in i_froms:
                    if ii_from[0:3] == "clb" or ii_from[0:2] == "OG" or ii_from[0:4] == "omux":
                        new_from_str = new_from_str + str("")
                    else:
                        new_from_str = new_from_str + ii_from + str(" ")
                new_from_str = new_from_str[:-1]
            
                new_from.text = new_from_str

    for mux in new_second_stage.findall("mux"):
        new_to = mux.find("to")
        if new_to.text[0] == "l":
            new_str = ""
            froms = mux.find("from").text
            for i_from in froms.split(" "):
                if i_from[0] == "l":
                    new_str = new_str
                else:
                    new_str = new_str + i_from + str(" ")
            new_str = new_str[:-1]
            mux.find("from").text = new_str
        if mux.find("from").text == "":
            new_second_stage.remove(mux)

def add_vib_layout(arch_root):
    vib_layout = ET.SubElement(arch_root, "vib_layout")
    fixed_layout = ET.SubElement(vib_layout, "fixed_layout")
    fixed_layout.set("name", LAYOUT_NAME)
    layout = arch_root.find("layout")
    
    for i_layout in layout.findall("fixed_layout"):
        if i_layout.get("name") == LAYOUT_NAME:
            for i_tag in i_layout.findall(".//"):
                vib_tag = ET.SubElement(fixed_layout, i_tag.tag)

                new_type = ""
                dsp_x = []
                ram9k_x = []
                for i_attrib in i_tag.attrib:
                    if i_attrib == "type":
                        if i_tag.get("type") == "clb":
                            new_type = "vib0"
                        elif i_tag.get("type") == "io_leftL":
                            new_type = "vib1"
                        elif i_tag.get("type") == "io_rightL":
                            new_type = "vib2"
                        elif i_tag.get("type") == "io_topL":
                            new_type = "vib3"
                        elif i_tag.get("type") == "io_bottomL":
                            new_type = "vib4"
                        elif i_tag.get("type") == "EMPTY":
                            new_type = "vib5"
                        elif i_tag.get("type") == "io_top_dspL":
                            new_type = "vib10"
                            dsp_x.append(i_tag.get("x"))
                        elif i_tag.get("type") == "io_top_ramL":
                            new_type = "vib11"
                            ram9k_x.append(i_tag.get("x"))
                        elif i_tag.get("type") == "io_bottom_dspL":
                            new_type = "vib12"
                        elif i_tag.get("type") == "io_bottom_ramL":
                            new_type = "vib13"
                        elif i_tag.get("type") == "dsp":
                            new_type = "vib6"
                        elif i_tag.get("type") == "ram9k":
                            new_type = "vib8"
                        else:
                            print("We do not support %s type!\n", i_tag.get("type"))
                        vib_tag.set("type", new_type)

                    else:
                        vib_tag.set(i_attrib, i_tag.get(i_attrib))
                
                for i_dsp_x in dsp_x:
                    for i_y in range(1, int(i_layout.get("height")) - 1, 2):
                        dsp_tag = ET.SubElement(fixed_layout, "single")
                        dsp_tag.set("type", "vib7")
                        dsp_tag.set("x", i_dsp_x)
                        dsp_tag.set("y", str(i_y))
                        dsp_tag.set("priority", "102")
                for i_ram9k_x in ram9k_x:
                    for i_y in range(1, int(i_layout.get("height")) - 1, 2):
                        ram9k_tag = ET.SubElement(fixed_layout, "single")
                        ram9k_tag.set("type", "vib9")
                        ram9k_tag.set("x", i_ram9k_x)
                        ram9k_tag.set("y", str(i_y))
                        ram9k_tag.set("priority", "102")

                    

def add_dsp_vib(arch_gsb):
    new_vib = ET.SubElement(arch_gsb, "vib")
    new_vib_ = ET.SubElement(arch_gsb, "vib")
    vib = arch_gsb.find("vib")
    new_vib.set("name", "vib6")
    new_vib.set("pbtype_name", "dsp")
    new_vib.set("vib_seg_group", vib.get("vib_seg_group"))
    new_vib.set("arch_vib_switch", vib.get("arch_vib_switch"))

    new_vib_.set("name", "vib7")
    new_vib_.set("pbtype_name", "dsp")
    new_vib_.set("vib_seg_group", vib.get("vib_seg_group"))
    new_vib_.set("arch_vib_switch", vib.get("arch_vib_switch"))

    for i_seg_group in vib.findall("seg_group"):
        new_seg_group = ET.SubElement(new_vib, "seg_group")
        new_seg_group.set("name", i_seg_group.get("name"))
        new_seg_group.set("track_nums", i_seg_group.get("track_nums"))

        new_seg_group_ = ET.SubElement(new_vib_, "seg_group")
        new_seg_group_.set("name", i_seg_group.get("name"))
        new_seg_group_.set("track_nums", i_seg_group.get("track_nums"))

    new_multistage_muxs = ET.SubElement(new_vib, "multistage_muxs")
    new_first_stage = ET.SubElement(new_multistage_muxs, "first_stage")
    new_second_stage = ET.SubElement(new_multistage_muxs, "second_stage")

    new_multistage_muxs_ = ET.SubElement(new_vib_, "multistage_muxs")
    new_first_stage_ = ET.SubElement(new_multistage_muxs_, "first_stage")
    new_second_stage_ = ET.SubElement(new_multistage_muxs_, "second_stage")

    first_stage = vib.find("./multistage_muxs/first_stage")
    second_stage = vib.find("./multistage_muxs/second_stage")

    # Process first stage
    new_first_stage.set("switch_name", first_stage.get("switch_name"))
    new_first_stage_.set("switch_name", first_stage.get("switch_name"))

    empty_1st_stage_mux = []
    empty_1st_stage_mux_ = []
    for mux in first_stage.findall("mux"):
        new_mux = ET.SubElement(new_first_stage, "mux")
        new_mux_ = ET.SubElement(new_first_stage_, "mux")
        new_mux.set("name", mux.get("name"))
        new_mux_.set("name", mux.get("name"))
        for i_from in mux.findall("from"):
            new_from = ET.SubElement(new_mux, "from")
            new_from_ = ET.SubElement(new_mux_, "from")
            i_froms = i_from.text.split(" ")

            new_from_str = ""
            new_from_str_ = ""
            for ii_from in i_froms:
                ii_from_ = ii_from
                if ii_from[0:3] == "clb":
                    from_clb_text = ii_from.split(".O[")
                    from_clb_index = from_clb_text[1]
                    from_clb_index = from_clb_index[:-1]
                    index = int(from_clb_index)
                    new_index = index % len(DSP_OUTPUT_PINS_UP)
                    new_index_ = index % len(DSP_OUTPUT_PINS_DOWN)
                    ii_from = DSP_OUTPUT_PINS_UP[new_index]
                    ii_from_ = DSP_OUTPUT_PINS_DOWN[new_index_]
                
                if ii_from != "":
                    new_from_str = new_from_str + ii_from + str(" ")

                if ii_from_ != "":
                    new_from_str_ = new_from_str_ + ii_from_ + str(" ")
            new_from_str = new_from_str[:-1]
            new_from.text = new_from_str
            new_from_str_ = new_from_str_[:-1]
            new_from_.text = new_from_str_
        if new_mux.find("from").text == "":
            empty_1st_stage_mux.append(new_mux.get("name"))
            new_first_stage.remove(new_mux)

        if new_mux_.find("from").text == "":
            empty_1st_stage_mux_.append(new_mux_.get("name"))
            new_first_stage_.remove(new_mux_)

    # Process second stage
    #new_second_stage.set("switch_name", first_stage.get("switch_name"))
    for mux in second_stage.findall("mux"):
        new_mux = ET.SubElement(new_second_stage, "mux")
        new_mux.set("name", mux.get("name"))
        new_mux_ = ET.SubElement(new_second_stage_, "mux")
        new_mux_.set("name", mux.get("name"))

        new_to = ET.SubElement(new_mux, "to")
        mux_to = mux.find("to").text
        new_to_text = mux_to
        new_to_ = ET.SubElement(new_mux_, "to")
        new_to_text_ = mux_to
        if mux_to[0:3] == "clb":
            mux_to_token = mux_to.split(".")[1]
            mux_to_port = mux_to_token.split("[")[0]
            mux_to_pin = mux_to_token[-2]
            abso_pin_index = 0
            for i_port in range(len(CLB_IPIN_NAME)):
                if CLB_IPIN_NAME[i_port] == mux_to_port:
                    abso_pin_index = int(mux_to_pin) + i_port * CLB_IPIN_NUM_PER_PORT
            
            new_index = abso_pin_index % len(DSP_INPUT_PINS_UP)
            new_to_text = DSP_INPUT_PINS_UP[new_index]
            new_index_ = abso_pin_index % len(DSP_INPUT_PINS_DOWN)
            new_to_text_ = DSP_INPUT_PINS_DOWN[new_index_]
        new_to.text = new_to_text
        new_to_.text = new_to_text_


        for i_from in mux.findall("from"):
            new_from = ET.SubElement(new_mux, "from")
            new_from_ = ET.SubElement(new_mux_, "from")
            i_froms = i_from.text.split(" ")

            new_from_str = ""
            new_from_str_ = ""
            for ii_from in i_froms:
                ii_from_ = ii_from
                if ii_from[0:3] == "clb":
                    from_clb_text = ii_from.split(".O[")
                    from_clb_index = from_clb_text[1]
                    from_clb_index = from_clb_index[:-1]
                    index = int(from_clb_index)
                    new_index = index % len(DSP_OUTPUT_PINS_UP)
                    ii_from = DSP_OUTPUT_PINS_UP[new_index]
                    new_index_ = index % len(DSP_OUTPUT_PINS_DOWN)
                    ii_from_ = DSP_OUTPUT_PINS_DOWN[new_index_]
                
                for i_1st_stage_mux in empty_1st_stage_mux:
                    if ii_from == i_1st_stage_mux:
                        ii_from = ""

                for i_1st_stage_mux_ in empty_1st_stage_mux_:
                    if ii_from_ == i_1st_stage_mux_:
                        ii_from_ = ""

                if ii_from != "":
                    new_from_str = new_from_str + ii_from + str(" ")
                if ii_from_ != "":
                    new_from_str_ = new_from_str_ + ii_from_ + str(" ")
            new_from_str = new_from_str[:-1]
            new_from.text = new_from_str
            new_from_str_ = new_from_str_[:-1]
            new_from_.text = new_from_str_

def add_ram9k_vib(arch_gsb):
    new_vib = ET.SubElement(arch_gsb, "vib")
    new_vib_ = ET.SubElement(arch_gsb, "vib")
    vib = arch_gsb.find("vib")
    new_vib.set("name", "vib8")
    new_vib.set("pbtype_name", "ram9k")
    new_vib.set("vib_seg_group", vib.get("vib_seg_group"))
    new_vib.set("arch_vib_switch", vib.get("arch_vib_switch"))

    new_vib_.set("name", "vib9")
    new_vib_.set("pbtype_name", "ram9k")
    new_vib_.set("vib_seg_group", vib.get("vib_seg_group"))
    new_vib_.set("arch_vib_switch", vib.get("arch_vib_switch"))

    for i_seg_group in vib.findall("seg_group"):
        new_seg_group = ET.SubElement(new_vib, "seg_group")
        new_seg_group.set("name", i_seg_group.get("name"))
        new_seg_group.set("track_nums", i_seg_group.get("track_nums"))

        new_seg_group_ = ET.SubElement(new_vib_, "seg_group")
        new_seg_group_.set("name", i_seg_group.get("name"))
        new_seg_group_.set("track_nums", i_seg_group.get("track_nums"))

    new_multistage_muxs = ET.SubElement(new_vib, "multistage_muxs")
    new_first_stage = ET.SubElement(new_multistage_muxs, "first_stage")
    new_second_stage = ET.SubElement(new_multistage_muxs, "second_stage")

    new_multistage_muxs_ = ET.SubElement(new_vib_, "multistage_muxs")
    new_first_stage_ = ET.SubElement(new_multistage_muxs_, "first_stage")
    new_second_stage_ = ET.SubElement(new_multistage_muxs_, "second_stage")

    first_stage = vib.find("./multistage_muxs/first_stage")
    second_stage = vib.find("./multistage_muxs/second_stage")

    # Process first stage
    new_first_stage.set("switch_name", first_stage.get("switch_name"))
    new_first_stage_.set("switch_name", first_stage.get("switch_name"))

    empty_1st_stage_mux = []
    empty_1st_stage_mux_ = []
    for mux in first_stage.findall("mux"):
        new_mux = ET.SubElement(new_first_stage, "mux")
        new_mux_ = ET.SubElement(new_first_stage_, "mux")
        new_mux.set("name", mux.get("name"))
        new_mux_.set("name", mux.get("name"))
        for i_from in mux.findall("from"):
            new_from = ET.SubElement(new_mux, "from")
            new_from_ = ET.SubElement(new_mux_, "from")
            i_froms = i_from.text.split(" ")

            new_from_str = ""
            new_from_str_ = ""
            for ii_from in i_froms:
                ii_from_ = ii_from
                if ii_from[0:3] == "clb":
                    from_clb_text = ii_from.split(".O[")
                    from_clb_index = from_clb_text[1]
                    from_clb_index = from_clb_index[:-1]
                    index = int(from_clb_index)
                    new_index = index % len(RAM9K_OUTPUT_PINS_UP)
                    new_index_ = index % len(RAM9K_OUTPUT_PINS_DOWN)
                    ii_from = RAM9K_OUTPUT_PINS_UP[new_index]
                    ii_from_ = RAM9K_OUTPUT_PINS_DOWN[new_index_]
                
                if ii_from != "":
                    new_from_str = new_from_str + ii_from + str(" ")

                if ii_from_ != "":
                    new_from_str_ = new_from_str_ + ii_from_ + str(" ")
            new_from_str = new_from_str[:-1]
            new_from.text = new_from_str
            new_from_str_ = new_from_str_[:-1]
            new_from_.text = new_from_str_
        if new_mux.find("from").text == "":
            empty_1st_stage_mux.append(new_mux.get("name"))
            new_first_stage.remove(new_mux)

        if new_mux_.find("from").text == "":
            empty_1st_stage_mux_.append(new_mux_.get("name"))
            new_first_stage_.remove(new_mux_)

    # Process second stage
    #new_second_stage.set("switch_name", first_stage.get("switch_name"))
    for mux in second_stage.findall("mux"):
        new_mux = ET.SubElement(new_second_stage, "mux")
        new_mux.set("name", mux.get("name"))
        new_mux_ = ET.SubElement(new_second_stage_, "mux")
        new_mux_.set("name", mux.get("name"))

        new_to = ET.SubElement(new_mux, "to")
        mux_to = mux.find("to").text
        new_to_text = mux_to
        new_to_ = ET.SubElement(new_mux_, "to")
        new_to_text_ = mux_to
        if mux_to[0:3] == "clb":
            mux_to_token = mux_to.split(".")[1]
            mux_to_port = mux_to_token.split("[")[0]
            mux_to_pin = mux_to_token[-2]
            abso_pin_index = 0
            for i_port in range(len(CLB_IPIN_NAME)):
                if CLB_IPIN_NAME[i_port] == mux_to_port:
                    abso_pin_index = int(mux_to_pin) + i_port * CLB_IPIN_NUM_PER_PORT
            
            new_index = abso_pin_index % len(RAM9K_INPUT_PINS_UP)
            new_to_text = RAM9K_INPUT_PINS_UP[new_index]
            new_index_ = abso_pin_index % len(RAM9K_INPUT_PINS_DOWN)
            new_to_text_ = RAM9K_INPUT_PINS_DOWN[new_index_]
        new_to.text = new_to_text
        new_to_.text = new_to_text_


        for i_from in mux.findall("from"):
            new_from = ET.SubElement(new_mux, "from")
            new_from_ = ET.SubElement(new_mux_, "from")
            i_froms = i_from.text.split(" ")

            new_from_str = ""
            new_from_str_ = ""
            for ii_from in i_froms:
                ii_from_ = ii_from
                if ii_from[0:3] == "clb":
                    from_clb_text = ii_from.split(".O[")
                    from_clb_index = from_clb_text[1]
                    from_clb_index = from_clb_index[:-1]
                    index = int(from_clb_index)
                    new_index = index % len(RAM9K_OUTPUT_PINS_UP)
                    ii_from = RAM9K_OUTPUT_PINS_UP[new_index]
                    new_index_ = index % len(RAM9K_OUTPUT_PINS_DOWN)
                    ii_from_ = RAM9K_OUTPUT_PINS_DOWN[new_index_]
                
                for i_1st_stage_mux in empty_1st_stage_mux:
                    if ii_from == i_1st_stage_mux:
                        ii_from = ""

                for i_1st_stage_mux_ in empty_1st_stage_mux_:
                    if ii_from_ == i_1st_stage_mux_:
                        ii_from_ = ""

                if ii_from != "":
                    new_from_str = new_from_str + ii_from + str(" ")
                if ii_from_ != "":
                    new_from_str_ = new_from_str_ + ii_from_ + str(" ")
            new_from_str = new_from_str[:-1]
            new_from.text = new_from_str
            new_from_str_ = new_from_str_[:-1]
            new_from_.text = new_from_str_

def process_segmentlist(arch_root):
    segmentlist = arch_root.find("segmentlist")
    for segment in segmentlist.findall("segment"):
        if segment.get("name") == "imux_medium" or segment.get("name") == "omux_medium" or segment.get("name") == "gsb_medium":
            segmentlist.remove(segment)

def convert_gsb2vib(gsb_xml, vib_xml):
    archtree = ET.parse(gsb_xml)
    arch_root = archtree.getroot()
    arch_gsb = archtree.getroot().find("gsb_arch")

    #arch_seg = archtree.getroot().find("segmentlist")
    #segElem = arch_seg.find("segment")
    #cbElem = segElem.find("sb")

    gsbElem = arch_gsb.find("gsb")
    imuxElem = arch_gsb.find("imux")
    omuxElem = arch_gsb.find("omux")

    change_omux_pins(omuxElem, imuxElem, gsbElem)
    rewrite_imux_2nd_stage(imuxElem)
    remove_glb_cas(imuxElem, gsbElem)
    swap_tags(imuxElem, gsbElem)
    arch_gsb.remove(imuxElem)
    add_omuxes(arch_gsb, omuxElem, gsbElem)
    # No imux and omux now
    remove_from(gsbElem)
    remove_glb_cas_in_mux(gsbElem)
    
    arch_gsb.tag = "vib_arch"
    arch_gsb.attrib.pop("pbtype_name")

    modify_seg(gsbElem)

    modify_rules(gsbElem)

    add_left_io_vib(arch_gsb)
    add_right_io_vib(arch_gsb)
    add_top_io_vib(arch_gsb)
    add_bottom_io_vib(arch_gsb)
    add_empty_vib(arch_gsb)
    add_dsp_vib(arch_gsb)
    add_ram9k_vib(arch_gsb)

    add_vib_layout(arch_root)

    process_segmentlist(arch_root)

    writeArch(arch_root, vib_xml)

def add_seg_group(segment_names, segment_freqs, vib):
    for i in range(0, len(segment_names)):
        seg_group = ET.SubElement(vib, "seg_group")
        seg_group.set("name", segment_names[i])
        seg_group.set("track_nums", str(int(int(segment_freqs[i]) / 2)))

def gen_omux(first_stage):
    count = 0
    for i_mux in range(0, 16):
        mux = ET.SubElement(first_stage, "mux")
        name = "omux-" + str(i_mux)
        mux.set("name", name)
        mux_from = ET.SubElement(mux, "from")
        from_str = ""
        for i_from in range(0, 6):
            from_str = from_str + "clb.O[" + str(count % CLB_OPIN_NUM) + "] "
            count = count + 1
        from_str = from_str[:-1]
        mux_from.text = from_str

def gen_sharing_mux(first_stage, segment_names, segment_freqs, from_N_mux, from_S_mux, from_W_mux, from_E_mux):
    from_seg_num_in_one_mux = 4
    total_seg = 0
    for freq in segment_freqs:
        total_seg = total_seg + int(int(freq) / 2)

    group_num = int(total_seg / from_seg_num_in_one_mux)
    sharing_mux_num = int(total_seg / from_seg_num_in_one_mux) * 4  # 4 directions

    num = []
    for i in range(0, group_num):
        num.append([])
    for j in range(0, total_seg):
        num[j % group_num].append(j)

    for i_mux in range(0, sharing_mux_num):
        mux = ET.SubElement(first_stage, "mux")
        name = "mux-" + str(i_mux)
        mux.set("name", name)
        mux_from = ET.SubElement(mux, "from")
        direc = "N"
        if i_mux % 4 == 0:
            direc = "N"
            from_N_mux.append(name)
        elif i_mux % 4 == 1:
            direc = "S"
            from_S_mux.append(name)
        elif i_mux % 4 == 2:
            direc = "W"
            from_W_mux.append(name)
        else:
            direc = "E"
            from_E_mux.append(name)

        mux_index = num[int(i_mux / 4) % group_num]

        from_str = ""
        for i_index in mux_index:
            count = 0
            temp = 0
            for i_seg in range(0, len(segment_freqs)):

                count = count + int(int(segment_freqs[i_seg]) / 2)
                if i_index < count:
                    temp = count - i_index
                    break
            seg_name = segment_names[i_seg]
            seg_index = int(int(segment_freqs[i_seg]) / 2) - temp
            from_seg = seg_name + "." + direc + str(seg_index)
            from_str = from_str + from_seg + " "

        para4opin = i_mux % (CLB_OPIN_NUM + 16)   # 16 omux; 24 opin
        if para4opin < CLB_OPIN_NUM:
            from_str = from_str + "clb.O[" + str(para4opin) + "]"
        else:
            from_str = from_str + "omux-" + str(para4opin - CLB_OPIN_NUM)

        mux_from.text = from_str

def gen_seg_mux(first_stage, segment_names, segment_freqs, from_N_mux, from_S_mux, from_W_mux, from_E_mux):
    segment_mux_num = 20
    group_num = segment_mux_num + random.randint(1,10)

    total_seg = 0
    for freq in segment_freqs:
        total_seg = total_seg + int(int(freq) / 2)

    num = []
    for i in range(0, group_num):
        num.append([])
    for j in range(0, total_seg):
        num[j % group_num].append(j)

    for i_mux in range(0, segment_mux_num):
        mux = ET.SubElement(first_stage, "mux")
        name = "mux-_" + str(i_mux)
        mux.set("name", name)
        mux_from = ET.SubElement(mux, "from")
        direc = "N"
        if i_mux % 4 == 0:
            direc = "N"
            from_N_mux.append(name)
        elif i_mux % 4 == 1:
            direc = "S"
            from_S_mux.append(name)
        elif i_mux % 4 == 2:
            direc = "W"
            from_W_mux.append(name)
        else:
            direc = "E"
            from_E_mux.append(name)

        mux_index = num[int(i_mux / 4) % group_num]

        from_str = ""
        for i_index in mux_index:
            count = 0
            temp = 0
            for i_seg in range(0, len(segment_freqs)):

                count = count + int(int(segment_freqs[i_seg]) / 2)
                if i_index < count:
                    temp = count - i_index
                    break
            seg_name = segment_names[i_seg]
            seg_index = int(int(segment_freqs[i_seg]) / 2) - temp
            from_seg = seg_name + "." + direc + str(seg_index)
            from_str = from_str + from_seg + " "

        para4opin = i_mux % (CLB_OPIN_NUM + 16)   # 16 omux; 24 opin
        if para4opin < CLB_OPIN_NUM:
            from_str = from_str + "clb.O[" + str(para4opin) + "]"
        else:
            from_str = from_str + "omux-" + str(para4opin - CLB_OPIN_NUM)

        mux_from.text = from_str
        
def gen_second_stage_ipin(second_stage, from_N_mux, from_S_mux, from_W_mux, from_E_mux):
    group_num = 10
    total_mux_num = len(from_N_mux) + len(from_S_mux) + len(from_W_mux)+ len(from_E_mux)
    num_mux_per_group = int(total_mux_num / group_num)    # 10
    total_ipin_num = CLB_IPIN_NUM_PER_PORT * len(CLB_IPIN_NAME)
    num_ipin_per_group = int(total_ipin_num / group_num)  # 6

    count_mux = 0
    
    for i in range(0, CLB_IPIN_NUM_PER_PORT):
        for port in CLB_IPIN_NAME:
            group_index = int(count_mux / num_ipin_per_group)

            mux = ET.SubElement(second_stage, "mux")
            name = "mux--" + str(count_mux)
            mux.set("name", name)
            mux_to = ET.SubElement(mux, "to")
            mux_to.text = "clb." + port + "[" + str(i) + "]"

            mux_from = ET.SubElement(mux, "from")
            from_str = ""
            for i_from_mux in range(group_index * num_mux_per_group, (group_index + 1) * num_mux_per_group):
                from_str = from_str + "mux-" + str(i_from_mux) + " "
            mux_from.text = from_str[:-1]

            count_mux = count_mux + 1

def gen_second_stage_seg(second_stage, segment_names, segment_lengths, segment_freqs, from_N_mux, from_S_mux, from_W_mux, from_E_mux):
    count = 0
    for i_seg in range(0, len(segment_names)):
        for i_track in range(0, int(int(segment_freqs[i_seg]) / 2)):
            if i_track % int(segment_lengths[i_seg]) == 0:
                count = count + 1
    step = int(len(from_N_mux) / count) + 1

    

    count = 0
    count4N = 0
    count4S = 0
    count4W = 0
    count4E = 0
    for i_seg in range(0, len(segment_names)):
        for i_track in range(0, int(int(segment_freqs[i_seg]) / 2)):
            if i_track % int(segment_lengths[i_seg]) == 0:
                mux = ET.SubElement(second_stage, "mux")
                name = "mux_" + str(count)
                mux.set("name", name)
                mux_to = ET.SubElement(mux, "to")
                mux_to.text = segment_names[i_seg] + ".N" + str(i_track)
                mux_from = ET.SubElement(mux, "from")
                from_str = ""
                for i in range(count4N, count4N + step):
                    from_str = from_str + from_N_mux[i % len(from_N_mux)] + " "
                for i in range(count4S, count4S + step):
                    from_str = from_str + from_S_mux[i % len(from_S_mux)] + " "
                for i in range(count4W, count4W + step):
                    from_str = from_str + from_W_mux[i % len(from_W_mux)] + " "
                for i in range(count4E, count4E + step):
                    from_str = from_str + from_E_mux[i % len(from_E_mux)] + " "

                para4opin = count % (16)   # 16 omux
                from_str = from_str + "omux-" + str(para4opin)
                mux_from.text = from_str
                count = count + 1

                mux = ET.SubElement(second_stage, "mux")
                name = "mux_" + str(count)
                mux.set("name", name)
                mux_to = ET.SubElement(mux, "to")
                mux_to.text = segment_names[i_seg] + ".S" + str(i_track)
                mux_from = ET.SubElement(mux, "from")
                from_str = ""
                for i in range(count4N, count4N + step):
                    from_str = from_str + from_N_mux[i % len(from_N_mux)] + " "
                for i in range(count4S, count4S + step):
                    from_str = from_str + from_S_mux[i % len(from_S_mux)] + " "
                for i in range(count4W, count4W + step):
                    from_str = from_str + from_W_mux[i % len(from_W_mux)] + " "
                for i in range(count4E, count4E + step):
                    from_str = from_str + from_E_mux[i % len(from_E_mux)] + " "
                para4opin = count % (16)   # 16 omux
                from_str = from_str + "omux-" + str(para4opin)
                mux_from.text = from_str
                
                count = count + 1

                mux = ET.SubElement(second_stage, "mux")
                name = "mux_" + str(count)
                mux.set("name", name)
                mux_to = ET.SubElement(mux, "to")
                mux_to.text = segment_names[i_seg] + ".W" + str(i_track)
                mux_from = ET.SubElement(mux, "from")
                from_str = ""
                for i in range(count4N, count4N + step):
                    from_str = from_str + from_N_mux[i % len(from_N_mux)] + " "
                for i in range(count4S, count4S + step):
                    from_str = from_str + from_S_mux[i % len(from_S_mux)] + " "
                for i in range(count4W, count4W + step):
                    from_str = from_str + from_W_mux[i % len(from_W_mux)] + " "
                for i in range(count4E, count4E + step):
                    from_str = from_str + from_E_mux[i % len(from_E_mux)] + " "
                para4opin = count % (16)   # 16 omux
                from_str = from_str + "omux-" + str(para4opin)
                mux_from.text = from_str
                
                count = count + 1

                mux = ET.SubElement(second_stage, "mux")
                name = "mux_" + str(count)
                mux.set("name", name)
                mux_to = ET.SubElement(mux, "to")
                mux_to.text = segment_names[i_seg] + ".E" + str(i_track)
                mux_from = ET.SubElement(mux, "from")
                from_str = ""
                for i in range(count4N, count4N + step):
                    from_str = from_str + from_N_mux[i % len(from_N_mux)] + " "
                for i in range(count4S, count4S + step):
                    from_str = from_str + from_S_mux[i % len(from_S_mux)] + " "
                for i in range(count4W, count4W + step):
                    from_str = from_str + from_W_mux[i % len(from_W_mux)] + " "
                for i in range(count4E, count4E + step):
                    from_str = from_str + from_E_mux[i % len(from_E_mux)] + " "
                para4opin = count % (16)   # 16 omux
                from_str = from_str + "omux-" + str(para4opin)
                mux_from.text = from_str

                count = count + 1

                count4N += step
                count4S += step
                count4W += step
                count4E += step
                

def convert_vib2openFPGAvib(gsb_xml, vib_xml):
    archtree = ET.parse(gsb_xml)
    arch_root = archtree.getroot()
    arch_gsb = archtree.getroot().find("vib_arch")

    if arch_gsb == None:
        arch_gsb = archtree.getroot().find("gsb_arch")
    
    arch_root.remove(arch_gsb)

    segmentlist = arch_root.find("segmentlist")
    segment_names = []
    segment_lengths = []
    segment_freqs = []
    for segment in segmentlist.findall("segment"):
        freq = segment.get("freq")
        if float(freq) == 0:
            continue
        segment_names.append(segment.get("name"))
        segment_lengths.append(segment.get("length"))
        segment_freqs.append(freq)

    vib_arch = ET.SubElement(arch_root, "vib_arch")
    vib = ET.SubElement(vib_arch, "vib")
    vib.set("name", "vib0")
    vib.set("pbtype_name", "clb")
    vib.set("vib_seg_group", str(len(segment_names)))
    vib.set("arch_vib_switch", "only_mux")
    
    add_seg_group(segment_names, segment_freqs, vib)

    multistage_muxs = ET.SubElement(vib, "multistage_muxs")
    first_stage = ET.SubElement(multistage_muxs, "first_stage")
    first_stage.set("switch_name", "only_mux")
    second_stage = ET.SubElement(multistage_muxs, "second_stage")

    gen_omux(first_stage)

    from_N_mux = []
    from_S_mux = []
    from_W_mux = []
    from_E_mux = []
    gen_sharing_mux(first_stage, segment_names, segment_freqs, from_N_mux, from_S_mux, from_W_mux, from_E_mux)
    gen_second_stage_ipin(second_stage, from_N_mux, from_S_mux, from_W_mux, from_E_mux)

    gen_seg_mux(first_stage, segment_names, segment_freqs, from_N_mux, from_S_mux, from_W_mux, from_E_mux)

    gen_second_stage_seg(second_stage, segment_names, segment_lengths, segment_freqs, from_N_mux, from_S_mux, from_W_mux, from_E_mux)

    #writeArch(arch_root, vib_xml)

    add_left_io_vib(vib_arch)
    add_right_io_vib(vib_arch)
    add_top_io_vib(vib_arch)
    add_bottom_io_vib(vib_arch)
    add_empty_vib(vib_arch)
    add_dsp_vib(vib_arch)
    add_ram9k_vib(vib_arch)

    add_vib_layout(arch_root)

    process_segmentlist(arch_root)
    

    writeArch(arch_root, vib_xml)

if __name__ == '__main__':
    gsb_xml = "/home/yqwang/gsb2openFPGA/vpr_arch_wo_crossbar_vib_arch2me.xml"
    vib_xml = "/home/yqwang/gsb2openFPGA/vpr_arch_wo_crossbar_vib_arch2me_T22.xml"
    #convert_gsb2vib(gsb_xml, vib_xml)
    convert_vib2openFPGAvib(gsb_xml, vib_xml)