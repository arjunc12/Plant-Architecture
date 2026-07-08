import sys
import csv
from constants import EVALUATED_COSTS_DIR

# get all generated files in gravitropism_pareto_fronts
def extract_optimal_alpha_vals():
    '''
    Reads through all of the generated CSVs in the gravitropism_pareto_fronts folder, which contains evaluated costs for 
    each arbor, and extracts them. All of these values will be organized into a new CSV file. 

    '''

    # go through all CSVs in the gravitropism_pareto_fronts folder
    #with open('%s/%s' % (EVALUATED_COSTS_DIR, fname)) as f:
    with open('data/results/gravitropism_pareto_fronts/pimpi_ABA_D9_set1_day9_20220610_RSA_M248M058LA1511_ABA_Salt003_M248_8_C_10aba.csv') as f:
        arbor_csv = csv.reader(f)
        next(arbor_csv)
        csv_lines = []

        opt_info = []
        opt_sq_orthog_dist = float('inf')

        for line in arbor_csv:

            #line = line.strip('\n')
            #line = line.split(',')
            csv_lines.append(line)

            # checking if the current squared orthogonal distance is the smallest
        
            print(f"this is sq_orthog: {line[-1].strip()}")
            print(f"    and this is opt_sq_orthog_dist: {opt_sq_orthog_dist}")
            sq_orthog = float(line[-1].strip())

            # skipping the sq. orthogonal distance at the observed arbor values
            if sq_orthog != 0 and sq_orthog < opt_sq_orthog_dist:
                    opt_info = line[0:-1] # 
                    opt_sq_orthog_dist = sq_orthog
            '''
            try:
                print(f"this is sq_orthog: {line[-1].strip()}")
                sq_orthog = float(line[-1].strip())
            else:
                if sq_orthog != 0 and sq_orthog < opt_sq_orthog_dist:
                    opt_info = line
                    opt_sq_orthog_dist = line[-1]
            '''
        alpha_vals = [row[3] for row in csv_lines]
        #print(f"All lines: {csv_lines}\n")
        print(f"Extracted values: {alpha_vals}")
        print(f"Optimal squared orthogonal distance: {opt_sq_orthog_dist}")
        print(f"Info related to optimal orthog: {opt_info}")

        


def main():
    print("Compiling all optimal heterogeneous/homogeneous alpha values...")
    extract_optimal_alpha_vals()


if __name__ == '__main__':
    
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
    