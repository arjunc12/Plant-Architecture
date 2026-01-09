Guide for Arbor.java, ArborBuild.java, ArborTest.java, Point.java, and PointDistance.java

Arbor.java
-stores the geometry of the arbor 
-provides accessors for main and lateral roots
-builds arbor objects, sweeps alpha values, computes wiring cost, and computes conduction delay
-writes Pareto front data to CSV files. 

ArborBuild.java
-reads an arbor reconstruction file and constructs an Arbor object. 

ArborTest.java
-Tests the validity of arbor calculations. 

Point.java
-stores coordinates of the main root, lateral root, and connection points of both. 
-computes distance between points

PointDistance.java
-Calculates the difference between the optimal and the actual lateral roots. 
-Sweeps alpha values and finds best connection points, computes wiring cost, and 
computes conduction delay. Also computes RMSE 

To run the scripts:
-"java Arbor" 
		-uses the old method to compute results for all files
		-writes results to hetereogeneous_pareto_fronts
		
-"java ArborTest"
		-prompts for a specific file name 
		-meant for testing validity
		
-"java PointDistance file.txt"
		-uses the old method to compute results for specific file
		-writes results to pareto_fronts
		
-"java PointDistance --new file.txt"
		-uses the new method to compute results for specific file
		-writes results to hetereogeneous_pareto_fronts

-"java PointDistance --new"
		-uses the new method to compute results for all files
		-writes results to hetereogeneous_pareto_fronts

Old and new methods are found in BestArbor: findBestConnection is the old method and 
findBestConnectionEnhanced is the new method. 

OLD METHOD: outputs alpha, wiring cost, and conduction delay. 

NEW METHOD: outputs alpha, wiring cost, conduction delay, and point distance (RMSE). 
			-computes RMSE for point distance
			-includes a row for the best alpha with the lowest RMSE.
			-calculations for wiring cost and conduction delay are more accurate than 
			old method. 