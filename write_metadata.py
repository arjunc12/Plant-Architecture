import os
import utils
import pandas as pd
pd.set_option('display.max_rows', 500)
from constants import CLEANED_ROOT_NODES_DIR, METADATA_DIR
import os
import sys

def check_df(df):
    def num_root_items(root_name):
        return len(root_name.split('_'))

    df['root items'] = df['root_name'].apply(num_root_items)
    df = df[df['root items'] < 3]
    if len(df.index) > 0:
        print(df[['root_name', 'root_order', 'root items']])
        sys.exit(1)

def write_metadata(tracing_fname, output_fname):
    tracing_fname_items = tracing_fname.split('/')
    relative_fname = tracing_fname_items[-1]
    experiment = utils.get_experiment(relative_fname)

    df = pd.read_csv(tracing_fname, skipinitialspace=True)
    df = df[df['root_order'] == 0]
    df = df[['image', 'root_name', 'root_order']]
    df.drop_duplicates(inplace=True)

    check_df(df)

    first_time = not os.path.exists(output_fname)

    with open(output_fname, 'a') as f:
        if first_time:
            f.write('experiment, arbor name, day, Picture #, genotype, replicate, condition\n')

        for image, root_name in zip(df['image'], df['root_name']):
            day, picture_num = utils.image_metadata(image)
            genotype, replicate, condition = utils.root_name_metadata(root_name)

            arbor = utils.arbor_name(image, root_name)

            f.write('%s, %s, %s, %s, %s, %s, %s\n' % (experiment, arbor, day, picture_num, genotype, replicate, condition))

def main():
    output_fname = '%s/%s' % (METADATA_DIR, 'metadata.csv')
    for fname in os.listdir(CLEANED_ROOT_NODES_DIR):
        if 'Root_Nodes' in fname and fname.endswith('.csv'):
            raw_data_fname = '%s/%s' % (CLEANED_ROOT_NODES_DIR, fname)
            print(raw_data_fname)
            write_metadata(raw_data_fname, output_fname)

if __name__ == '__main__':
    main()
