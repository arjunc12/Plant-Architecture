import java.io.File;
import java.io.*;
import java.util.*;

//finds best place to connect a lateral root the the main root
public class BestArbor {
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
				
				//creating vector representing last direction of lat root
				Point lastLat = latPoints.get(latPoints.size() - 2);
				double dx1 = tip.p - lastLat.p;
				double dy1 = tip.q - lastLat.q;
				
				//vector from tip to main root
				double dx2 = mainPoint.p - tip.p;
				double dy2 = mainPoint.q - tip.q;
				
				//computing the angle between the two vectors
				double dot = dx1 * dx2 + dy1 * dy2;
				double mag1 = Math.sqrt(dx1 * dx1 + dy1 * dy1);
				double mag2 = Math.sqrt(dx2 * dx2 + dy2 * dy2);
				
				double angleDiff = Math.acos(dot / (mag1 * mag2));
				
				//combines two previous values to calculate the cost
				double cost = (1 - alpha) * distance + alpha * angleDiff;
				
				System.out.println("lat root: " + latID + ", main root point: (" + mainPoint.p + ", " + mainPoint.q + "), cost: " + cost + ", alpha: " + alpha);
				
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