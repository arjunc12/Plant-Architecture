import java.io.File;
import java.io.IOException;
import java.util.*;

//instructions (complete):
//create a test data set based on the chalk board picture
//use this data set to find the best connection point for alpha 0.0, 0.5, and 1.0

//uses test data to make sure the output of Arbor.java is correct

public class ArborTest {
	 public static void main(String[] args) throws IOException {
    	System.out.println("Arbor Data Files: ");
    	
    	//objects that tell program where to find arbor files & lists them
    	File folder = new File("data/architecture-data/arbor-reconstructions");
    	File[] files = folder.listFiles();
    	
    	//gathers user input
    	Scanner scanner = new Scanner(System.in);
    	System.out.println("Enter the name of the file you want to use: ");
    	String fileName = scanner.nextLine().trim();
    	
    	File selectedFile = new File(folder, fileName);
    	
    	//accounting for typing errors
		if(!selectedFile.exists()) {
			System.out.println(" File " + fileName + " wasn't found. Did you type it correctly?");
			return;
		}
		
		System.out.println("Running Arbor Build Using File: " + fileName + ". . .");
		Arbor arbor = ArborBuild.buildArborFile(selectedFile.getPath());
    	
    	testArbor(arbor, new double[] {0.0, 0.5, 1.0});
    }
    
    private static void testArbor(Arbor arbor, double[] alphaValues) {
    	for (double alpha : alphaValues) {
    		System.out.println("alpha value: " + alpha);
    		//stores best connection for each lat root
    		Map<String, Point> connections = BestArbor.findBestConnection(arbor, alpha);
    		
    		//loops through lat roots to find best connection
    		for (String ID : connections.keySet()) {
    			Point p = connections.get(ID);
    			System.out.println("Best connection for " + ID + " is at (" + p.p + ", " + p.q + ")");
    		}
    	}
    }
}