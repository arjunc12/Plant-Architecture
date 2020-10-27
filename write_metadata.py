import os
import utils
import pandas as pd
from constants import RAW_DATA_DIR, METADATA_DIR

def write_metadata(tracing_fname, output_fname):
    df = pd.read_csv(tracing_fname, skipinitialspace=True)
    df = df[df['root_order'] == 0]
    df = df[['image', 'root_name', 'root_order']]
    df.drop_duplicates(inplace=True)

    with open(output_fname, 'w') as f:
        f.write('arbor name, day, Picture #, genotype, replicate, condition\n')

        for image, root_name in zip(df['image'], df['root_name']):
            day, picture_num = utils.image_metadata(image)
            genotype, replicate, condition = utils.root_name_metadata(root_name)

            arbor = utils.arbor_name(image, root_name)

            f.write('%s, %s, %s, %s, %s, %s\n' % (arbor, day, picture_num, genotype, replicate, condition))

def main():
    tracing_fname = '%s/%s' % (RAW_DATA_DIR, 'pimpiBig2_D0D1D2-full-tracing.csv')
    output_fname = '%s/%s' % (METADATA_DIR, 'metadata.csv')
    write_metadata(tracing_fname, output_fname)

if __name__ == '__main__':
    main()
