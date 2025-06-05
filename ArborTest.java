import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.*;

//create a test data set based on the chalk board picture
//use this data set to find the best connection point for alpha 0.0, 0.5, and 1.0

//uses test data to make sure the output of Arbor.java is correct
public class ArborTest {
	
	public static void main(String[] args) throws IOException {
		//creating temp test file
		File testFile = createTestData();
	
		//building arbor from file
		Arbor arbor = ArborBuild.buildArborFile(testFile.getPath());
		
		//trying alpha values 0, 0.5, and 1
		double[] alphas = {0.0, 0.5, 1.0};
		for (double alpha : alphas) {
			System.out.println("alpha: " + alpha);
			
			//finding best connection
			Map<String, Point> connections = BestArbor.findBestConnection(arbor, alpha);
			
			//printing connections
			for (String ID : connections.keySet()) {
				Point p = connections.get(ID);
				System.out.println("Best connection for " + ID + " is at (" + p.p + ", " + p.q + ")");
			}		
		}
	
		//delete temp file
		testFile.delete();	
	}
	
	//writes a small test file
	private static File createTestData() throws IOException {
		File file = new File("test_data.txt");
		FileWriter writer = new FileWriter(file);
		
		//main root points
		double[][] mainRoot = {
			{4.0, 1.0},
			{6.0, 5.0},
			{5.5, 8.0},
			{6.0, 11.0}
		};
		writePoints(writer, mainRoot);
		
		//lat root 1
		writer.write("Lat-1\n");
		double[][] lat1 = {
			{5.8, 6.2},
			{5.2, 6.8},
			{5.0, 8.0}, 
			{4.0, 9.0},
			{3.8, 12.0}
		};
		writePoints(writer, lat1);
		
		//lat root 2
		writer.write("Lat-2\n");
		double[][] lat2 = {
			{5.9, 5.5}, 
			{7.0, 7.0},
			{8.0, 7.5},
			{9.5, 9.8}
		};
		writePoints(writer, lat2);
		
		writer.close();
		return file;
	}
	
	//helper method that writes a list of points
	private static void writePoints(FileWriter writer, double[][] points) throws IOException {
		for (double[] point : points) {
			writer.write(point[0] + "," + point[1] + "\n");
		}
	}
}