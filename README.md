# FPGA_Arch_Exploration
 FPGA_Arch_Exploration is used for explore the routing architecture for FPGAs.

 ## Introduction
 This routing architecture is based on VIB architecture. To explore the magnificant design space for [VIB architecture](https://ieeexplore.ieee.org/document/10416125), Bayesian Optimization is used for efficient exploration. Bayesian Optimization is a probabilistic strategy for optimizing complex black-box functions across various parameters. At its core, BO constructs a surrogate model to approximate the objective function and utilizes an acquisition function to sample high-quality candidates, balancing exploration and exploitation.

 Hyperopt is a hyperparameter optimization framework using the Tree-structured Parzen Estimator (TPE), a prominent Bayesian Optimization variant. It supports exploration in parallel.

 ## Requirements
 ### Hyperopt Installation
 Hyperopt is needed for Bayesian Optimization and parallel exploration.

 Install Hyperopt using pip:
 ```bash
 pip install hyperopt
 ```

 After installation, verify that Hyperopt is installed correctly:
 ```bash
 python -c "import hyperopt; print(hyperopt.__version__)"
 ```

 Install MongoDB Dependency：
 ```bash
 pip install pymongo
 ```
 ### VTR Installation
 VTR supported VIB architecture can be downloaded from [VTR4VIB](https://github.com/Wang-Yuanqi-source/vtr-verilog-to-routing/tree/patch-1). Install it in the ``vtr/`` directory of this project.

 Install VTR：
 ```bash
 cd vtr
 make vpr
 ```
 ## File Description
 ``blif_files/`` consists of benchmarks in ``.blif`` format for VPR.
 
 ``blif_list`` lists the circuits for architecture exploration evaluation. The circuits in ``blif_list`` should also contained in ``blif_files/``.

 ``baseline_result.csv`` cantains the baseline data such as routing area and critical path delay for each circuit.

 ``alkaidT_vib.xml`` is the baseline architecture. The exploration is based on it.

 ``Seeker_bayes_seg.py`` is the main document of the exploration. Various wire types and VIB parameters combinations are generated via Bayesian Optimization and then converted to new architecture description files (.xml). VPR evaluates the routing area and critical path delay of the architectures for exploration iteratively. The optimization goal is the area delay product (ADP) here. ``get_info.sh`` is embedded to get the value of area and delay from vpr log file.

 ``run_hyperopt_seg.sh`` is the interface of the project. The information of the exploration is saved in ``log.txt`` and ``logfile.txt`` (rough and detailed).

 ## How to Use
 First, 
 Run exploration by:
 ```bash
 ./run_hyperopt_seg.sh
 ```

 

