import java.io.File;
import java.io.*;
import java.util.*;

public class pointDistance {

	private static void testBestConnections(Arbor arbor, double[] alphaValues) {
        for (double alpha = 0.0; alpha <= 1.0; alpha += 0.01) {
            //ensures num stability
            alpha = Math.round(alpha * 100.0) / 100.0;
            System.out.println("alpha value: " + alpha);
            
            //stores best connection for each lat root
            Map<String, Point> connections = BestArbor.findBestConnection(arbor, alpha);
            
            double totalWiring = 0.0;
            double totalDelay = 0.0;
            
            for (String ID : connections.keySet()) {
            	List<Point> latPoints = arbor.getLateralRoots().get(ID);
            	Point tip = latPoints.get(latPoints.size() - 1);
            	Point conn = connections.get(ID);
            
            	double wiringCost = tip.distanceTo(conn);
            	double conductionDelay = BestArbor.getPathDistanceTo(arbor.getMainRoot(), conn) + wiringCost;
            
            	totalWiring += wiringCost;
            	totalDelay += conductionDelay;
            
            	System.out.println("Lateral Root: " + ID);
            	System.out.println("		Best connection: (" + String.format("%.4f", conn.p) + ", " + String.format("%.4f", conn.q) + ")");
            	System.out.println("		Wiring cost: " + String.format("%.4f", wiringCost));
            	System.out.println("		Conduction delay: " + String.format("%.4f", conductionDelay));
            }
            
        	//rounding to 2 decimal places
        	String alphaStr = String.format("%.2f", alpha);
        	String wiringStr = String.format("%.4f", totalWiring);
        	String delayStr = String.format("%.4f", totalDelay);
        }
    }
}