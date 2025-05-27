import java.io.*;
import java.util.*;

//instructions:
//read through arbor file <- note to self: unsure which file to read from
//create arbor class that stores the main root and lateral roots
//maybe a main root class and a lateral root class
//write the code to initialize an arbor from the arbor file
//write the code to (for a given value of alpha) find the best place to connect a lateral root tie to the main root

public class Arbor {
    private String mainRoot;
    private List<String> lateralRoots;
    
    //constructor
    public Arbor (String mainRoot, List<String> lateralRoots) {
        this.mainRoot = mainRoot;
        this.lateralRoots = new ArrayList<String>();
    }

    public AddLatRoots (String lateralRoot)
    {
        lateralRoots.add(lateralRoot);
    }

    public String getMainRoot() {
        return mainRoot;
    }

    public List<String> getLateralRoots(); {
        return lateralRoots;
    }
}

public static class ArborBuild {
    //not sure which file to pull from
    public static Arbor buildArborFile (String filename) {
        Arbor arbor = null;
        try { 
            Scanner scanner = new Scanner(new File(filename));
            //unsure what format of file is, so cant scan right now
        }
        catch (FileNotFoundException e) {
            throw new FileNotFoundException();
        }
        return arbor;
    }
}

//know the points are formatted x, y
public class Point {
    public double x;
    public double y;

    //constructor
    public Point (double x, double y) {
        this.x = x;
        this.y = y;
    }

    //need to calculate the distance of a specific point to the lat and main root
    public double distanceTo(Point p) {
        double dx = x - p.x; //accessing the x coordinate of point p
        double dy = y - p.y; //same thing for y coordinate

        //using pythagorean theorem to calculate distance
        return Math.sqrt(dx * dx + dy * dy);
    }
}