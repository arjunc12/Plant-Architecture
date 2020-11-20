import pandas as pd
import pylab
from constants import STATISTICS_DIR, PLOTS_DIR, METADATA_DIR, SCORING_DATA_DIR
import seaborn as sns
import pingouin as pg

IDEOTYPES = {'T' : 'Telephone', 'dT' : 'Droopy Telephone', 'C' : 'Christmas Tree', 'B' : 'Broomstick'}

sns.set()

sns.set()

def get_dfs():
    pareto_front_df = pd.read_csv('%s/arbor_stats.csv' % STATISTICS_DIR, skipinitialspace=True)
    metadata_df = pd.read_csv('%s/metadata.csv' % METADATA_DIR, skipinitialspace=True)

    ideotypes_df = pd.read_csv('%s/manual-scoring-last-day.csv' % SCORING_DATA_DIR, skipinitialspace=True)
    ideotypes_df['ideotype'] = ideotypes_df['ideotype (T/C/B)'].map(IDEOTYPES)

    return pareto_front_df, metadata_df, ideotypes_df

def alphas_hist(df, hue='condition'):
    pylab.figure()
    sns.histplot(df, x='pareto front location', hue=hue, stat="probability")
    pylab.ylim(0, 1)
    pylab.tight_layout()
    pylab.savefig('%s/alpha_hist.pdf' % PLOTS_DIR, format='pdf')
    pylab.close()

def alpha_distribution_plot(df):
    pylab.figure()
    sns.boxenplot(x='ideotype', y='pareto front location', hue='condition', data=df)
    pylab.tight_layout()
    pylab.savefig('%s/alpha_distribution.pdf' % PLOTS_DIR, format='pdf')
    pylab.close()

def last_day_df(df):
    return df.sort_values('day', ascending=False).drop_duplicates(['experiment', 'genotype', 'replicate', 'condition'])

def alpha_time_plot(df):
    pylab.figure()
    ax = pylab.gca()
    for name, group in df.groupby(['genotype', 'replicate']):
        pass
        #sns.lineplot(x='day', y='pareto front location', hue='condition', data=group, ax=ax, dashes=True, markers=False, legend=False)

    sns.lineplot(x="day", y="pareto front location", hue="condition", data=df, ax=ax)

    pylab.tight_layout()
    pylab.savefig('%s/alpha_time_plot.pdf' % PLOTS_DIR, format='pdf')
    pylab.close()

def alpha_anova(df):
    print(pg.welch_anova(data=df, dv='pareto front location', between='ideotype'))

def main():
    pareto_front_df, metadata_df, ideotypes_df = get_dfs()
    arbor_stats_df = pd.merge(pareto_front_df, metadata_df)

    last_day_arbors = last_day_df(arbor_stats_df)
    arbor_ideotypes = pd.merge(last_day_arbors, ideotypes_df)
    alpha_distribution_plot(arbor_ideotypes)

    alpha_time_plot(arbor_stats_df)

if __name__ == '__main__':
    main()