# Plant-Architecture
Studying whether plants grow in a Pareto-optimal manner

Authors: Magdalena Julkowska and Arjun Chandrasekhar

Data pipeline: 

1. Clean root data
- replace '-' with '_' in the 'root_name' column
- put all data in the 'root_name' column into 'genotype_replicate_condition_hormone' format

2. Check for nodes mistakenly marked as lateral roots
- `rm -f data/metadata/metadata.csv`
- `python write_metadata.py`
   
3. `python write_architecture_files.py ...`
- This turns the spreadsheet data into a list of architecture files
- command line arguments are the list of spreadsheets to create architecture files for

4. `python read_arbor_reconstruction.py ...`
- This verifies that all of the arbors that we created are valid trees (connected w/ no cycles)
- command line argument is the hormone to search for. This argument is optional

5. `python analyze_arbors.py --analyze`
- computes the pareto front for the new arbors

6. `python analyze_arbors.py --scaling`
- computes the scaling pareto front for the new arbors


SETUP:  
`pip install numpy`  
`pip install networkx`  
`pip install scipy`  
`pip install matplotlib`  
`pip install pandas`  
`pip install seaborn`  
`pip install pyarrow`  
`pip install pingouin`  

folders to create:  
figs - plots  
in data:  
architecture-data - raw-data  
architecture-data - arbor-reconstructions  
metadata  
results - pareto-fronts  
results - statistics  
