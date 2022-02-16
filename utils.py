from time import sleep
from IPython.core.display import display, HTML
from IPython.display import Javascript, display
import ipywidgets as widgets
import os
import re
from tqdm.auto import tqdm

###########################################
##### Explore function ####################
###########################################
def run_all(ev):
    display(Javascript('IPython.notebook.execute_cells_below()'))

def fileselector():
    return os.getcwd() + '/arti/out/'

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

###########################################
############ Hide code ####################
###########################################

# source: https://www.titanwolf.org/Network/q/8f9729f8-fc73-4bc7-97b8-dcb9604a9356/y

javascript_functions = {False: "hide()", True: "show()"}
button_descriptions  = {False: "Show code", True: "Hide code"}


def toggle_code(state):

    """
    Toggles the JavaScript show()/hide() function on the div.input element.
    """

    output_string = "<script>$(\"div.input\").{}</script>"
    output_args   = (javascript_functions[state],)
    output        = output_string.format(*output_args)

    display(HTML(output))


def button_action(value):

    """
    Calls the toggle_code function and updates the button description.
    """

    state = value.new

    toggle_code(state)

    value.owner.description = button_descriptions[state]

def display_hidebuttom():
    state = False
    toggle_code(state)

    button = widgets.ToggleButton(state, description = button_descriptions[state])
    button.observe(button_action, "value")

    display(button)

###########################################
########### Progress bar ##################
###########################################

def progress_bar(file: str, row: int, spec: str):
    steps = [f"Extracting Assessments from '{file}'",
             f'Extracting data from the {row}º Assessment in "{file}" into a python dictionary',
             f"'{spec}' retrieved!", f"'{spec}' CAMSS Knowledge Graph created!"]
    with tqdm(total=4, position=0, ncols=300, leave=True, desc=spec,
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as bar:
        for i in range(4):
            bar.update(int(1))
            sleep(0.5)
        print('                                               ' + spec + ' Completed!')
        print()