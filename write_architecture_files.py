import networkx as nx
import csv
import pandas as pd
from math import sin, cos
import numpy as np
from constants import *
import os

def write_arbor_file(output_fname, points):
    with open(output_fname, 'w') as f:
        f.write('root order, x coordinate, y coordinate, insertion point\n')
        for root_type, x, y, insertion in points:
            f.write('%d, %f, %f, %f\n' % (root_type, x, y, insertion))

def get_day(image_name):
    day_pos = image_name.index('day')
    return image_name[day_pos:day_pos + 4]

def write_arbor_files(raw_data_fname, reconstruction_dir):
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
                    write_arbor_file(curr_fname, curr_points)

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
    raw_data_fname = '%s/%s' % (RAW_DATA_DIR, 'pimpi_Big2_D0_D1.csv')
    write_arbor_files(raw_data_fname, RECONSTRUCTIONS_DIR)

if __name__ == '__main__':
    main()
