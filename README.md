# FPGA_Arch_Exploration
 FPGA_Arch_Exploration is used for explore the routing architecture for FPGAs.

 ## Introduction
 This routing architecture is based on VIB architecture. To explore the magnificant design space for [VIB architecture](https://ieeexplore.ieee.org/document/10416125), Bayesian Optimization is used for efficient exploration. Bayesian Optimization is a probabilistic strategy for optimizing complex black-box functions across various parameters. At its core, BO constructs a surrogate model to approximate the objective function and utilizes an acquisition function to sample high-quality candidates, balancing exploration and exploitation.

 Hyperopt is a hyperparameter optimization framework using the Tree-structured Parzen Estimator (TPE), a prominent Bayesian Optimization variant. It supports exploration in parallel.

 ## Requirements
 Hyperopt is needed for Bayesian Optimization and parallel exploration.

 Install Hyperopt using pip:
 ```bash
 pip install hyperopt

 After installation, verify that Hyperopt is installed correctly:
 ```bash
 python -c "import hyperopt; print(hyperopt.__version__)"

 Install MongoDB Dependency：
 ```bash
 pip install pymongo
