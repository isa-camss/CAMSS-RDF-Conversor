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

###########################################
########## EIF score counting #############
###########################################


def get_punct (criteria, ass_dict):
    os.makedirs('arti/punct/', exist_ok=True)
    os.makedirs(f'arti/punct/{ass_dict["title"]["P1"]}/', exist_ok=True)

    def get_range(interval: tuple):
        start = interval[0]
        l = []
        while start < interval[1]:
            l.append(start)
            start += 1
        return l

    def get_strength(not_app: int, total: int, criteria_short = False):
        if criteria_short:
            return round(((total - not_app) / total - 1) * 100, 4)
        else:
            return round(((total - not_app) / total) * 100, 4)

    def get_compliance_level (cat: int, sc: int, ):
        compliance_level = {1: {'Ad-hoc': range(21), 'Opportunistic': [40], 'Essential': [60], 'Sustainable': [80], 'Seamless': [100]},
                            2: {'Ad-hoc': range(0,441), 'Opportunistic': range(441, 881), 'Essential': range(881, 1321), 'Sustainable': range(1321, 1761), 'Seamless': range(1761, 2201)},
                            3: {'Ad-hoc': range(0,101), 'Opportunistic': range(101, 201), 'Essential': range(201, 301), 'Sustainable': range(301, 401), 'Seamless': range(401, 501)},
                            4: {'Ad-hoc': range(0,101), 'Opportunistic': range(101, 201), 'Essential': range(201, 301), 'Sustainable': range(301, 401), 'Seamless': range(401, 501)},
                            5: {'Ad-hoc': range(0,221), 'Opportunistic': range(221, 441), 'Essential': range(441, 661), 'Sustainable': range(661, 881), 'Seamless': range(881, 1100)}
                            }
        for level in compliance_level[cat]:
            if sc in compliance_level[cat][level]:
                return level

    def run_criteria():
        category_range = [(0, 1), (1, 23), (23, 28), (28, 33), (33, 44)]
        criteria_list = list(criteria.keys())
        if criteria[criteria_list[2]][4] == 'None':
            criteria_short = True
        else:
            criteria_short = False
        # list of criterion scores
        criterion_score_list = []
        ass_punct = []
        # lists population
        count_overall_notapp = 0
        for rang in category_range:
            count_notapp = 0
            rang_ = get_range(rang)
            for i in rang_:
                criterion_score = criteria[criteria_list[i]][4]
                #print('------')
                #print('i', i)
                #print(criteria_list[rang_[0]:rang_[-1] + 1])
                #print(criteria_list[i])
                #print(criterion_score)
                # count not applicable
                notapp = criteria[criteria_list[i]][-1]
                #print('notapp', notapp)
                if notapp.lower() == 'not applicable':
                    if i != 2:
                        count_notapp += 1
                # append
                try:
                    if criterion_score != 'None':
                        criterion_score_list.append(int(criterion_score))
                    else:
                        criterion_score_list.append(0)
                        #print('empty -->', criterion_score)
                        #print()
                except:
                    print('empty criterion')
            #print('next category')
            # score per category
            category_score = sum(criterion_score_list[rang_[0]:rang_[-1] + 1])
            #print([rang_[0],rang_[-1] + 1])
            #print('count_notapp',count_notapp)
            #print(category_score)
            if criteria_short and rang == (1,23):
                # score per category (string)
                total_category_score = str(category_score) + '/' + str(((rang[1] - rang[0]) * 100) - 100)
                # strength score of the category
                category_strength = get_strength(count_notapp, ((rang[1] - rang[0])) - 1)
            else:
                # score per category (string)
                total_category_score = str(category_score) + '/' + str((rang[1] - rang[0]) * 100)
                # strength score of the category
                category_strength = get_strength(count_notapp, rang[1] - rang[0])
            # compliance level of the category
            compliance_level = get_compliance_level(category_range.index(rang) + 1, category_score)
            ass_punct.append([category_score, total_category_score, category_strength, compliance_level, count_notapp])
            count_overall_notapp = count_overall_notapp + count_notapp
        # overall punctuations (last element of the ass_punct list)
        overall_score = sum(punct[0] for punct in ass_punct)
        if criteria_short:
            total_overall_score = [overall_score, (category_range[-1][1] - 1 - category_range[0][0]) * 100]
            #str(overall_score) + '/' + str((category_range[-1][1] - 1 - category_range[0][0]) * 100)
        else:
            total_overall_score = [overall_score, (category_range[-1][1] - category_range[0][0]) * 100]
            #str(overall_score) + '/' + str((category_range[-1][1] - category_range[0][0]) * 100)
        total_overall_score = [str(item) for item in total_overall_score]
        total_overall_score = '/'.join(total_overall_score)
        overall_strength = get_strength(count_overall_notapp, len(criteria))
        ass_punct.append([total_overall_score, overall_strength])
        #print(ass_punct)
        #print(criterion_score_list)
        #print(criteria)
        return ass_punct


    with open(f'arti/punct/{ass_dict["title"]["P1"]}/' + f'{ass_dict["title"]["P1"]}-EIFScenario-scores.csv', 'w', encoding='utf-8') as f:
        print(ass_dict["title"]["P1"])
        ass_scores = run_criteria()
        # EIF Principles setting the context for EU Actions on Interoperability
        # category 1
        print('', 'score', 'strength', 'compliance level', sep='\t', file=f)
        print('EIF Principles setting the context for EU Actions on Interoperability', ass_scores[0][1], ass_scores[0][2], ass_scores[0][3], sep='\t', file=f)
        if len(criteria) == 43:
            # EIF Core Interoperability Principles
            # 2
            print('EIF Core Interoperability Principles', ass_scores[1][1], ass_scores[1][2], ass_scores[1][3], sep='\t', file=f)
            # EIF Principles Related to generic user needs and expectations
            # 3
            print('EIF Principles Related to generic user needs and expectations', ass_scores[2][1], ass_scores[2][2], ass_scores[2][3], sep='\t', file=f)
            # EIF Foundation principles for cooperation among public administrations
            # 4
            print('EIF Foundation principles for cooperation among public administrations', ass_scores[3][1], ass_scores[3][2], ass_scores[3][3], sep='\t', file=f)
            # EIF Interoperability Layers
            # 5
            print('EIF Interoperability Layers', ass_scores[4][1], ass_scores[4][2], ass_scores[4][3], sep='\t', file=f)
        else:
            # EIF Core Interoperability Principles
            # 2
            print('EIF Core Interoperability Principles', ass_scores[1][1], ass_scores[1][2], ass_scores[1][3], sep='\t', file=f)
            # EIF Principles Related to generic user needs and expectations
            # 3
            print('EIF Principles Related to generic user needs and expectations', ass_scores[2][1], ass_scores[2][2], ass_scores[2][3], sep='\t', file=f)
            # EIF Foundation principles for cooperation among public administrations
            # 4
            print('EIF Foundation principles for cooperation among public administrations', ass_scores[3][1], ass_scores[3][2], ass_scores[3][3], sep='\t', file=f)
            # EIF Interoperability Layers
            # 5
            print('EIF Interoperability Layers', ass_scores[4][1], ass_scores[4][2], ass_scores[4][3], sep='\t', file=f)
        print('Overall Score', ass_scores[5][0], ass_scores[5][1], '', sep='\t', file=f)
        print('', round(int(ass_scores[5][0].split("/")[0])/int(ass_scores[5][0].split("/")[1]),4), '', '', sep='\t', file=f)