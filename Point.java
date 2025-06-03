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