import pandas as pd
import pylab
from constants import *
import seaborn as sns

sns.set()

def get_dfs():
    pareto_front_stats = pd.read_csv('%s/arbor_stats.csv' % STATISTICS_DIR, skipinitialspace=True)

    return pareto_front_stats

def alphas_hist(df):
    pylab.figure()
    sns.histplot(df, x='pareto front location', stat="probability")
    pylab.ylim(0, 1)
    pylab.tight_layout()
    pylab.savefig('%s/alpha_hist.pdf' % PLOTS_DIR, format='pdf')
    pylab.close()

def main():
    pareto_front_stats = get_dfs()
    alphas_hist(pareto_front_stats)

if __name__ == '__main__':
    main()