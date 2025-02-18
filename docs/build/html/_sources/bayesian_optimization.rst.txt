Bayesian Optimization
====================

Bayesian optimization is a sequential design strategy used for black-box optimization. It leverages information from already explored points to model the unknown function and determines the next most valuable search point, guiding the search process and reducing the number of iterations. It is typically used to optimize expensive evaluation functions. The core idea is to estimate the posterior distribution of the objective function using Bayes' theorem based on the data, and then select the next sampling parameter combination according to the distribution. In general, Bayesian optimization is suitable for situations where the objective function is unknown and the evaluation cost is high.

Figure 1 shows an experimental diagram of the iterative process of one-dimensional Bayesian optimization. First, the algorithm generates an initial set of solutions, then searches for the next point that is likely to be an extremum based on these points. This point is added to the set, and the process is repeated until the iteration terminates. Finally, the best point from these points is selected as the solution to the problem. The key question here is how to determine the next search point based on the already evaluated points. Bayesian optimization estimates the mean and variance (i.e., the fluctuation range) of the true objective function value using the function values of the already searched points, as shown in Figure 1. The dashed line in the figure represents the estimated objective function values, i.e., the mean objective function value at each point, with the already searched points shown as black solid points. The blue region represents the fluctuation range of the function values at each point, centered around the mean (the dashed line), and proportional to the standard deviation. At the search points, the dashed line passes through the search points, where the variance is smallest, and the variance increases further from the search points. This also aligns with intuition: the function value estimates are less reliable further away from the sampled points. Based on the mean and variance, an acquisition function can be constructed, which estimates the likelihood of each point being an extremum, reflecting the degree to which each point is worth searching. The extremum of this function is the next search point. As shown in Figure 1, the points represented by red triangles are the maxima of the acquisition function, which are the next search points at the end of each iteration.

.. figure:: Images/Bayes.png
    :align: center 
    :height: 300
    
Figure 1. Schematic diagram of the Bayesian Optimization process.
    
The core of the Bayesian optimization algorithm consists of two parts: (1) modeling the objective function, which involves calculating the mean and variance of the function values at each point, typically implemented using Gaussian process regression; (2) constructing the acquisition function, which is used to decide at which point to sample during the current iteration.

Figure 2 illustrates the basic flow of the Bayesian optimization algorithm. As shown in the pseudocode, it is based on a Sequential Model-based Global Optimization. It runs experiments one by one, each time attempting better parameters by applying Bayesian inference and updating the surrogate model. Then, it finds the parameters that perform best on the surrogate model, applies these parameters to the true objective function, and updates the surrogate model with the new results. This process is repeated continuously until the maximum number of iterations or time is reached.

.. figure:: Images/Bayes_code.png
    :align: center 
    :height: 300
    
Figure 2. The pseudocode of Bayesian optimization.
