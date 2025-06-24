import java.io.File;
import java.io.*;
import java.util.*;

public class pointDistance {
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
    		
    		// System.out.println("Processing file: " + file.getName());
    		
    		Arbor arbor = ArborBuild.buildArborFile(file.getPath());
    		if (arbor.getMainRoot().isEmpty()) {
    			System.out.println("Skipping " + file.getName() + ": no main root data");
    			continue;
    		}
            for (double alpha = 0.0; alpha <= 1.0; alpha += 0.01) {
                Map<String, Point> connections = bestArbor.findBestConnection(arbor, alpha);
                Map<String, ArrayList<Point>> points = getPoints(file);

	private static void testBestConnections(Arbor arbor, double[] alphaValues) {
                for(Point bestConnection : connections.values()) {
                    List<Point> latPoints = arbor.getLateralRoots().get(ID);
                    Point tip = latPoints.get(latPoints.size() - 1);

                    double[] coefficients = getCoefficients(tip, bestConnection);
                    ArrayList<Double> optimal_y = fillLateralRoot(cofficients, latPoints);

                    int i = 0;
                    double distance = 0.0;
                    for(double opt_y : optimal_y) {
                        double diff = 0.0;
                        diff = (opt_y - latPoints[i].q);
                        distance += (diff * diff);
                        i++;
                    }

                    

                    
                ///for(ArrayList<Point> bestPoints : points.values()) {
                  //  Point tip = points.size - 1;
                    
                
            }
    		// writeResults(file.getName(), arbor, outputDir);
    	}
    }
    public static Map<String, ArrayList<Point> getPoints (String filename) throws IOException {
        
        // Arbor arbor = new Arbor();
        Map<String, ArrayList<Point>> map = new HashMap<>();
        boolean firstTime = true
        ArrayList<Point> points 
		try (BufferedReader reader = new BufferedReader(new FileReader(filename))) {
			String line;
			String currentID = null;
			while ((line = reader.readLine()) != null) {
				//encountering lateral root ID
				line = line.trim();
				if(line.isEmpty()) {
					continue;
				}
				
				//switching to main root 
				if (line.toLowerCase().contains("main root")) {
					currentID = null;
				}
				
				else if (line.contains("-") && line.split(",").length <= 1) {
                    if(firstTime == true) {
                        ArrayList<Point> points;
                        firstTime == false
                    }
                    else {
                        map.put(currentID, points);
                        points.clear();
                        
					currentID = line.replace(",", "").trim();
					System.out.println("Switched to lateral root: " + currentID);
				}
				else {
					String[] tokens = line.split(",");
					//checking that p/q are present and initializing them
					if (tokens.length == 2) {
						double p = Double.parseDouble(tokens[0].trim());
        				double q = Double.parseDouble(tokens[1].trim());
        				Point point = new Point(p, q);
            			points.add(point)
        				//adding lat root
        				if (currentID != null) {
        					///arbor.addLatRoots(currentID, point);
                            points.put(currentID, point
        					System.out.println("Added to " + currentID + ": " + point);
        				}
        				///else {
        				///	arbor.addMainRoot(point);
        				///	System.out.println("Added to main root: " + point);
        				}
					}
				}
			}
		}
		return map;	
	}

    private static ArrayList<Double> fillLateralRoot(Double[] coeffs, List<Point> points) {
        ArrayList<Double> optimal_y = new ArrayList<Double>;
        double m = coeffs[0];
        double y_int = coeffs[1];
        
        double y_value = 0.0;
        for(Point point : points) {
            y_value = (m * point.p + y_int);
            optimal_y.add(y_value);

        return optimal_y
    }
    
    private static double[] getCoefficients(Point tip, Point connection) {
        double[] coeffs = new Array[2];
        double m = 0.0;
        double y_int = 0.0;
        
        double x1 = tip.p;
        double y1 = tip.q;

        double x2 = connection.p;
        double y2 = connection.q;

        m = ((y2 - y1) / (x2 - x1));
        y_int = (y1 - m * x1);

        coeffs[0] = m;
        coeffs[1] = y_int;
        return coeffs
    }
    private static void testBestConnections(Arbor arbor, double[] alphaValues) {
        for (double alpha = 0.0; alpha <= 1.0; alpha += 0.01) {
            //ensures num stability
            alpha = Math.round(alpha * 100.0) / 100.0;
            System.out.println("alpha value: " + alpha);
            
            //stores best connection for each lat root
            Map<String, Point> connections = BestArbor.findBestConnection(arbor, alpha);
            
            double totalWiring = 0.0;
            double totalDelay = 0.0;
            
            for (String ID : connections.keySet()) {
            	List<Point> latPoints = arbor.getLateralRoots().get(ID);
            	Point tip = latPoints.get(latPoints.size() - 1);
            	Point conn = connections.get(ID);
            
            	double wiringCost = tip.distanceTo(conn);
            	double conductionDelay = BestArbor.getPathDistanceTo(arbor.getMainRoot(), conn) + wiringCost;
            
            	totalWiring += wiringCost;
            	totalDelay += conductionDelay;
            
            	System.out.println("Lateral Root: " + ID);
            	System.out.println("		Best connection: (" + String.format("%.4f", conn.p) + ", " + String.format("%.4f", conn.q) + ")");
            	System.out.println("		Wiring cost: " + String.format("%.4f", wiringCost));
            	System.out.println("		Conduction delay: " + String.format("%.4f", conductionDelay));
            }
            
        	//rounding to 2 decimal places
        	String alphaStr = String.format("%.2f", alpha);
        	String wiringStr = String.format("%.4f", totalWiring);
        	String delayStr = String.format("%.4f", totalDelay);
        }
    }
}