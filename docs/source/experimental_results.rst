Experimental Results
====================

VIB architecture parameterization
---------------------------------

The search platform explores routing wires with lengths ranging from 1 to 12, represented by \( n = [n_1, n_2, \dots, n_{12}] \), where these 12 values correspond to the number of routing wires for each length. Additionally, it is specified that routing wires with the same length share the same bending pattern, with a maximum of one bend. The bend position and direction for each wire are represented by \( b = [b_1, b_2, \dots, b_{12}] \) and \( c = [c_1, c_2, \dots, c_{12}] \), respectively. Based on empirical routing architectures, the number of different wire types should vary. For instance, shorter wires (e.g., 1x, 2x lines) should have more connections, while longer wires should be fewer in number. To improve search efficiency, we define upper and lower bounds for each wire type, with specific distributions provided in Table below.

.. table:: The upper and lower bounds for each wire type.
   :widths: auto

   +------------+------------+-----------+
   | Wire       | Upper Num  | Lower Num |
   +============+============+===========+
   | l1         | 10         | 30        |
   +------------+------------+-----------+
   | l2         | 12         | 48        |
   +------------+------------+-----------+
   | l3         | 0          | 48        |
   +------------+------------+-----------+
   | l4         | 0          | 64        |
   +------------+------------+-----------+
   | l5         | 0          | 50        |
   +------------+------------+-----------+
   | l6         | 0          | 60        |
   +------------+------------+-----------+
   | l7         | 0          | 0         |
   +------------+------------+-----------+
   | l8         | 0          | 48        |
   +------------+------------+-----------+
   | l9         | 0          | 0         |
   +------------+------------+-----------+
   | l10        | 0          | 40        |
   +------------+------------+-----------+
   | l11        | 0          | 44        |
   +------------+------------+-----------+
   | l12        | 0          | 48        |
   +------------+------------+-----------+
   
Exploration Results
-------------------
In the Linux version 3.10.0-1160.el7.x86_64 environment, with the CPU being Intel(R) Xeon(R) Platinum 8354H CPU @ 3.10GHz, 30 cores were used for parallel iterative architecture generation, resulting in a total of 634 iterations.

The best 10 architectures compared to the baseline are shown in Figure 1.

.. figure:: Images/exploration_result.png
    :align: center 
    :height: 300
    
    Figure 1. The best 10 archs.
    
In Figure 1, `Delay Imp` refers to the percentage reduction in critical path delay, `Area Imp` refers to the percentage reduction in routing area, and `ADP Imp` refers to the percentage reduction in area-delay product.
The Arch name m_n represents the n-th architecture generated in the m-th thread.

The distribution of various line types for these ten architectures is shown in Figure 2.

.. figure:: Images/wire_distribution.png
    :align: center 
    :height: 300
    
    Figure 2. The wire distribution of ten architectures.
    
In the parentheses in Figure 2, U and D represent counterclockwise and clockwise bends, respectively. Besides, The numbers in parentheses represent the position of the bend.

The information for each benchmark circuit implemented by the two optimal architectures is shown in Figure 3 and Figure 4.

.. figure:: Images/arch1_result.png
    :align: center 
    :height: 300
    
    Figure 3. The detailed results of architecture 15_18.
    
.. figure:: Images/arch2_result.png
    :align: center 
    :height: 300
    
    Figure 4. The detailed results of architecture 27_11.

Analysis
--------
Through the search process based on the VIB architecture on this exploration platform, the final optimal architecture achieves an 11.58% delay improvement, a 20.06% area improvement, and a 29.32% area-delay product improvement compared to the baseline architecture.

Based on the distribution of various wire types in the top 10 optimal architectures, it can be seen that the best performance is achieved when the number of length-1 and length-2 wires are 10 and 12, respectively. This trend remains consistent across these 10 architectures. Length-3 and length-5 wires are generally used less frequently than other wires; the performance is better when the number of length-4 wires is around 24, and when the number of length-8 wires is 32. For other longer wire types, such as length-10 and length-12 wires, the numbers are typically 20 and 24, respectively. Whether both types are present, or only one, or no long wires at all, the performance varies across different architectures.

Through the detailed data statistics for each circuit implemented on the optimal architecture, it can be observed that the routing area improvement is the same for all benchmarks. This is because the architecture is a fixed 50*50 layout, and the routing area remains constant when the same architecture is used to implement different circuits. By observing the delay improvements of different circuits, it can be seen that some circuits experience negative optimization, such as cordic_tanh, Murax, and zipcore. These circuits are larger in scale compared to others. it is likely that the optimization of routing area reduces the width of the routing channels and the number of MUXes in each tile. As a result, some paths in larger circuits required additional detours for successful routing, which leads to the deterioration of the critical path delay for these circuits. However, for other small circuits, the two level MUX topology shrinks the size of each MUX, which leads to less critical path delay to a large extent. Therefore, for the overall benchmark, the architecture obtained through the exploration shows significant optimization in delay compared to the baseline.





