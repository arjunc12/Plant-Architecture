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