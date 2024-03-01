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

* note: `pip install pandas` should also install `numpy`

New setup:  
oryx build  
pip install pingoiun  
python makeDir.py  
  
This should set up the basic environment and folders needed for the project.  

new new setup:  
`python makeDir.py`  
`pip install pipreqs`  
`pipreqs`  
`pip install -r requirements.txt`  

then make sure to put the file in arbor-reconstructions folder  
afterwards can run command  
`python automated_data_pipeline_single_file.py`  

folders to create:  
figs - plots  
in data:  
architecture-data - raw-data  
architecture-data - arbor-reconstructions  
metadata  
results - pareto-fronts  
results - statistics  
results - null-models  
  
pylab files:  
arbor_statistics.py  
utils.py    - contains draw_arbor function  
  
files that import utils:  
null_models.py  
read_arbor_reconstruction.py  
write_architecture_files.py  
write_metadata.py  
  
files with main:  
analyze_arbors.py  
```
'--analyze'
 '--scaling' 
``` 
- neither does any drawing  

arbor_statistics.py  
```
parser.add_argument('--histogram', action='store_true')
    parser.add_argument('--distribution', action='store_true')
    parser.add_argument('--time', action='store_true')
    parser.add_argument('--anova', action='store_true')
```
- unable to use: histogram, distribution, and anova since all depend on manually transcribed data  

clean_architecture_data.py  
```
    parser.add_argument('--incorrect', action='store_true')
    parser.add_argument('--image_order', action='store_true')
    parser.add_argument('--root_names', action='store_true')
    clean_data(parser.parse_args())
```

null_models.py  --  takes arguments --  

    '-a', '--analyze'
    '-w', '--write'
    if args.analyze:
        analyze_null_models()
    if args.write:
        write_null_models_file() 

- analyze calls `read_arbor_full` from `read_arbor_reconstruction`
- no drawing just file construction it looks like, makes a tree graph
- calls pareto_cost from pareto_functions.py
- write: just writes some files  

optimal_midpoint.py  -- seems to just be for testing of math  
pareto_functions.py   -seems to just run a set file that I do not have  
read_arbor_reconstruction.py  
write_architecture_files.py  
write_metadata.py  
  
pareto_functions:  
viz_front -- draws pareto front
viz_trees -- draws tree graphs for each 

Notes:  
Oryx-build-commands.txt seems to build the environment  
    https://github.com/microsoft/Oryx  
for codespace recomment python extension pack for extension to use  


data processing procedures:
python write_architecture_files.py <filename> creates files in architecture-reconstructions containing two columns first one titled "main root"

Skipped read_arbor_reconstructions step

For example input file, start here

`python analyze_arbors.py --analyze` creates files in pareto-fronts and one file in statistics, takes over 30min for the large file
When using the small file creates a single file in pareto-fronts containing the calculated fronts, creates the arbor_stats file in statistics folder

`python analyze_arbors.py --scaling` creates scaling_distances file in statistics and prints to screen all file names that it reads from

`python null_models.py -a` creates a null models file with random arbors for comparison

`python null_models.py -w` creates `models` file in statistics folder

`python pareto_functions.py` contains viz_front which creates a pareto front graph, and viz_trees which draws all the graph trees.

065_3_S_day2 - example input file (an arbor reconstruction)
