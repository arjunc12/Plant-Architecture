import networkx as nx
import csv
import pandas as pd
from math import sin, cos
import numpy as np
from constants import *
import os
from collections import defaultdict

def write_arbor_file_condensed(output_fname, points):
    with open(output_fname, 'w') as f:
        f.write('root order, x coordinate, y coordinate, insertion point\n')
        for root_type, x, y, insertion in points:
            f.write('%d, %f, %f, %f\n' % (root_type, x, y, insertion))

def write_arbor_file_full(output_fname, root_points, lateral_roots):
    with open(output_fname, 'w') as f:
        f.write('main root\n')
        for x, y in root_points:
            f.write('%f, %f\n' % (x, y))

        for lateral_root, points in lateral_roots.items():
            f.write('%s\n' % lateral_root)
            for x, y in points:
                f.write('%f, %f\n' % (x, y))

def get_day(image_name):
    day_pos = image_name.index('day')
    return image_name[day_pos:day_pos + 4]

def write_arbor_files_full(raw_data_fname, reconstruction_dir):
    df = pd.read_csv(raw_data_fname, skipinitialspace=True)
    root_id = df['root']
    root_name = df['root_name']
    x_pos = df['x']
    y_pos = df['y']
    root_order = df['root_order']
    root_ontology = df['root_ontology']
    image_day = df['image'].apply(get_day)

    curr_name = None
    curr_fname = None
    curr_root_points = None
    curr_lateral_roots = None

    for id, name, x, y, day, order, ontology in zip(root_id, root_name, x_pos, y_pos,\
                                                    image_day, root_order, root_ontology):
        if order == 0:
            assert ontology == 'Root'
            if curr_name != name:
                if curr_lateral_roots != None and len(curr_lateral_roots) > 1:
                    write_arbor_file_full(curr_fname, curr_root_points, curr_lateral_roots)

                curr_name = name
                reconstruction_fname = '%s_%s' % (name, day)
                curr_fname = '%s/%s.csv' % (reconstruction_dir, reconstruction_fname)
                curr_root_points = [(x, y)]
                curr_lateral_roots = defaultdict(list)
            else:
                curr_root_points.append((x, y))
        else:
            assert ontology == 'Lateral root'
            curr_lateral_roots[id].append((x, y))

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
        if order == 0:
            assert ontology == "Root"
            if curr_fname != None:
                assert curr_points != None
                if len(curr_points) > 1:
                    write_arbor_file_condensed(curr_fname, curr_points)

            reconstruction_fname = '%s_%s' % (name, day)
            curr_fname = '%s/%s.csv' % (reconstruction_dir, reconstruction_fname)
            curr_points = [(0, 0, position, 0)]
        else:
            assert ontology == 'Lateral root'
            x = length * sin(angle)
            y = position + length * cos(angle)
            assert curr_points != None
            curr_points.append((1, x, y, position))

def main():
    raw_data_fname = '%s/%s' % (RAW_DATA_DIR, 'pimpiBig2_D0D1D2-full-tracing.csv')
    write_arbor_files_full(raw_data_fname, RECONSTRUCTIONS_DIR)

if __name__ == '__main__':
    main()
