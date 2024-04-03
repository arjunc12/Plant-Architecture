Readme for backend code.

Pipeline for extepted single arbor reconstruction input using automated pipeline:  
1. Analyze the arbors using `analyze_arbors()` in `analyze_arbors.py`  
    - calculates the pareto front arbors based on given arbor and the statistics file that contains a single line of information about where the original arbor is located on the pareto front.  

2. Calculate scaling distances using `write_scaling_dists()` in `analyze_arbors.py`  
    - creates scaling distance file that has a single line of information in the statistics folder  

3. Create and save null models using `analyze_null_models()` in `null_models.py`. These are randomly generated arbors used for comparison.  
    - creates a file in null-models folder that contains the random arbor  

4. Analyze and compare null models to original arbor and calculates position in Pareto front using `write_null_models_file()` in `null_models.py`
    - creates file in statistics folder that is used for drawing the Pareto front.

5. Create the Pareto front drawing and arbor drawings for each file in the reconstructions folder using a three step process.
    - Create the graph of the arbor from the reconstruction file using `read_arbor_full()` from `read_arbor_reconstructions.py`.
    - Use the generated arbor graph to create the Pareto front graph using `viz_front()` in `pareto_functions.py`. (this involves the null model for comparison)
    - Use the generated arbor graph to create the simple tree drawings for the original arbor and the generated optimal arbors using viz_trees() in `pareto_functions.py`.