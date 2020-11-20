import pandas as pd
from constants import CLEANED_ROOT_NODES_DIR
import os
import argparse

def count_root_name_items(root_name):
    root_name = str(root_name)
    return len(root_name.split('_'))

def print_incorrect_main_roots(df):
    df = df[['root_name', 'root_order']]
    df = df[df['root_order'] == 0]
    df['root order items'] = df['root_name'].apply(count_root_name_items)
    df = df[df['root order items'] != 3]
    print(df)

def print_incorrect_lateral_roots(df):
    df = df[['root_name', 'root_order']]
    df = df[df['root_order'] == 1]
    df['root order items'] = df['root_name'].apply(count_root_name_items)
    df = df[df['root order items'] != 2]
    print(df)

def print_incorrect_rows(fname):
    df = pd.read_csv(fname, skipinitialspace=True)
    print_incorrect_main_roots(df)
    print_incorrect_lateral_roots(df)

def check_image_order(full_fname):
    df = pd.read_csv(full_fname, skipinitialspace=True)
    images = df['image']

    prev_images = set()
    curr_image = None

    for image in images:
        if image != curr_image:
            assert image not in prev_images
            prev_images.add(curr_image)
            curr_image = image

def clean_data(args):
    for fname in os.listdir(CLEANED_ROOT_NODES_DIR):

        if fname.endswith('csv'):
            print('+' + ('-' * (len(fname) + 2)) + '+')
            print('+ ' + fname + ' +')
            print('+' + ('-' * (len(fname) + 2)) + '+')

            full_fname = '%s/%s' % (CLEANED_ROOT_NODES_DIR, fname)

            if args.incorrect:
                print_incorrect_rows(full_fname)

            if args.image_order:
                check_image_order(full_fname)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--incorrect', action='store_true')
    parser.add_argument('--image_order', action='store_true')
    clean_data(parser.parse_args())

if __name__ == '__main__':
    main()
