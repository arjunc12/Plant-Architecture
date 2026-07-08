import sys
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
        csv_lines = []

        for line in f:
            line = line.strip('\n')
            line = line.split(',')
            csv_lines.append(line)
        alpha_vals = [row[3] for row in csv_lines]
        print(f"All lines: {csv_lines}\n")
        print(f"Extracted values: {alpha_vals}")

           

    


def main():
    print("Compiling all optimal heterogeneous/homogeneous alpha values...")
    extract_optimal_alpha_vals()


if __name__ == '__main__':
    
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
    