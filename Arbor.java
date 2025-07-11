import java.io.File;
import java.io.FileWriter;
import java.io.*;
import java.util.*;

//instructions1 (complete):
//read through arbor file
//create arbor class that stores the main root and lateral roots
//maybe a main root class and a lateral root class
//write the code to initialize an arbor from the arbor file
//write the code to (for a given value of alpha) find the best place to connect a lateral root tie to the main root

//instructions2 (complete):
//alpha value is not supposed to be randomly generated
//store all results for alpha values 0.0-1.0 to 2 decimal places. 
//create a file with the names of the arbors in data/results/hetereogeneous_pareto_fronts
//this file should have three columns under the name of each arbor: alpha, wiring cost, and conduction delay


//stores the main root and lateral roots
public class Arbor {
    
    private List<Point> mainRoot;
    private Map<String, List<Point>> lateralRoots;
    
       
    //constructor
    public Arbor() {
        mainRoot = new ArrayList<>();
        lateralRoots = new LinkedHashMap<>();
    }
	
	//add main root coords
	public void addMainRoot(Point p) {
		mainRoot.add(p);
	}
	
	//adds lateral roots
    public void addLatRoots(String ID, Point p)
    {
        if (!lateralRoots.containsKey(ID)) {
        	lateralRoots.put(ID, new ArrayList<>());
        }
        lateralRoots.get(ID).add(p);
    }
	
	//accesses mainRoot
    public List<Point> getMainRoot() {
        return mainRoot;
    }
	
	//accesses lateral roots
    public Map<String, List<Point>> getLateralRoots() {
        return lateralRoots;
    }
    
    //builds arbor from a file
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
    		
    		System.out.println("Processing file: " + file.getName());
    		
    		Arbor arbor = ArborBuild.buildArborFile(file.getPath());
    		if (arbor.getMainRoot().isEmpty()) {
    			System.out.println("Skipping " + file.getName() + ": no main root data");
    			continue;
    		}
    		
    		writeResults(file.getName(), arbor, outputDir);
    	}
    }
    
    private static void writeResults(String fileName, Arbor arbor, File outputDir) throws IOException {
    	//creating output file
    	File outFile = new File(outputDir, fileName);
    	try (FileWriter writer = new FileWriter(outFile)) {
    		writer.write("alpha, wiring_cost, conduction_delay\n");
    			
    		Point firstPoint = arbor.getMainRoot().get(0);
    			
    		//looping alpha from 0.1 to 1.0 by 0.01
    		for (double alpha = 0.0; alpha <= 1.0; alpha += 0.01) {
    			//ensures num stability
    			alpha = Math.round(alpha * 100.0) / 100.0;
		
    			//stores best connection for each lat root
    			BestArbor.BestConnectionResult result = BestArbor.findBestConnection(arbor, alpha);
    			Map<String, Point> connections = result.connections;
    	
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
    			}
    			
				//rounding to 2 decimal places
    			String alphaStr = String.format("%.2f", alpha);
    			String wiringStr = String.format("%.4f", totalWiring);
    			String delayStr = String.format("%.4f", totalDelay);
    	
				writer.write(alphaStr + ", " + wiringStr + ", " + delayStr + "\n");
    		}
    	}
    	System.out.println("Results written to: " + outFile.getPath());
    }
}