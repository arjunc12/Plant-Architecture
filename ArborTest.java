import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.*;

//instructions (complete):
//create a test data set based on the chalk board picture
//use this data set to find the best connection point for alpha 0.0, 0.5, and 1.0

//uses test data to make sure the output of Arbor.java is correct

public class ArborTest {
	 public static void main(String[] args) throws IOException {
	 	//gathers user input
	 	Scanner scanner = new Scanner(System.in);
	 	System.out.print("Enter file name:");
    	String testFileName = scanner.nextLine().trim();
    	
    	//objects that tell program where to find arbor files & lists them
    	File folder = new File("data/architecture-data/arbor-reconstructions");
    	File selectedFile = new File(folder, testFileName);
    	
    	if (!selectedFile.exists()) {
    		System.out.println("File not found: " + selectedFile.getPath());
    		return;
    	}
    	
    	System.out.println("Running Arbor Build on: " + testFileName);
    	Arbor arbor = ArborBuild.buildArborFile(selectedFile.getPath());
    	
 		//print best connection points at alpha values
 		System.out.println("=== best connection points for alpha values ===");
 		testBestConnections(arbor, new double[] {0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0});
		
		//sweep alpha and printing wiring cost/conduction delay
		System.out.println("\n=== alpha sweep: wiring cost & conduction delay ===");
		testAlphaSweep(arbor, testFileName);

    }
    
    private static void testBestConnections(Arbor arbor, double[] alphaValues) {
    	for (double alpha : alphaValues) {
    		System.out.println("alpha value: " + alpha);
    		//stores best connection for each lat root
    		Map<String, Point> connections = BestArbor.findBestConnection(arbor, alpha);
    		
    		//loops through lat roots to find best connection
    		for (String ID : connections.keySet()) {
    			Point tip = arbor.getLateralRoots().get(ID).getLast();
    			Point conn = connections.get(ID);
    			double wiring = tip.distanceTo(conn);
    			double delay = BestArbor.getPathDistanceTo(arbor.getMainRoot(), conn) + conn.distanceTo(tip);
    			
    			System.out.println("Lateral Root: " + ID);
    			System.out.println("		Best connection: (" + String.format("%.4f", conn.p) + ", " + String.format("%.4f", conn.q) + ")");
    			System.out.println("		Wiring cost: " + String.format("%.4f", wiring));
    			System.out.println("		Conduction delay: " + String.format("%.4f", delay));
    		}
    	}
    }
    
    private static void testAlphaSweep(Arbor arbor, String fileNameBase) throws IOException {
    	File resultFile = new File("data/results/test-results-" + fileNameBase + ".csv");
    	
    	//making sure directory exists
    	resultFile.getParentFile().mkdirs();
    	
    	try (FileWriter writer = new FileWriter(resultFile)) {
    		writer.write("alpha, wiring cost, conduction_delay\n");
    		
    		for (double alpha = 0.0; alpha <= 1.0; alpha += 0.01) {
    			alpha = Math.round(alpha * 100.0) / 100.0;
    			
    			Map<String, Point> connections = BestArbor.findBestConnection(arbor, alpha);
    			double totalWiring = 0.0;
    			double totalDelay = 0.0;
    			
    			for (String ID : connections.keySet()) {
    				Point tip = arbor.getLateralRoots().get(ID).getLast();
    				Point conn = connections.get(ID);
    				
    				double wiringCost = tip.distanceTo(conn);
    				double conductionDelay = BestArbor.getPathDistanceTo(arbor.getMainRoot(), conn) + conn.distanceTo(tip);
    				
    				totalWiring += wiringCost;
    				totalDelay += conductionDelay;
    			}
    			writer.write(String.format("%.2f, %.4f, %4f\n", alpha, totalWiring, totalDelay));	
    		}
    	}
    	System.out.println("wiring/delay results written to: " + resultFile.getPath());
    }
}