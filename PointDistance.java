import java.io.File;
import java.io.*;
import java.util.*;

public class PointDistance {
    public static void main(String[] args) throws IOException {
    	//parse args
    	boolean useNewMethod = false;
    	File specifiedFile = null;
    	
    	for (String arg : args) {
    		if (arg.equals("--new")) {
    			useNewMethod = true;
    		}
    		else {
    			specifiedFile = new File(arg);
    		}
    	}
    	
        //Dir containing data files
    	File inputDir = new File("data/architecture-data/arbor-reconstructions");
    	
    	//Dir where output results are stored
		File outputDir;
		if (useNewMethod) {
			outputDir = new File("data/results/heterogeneous_pareto_fronts");
		}
		else {
			outputDir = new File("data/results/pareto_fronts");
		}
		
		outputDir.mkdirs();
    	
    	File[] files;

    	//run of specific file
    	if (specifiedFile != null) {
    		if (!specifiedFile.exists() | !specifiedFile.isFile()) {
    			System.err.println("Specified file does not exist or is not a file: " + args[0]);
    			return;
    		}
    		files = new File[]{specifiedFile};
    	}
    	//run on all files in the input dir
    	else {
    		files = inputDir.listFiles();
    	}
    	
    	//processing each file
    	for (File file : files) {
    		//skipping potential directories or non-files
    		if (!file.isFile()) {
    			continue;
    		}
    		
    		//building arbor from file
    		Arbor arbor = ArborBuild.buildArborFile(file.getPath());
    		
    		//skipping files w no main root data
    		if (arbor.getMainRoot().isEmpty()) {
    			System.out.println("Skipping " + file.getName() + ": no main root data");
    			continue;
    		}
    		
    		String outputFileName = outputDir + "/" + file.getName().replace(".txt", ".csv");
    		try (FileWriter writer = new FileWriter(outputFileName)) {
    			writer.write("alpha,wiring_cost,conduction_delay,point_distance\n");
    			
    			double bestAlpha = -1;
    			double minRMSE = Double.MAX_VALUE;
    			double bestWiringCost = 0.0;
    			double bestConductionDelay = 0.0;
    		
    			//getting best connections for alphas 0.0 - 1.0
            	for (double alpha = 0.0; alpha <= 1.0; alpha += 0.01) {
            		alpha = Math.round(alpha * 100.0) / 100.0;
            		System.out.println("\n---Alpha = " + alpha + "---\n");
            	
            		//finding best connection points for given alpha
            		BestArbor.BestConnectionResult result;
            		if (useNewMethod) {
            			result = BestArbor.findBestConnectionEnhanced(arbor, alpha);
            		}
            		else {
            			result = BestArbor.findBestConnection(arbor, alpha);
            		}
            		
                	Map<String, Point> connections = result.connections;
                
                	double totalRMSE = 0.0;
                	int rootCount = 0;
                	
                	//going through lat roots
                	for (String ID : connections.keySet()) {
                		List<Point> latPoints = arbor.getLateralRoots().get(ID);
                	
                		//getting tip & best connection point
                		Point tip = latPoints.get(latPoints.size() - 1);
                		Point connection = connections.get(ID);
                	
                		//computing line coefficients
                		double[] coeffs = getCoefficients(tip, connection);
                		//generating predicted Y values along the line
                		ArrayList<Double> predictedY = fillLateralRoot(coeffs, latPoints);
                	
                		//compute rmse
                		double totalError = 0.0;
                		for (int i = 0; i < latPoints.size(); i++) {
                			double actualY = latPoints.get(i).q;
                			double bestY = predictedY.get(i);
                			double diff = bestY - actualY;
                			totalError += diff * diff;
                		}
                	
                		//root mean square error
                		//low rmse = close to actual, high = far from actual
                		double rmse = Math.sqrt(totalError / latPoints.size());
                		totalRMSE += rmse;
                		rootCount++;
                		System.out.printf("Lat Root: %s | RMSE: %.4f%n", ID, rmse);
                	}
                
                	double avgRMSE;
                	if (rootCount > 0) {
                		avgRMSE = totalRMSE / rootCount;
                	}
                	else {
                		avgRMSE = 0.0;
                	}
                
                	double wiringCost = result.totalWiringCost;
                	double conductionDelay = result.totalConductionDelay;
                
                	writer.write(String.format(Locale.US, "%.2f,%.4f,%.4f,%.4f\n", alpha, wiringCost, conductionDelay, avgRMSE));
                
                	if (avgRMSE < minRMSE) {
                		minRMSE = avgRMSE;
                		bestAlpha = alpha;
                		bestWiringCost = wiringCost;
                		bestConductionDelay = conductionDelay;
                	}
                }
                writer.write(String.format(Locale.US, "BEST,%.4f,%.4f,%.4f\n", bestWiringCost, bestConductionDelay, minRMSE));
                System.out.printf("Best alpha for %s: %.2f (RMSE=%.4f)\n", file.getName(), bestAlpha, minRMSE);
                
            }
        }
    }

	//fills a list of predicted y-values using a line defined by a given slope & intercept
    private static ArrayList<Double> fillLateralRoot(double[] coeffs, List<Point> points) {
        ArrayList<Double> optY = new ArrayList<>();
        double m = coeffs[0];
        double b = coeffs[1];

        for(Point point : points) {
            double y = (m * point.p + b);
            optY.add(y);
		}
        return optY;
    }
    
    //computes the slope and y-int of the line through the tip & connection point
    private static double[] getCoefficients(Point tip, Point connection) {
        double[] coeffs = new double[2];
        double x1 = tip.p;
        double y1 = tip.q;

        double x2 = connection.p;
        double y2 = connection.q;
        
        double m = 0.0;
        if (x1 == x2) {
        	m = 0;
        }
        else {
        	m = (y2 - y1) / (x2 - x1);
        }
        
        double b = y1 - m * x1;

        coeffs[0] = m;
        coeffs[1] = b;
        return coeffs;
    }
}