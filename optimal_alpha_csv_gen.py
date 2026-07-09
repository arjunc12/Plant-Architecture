import sys
import csv
from constants import EVALUATED_COSTS_DIR
from pathlib import Path

# get all generated files in gravitropism_pareto_fronts
def extract_optimal_dist_vals(fname):
    '''
    Reads through a generated CSV in the gravitropism_pareto_fronts folder, which contains evaluated costs for 
    each arbor, and extracts information related to the minimum squared orthogonal distance in the file for each 
    computation method.  

    '''

    # go through all CSVs in the gravitropism_pareto_fronts folder
    #with open('%s/%s' % (EVALUATED_COSTS_DIR, fname)) as f:
    with open(fname) as f:
        arbor_csv = csv.reader(f)
        next(arbor_csv)
        csv_lines = []

        homog_opt_info = []
        homog_opt_sq_orthog_dist = float('inf')

        heterog_opt_info = []
        heterog_opt_sq_orthog_dist = float('inf')

        for line in arbor_csv:

            csv_lines.append(line)

            cost_method = line[1]
            # checking if the current squared orthogonal distance is the smallest
            sq_orthog = float(line[-1].strip())

            if cost_method == ' homogeneous':
                 if sq_orthog != 0 and sq_orthog < homog_opt_sq_orthog_dist:  # skipping the sq. orthogonal distance at the observed arbor values
                    homog_opt_info = [fname, line[1], line[2], line[3], line[-1]] # extracting cost method, G, alpha, and sq. orthogonal distance
                    homog_opt_sq_orthog_dist = sq_orthog
            else:
                if sq_orthog != 0 and sq_orthog < heterog_opt_sq_orthog_dist:
                    heterog_opt_info = [fname, line[1], line[2], line[3], line[-1]]
                    heterog_opt_sq_orthog_dist = sq_orthog
            

        print(f"HOMOGENEOUS Info related to optimal orthog: {homog_opt_info}")
        print(f"HETEROGENEOUS Info related to optimal orthog: {heterog_opt_info}")

        return homog_opt_info, heterog_opt_info


def construct_CSV(arbor_folder):
        folder = Path(arbor_folder)
        csv_content = [["arbor", "cost method", "G", "alpha", "total squared orthogonal distance"]]

        for arbor_file in folder.glob("*.csv"):
            print(f"This is arbor file: {arbor_file}")
            homog_opt_info, heterog_opt_info = extract_optimal_dist_vals(arbor_file)
            csv_content.append(homog_opt_info)
            csv_content.append(heterog_opt_info)
        
        print(csv_content)

        with open("data/results/heterogeneous_results", "w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(csv_content)


def main():
    print("Compiling all optimal heterogeneous/homogeneous alpha values...\n")
    #construct_CSV(EVALUATED_COSTS_DIR)
    construct_CSV("data/results/hetero_and_homogeneous")
    print("\nDone.")

if __name__ == '__main__':
    
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
    