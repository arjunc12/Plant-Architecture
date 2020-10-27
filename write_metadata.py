import os
import utils
import pandas as pd
from constants import RAW_DATA_DIR, METADATA_DIR
import os

def write_metadata(tracing_fname, output_fname):
    df = pd.read_csv(tracing_fname, skipinitialspace=True)
    df = df[df['root_order'] == 0]
    df = df[['image', 'root_name', 'root_order']]
    df.drop_duplicates(inplace=True)

    first_time = os.path.exists(output_fname)

    with open(output_fname, 'a') as f:
        if first_time:
            f.write('arbor name, day, Picture #, genotype, replicate, condition\n')

        for image, root_name in zip(df['image'], df['root_name']):
            day, picture_num = utils.image_metadata(image)
            genotype, replicate, condition = utils.root_name_metadata(root_name)

            arbor = utils.arbor_name(image, root_name)

            f.write('%s, %s, %s, %s, %s, %s\n' % (arbor, day, picture_num, genotype, replicate, condition))

def main():
    output_fname = '%s/%s' % (METADATA_DIR, 'metadata.csv')
    for fname in os.listdir(RAW_DATA_DIR):
        if 'full-tracing' in fname and fname.endswith('.csv'):
            raw_data_fname = '%s/%s' % (RAW_DATA_DIR, fname)
            write_metadata(raw_data_fname, output_fname)

if __name__ == '__main__':
    main()
