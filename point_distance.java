import java.io.File;
import java.io.*;
import java.util.*;

public class PointDistance {
    public static void main(String[] args) throws IOException {
        //object that tells program where to find arbor files
    	File inputDir = new File("data/architecture-data/arbor-reconstructions");
    	//preparing result output 
    	File outputDir = new File("data/results/hetereogeneous_pareto_fronts");
    	outputDir.mkdirs();
    	
    	File[] files = inputDir.listFiles();
    	
    	for (File file : files) {
    		//skipping potential directories or non-files
    		if (!file.isFile()) {
    			continue;
    		}
    		
    		Arbor arbor = ArborBuild.buildArborFile(file.getPath());
    		if (arbor.getMainRoot().isEmpty()) {
    			System.out.println("Skipping " + file.getName() + ": no main root data");
    			continue;
    		}
    		
            for (double alpha = 0.0; alpha <= 1.0; alpha += 0.01) {
            	alpha = Math.round(alpha * 100.0) / 100.0;
            	System.out.println("---Alpha = " + alpha + "---");
            	
                Map<String, Point> bestConnections = bestArbor.findBestConnection(arbor, alpha);
                
                for (String ID : bestConnections.keySet()) {
                	List<Point> latPoints = arbor.getLateralRoots().get(ID);
                	
                	Point tip = latPoints.get(latPoints.size() - 1);
                	Point connection = bestConnections.get(ID);
                	
                	double[] coeffs = getCoefficients(tip, connection);
                	ArrayList<Double> predictedY = fillLateralRoot(coeffs, latPoints);
                	
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
                	System.out.println("Lat Root: " + ID + " | RMSE: " + String.format("%.4f", rmse));
                }
            }
        }
    }

    private static ArrayList<Double> fillLateralRoot(double[] coeffs, List<Point> points) {
        ArrayList<Double> optY = new ArrayList<>();
        double m = coeffs[0];
        double b = coeffs[1];

        for(Point point : points) {
            double y = (m * pt.p + b);
            optY.add(y);
		}
        return optY;
    }
    
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