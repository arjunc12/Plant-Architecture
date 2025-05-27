import java.io.File;
import java.io.*;
import java.util.*;

//instructions:
//read through arbor file
//create arbor class that stores the main root and lateral roots
//maybe a main root class and a lateral root class
//write the code to initialize an arbor from the arbor file
//write the code to (for a given value of alpha) find the best place to connect a lateral root tie to the main root

public class Arbor {
    
    private Point mainRoot;
    private List<Point> lateralRoots;
    
    public static void main(String[] args) throws FileNotFoundException {
    	System.out.println("Running Arbor Build...");
    	Arbor arbor = buildArborFile("005_3_S_day5.csv");
    }
    
    //constructor
    public Arbor(Point mainRoot) {
        this.mainRoot = mainRoot;
        this.lateralRoots = new ArrayList<Point>();
    }
	
	//method to map lateral roots
    public void addLatRoots(Point latRoot)
    {
        lateralRoots.add(latRoot);
    }
	
	//method to map main root
    public Point getMainRoot() {
        return mainRoot;
    }

    public List<Point> getLateralRoots() {
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
    
    public double thetaTo(Point mainRoot) {
    	double[] delta = deltaTo(mainRoot);
    	return Math.atan2(delta[1], delta[0]);
    }
    
}

class ArborBuild {
    //create a way to sift through all the files
    public static Arbor buildArborFile (String filename) throws FileNotFoundException {
        Arbor arbor = null;
        return null;
    }
}