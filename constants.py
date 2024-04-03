import numpy as np

DATA_DIR = 'data'
ARCHITECTURE_DIR = '%s/architecture-data' % DATA_DIR

RAW_DATA_DIR = '%s/raw-data' % ARCHITECTURE_DIR
ORIGINAL_ROOT_NODES_DIR = '%s/root-nodes-original' % RAW_DATA_DIR
CLEANED_ROOT_NODES_DIR = '%s/root-nodes-cleaned' % RAW_DATA_DIR  #data/architecture-data/raw-data/root-nodes-cleaned

RECONSTRUCTIONS_DIR = '%s/arbor-reconstructions' % ARCHITECTURE_DIR #data/architecture-data/arbor-reconstructions

METADATA_DIR = '%s/metadata' % DATA_DIR

RESULTS_DIR = '%s/results' % DATA_DIR
PARETO_FRONTS_DIR = '%s/pareto-fronts' % RESULTS_DIR
STATISTICS_DIR = '%s/statistics' % RESULTS_DIR
NULL_MODELS_DIR = '%s/null-models' % RESULTS_DIR

FIGS_DIR = 'figs'
PLOTS_DIR = '%s/plots' % FIGS_DIR
NULL_MODELS_PLOTS_DIR = '%s/null-models-analysis' % PLOTS_DIR
LOCATION_ANALYSIS_PLOTS_DIR = '%s/pareto-front-location-analysis' % PLOTS_DIR 
DRAWINGS_DIR = '%s/drawings' % FIGS_DIR
ARBOR_DRAWINGS_DIR = '%s/arbors' % DRAWINGS_DIR
TOY_NETWORK_DRAWINGS_DIR = '%s/toy-network' % DRAWINGS_DIR
FRONT_DRAWINGS_DIR = '%s/pareto-front-drawings' % DRAWINGS_DIR

PARETO_FRONT_DELTA = 0.01
DEFAULT_ALPHAS = np.arange(0, 1 + PARETO_FRONT_DELTA, PARETO_FRONT_DELTA)

SCORING_DATA_DIR = '%s/scoring-data' % DATA_DIR

#list of all needed directories for processing a single arbor reconstruction file
NECESSARY_DIR_LIST = [RECONSTRUCTIONS_DIR, PARETO_FRONTS_DIR, STATISTICS_DIR, NULL_MODELS_DIR, FRONT_DRAWINGS_DIR]