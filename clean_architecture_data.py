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
    root_orders = df['root_order']

    prev_images = set()
    curr_image = None
    has_main_root = None
    missing_main_root = []

    for image, root_order in zip(images, root_orders):
        if image != curr_image:
            if curr_image != None:
                assert image not in prev_images
                if not has_main_root:
                    missing_main_root.append(curr_image)
                prev_images.add(curr_image)

            curr_image = image
            has_main_root = False

        if root_order == 0:
            has_main_root = True

    if len(missing_main_root) > 0:
        print("the following images are missing a main root")
        print("--------------------------------------------")
        for image in missing_main_root:
            print(image)

def check_root_names(full_fname):
    df = pd.read_csv(full_fname, skipinitialspace=True)
    df = df[df['root_order'] == 0]
    for root_name in df['root_name'].unique():
        root_name_items = root_name.split('_')
        root_name_items = list(filter(lambda x : len(x) > 0, root_name_items))
        if len(root_name_items) != 3:
            print(root_name)

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

            if args.root_names:
                check_root_names(full_fname)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--incorrect', action='store_true')
    parser.add_argument('--image_order', action='store_true')
    parser.add_argument('--root_names', action='store_true')
    clean_data(parser.parse_args())

if __name__ == '__main__':
    main()
