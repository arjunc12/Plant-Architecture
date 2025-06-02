import java.io.File;
import java.io.*;
import java.util.*;

//instructions:
//read through arbor file
//create arbor class that stores the main root and lateral roots
//maybe a main root class and a lateral root class
//write the code to initialize an arbor from the arbor file
//write the code to (for a given value of alpha) find the best place to connect a lateral root tie to the main root

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

//class representing a 2D point
class Point {
    public double p; //x coord
    public double q; // y coord

    //constructor
    public Point (double p, double q) {
        this.p = p;
        this.q = q;
    }
    
    //helper method for delta between two points
    public double[] deltaTo(Point mainRoot) {
    	double dp = this.p - mainRoot.p; //accessing the x coordinate of point p
    	double dq = this.q - mainRoot.q; //same thing for y coordinate
    	return new double[] {dp, dq};
    }
        
    //need to calculate the distance of a specific point to the lat and main root
    public double distanceTo(Point mainRoot) {
    	double[] delta = deltaTo(mainRoot);
		//using pythagorean theorem to calculate distance
		return Math.sqrt(delta[0] * delta[0] + delta[1] * delta[1]);
    }
    
    //returns the angle for the line connecting the points and the x axis
    public double thetaTo(Point mainRoot) {
    	double[] delta = deltaTo(mainRoot);
    	return Math.atan2(delta[1], delta[0]);
    }
    
}

//builds an arbor from a file
class ArborBuild {
    public static Arbor buildArborFile (String filename) throws FileNotFoundException {
        Scanner scanner = new Scanner(new File(filename));
        //separate coords based on comma
        //if scanner line has a dash, it is a lateral root (assuming the strings of letters/nums are IDS)
        Arbor arbor = new Arbor();
        
        //if main root, continue until lateral root is encountered
        boolean readingMain = true;
        //keeps track of sub roots
        String currentLatID = null;
        
        while (scanner.hasNextLine()) {
        	String line = scanner.nextLine().trim();
        	
        	//checking for sub root ID
        	if (line.contains("-")) {
        		currentLatID = line;
        	}
        	else
        	{
        		String[] tokens = line.split(",");
        		//checking that p and q are present and initializing the point
        		if (tokens.length == 2) {
        			double p = Double.parseDouble(tokens[0]);
        			double q = Double.parseDouble(tokens[1]);
        			Point point = new Point(p, q);
        			
        			//adding lat root
        			if (currentLatID != null) {
        				arbor.addLatRoots(currentLatID, point);
        			}
        			//adding main root
        			else {
        				arbor.addMainRoot(point);
        			}
        		}
        	}
        }
        return arbor;
    }
}

//finds best place to connect a lateral root the the main root
class BestArbor {
	public static Map<String, Point> findBestConnection(Arbor arbor, double alpha) {
		//creating a place to store the best connection points
		Map<String, Point> bestConnection = new LinkedHashMap<>();
		
		//getting main and lateral roots
		List<Point> mainRoot = arbor.getMainRoot();
		Map<String, List<Point>> lateralRoots = arbor.getLateralRoots();
		
		//looping through each lat root
		for (String latID : lateralRoots.keySet()) {
			//retrieving points of current lat root
			List<Point> latPoints = lateralRoots.get(latID);
			//getting last point of lat root
			Point tip = latPoints.get(latPoints.size() - 1);
			
			double minCost = Double.MAX_VALUE;
			Point bestPoint = null;
			
			//looping through main root
			for(Point mainPoint : mainRoot) {
				//computing the distance from the lat root start to the main root
				double distance = tip.distanceTo(mainPoint);
				//computing the angle difference
				double angleDiff = Math.abs(tip.thetaTo(mainPoint) - mainPoint.thetaTo(tip));
				//combines two previous values to calculate the cost
				double cost = distance + alpha * angleDiff;
				
				//updating the min cost to decide best point
				if (cost < minCost) {
					minCost = cost;
					bestPoint = mainPoint;				
				}
			}
			bestConnection.put(latID, bestPoint);
		}
		return bestConnection;
	}
}