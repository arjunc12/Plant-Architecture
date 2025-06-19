import java.io.*;
import java.util.*;

//builds an arbor from a file
public class ArborBuild {
    public static Arbor buildArborFile (String filename) throws IOException {
        
        Arbor arbor = new Arbor();

		try (BufferedReader reader = new BufferedReader(new FileReader(filename))) {
			String line;
			String currentID = null;
			
			while ((line = reader.readLine()) != null) {
				//encountering lateral root ID
				line = line.trim();
				if(line.isEmpty()) {
					continue;
				}
				
				//switching to main root 
				if (line.toLowerCase().contains("main root")) {
					currentID = null;
				}
				
				else if (line.contains("-") && line.split(",").length <= 1) {
					currentID = line.replace(",", "").trim();
					System.out.println("Switched to lateral root: " + currentID);
				}
				else {
					String[] tokens = line.split(",");
					//checking that p/q are present and initializing them
					if (tokens.length == 2) {
						double p = Double.parseDouble(tokens[0].trim());
        				double q = Double.parseDouble(tokens[1].trim());
        				Point point = new Point(p, q);
        			
        				//adding lat root
        				if (currentID != null) {
        					arbor.addLatRoots(currentID, point);
        					System.out.println("Added to " + currentID + ": " + point);
        				}
        				else {
        					arbor.addMainRoot(point);
        					System.out.println("Added to main root: " + point);
        				}
					}
				}
			}
		}
		return arbor;	
	}
}