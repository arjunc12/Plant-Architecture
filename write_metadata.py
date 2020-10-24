import os

def image_metadata(image):
    image = image.strip('_')
    image = image.strip('.rsml')

    image_items = image.split('_')

    day = image_items[1]
    day = day.strip('day')

    picture_num = image_items[-1]

    return day, picture_num

def root_name_metadata(root_name):
    root_name_items = root_name.split("_")

    genotype = root_name_items[0]
    replicate = root_name_items[1]
    condition = root_name_items[2]

    return genotype, replicate, condition

def write_metadata(tracing_fname, output_fname):
    df = pd.read_csv(tracing_fnamem skipinitialspace=True)
    df = df[df['root_order'] == 0]
    df = df[['image', 'root_name', 'root_order']]
    df.drop_duplicates(inplace=True)

    with open(output_fname, 'w') as f:
        f.write('arbor name, day, Picture #, genotype, replicate, condition\n')

        for image, root_name in zip(df['image'], df['root_name']):
            pass