"""This file has a function to remove all the files in a directory.
It has a second function to go through each directory to remove the files.

"""
import os
from constants import *
import shutil

def delete_files_and_subdirectories(directory_path):
   """deletes files and subdirectories in the given directory"""
   try:
     with os.scandir(directory_path) as entries:
       for entry in entries:
         if entry.is_file():
            os.unlink(entry.path)
         else:
            shutil.rmtree(entry.path)
     print("All files and subdirectories deleted successfully.")
   except OSError:
     print("Error occurred while deleting files and subdirectories.")

# # Usage
# directory_path = '/path/to/directory'
# delete_files_and_subdirectories(directory_path)

def remove_files(directory):
    """removes all files from a given directory
    """
    for file in os.listdir(directory):
        print("removing file:", file, "from directory:",directory)
        full_name = directory+"/"+file
        os.remove(directory+"/"+file)

def remove_all_files():
    """removes files from all directories in the necessary_dir_list"""
    # print("testing with null models directory")
    # for file in os.listdir(STATISTICS_DIR):
    #     os.remove(STATISTICS_DIR+"/"+file)
    for directory in NECESSARY_DIR_LIST:
        print("directory name where files will be removed:", directory)
        # remove_files(directory)
        delete_files_and_subdirectories(directory)

def main():
    print("remove-files.py will now remove all files.")
    remove_all_files()

if __name__ == '__main__':
    main()