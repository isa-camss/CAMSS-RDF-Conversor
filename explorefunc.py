from IPython.display import Javascript, display
import os
import re


def run_all(ev):
    display(Javascript('IPython.notebook.execute_cells_below()'))

def fileselector():
    return os.getcwd() + '/out/'

def file_validator(filepath):
    pattern = re.compile(r'(.*\/)(.*?)$')

    if filepath is not None:
        filename = pattern.search(filepath)

        with open(filename.group(1) + filename.group(2), 'r') as f:
            print(f.read())
    else:
        print('There is no file of your choice...')

def display_filecontent(filepath):
    file_validator(filepath)
