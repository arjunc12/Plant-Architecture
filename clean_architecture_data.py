import pandas as pd
from constants import CLEANED_ROOT_NODES_DIR
import os

def count_root_name_items(root_name):
    return len(root_name.split('_'))

def print_incorrect_rows(df):
    df = df[['root_name', 'root_order']]
    df = df[df['root_order'] == 0]
    df['root order items'] = df['root_name'].apply(count_root_name_items)
    df = df[df['root order items'] != 3]
    print(df)

def clean_dataset(fname):
    df = pd.read_csv(fname, skipinitialspace=True)
    print_incorrect_rows(df)

def clean_data():
    for fname in os.listdir(CLEANED_ROOT_NODES_DIR):
        if fname.endswith('csv'):
            print('+' + ('-' * (len(fname) + 2)) + '+')
            print('+ ' + fname + ' +')
            print('+' + ('-' * (len(fname) + 2)) + '+')

            full_fname = '%s/%s' % (CLEANED_ROOT_NODES_DIR, fname)

            clean_dataset(full_fname)

def main():
    clean_data()

if __name__ == '__main__':
    main()
