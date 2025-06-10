import java.io.File;
import java.io.*;
import java.util.*;

//instructions1:
//read through arbor file
//create arbor class that stores the main root and lateral roots
//maybe a main root class and a lateral root class
//write the code to initialize an arbor from the arbor file
//write the code to (for a given value of alpha) find the best place to connect a lateral root tie to the main root

//instructions2:
//alpha value is not supposed to be randomly generated
//store all results for alpha values 0.0-1.0 to 2 decimal places. 
//create a file with the names of the arbors in data/results/hetereogeneous_pareto_fronts
//this file should have three columns under the name of each arbor: alpha, wiring cost, and conduction delay


//stores the main root and lateral roots
public class Arbor {
    
    private List<Point> mainRoot;
    private Map<String, List<Point>> lateralRoots;
    
    //builds arbor from a file
    public static void main(String[] args) throws FileNotFoundException {
    	System.out.println("Arbor Data Files: ");
    	
    	//objects that tell program where to find arbor files & lists them
    	File folder = new File("data/architecture-data/arbor-reconstructions");
    	File[] files = folder.listFiles();
    	
    	//prints each file name
    	for (File file : files) {
    		System.out.println(file.getName());
    	}
    	
    	//gathers user input
    	Scanner scanner = new Scanner(System.in);
    	System.out.println("Enter the name of the file you want to use: ");
    	String fileName = scanner.nextLine().trim();
    	
    	//holds user selected file
    	File selectedFile = new File(folder, fileName);
    	
    	//accounting for typing errors
		if(!selectedFile.exists()) {
			System.out.println(" File " + fileName + " wasn't found. Did you type it correctly?");
			return;
		}
		
		System.out.println("Running Arbor Build Using File: " + fileName + ". . .");
		Arbor arbor = ArborBuild.buildArborFile(selectedFile.getPath());
    	
    	//generating random alpha
    	double alpha = Math.random();
    	//printing alpha value
    	System.out.println("Alpha value generated: " + alpha);
    	
    	//stores best connection for each lat root
    	Map<String, Point> connections = BestArbor.findBestConnection(arbor, alpha);
    	
    	//loops through lat roots to find best connection
    	for (String ID : connections.keySet()) {
    		Point p = connections.get(ID);
    		System.out.println("Best connection for " + ID + " is at (" + p.p + ", " + p.q + ")");
    	}
    }
    
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
}