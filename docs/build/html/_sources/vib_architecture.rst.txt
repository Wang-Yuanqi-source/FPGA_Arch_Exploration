VIB Interconnect Architecture
=============================

This section introduces the VIB interconnect architecture.

The VIB architecture adds modeling support for double-level MUX topology and bent wires. In past, switch blocks have only one level of routing MUXes, whose inputs are driven by outputs of programmable blocks and routing tracks. Now outputs of programmable blocks can shape the first level of routing MUXes, while the inputs of second level involves the outputs of first level and other routing tracks. This can reduce the number and input sizes of routing MUXes.

Figure 1 shows the proposed VIB architecture which is tile-based. Each tile is composed of a CLB and a VIB. Each CLB can interact with the corresponding VIB which contains all the routing programmable switches in one tile. Figure 2 shows an example of the detailed interconnect architecture in VIB. The CLB input muxes and the driving muxes of wire segments can share the same fanins. A routing path of a net with two sinks is presented red in the Figure.

.. figure:: Images/VIB.png
    :align: center 
    :height: 300
    
Figure 1. VIB architecture. The connections between the inputs and outputs of the LB and the routing wires are all implemented within the VIB.

.. figure:: Images/double-level.png
    :align: center
    
Figure 2. Double-level MUX topology.

Figure 3 shows the modeling for bent wires. A bent L-length wire is modeled as two segments in CHANX and CHANY respectively connected by a delayless switch. The orange and red arrows represent conterclockwise and clockwise bent wires respectively. The bent wires can connect to both bent and straight wire segments.
    
.. figure:: Images/bent_wires.png
    :align: center
    
Figure 3. Presentation for bent wires.
