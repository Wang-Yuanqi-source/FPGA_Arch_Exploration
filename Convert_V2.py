import xml.etree.cElementTree as ET
from xml.dom import minidom
import re

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

# remove the imux into the gsb tag and modify the imux and gsb in one group, no need to modify the mux name
def swap_tags_v2(imuxElem, gsbElem):
    imux_1st_stage = imuxElem.find("./multistage_muxs/first_stage")
    gsb_1st_stage = gsbElem.find("./multistage_muxs/first_stage")
    gsb_2nd_stage = gsbElem.find("./multistage_muxs/second_stage")
    cas_stage = gsbElem.find("./multistage_muxs/cas_stage")
    gsb_1st_stage.set("switch_name", "only_mux")

    # modify the mux_name in gsb
    for mux in gsb_1st_stage.findall("mux"):
        if "_" in mux.get("name") and mux.get("name").startswith("mux"):
            token = mux.get("name").split('_')
            mux.set("name", token[0] + '-' + token[1])

    for mux in gsb_2nd_stage.findall("mux"):
        for mux_from in mux.findall("from"):
            if mux_from.get("mux_name") != None:
                name_list = mux_from.get("mux_name").split("_")
                mux_from.set("mux_name", "-".join(name_list))




    count = 0
    count_gsb = 0
    for mux in imux_1st_stage.findall("mux"):
        count += 1
    for mux in gsb_1st_stage.findall("mux"):
        count_gsb += 1

    for mux in imux_1st_stage.findall("mux"):
        gsb_1st_stage.append(mux)
        imux_1st_stage.remove(mux)

    for mux in gsb_1st_stage.findall("mux"):
        if count == 0 or count_gsb == 0:
            break
        gsb_1st_stage.remove(mux)
        count -= 1
        count_gsb -= 1

    imux_2nd_stage = imuxElem.find("./multistage_muxs/second_stage")
    gsb_2nd_stage = gsbElem.find("./multistage_muxs/second_stage")

    for mux in imux_2nd_stage.findall("mux"):
        gsb_2nd_stage.append(mux)
        imux_2nd_stage.remove(mux)


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

#modify the omux description in the output file
def modify_omux(gsbElem):
    
    gsb_1st_stage = gsbElem.find("./multistage_muxs/first_stage")
    gsb_2nd_stage = gsbElem.find("./multistage_muxs/second_stage")
    
    for mux in gsb_1st_stage.findall("mux"):
        for mux_from in mux.findall("from"):
            from_type = mux_from.get("type")
            from_name = mux_from.get("name")
            if from_type == "omux" and from_name == "oxbar":
                from_detail = mux_from.get("from_detail")
                mux.remove(mux_from)
                new_from = ET.SubElement(mux, "from")
                new_from.set("mux_name", from_detail)
            elif from_type == "glb" and from_name == "glb":
                from_detail = mux_from.get("from_detail")
                mux.remove(mux_from)
                new_from = ET.SubElement(mux, "from")
                new_from.set("mux_name", from_detail)
            elif from_type == "cas" and from_name == "cas":
                from_detail = mux_from.get("from_detail")
                mux.remove(mux_from)
                new_from = ET.SubElement(mux, "from")
                new_from.set("mux_name", from_detail)
                
    for mux in gsb_2nd_stage.findall("mux"):
        for mux_from in mux.findall("from"):
            from_type = mux_from.get("type")
            from_name = mux_from.get("name")
            if from_type == "omux" and from_name == "oxbar":
                from_detail = mux_from.get("from_detail")
                mux.remove(mux_from)
                new_from = ET.SubElement(mux, "from")
                new_from.set("mux_name", from_detail)
            elif from_type == "glb" and from_name == "glb":
                from_detail = mux_from.get("from_detail")
                mux.remove(mux_from)
                new_from = ET.SubElement(mux, "from")
                new_from.set("mux_name", from_detail)
            elif from_type == "cas" and from_name == "cas":
                from_detail = mux_from.get("from_detail")
                mux.remove(mux_from)
                new_from = ET.SubElement(mux, "from")
                new_from.set("mux_name", from_detail)


    
#add the omux description in the arch file
def add_omuxes(archtree, omuxElem, gsbElem):
    gsb_1st_stage = gsbElem.find("./multistage_muxs/first_stage")
    omux_1st_stage = omuxElem.find("./multistage_muxs/first_stage")
    omux_2nd_stage = omuxElem.find("./multistage_muxs/second_stage")

    for mux in omux_1st_stage.findall("mux"):
        gsb_1st_stage.append(mux)
    for mux in omux_2nd_stage.findall("mux"):
        gsb_1st_stage.append(mux)

    archtree.remove(omuxElem)


def add_glb_cas(imuxElem, gsbElem):
    gsb_1st_stage = gsbElem.find("./multistage_muxs/first_stage")
    glb_stage = imuxElem.find("./multistage_muxs/glb_stage")
    cas_stage = gsbElem.find("./multistage_muxs/cas_stage")

    for mux in cas_stage.findall("mux"):
        for mux_from in mux.findall("from"):
            if mux_from.get("mux_name") != None:
                name_list = mux_from.get("mux_name").split("_")
                mux_from.set("mux_name", "-".join(name_list))

    for mux in glb_stage.findall("mux"):
        gsb_1st_stage.append(mux)
    for mux in cas_stage.findall("mux"):
        gsb_1st_stage.append(mux)
    gsbElem.find("./multistage_muxs").remove(cas_stage)
    imuxElem.find("./multistage_muxs").remove(glb_stage)

#remove the from description in the seg_group
def remove_from(gsbElem):
    gsbElem.set("arch_gsb_switch", "only_mux")
    for group_tag in gsbElem.findall("seg_group"):
        for from_tag in group_tag.findall("from"):
            group_tag.remove(from_tag)




# convert the xml format arch file of V100 to the xml arch file in gsb_all_in
def convert(V1_xml, V2_xml):
    archtree = ET.parse(V1_xml)
    arch_root = archtree.getroot()
    arch_gsb = archtree.getroot().find("gsb_arch")
    gsbElem = arch_gsb.find("gsb")
    imuxElem = arch_gsb.find("imux")
    omuxElem = arch_gsb.find("omux")

    add_glb_cas(imuxElem, gsbElem)
    swap_tags(imuxElem, gsbElem)
    arch_gsb.remove(imuxElem)
    remove_from(gsbElem)
    modify_omux(gsbElem)
    add_omuxes(arch_gsb, omuxElem, gsbElem)


    writeArch(arch_root, V2_xml)


# convert the xml format arch file of V100 to the xml arch file in the two level muxes of gsb and ib together
def convert_v2(V1_xml, V3_xml):
    archtree = ET.parse(V1_xml)
    arch_root = archtree.getroot()
    arch_gsb = archtree.getroot().find("gsb_arch")
    gsbElem = arch_gsb.find("gsb")
    imuxElem = arch_gsb.find("imux")
    omuxElem = arch_gsb.find("omux")

    add_glb_cas(imuxElem, gsbElem)
    swap_tags_v2(imuxElem, gsbElem)
    arch_gsb.remove(imuxElem)
    remove_from(gsbElem)
    modify_omux(gsbElem)
    add_omuxes(arch_gsb, omuxElem, gsbElem)
    
    writeArch(arch_root, V3_xml)
    


if __name__ == '__main__':
    V1_xml = "./1.xml"
    V2_xml = "./V2.xml"
    V3_xml = "./V3.xml"
    convert(V1_xml, V2_xml)
    convert_v2(V1_xml, V3_xml)
