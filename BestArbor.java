import java.io.File;
import java.io.*;
import java.util.*;

//note to self: alpha of 0 favors the shortest direct connection to main root
//				alpha of 1 favors connections points closer to the firstPoint to reduce conduction delay
//				alpha 0.5 balances both 

//finds best place to connect a lateral root the the main root
public class BestArbor {
	public static Map<String, Point> findBestConnection(Arbor arbor, double alpha) {
		//creating a place to store the best connection points
		Map<String, Point> bestConnection = new LinkedHashMap<>();
		
		//getting main and lateral roots
		List<Point> mainRoot = arbor.getMainRoot();
		Map<String, List<Point>> lateralRoots = arbor.getLateralRoots();
		
		//computing cumulative distances along main root
		double[] cumulativeDistances = new double[mainRoot.size()];
		cumulativeDistances[0] = 0.0;
		for (int i = 1; i < mainRoot.size(); i++) {
			double dist = mainRoot.get(i).distanceTo(mainRoot.get(i - 1));
			cumulativeDistances[i] = cumulativeDistances[i - 1] + dist;
		}
		
		for (Map.Entry<String, List<Point>> entry : lateralRoots.entrySet()) {
			String latID = entry.getKey();
			List<Point> latPoints = entry.getValue();
			Point tip = latPoints.get(latPoints.size() - 1);
			
			double minCost = Double.MAX_VALUE;
			Point bestPoint = null;
	
			//looping through each segment of the main root
			for(int i = 0; i < mainRoot.size() - 1; i++) {
				Point p0 = mainRoot.get(i);
				Point p1 = mainRoot.get(i + 1);
				
				double dx = p1.p - p0.p;
				double dy = p1.q - p0.q;
				double segLen = Math.sqrt(dx * dx + dy * dy);
				
				//sample points along the segment
				for (double t = 0.0; t <= 1.0; t += 0.01) {
					//computes points using linear interpolation
					double px = p0.p + t * dx;
					double py = p0.q + t * dy;
					
					double wiringCost = Point.distance(px, py, tip.p, tip.q);
					double pathDistance = cumulativeDistances[i] + t * segLen;
					
					//closest main point -> sampled -> tip
					double conductionDelay = pathDistance + wiringCost;
					
					double cost = alpha * wiringCost + (1 - alpha) * conductionDelay;
					
					if (cost < minCost) {
						minCost = cost;
						bestPoint = new Point(px, py);
					}
				}
			}
			bestConnection.put(latID, bestPoint);
		}
		return bestConnection;
	}
	
	//helper method to compute path distance to any point along main root
	public static double getPathDistanceTo(List<Point> mainRoot, Point target) {
		double total = 0.0;
		for (int i = 0; i < mainRoot.size() - 1; i++)
		{
			Point p0 = mainRoot.get(i);
			Point p1 = mainRoot.get(i + 1);
			
			//checking if target lies of segment
			double dx = p1.p - p0.p;
			double dy = p1.q - p0.q;
			double segLen = Math.sqrt(dx * dx + dy * dy);
			
			//sample points along the segment
			for (double t = 0.0; t <= 1.0; t += 0.01) {
				//computes points using linear interpolation
				double px = p0.p + t * dx;
				double py = p0.q + t * dy;

				if (Math.abs(px - target.p) < 1e-4 && Math.abs(py - target.q) < 1e-4) {
					return total + t * segLen;
				}
			}
			total += segLen;
		}
		return total;
	}
}