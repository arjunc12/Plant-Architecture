import java.io.File;
import java.io.*;
import java.util.*;

//class representing a 2D point
public class Point {
    public double p; //x coord
    public double q; // y coord

    //constructor
    public Point (double p, double q) {
        this.p = p;
        this.q = q;
    }
        
    //need to calculate the distance of a specific point to main root
    //standard case- distance to another point
    public double distanceTo(Point other) {
		double dx = this.p - other.p;
		double dy = this.q - other.q;
		return Math.sqrt(dx * dx + dy * dy);
    }
    
    //avoids creating Point- distance to raw coords (for calculations)
    public double distanceTo(double x, double y) {
    	double dx = this.p - x;
    	double dy = this.q - y;
    	return Math.sqrt(dx * dx + dy * dy);
    }
    
    public static double distance(double x1, double y1, double x2, double y2) {
    	double dx = x1 - x2;
    	double dy = y1 - y2;
    	return Math.sqrt(dx * dx + dy * dy);
    }
    
    public String toString() {
    	return "(" + p + ", " + q + ")";
    }
}