# Plant-Architecture
Studying whether plants grow in a Pareto-optimal manner

## Overview

This repository contains code and analysis for understanding how wild tomato plants grow their root systems in response to environmental stresses. This work is fundamentally about **mechanistic interpretability** - reverse-engineering the computational "program" that determines root architecture from observable behavior.

## The Core Question

How do tomato plants decide where to grow roots? They have no central processor, no global view of their environment, yet they produce remarkably adaptive root architectures that optimize for water uptake, nutrient access, and stress resistance. This is a **distributed algorithm** problem: local growth decisions at individual root tips somehow coordinate to produce globally optimal structures.

## Publications

- Chandrasekhar, A. (2025). [Gottfried Green Tomatoes: Using Leibniz's Rule to Find the Roots of Tomato Plant Equations." *Mathematics Magazine*](https://doi.org/10.1080/0025570X.2024.2436481)

- Chandrasekhar, A. & Julkowska, M. (2022). [A mathematical framework for analyzing wild tomato root architecture. *Journal of Computational Biology*, 29(6), 711-727](https://doi.org/10.1089/cmb.2021.0593)

## Funding Acknowledgment

This work is supported by the National Science Foundation, Division of Mathematical Sciences, Mathematical Biology Program (Grant DMS-2220168).

## Contributors

Principal Investigators: Magdalena Julkowska and Arjun Chandrasekhar

Undergraduate researchers: 
- Kathryn Altman
- Alley Koenig
- Joanna Blatt
- Zekkie McCormick
- Aaron Garza
- Cassidy Shellberg
- Alyanna Martinez

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

7. `python plant_gravitropism.py ...`
- computes the pareto front arbors taking into account the effects of gravitropism and 
cost heterogeneity. Run `python plant_gravitropism.py -h` for a list of all options.


## SETUP:  
We recommend creating a dedicated Conda environment using the provided environment specification.

```bash
conda env create -f environment.yml
conda activate plant-architecture
```

If the environment already exists, it can be updated using

```bash
conda env update -f environment.yml --prune
```

### folders to create:  
figs - plots  
in data:  
architecture-data - raw-data  
architecture-data - arbor-reconstructions  
metadata  
results - pareto-fronts, gravitropism_pareto_fronts, statistics, null-models, gravitropism_results  