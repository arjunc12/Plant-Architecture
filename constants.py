import numpy as np

DATA_DIR = 'data'
ARCHITECTURE_DIR = '%s/architecture-data' % DATA_DIR
RAW_DATA_DIR = '%s/raw-data' % ARCHITECTURE_DIR
RECONSTRUCTIONS_DIR = '%s/arbor-reconstructions' % ARCHITECTURE_DIR
METADATA_DIR = '%s/metadata' % DATA_DIR

RESULTS_DIR = '%s/results' % DATA_DIR
PARETO_FRONTS_DIR = '%s/pareto-fronts' % RESULTS_DIR
STATISTICS_DIR = '%s/statistics' % RESULTS_DIR

FIGS_DIR = 'figs'
DRAWINGS_DIR = '%s/drawings' % FIGS_DIR
PLOTS_DIR = '%s/plots' % FIGS_DIR

PARETO_FRONT_DELTA = 0.01
DEFAULT_ALPHAS = np.arange(0, 1 + PARETO_FRONT_DELTA, PARETO_FRONT_DELTA)

