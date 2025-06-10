import java.io.File;
import java.io.*;
import java.util.*;

//builds an arbor from a file
public class ArborBuild {
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