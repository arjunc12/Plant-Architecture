import networkx as nx
import csv
import pandas as pd
from math import sin, cos
import numpy as np
from constants import RAW_DATA_DIR, RECONSTRUCTIONS_DIR
import os
from collections import defaultdict
import utils

def write_arbor_file_condensed(output_fname, points):
    with open(output_fname, 'w') as f:
        f.write('root order, x coordinate, y coordinate, insertion point\n')
        for root_type, x, y, insertion in points:
            f.write('%d, %f, %f, %f\n' % (root_type, x, y, insertion))

def write_arbor_file_full(output_fname, root_points, lateral_roots):
    with open(output_fname, 'w') as f:
        # write the main root points
        f.write('main root\n')
        for x, y in root_points:
            f.write('%f, %f\n' % (x, y))

        # loop through each lateral root, and write the points for that lateral root
        for lateral_root, points in lateral_roots.items():
            f.write('%s\n' % lateral_root)
            for x, y in points:
                f.write('%f, %f\n' % (x, y))

def write_arbor_files_full(raw_data_fname, reconstruction_dir):
    df = pd.read_csv(raw_data_fname, skipinitialspace=True)
    images = df['image']
    root_ids = df['root']
    root_names = df['root_name']
    x_pos = df['x']
    y_pos = df['y']
    root_orders = df['root_order']

    curr_image = None
    curr_name = None
    curr_day = None
    curr_root_points = None
    curr_lateral_roots = None

    for image, root_id, root_name, x, y, root_order in\
        zip(images, root_ids, root_names, x_pos, y_pos, root_orders):

        if root_order == 0:
            # check if we've found a the main root for a new arbor
            if root_name != curr_name:
                # check if this is not the first arbor
                if curr_lateral_roots != None and len(curr_lateral_roots) > 1:
                    # if not the first main root, write the architecture file for the previous arbor
                    reconstruction_fname = utils.arbor_name(curr_image, curr_name)
                    output_fname = '%s/%s.csv' % (reconstruction_dir, reconstruction_fname)
                    write_arbor_file_full(output_fname, curr_root_points, curr_lateral_roots)

                # reset the points associated with the current (new) arbor
                curr_image = image
                curr_name = root_name
                curr_day = utils.get_day(image)
                curr_root_points = [(x, y)]
                curr_lateral_roots = defaultdict(list)
            else:
                # the next point is associated with our current arbor's main root
                curr_root_points.append((x, y))
        else:
            # the next point is associated with a lateral root for our current arbor
            curr_lateral_roots[root_id].append((x, y))

def write_arbor_files_condensed(raw_data_fname, reconstruction_dir):
    df = pd.read_csv(raw_data_fname, skipinitialspace=True)
    root_name = df['root_name']
    root_length = df['length']
    root_order = df['root_order']
    root_ontology = df['root_ontology']
    insertion_position = df['insertion_position']
    insertion_angle = np.radians(df['insertion_angle'])
    image_day = df['image'].apply(get_day)

    curr_fname = None
    curr_points = None

    for name, length, order, ontology, position, angle, day in\
        zip(root_name, root_length, root_order, root_ontology, insertion_position,\
            insertion_angle, image_day):

        # check if the current line is a main root for a new arbor, or a lateral root for the current arbor
        if order == 0:
            # 0 should correspond to a  main root point
            assert ontology == "Root"

            # check if this is not our first arbor
            if curr_fname != None:
                '''
                if this not our first arbor, and if the current arbor has more than one
                point, write the arbor to an new architecture file
                '''
                assert curr_points != None
                if len(curr_points) > 1:
                    write_arbor_file_condensed(curr_fname, curr_points)

            # reset the points associated with the current arbor
            reconstruction_fname = '%s_%s' % (name, day)
            curr_fname = '%s/%s.csv' % (reconstruction_dir, reconstruction_fname)
            curr_points = [(0, 0, position, 0)]
        else:
            # use trigonometry to obtain the x/y coordinates of the lateral root tip
            assert ontology == 'Lateral root'
            x = length * sin(angle)
            y = position + length * cos(angle)
            assert curr_points != None
            curr_points.append((1, x, y, position))

def main():
    for fname in os.listdir(RAW_DATA_DIR):
        if 'full-tracing' in raw_data_fname:
            raw_data_fname = '%s/%s' % (RAW_DATA_DIR, fname)
            write_arbor_files_full(raw_data_fname, RECONSTRUCTIONS_DIR)

if __name__ == '__main__':
    main()
