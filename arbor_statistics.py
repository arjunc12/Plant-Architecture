import pandas as pd
import pylab
from constants import STATISTICS_DIR, PLOTS_DIR, METADATA_DIR
import seaborn as sns
sns.set()

sns.set()

def get_dfs():
    pareto_front_df = pd.read_csv('%s/arbor_stats.csv' % STATISTICS_DIR, skipinitialspace=True)
    metadata_df = pd.read_csv('%s/metadata.csv' % METADATA_DIR, skipinitialspace=True)
    return pareto_front_df, metadata_df

def alphas_hist(df):
    pylab.figure()
    sns.histplot(df, x='pareto front location', stat="probability")
    pylab.ylim(0, 1)
    pylab.tight_layout()
    pylab.savefig('%s/alpha_hist.pdf' % PLOTS_DIR, format='pdf')
    pylab.close()

def alpha_time_plot(pareto_front_df, metadata_df):
    df = pd.merge(pareto_front_df, metadata_df)
    pylab.figure()
    ax = pylab.gca()
    for name, group in df.groupby(['genotype', 'replicate']):
        if len(group['day'].unique()) < 3:
            continue
        sns.lineplot(x='day', y='pareto front location', hue='condition', data=group, ax=ax)
    pylab.tight_layout()
    pylab.savefig('%s/alpha_time_plot.pdf' % PLOTS_DIR, format='pdf')
    pylab.close()

def main():
    pareto_front_df, metadata_df = get_dfs()
    alpha_time_plot(pareto_front_df, metadata_df)

if __name__ == '__main__':
    main()