import os
import re
import sys
import glob
import uuid
import hashlib
import datetime
import pandas as p
import logging
from pathlib import PurePath
import pandas as pd
import rdflib
from rdflib import Namespace

import utils


class AssessmentScenario:
    """
    Collection of assessments. It collects all the assessments from an EU Survey output.
    """
    ass_file_path: str  # file path data (string type)
    ass_df: p.DataFrame  # data structure (DataFrame type)
    scenario: str  # scenario for the assessments (string type)
    scenario_full: str  # scenario full name (string type)
    url_scenario: str # EUSurvey URL scenario
    tool_version: str  # current Assessments Toolkit Version (string type)
    ass_date: str  # date of export of the EU Survey output (string type)
    criteria: dict  # criteria dictionary, used by child class Extractor
    gradients: dict = None  # EIF gradients dictionary
    ass_dict: dict  # Assessment dictionary

    def __init__(self, file_path: str = None, row: int = 0):
        """
        Assessments class initializer. Collection of the assessments' common metadata.
        :param file_path: file path data
        """
        self.ass_file_path = file_path  # file path
        self.ass_df = self.open_file()  # assessments stored in DataFrame
        self.scenario = self.get_scenario()  # assessments scenario
        self.scenario_full = self.get_scenario_full()  # the assessment scenario full name
        self.url_scenario = self.get_url_eusurvey() # the EUSurvey URL of the CAMSS Assessment Scenario
        self.tool_version = self.get_version()  # EU Survey/CAMSS Tool version
        self.ass_date = self.get_date()  # assessment date
        self.get_criteria()
        if self.scenario == 'EIF':
            self.gradients = self.get_gradients()
        self.get_ass_dict()

    def open_file(self) -> p.DataFrame:
        """
        Loads from an excel workbook all the assessments  from a EU Survey/CAMSS Tool and transforms it into a DataFrame
        """
        self.ass_df = p.read_excel(self.ass_file_path, header=None)
        return self.ass_df

    def get_scenario(self):
        """
        Takes the EU Survey output file name and extracts the scenario.
        """
        pattern1 = re.compile(r'([A-Za-z][A-Za-z][A-Za-z]?)Scenario_v(\d*)')  # previous EUSurvey format
        pattern2 = re.compile(r'(CAMSSAssessment)(EIF)(Scenario)(\d+)')  # current EUSurvey format CAMSSAssessmentEIFScenario6
        scenario = str(self.ass_df.loc[0, 1]).strip()
        sc1 = pattern1.search(scenario)
        sc2 = pattern2.search(scenario)
        if sc1:
            return sc1.group(1)
        elif sc2:
            return sc2.group(2)

    def get_scenario_full(self):
        """
        Takes the scenario short name and returns its full name.
        :return:
        """
        if self.scenario == 'EIF':
            return 'European Interoperability Framework (EIF)'
        elif self.scenario == 'MSP':
            return 'Multi-Stakeholder Platform (MSP)'
        elif self.scenario == 'TS':
            return 'ICT Specification (TS)'

    def get_url_eusurvey(self):
        """
        Takes the EU Survey URL.
        """
        return str("https://ec.europa.eu/eusurvey/runner/" + str(self.ass_df.loc[0, 1]).strip())

    def get_version(self):
        """
        Takes the EU Survey output file name and extracts the Tool version.
        """
        pattern1 = re.compile(r'([A-Za-z][A-Za-z][A-Za-z]?)Scenario_v(\d*)')  # previous EUSurvey format
        pattern2 = re.compile(r'(CAMSSAssessment)(EIF)(Scenario)(\d+)')  # current EUSurvey format
        scenario = str(self.ass_df.loc[0, 1]).strip()
        vrs1 = pattern1.search(scenario)
        vrs2 = pattern2.search(scenario)
        # if self.scenario in ['MSP', 'TS']:
        #    return "1.1.0"
        if vrs1:
            vrs1 = re.split(r'(\w)', vrs1.group(2))[1:-1]
            return ".".join([el for el in vrs1 if el != ''])
        elif vrs2:
            vrs2 = re.split(r'(\w)', vrs2.group(4))
            return "6.0.0"

    def get_date(self):
        """
        Takes EU Survey export date (unused).
        """
        return str(self.ass_df.loc[1, 1])[:11]

    def get_criteria(self):
        self.criteria = {}
        pattern = re.compile(r'((A\d*?)\(?( ?\w)?\)?) ?-( )?(.*)')
        for i in range(len(self.ass_df.loc[3])):
            cell = pattern.search(self.ass_df.loc[3, i].strip())
            if cell:
                criterion_name = cell.group(1)
                criterion_description = cell.group(5)
                self.criteria[criterion_name] = [i]
                self.criteria[criterion_name].append(sha256(criterion_description))
                criterion_description = re.sub(r'"', "'", criterion_description)
                self.criteria[criterion_name].append(criterion_description)

    @staticmethod
    def get_gradients():
        """
        Extracts gradients from predefined answers and creates a DataFrame.
        :return: dict
        """
        df = p.read_csv('gradients_EIFv6.csv', sep='\t', header=None)
        df = df.apply(lambda x: x.astype(str).str.lower())
        return dict(zip(df[0], df[1]))

    def get_ass_dict(self):
        """
        Populates the dictionary containing the data of the current assessment.
        """
        # common key elements for EIF, MSP and ICT
        dict_keys = ['assessment_id', 'assessment_date', 'submission_date', 'tool_version', 'tool_release_date',
                     'contextualised_by', 'results_in', 'status', 'title', 'organization', 'agent', 'P5', 'P6', 'C1',
                     'C2', 'C3', 'C4', 'C5', 'P7', 'P8', 'P9', 'P10', 'io_spec_type', 'url_eusurvey']
        # main dictionary keys
        self.ass_dict = dict.fromkeys(dict_keys)
        # common elements for EIF, MSP and ICT
        self.ass_dict['assessment_date'] = str(datetime.date.today())  # date of the assessment
        self.ass_dict['submission_date'] = None  # assessment submission date
        self.ass_dict['tool_version'] = self.tool_version  # EU Survey/CAMSS Tool version
        self.ass_dict['tool_release_date'] = None  # Tool release date
        self.ass_dict['contextualised_by'] = {}  # context of the current assessment
        self.ass_dict['results_in'] = {}  # responses submitted by the submitter organisation
        # scenario
        self.ass_dict['contextualised_by']['scenario'] = self.scenario  # the assessment scenario
        self.ass_dict['contextualised_by']['scenario_id'] = sha256(
            self.scenario + '-' + str(self.tool_version))  # the scenario identifier
        self.ass_dict['contextualised_by']['L8'] = self.scenario_full  # the assessment scenario full name
        self.ass_dict['url_eusurvey'] = self.url_scenario


class Extractor(AssessmentScenario):
    """
    Extracts the data of an assessment only once from the EU Survey/CAMSS output file.
    """
    ass_: pd.DataFrame  # the Dataframe of the assessments, contains the input data of the assessments file
    row: int  # DataFrame row, this is the row pointing at the current assessment (integer type)
    ass_title: str  # the title of the specification being assessed (string type)
    ass_id: str  # the assessment identifier (string type)
    criteria_: dict  # criteria from AssessmentScenario
    ass_dict: dict  # the assessment data (dictionary type)

    def __init__(self, file_path: str, row: int = 0):
        """
        Extractor class initializer. Extracts the assessment data currently analysed.
        :param file_path: the file path of the current assessments
        :param row: the row pointing at the current assessment
        """
        super().__init__(file_path, row)
        self.ass_ = self.ass_df
        self.row = row
        self.ass = p.concat([self.ass_.iloc[3:4], self.ass_.iloc[
                                                  row:row + 1]])  # the Assessments instance header and the the input data of the assessments file
        self.ass_title = self.get_title()  # the title of the specification being assessed
        # criteria extraction from the current assessment
        self.criteria_ = self.criteria
        self._get_criteria()
        # creates a unique identifier for the current assessment
        self.ass_id = self.get_id()
        # populates the dictionary with the data of the current assessment
        self.ass_dict = self.ass_dict
        self._get_ass_dict()

    def get_title(self):
        """
        Extracts the title of the specification being assessed.
        """
        if self.scenario == 'EIF':
            title = str(self.ass_.loc[self.row, 11]).strip()
        elif self.scenario == 'MSP':
            title = str(self.ass_.loc[self.row, 10]).strip()
        else:
            title = str(self.ass_.loc[self.row, 12]).strip()
        title = re.sub("\s+", " ", title).strip()
        return title

    def get_id(self) -> str:
        """
        Creates a unique identifier for this assessment.
        :return: Returns a SHA-256 hash of the concatenation of 'scenario + toolkit_version + title'
        """
        ret = self.scenario + str(self.tool_version) + self.ass_title
        return sha256(ret)

    @staticmethod
    def _yesno_choice(option: str) -> int:
        """
        ################
        Origin: camss.py
        ################
        Transforms NO into 0 (False), YES into 1 (True), and N/A into 2 (None)
        :param option: the string YES, NO, or N/A
        :return:
        """
        o = option.strip().lower()
        if o == 'yes':
            return 1
        elif o == 'no':
            return -1
        elif o == "not answered":
            return -1
        elif o == "not applicable":
            return 0

    @staticmethod
    def _new_yesno_choice(option: str, grd: dict) -> int:
        """
        Transforms the submitter response into a percentage system, according to the EIF scenario version 5, for YES/NO-oriented responses.
        :param option: the string YES, NO, or N/A
        :return:
        """
        o = option.strip().lower()
        if o == 'yes':
            return 100
        elif o == 'no':
            return 20
        elif o in grd.keys():
            return grd[o]

    def _get_ass_dict(self):
        """
        Populates the dictionary containing the data of the current assessment.
        """
        # assessment id
        self.ass_dict['assessment_id'] = self.ass_id  # the current assessment identifier
        # EIF scenario
        if self.scenario == 'EIF':
            self.ass_dict['spec_type'] = re.sub(" ", "", str(self.ass.loc[self.row, 10]))
            # criterion, criterion description, submitter organisation's judgement and score
            for criterion in self.criteria.keys():
                self.ass_dict['results_in'][criterion] = {}  # a new dictionary in the dictionary
                self.ass_dict['results_in'][criterion]['criterion_sha_id'] = self.criteria[criterion][
                    1]  # the criterion identifier
                self.ass_dict['results_in'][criterion]['criterion_description'] = self.criteria[criterion][
                    2]  # the criterion description
                self.ass_dict['results_in'][criterion]['statement'] = self.criteria[criterion][
                    6]  # submitter organisation judgement
                self.ass_dict['results_in'][criterion]['statement_id'] = self.criteria[criterion][
                    5]  # the identifier of the submitter organisation judgement
                self.ass_dict['results_in'][criterion]['score'] = self.criteria[criterion][
                    4]  # the punctuation of the submitter organisation judgement
                self.ass_dict['results_in'][criterion]['score_id'] = self.criteria[criterion][
                    3]  # the identifier of the punctuation
            # status
            self.ass_dict['status'] = None  # to review
            # the specification elements
            self.ass_dict['title'] = {}  # a new dictionary in the dictionary
            #self.ass_title = self.ass.loc[self.row, 11]  # title of the specification
            self.ass_dict['title']['P1'] = self.ass_title  # title of the specification
            self.ass_dict['title']['description'] = self.ass.loc[self.row, 13]  # description of the specification
            self.ass_dict['title']['version'] = self.ass.loc[self.row, 12]  # description of the specification
            self.ass_dict['title']['spec_id'] = sha256(
                str(self.ass_dict['title']['P1']))  # the specification identifier, the MD5 of the title
            self.ass_dict['title']['distribution_id'] = str(uuid.uuid4())  # distribution_id
            self.ass_dict['title']['P2'] = self.ass.loc[self.row, 14]  # spec_download_url
            # organization
            self.ass_dict['organization'] = {}  # a new dictionary in the dictionary
            self.ass_dict['organization']['L1'] = self.ass.loc[self.row, 1]  # Submitter_name
            self.ass_dict['organization']['submitter_unit_id'] = sha256(
                str(self.ass_dict['organization']['L1']) + " " + str(self.ass.loc[self.row, 2]))  # Submitter_id
            self.ass_dict['organization']['L2'] = self.ass.loc[self.row, 4]  # submitter_organisation
            self.ass_dict['organization']['submitter_org_id'] = sha256(
                str(self.ass_dict['organization']['L2']))  # submitter_organisation_id
            self.ass_dict['organization']['L3'] = self.ass.loc[self.row, 3]  # submitter role/position
            self.ass_dict['organization']['L4'] = None  # submitter_address
            self.ass_dict['organization']['L5'] = self.ass.loc[self.row, 5]  # submitter_phone
            self.ass_dict['organization']['L6'] = self.ass.loc[self.row, 7]  # submitter_email
            self.ass_dict['organization']['L7'] = None  # submission_date
            self.ass_dict['organization']['uuid'] = uuid.uuid4() \
                if 'CAMSS' not in [self.ass_dict['organization']['L1'], self.ass_dict['organization']['L2']] \
                else 'ddf032efca18c9e6eaa97bc90924977af1d96bffe564b351a6081835c75d8164'  # organization contact point uuid (?)
            # agent, SDO
            self.ass_dict['agent'] = {}  # a new dictionary in the dictionary
            sdo_name = self.ass.loc[self.row, 15]
            if sdo_name == 'Other (SDO/SSO)':
                sdo_url = self.ass.loc[self.row, 17]
                self.ass_dict['agent']['P3'] = self.ass.loc[self.row, 16] + f" ({sdo_url})"
                # if self.ass_dict['agent']['P3'] == self.ass_dict['title']['P1']:
                #     self.ass_dict['agent']['P3'] = self.ass_dict['agent']['P3'] + ' (SDO/SSO)'
                # sdo_nameself.ass_dict['agent']['P3'] = self.ass.loc[self.row, 16]
                # find for parenthesis, i.e. short names
                # sdo_name_ = re.split('[() ]', sdo_name)
                # interv = [i for i in enumerate(sdo_name_) if i[1] == '']
                # if interv != list():
                #    self.ass_dict['agent']['P3'] = sdo_name_[interv[0][0]+1:interv[1][0]]
                #    self.ass_dict['agent']['P3'] = self.ass.loc[self.row, 16]  # sdo_name
                #    self.ass_dict['agent']['P3'] = self.ass_dict['agent']['P3'] + f' ({self.ass.loc[self.row, 17]})'
            else:
                self.ass_dict['agent']['P3'] = self.ass.loc[self.row, 15]  # sdo_name
            self.ass_dict['agent']['sdo_id'] = sha256(
                str(self.ass_dict['agent']['P3']))  # sdo_id (for the Agent instance)
            self.ass_dict['agent']['P4'] = self.ass.loc[self.row, 18]
            # sdo_contact_point
            self.ass_dict['agent']['uuid'] = uuid.uuid4()  # agent contact point uuid (?)
            # submission_rationale
            self.ass_dict['P5'] = None  # submission_rationale
            # 'other_evaluations'
            self.ass_dict['P6'] = self.ass.loc[self.row, 18]  # other_evaluations # revisar
            # 'considerations'
            self.ass_dict['C1'] = None  # correctness
            self.ass_dict['C2'] = None  # completeness
            self.ass_dict['C3'] = self.ass.loc[self.row, 19]  # egov_interoperability # revisar
            # 'io_spec_type'
            self.ass_dict['io_spec_type'] = None  # interoperability specification type
            # additional features
            self.ass_dict['P7'] = None  # submission scope
            self.ass_dict['P8'] = None  # backward and forward compatibility
            self.ass_dict['P9'] = None  # no longer compliance
            self.ass_dict['P10'] = None  # first SDO spec?
            self.ass_dict['C4'] = None  # egov_interoperability
            self.ass_dict['C5'] = None  # egov_interoperability

        elif self.scenario == 'MSP':
            self.ass_dict['spec_type'] = re.sub(" ", "", str(self.ass.loc[self.row, 9]))
            # criterion, judgement and score
            for criterion in self.criteria.keys():
                self.ass_dict['results_in'][criterion] = {}  # a new dictionary in the dictionary
                self.ass_dict['results_in'][criterion]['criterion_sha_id'] = self.criteria[criterion][
                    1]  # the criterion identifier
                self.ass_dict['results_in'][criterion]['criterion_description'] = self.criteria[criterion][
                    2]  # the criterion description
                self.ass_dict['results_in'][criterion]['statement'] = self.criteria[criterion][
                    6]  # submitter organisation judgement
                self.ass_dict['results_in'][criterion]['statement_id'] = self.criteria[criterion][
                    5]  # the identifier of the submitter organisation judgement
                self.ass_dict['results_in'][criterion]['score'] = self.criteria[criterion][
                    4]  # the punctuation of the submitter organisation judgement
                self.ass_dict['results_in'][criterion]['score_id'] = self.criteria[criterion][
                    3]  # the identifier of the punctuation
            # status
            self.ass_dict['status'] = None  # to review
            # title
            self.ass_dict['title'] = {}  # a new dictionary in the dictionary
            self.ass_title = self.ass.loc[self.row, 9]  # title of the specification
            self.ass_dict['title']['P1'] = self.ass_title  # title of the specification
            self.ass_dict['title']['spec_id'] = sha256(
                str(self.ass_dict['title']['P1']))  # the specification identifier, the MD5 of the title
            self.ass_dict['title']['distribution_id'] = str(uuid.uuid4())  # distribution_id
            self.ass_dict['title']['P2'] = self.ass.loc[self.row, 10]  # spec_download_url
            # organization
            self.ass_dict['organization'] = {}  # a new dictionary in the dictionary
            self.ass_dict['organization']['L1'] = self.ass.loc[self.row, 2]  # Submitter_name
            self.ass_dict['organization']['submitter_unit_id'] = sha256(
                str(self.ass_dict['organization']['L1']) + " " + str(self.ass.loc[self.row, 1]))  # Submitter_id
            self.ass_dict['organization']['L2'] = self.ass.loc[self.row, 3]  # submitter_organisation
            self.ass_dict['organization']['submitter_org_id'] = sha256(
                str(self.ass_dict['organization']['L2']))  # submitter_organisation_id
            self.ass_dict['organization']['L3'] = self.ass.loc[self.row, 4]  # submitter role/position
            self.ass_dict['organization']['L4'] = self.ass.loc[self.row, 5]  # submitter_address
            self.ass_dict['organization']['L5'] = self.ass.loc[self.row, 6]  # submitter_phone
            self.ass_dict['organization']['L6'] = self.ass.loc[self.row, 8]  # submitter_email
            self.ass_dict['organization']['L7'] = None  # submission_date
            self.ass_dict['organization']['uuid'] = uuid.uuid4()  # organization contact point uuid (?)
            # agent, SDO
            self.ass_dict['agent'] = {}  # a new dictionary in the dictionary
            self.ass_dict['agent']['P3'] = self.ass.loc[self.row, 11]  # sdo_name
            self.ass_dict['agent']['sdo_id'] = sha256(
                str(self.ass_dict['agent']['P3']))  # sdo_id (for the Agent instance)
            self.ass_dict['agent']['P4'] = self.ass.loc[self.row, 13]  # sdo_contact_point
            self.ass_dict['agent']['uuid'] = uuid.uuid4()  # agent contact point uuid (?) aqui
            # submission_rationale
            self.ass_dict['P5'] = self.ass.loc[self.row, 14]  # submission_rationale
            # 'other_evaluations'
            self.ass_dict['P6'] = self.ass.loc[self.row, 15]  # other_evaluations
            # 'considerations'
            self.ass_dict['C1'] = None  # correctness
            self.ass_dict['C2'] = None  # completeness
            self.ass_dict['C3'] = self.ass.loc[self.row, 20]  # egov_interoperability
            # 'io_spec_type'
            self.ass_dict['io_spec_type'] = None  # interoperability specification type
            # additional features
            self.ass_dict['P7'] = self.ass.loc[self.row, 16]  # submission scope
            self.ass_dict['P8'] = self.ass.loc[self.row, 17]  # backward and forward compatibility
            self.ass_dict['P9'] = self.ass.loc[self.row, 18]  # no longer compliance
            self.ass_dict['P10'] = self.ass.loc[self.row, 19]  # first SDO spec?
            self.ass_dict['C4'] = self.ass.loc[self.row, 22]  # egov_interoperability
            self.ass_dict['C5'] = self.ass.loc[self.row, 24]  # egov_interoperability

        elif self.scenario == 'TS':
            self.ass_dict['spec_type'] = re.sub(" ", "", str(self.ass.loc[self.row, 11]))
            # criterion, judgement and score
            for criterion in self.criteria.keys():
                self.ass_dict['results_in'][criterion] = {}  # a new dictionary in the dictionary
                self.ass_dict['results_in'][criterion]['criterion_sha_id'] = self.criteria[criterion][
                    1]  # the criterion identifier
                self.ass_dict['results_in'][criterion]['criterion_description'] = self.criteria[criterion][
                    2]  # the criterion description
                self.ass_dict['results_in'][criterion]['statement'] = self.criteria[criterion][
                    6]  # submitter organisation judgement
                self.ass_dict['results_in'][criterion]['statement_id'] = self.criteria[criterion][
                    5]  # the identifier of the submitter organisation judgement
                self.ass_dict['results_in'][criterion]['score'] = self.criteria[criterion][
                    4]  # the punctuation of the submitter organisation judgement
                self.ass_dict['results_in'][criterion]['score_id'] = self.criteria[criterion][
                    3]  # the identifier of the punctuation
            # status
            self.ass_dict['status'] = self.ass.loc[self.row, 31]  # to review
            # title
            self.ass_dict['title'] = {}  # a new dictionary in the dictionary
            self.ass_title = self.ass.loc[self.row, 11]  # global variable for the title of the specification
            self.ass_dict['title']['P1'] = self.ass_title  # spec_title
            self.ass_dict['title']['spec_id'] = sha256(
                str(self.ass_dict['title']['P1']))  # spec_id, the MD5 of the title
            self.ass_dict['title']['distribution_id'] = str(uuid.uuid4())  # distribution_id
            self.ass_dict['title']['P2'] = self.ass.loc[self.row, 12]  # spec_download_url
            # organization
            self.ass_dict['organization'] = {}  # a new dictionary in the dictionary
            self.ass_dict['organization']['L1'] = self.ass.loc[self.row, 2]  # Submitter_name
            self.ass_dict['organization']['submitter_unit_id'] = sha256(
                str(self.ass_dict['organization']['L1']) + " " + str(self.ass.loc[self.row, 1]))  # Submitter_id
            self.ass_dict['organization']['L2'] = self.ass.loc[self.row, 3]  # submitter_organisation
            self.ass_dict['organization']['submitter_org_id'] = sha256(
                str(self.ass_dict['organization']['L2']))  # submitter_organisation_id
            self.ass_dict['organization']['L3'] = self.ass.loc[self.row, 4]
            self.ass_dict['organization']['L4'] = self.ass.loc[self.row, 5]  # submitter_address
            self.ass_dict['organization']['L5'] = self.ass.loc[self.row, 6]  # submitter_phone
            self.ass_dict['organization']['L6'] = self.ass.loc[self.row, 8]  # submitter_email
            self.ass_dict['organization']['L7'] = None  # submission_date
            self.ass_dict['organization']['uuid'] = uuid.uuid4()  # organization contact point uuid (?)
            # agent, SDO
            self.ass_dict['agent'] = {}  # a new dictionary in the dictionary
            self.ass_dict['agent']['P3'] = self.ass.loc[self.row, 13]  # sdo_name
            self.ass_dict['agent']['sdo_id'] = sha256(
                str(self.ass_dict['agent']['P3']))  # sdo_id (for the Agent instance)
            self.ass_dict['agent']['P4'] = self.ass.loc[self.row, 15]  # sdo_contact_point
            self.ass_dict['agent']['uuid'] = uuid.uuid4()  # agent contact point uuid (?)
            # submission_rationale
            self.ass_dict['P5'] = self.ass.loc[self.row, 16]  # submission_rationale
            # 'other_evaluations'
            self.ass_dict['P6'] = self.ass.loc[self.row, 17]  # other_evaluations
            # 'considerations'
            self.ass_dict['C1'] = None  # correctness
            self.ass_dict['C2'] = None  # completeness
            self.ass_dict['C3'] = self.ass.loc[self.row, 33]  # egov_interoperability
            # 'io_spec_type'
            self.ass_dict['io_spec_type'] = None  # interoperability specification type
            # additional features
            self.ass_dict['P7'] = None  # submission scope
            self.ass_dict['P8'] = None  # backward and forward compatibility
            self.ass_dict['P9'] = None  # no longer compliance
            self.ass_dict['P10'] = None  # first SDO spec?
            self.ass_dict['C4'] = self.ass.loc[self.row, 34]  # egov_interoperability
            self.ass_dict['C5'] = self.ass.loc[self.row, 35]  # egov_interoperability
        for elem in self.ass_dict['title']:
            if type(self.ass_dict['title'][elem]) is str:
                self.ass_dict['title'][elem] = re.sub("\s+", " ", self.ass_dict['title'][elem]).strip()
        for elem in self.ass_dict['organization']:
            if type(self.ass_dict['organization'][elem]) is str:
                self.ass_dict['organization'][elem] = re.sub("\s+", " ", self.ass_dict['organization'][elem]).strip()
        for elem in self.ass_dict['agent']:
            if type(self.ass_dict['agent'][elem]) is str:
                self.ass_dict['agent'][elem] = re.sub("\s+", " ", self.ass_dict['agent'][elem]).strip()
        return

    def _get_criteria(self):
        """
                ################
                Origin: camss.py
                ################
                Builds a vector with groups of criteria
                :return: nothing, values are kept into a class-scoped vector
                """
        possible_answ = ['The working group is open to all without specific fees, registration, or other conditions.',
                         'All major and minor releases foresee a public review during which collected feedback is publicly visible.',
                         'Use of the specification is royalty-free and its Intellectual Property Right (IPR) policy or licence is aligned with Fair, Reasonable and Non-Discriminatory (F/RAND) principles.',
                         'The working group is open to participation by any stakeholder but requires fees and membership approval.',
                         'All major and minor releases foresee a public review but, during which, collected feedback is not publicly visible.',
                         'YES'
                         ]
        predefined_answ = {
            'W3C (https://www.w3.org)': [
                'W3C has a defined and publicly available Process for the Development and approval process of the specification as a recommended standard. Also, a clear Release Notes tracking the changes of the different versions is archived.\n\nW3C Process document:\nhttps://www.w3.org/2018/Process-20180201/#Policies',
                'W3C has a defined and publicly available Process for the Development and approval process of the specification as a recommended standard, including a public review.\n\nW3C Process document:\nhttps://www.w3.org/2018/Process-20180201/#Policies',
                'The W3C Royalty-Free IPR licenses granted under the W3C Patent Policy apply to all W3C specifications, including this specification.\n\nW3C Patent practice:\nhttps://www.w3.org/TR/patent-practice#ref-AC'],
            'IETF (https://www.ietf.org/)': [
                'IETF has a formal review and approval so that all the relevant stakeholders can formally appeal or raise objections to the development and approval of specifications.\nEach distinct version of an Internet standards-related specification is published as part of the "Request for Comments" (RFC) document series. This archival series is the official publication channel for Internet standards documents and other publications.\nDuring the development of a specification, draft versions of the document are made available for informal review and comment by placing them in the IETF\'s "Internet-Drafts" directory, which is replicated on a number of Internet hosts. This makes an evolving working document readily available to a wide audience, facilitating the process of review and revision.\n\nStandard process IETF:\nhttps://www.ietf.org/standards/process/\n\nInternet Best Current Practices IETF:\nhttps://tools.ietf.org/html/rfc2026',
                'The IETF is a consensus-based group, and authority to act on behalf of the community requires a high degree of consensus and the continued consent of the community. The process of creating and Internet Standard is straightforward: a specification undergoes a period of development and several iterations of review by the Internet community and revision based upon experience, is adopted as a Standard by the appropriate body... and is published. In practice, the process is more complicated, due to (1) the difficulty of creating specifications of high technical quality; (2) the need to consider the interests of all the affected parties; (3) the importance of establishing widespread community consensus; and (4) the difficulty of evaluating the utility of a particular specification for the Internet community. The goals of the Internet Standards Process are:\n- Technical excellence;\n- prior implementation and testing;\n- clear, concise, and easily understood documentation;\n- openness and fairness; and\n- timeliness.\nThe goal of technical competence, the requirement for prior implementation and testing, and the need to allow all interested parties to comment all require significant time and effort. The Internet Standards Process is intended to balance these conflicting goals. The process is believed to be as short and simple as possible without sacrificing technical excellence, thorough testing before adoption of a standard, or openness and fairness.\n\nStandard process IETF:\nhttps://www.ietf.org/standards/process/',
                'Like all the IETF standards, this specification is a free and open technical specification, built on IETF standards and licenses from the Open Web Foundation. Therefore it is licensed on a royalty-free basis.\nNo IPR disclosures have been submitted directly on this RFC.\n\nIntellectual Property Rights in IETF:\nhttps://tools.ietf.org/doc/html/rfc8179'],
            'ETSI (https://www.etsi.org/)' : [
                '',
                '',
                'The ETSI IPR Policy which is part of the ETSI directives seeks to reduce the risk that our standards-making efforts might be wasted if SEPs are unavailable under Fair, Reasonable and Non-Discriminatory (FRAND) terms and conditions.\nThe main objective of the ETSI IPR Policy is to balance the rights and interests of IPR holders to be fairly and adequately rewarded for the use of their SEPs in the implementation of ETSI standards and the need for implementers to get access to the technology defined in ETSI standards under FRAND terms and conditions.\n\nETSI’s intellectual property rights policy:\nhttps://www.etsi.org/intellectual-property-rights',
                'ETSI’s standards-making process has been clearly defined after years of experience. The organisation has adopted the open approach which means direct participation and consensus as a basis to develop standards. All the stakeholders have the opportunity to participate directly in the process of standardisation through the technical committees created to develop ETSI’s technical specifications and standards.\n\nETSI Standard-making process:\nhttps://portal.etsi.org/Resources/Standards-Making-Process/Process',
                'ETSI’s decision-making process includes a public review, where stakeholders involved can provide technical feedback in order to enhance and maximize the quality and accuracy of the standards.\n\nETSI standard-making process:\nhttps://portal.etsi.org/Resources/Standards-Making-Process/Process',
                'ETSI is a European standards development organisation, and as such, all the specifications developed within the organisation are available and can be accessed through its website repository.\n\nETSI standards repository:\nhttps://www.etsi.org/standards#page=1&search=ETSI%20TS%20319%20422&title=1&etsiNumber=1&content=1&version=0&onApproval=1&published=1&withdrawn=1&historical=1&isCurrent=1&superseded=1&startDate=1988-01-15&endDate=2022-07-25&harmonized=0&keyword=&TB=&stdType=&frequency=&mandate=&collection=&sort=1']
            }

        for criterion in self.criteria_.keys():
            index_0 = self.criteria_[criterion][0]
            index = index_0 + 1
            answer = str(self.ass.loc[self.row, index_0]).strip()
            # Score element ID and Value
            self.criteria_[criterion].append(str(uuid.uuid4()))
            if self.scenario == 'EIF':
                option = str(self._new_yesno_choice(str(answer), self.gradients))
                self.criteria_[criterion].append(option)
            else:
                option = str(self._yesno_choice(str(answer)))
                self.criteria_[criterion].append(option)
            # Criterion Justification Id and Judgement text
            self.criteria_[criterion].append(str(uuid.uuid4()))
            text = self.ass.loc[self.row, index]
            text = repr(text)
            text = re.sub(r'"', '\\"', text)
            text = re.sub(r'\\r', '', text)
            if answer in possible_answ[:3] and self.ass.loc[self.row, 15] == 'W3C (https://www.w3.org)':
                self.criteria_[criterion].append(
                    re.sub(r'"', '\\"', repr(predefined_answ['W3C (https://www.w3.org)'][possible_answ.index(answer)])))
            elif answer in possible_answ[:3] and self.ass.loc[self.row, 15] == 'IETF (https://www.ietf.org/)':
                self.criteria_[criterion].append(
                    re.sub(r'"', '\\"',
                           repr(predefined_answ['IETF (https://www.ietf.org/)'][possible_answ.index(answer)])))
            elif answer in possible_answ and self.ass.loc[self.row, 15] == 'ETSI (https://www.etsi.org/)':
                self.criteria_[criterion].append(
                    re.sub(r'"', '\\"',
                           repr(predefined_answ['ETSI (https://www.etsi.org/)'][possible_answ.index(answer)])))
            else:
                self.criteria_[criterion].append(text)
            self.criteria_[criterion].append(str(self.ass.loc[self.row, index_0]))
        return


class Graph:
    def __init__(self, extract: Extractor, ass_: AssessmentScenario = None):
        self.sc = extract.scenario
        self.tool_version = extract.tool_version
        self.dictionary = extract.ass_dict
        self.ass_description = self.get_description()
        self.criteria = extract.criteria
        if ass_ is None:
            self.spec_title = extract.ass_title
            print()
            files = get_files('arti/out/ass/nq/')
            if f'{self.sc}-{self.tool_version}-CAMSSAssessment_{self.spec_title}.nq' not in files:
                print(self.spec_title)
            else:
                print(self.spec_title, "\n", "Reminder: This CAMSS Assessments is already in your local folder!")
            #declare_namespace(ass_)
            self.create_ass_graph()
            os.makedirs('arti/punct/', exist_ok=True)
            calculator = utils.PunctuationCalculator(self.criteria, self.dictionary)
            calculator.generate_punctuation_file()
            #get_punct(extract.criteria, self.dictionary)
            self.create_specs_graph()
        else:
            self.create_criteria_graph()

    def get_description(self):
        if self.sc == 'EIF':
            return "The European Interoperability Framework(EIF) provides guidance to public administrations on how to improve governance of their interoperability activities, establish cross-organisational relationships, streamline processes supporting end-to-end digital services, and ensure that existing and new legislation do not compromise interoperability efforts.This CAMSS Scenario allows to assess the compliance of interoperability specifications with the EIF. The objective of the obtained assessment is to determine the suitability of the assessed interoperability specification for the delivery of interoperable European public services."
        elif self.sc == 'MSP':
            return "The CAMSSs scenario is dedicated to the assessment of formal specificactions in the context of public procurement. The criteria used are laid out in the Annex II of the regulation on standardisation 1025_2012 as requirements for the identification of ICT technical specifications for their use in procurement."
        else:
            return "This CAMSS scenario is dedicated to the assessment of formal technical specification, in general terms. According to the regulation on standardisation 1025/2012, a technical specification is a 'document that prescribes technical requirements to be fulfilled by a product, process, service or system'."

    # def get_predef_judgment(self):

    def create_ass_graph(self=None):
        origin_graph_org = f'<{CAMSSA}{self.dictionary["organization"]["submitter_org_id"]}>'
        origin_graph_contact_org = f'<{CAMSSA}{self.dictionary["organization"]["uuid"]}>'
        origin_graph_ass = f'<{CAMSSA}{self.dictionary["assessment_id"]}>'
        origin_graph_global_sco = f'<{CAMSSA}{uuid.uuid4()}>'
        target_graph_ass = f'<{CAMSSA}>'
        files = get_files('arti/out/ass/nq/')
        if f'{self.sc}-{self.tool_version}-CAMSSAssessment_{self.spec_title}.nq' not in files:
            with open('arti/out/ass/nq/' + f'{self.sc}-{self.tool_version}-CAMSSAssessment_{self.spec_title}.nq', 'w',
                      encoding='utf-8') as fa:
                # assessment
                print(origin_graph_ass + f' <{RDF}type> <{CAV}Assessment> {target_graph_ass} .', file=fa)
                print(origin_graph_ass + f' <{RDF}type> <{OWL}NamedIndividual> {target_graph_ass} .', file=fa)
                print(
                    origin_graph_ass + f' <{CAV}assesses> <{CSSV_RSC}{self.dictionary["title"]["spec_id"]}> {target_graph_ass} .',
                    file=fa)
                # print(
                #     origin_graph_ass + f' <{CAMSS}assessmentDate> "{self.dictionary["assessment_date"]}"^^<{XSD}date> {target_graph_ass} .',
                #     file=fa)
                print(
                    origin_graph_ass + f' <{DCT}issued> "{self.dictionary["assessment_date"]}"^^<{XSD}date> {target_graph_ass} .',
                    file=fa)
                # print(
                #     origin_graph_ass + f' <{CAMSS}submissionDate> "{self.dictionary["organization"]["L7"]}"^^<{XSD}date> {target_graph_ass} .',
                #     file=fa)
                # print(
                #     origin_graph_ass + f' <{CAMSS}toolVersion> <{TOOL}{self.dictionary["tool_version"]}> {target_graph_ass} .',
                #     file=fa)
                print(
                    origin_graph_ass + f' <{CAV}contextualisedBy> <{SC}{self.dictionary["contextualised_by"]["scenario_id"]}> {target_graph_ass} .',
                    file=fa)
                for criterion in self.dictionary['results_in'].keys():
                    print(
                        origin_graph_ass + f' <{CAV}resultsIn> <{CAMSSA}{self.dictionary["results_in"][criterion]["statement_id"]}> {target_graph_ass} .',
                        file=fa)
                #print(origin_graph_ass + f' <{CAV}status> <{STATUS}Complete> {target_graph_ass} .', file=fa)
                print(origin_graph_ass + f' <{DCT}title> "{self.dictionary["title"]["P1"]}"@en {target_graph_ass} .',
                      file=fa)
                print(origin_graph_ass + f' <{PAV}version> "1.0.0"@en {target_graph_ass} .',
                      file=fa)
                print(origin_graph_ass + f' <{CAV}performedBy> {origin_graph_org} {target_graph_ass} .',
                      file=fa)
                print(origin_graph_ass + f' <{CAV}considers> {origin_graph_global_sco} {target_graph_ass} .',
                      file=fa)
                ass_distribution = uuid.uuid4()
                print(origin_graph_ass + f' <{DCAT}distribution> <{CAMSSA}{ass_distribution}> {target_graph_ass} .',
                      file=fa)
                print(
                    f'<{CAMSSA}{ass_distribution}> <{RDF}type> <{OWL}NamedIndividual> {target_graph_ass} .',
                    file=fa)
                print(
                    f'<{CAMSSA}{ass_distribution}> <{RDF}type> <{DCAT}Distribution> {target_graph_ass} .',
                    file=fa)
                print(
                    f'<{CAMSSA}{ass_distribution}> <{DCAT}accessURL> "https://joinup.ec.europa.eu/collection/common-assessment-method-standards-and-specifications-camss"^^<{XSD}anyURI> {target_graph_ass} .',
                    file=fa)
                # organization
                print(origin_graph_org + f' <{RDF}type> <{OWL}NamedIndividual> {target_graph_ass} .', file=fa)
                print(origin_graph_org + f' <{RDF}type> <{ORG}Organization> {target_graph_ass} .', file=fa)
                # print(
                #     origin_graph_org + f' <{CAMSS}contactPoint> <{CAMSSA}{self.dictionary["organization"]["uuid"]}> {target_graph_ass} .',
                #     file=fa)
                print(
                    origin_graph_org + f' <{SCHEMA}contactPoint> <{CAMSSA}{self.dictionary["organization"]["uuid"]}> {target_graph_ass} .',
                    file=fa)
                print(
                    origin_graph_org + f' <{SKOS}prefLabel> "{self.dictionary["organization"]["L1"]} {self.dictionary["organization"]["L2"]}"@en {target_graph_ass} .',
                    file=fa)
                print(
                    origin_graph_contact_org + f' <{RDF}type> <{SCHEMA}ContactPoint> {target_graph_ass} .',
                    file=fa)
                print(origin_graph_contact_org + f' <{RDF}type> <{OWL}NamedIndividual> {target_graph_ass} .', file=fa)
                if self.dictionary["organization"]["L6"] == 'nan':
                    print(
                        origin_graph_contact_org + f' <{SCHEMA}email> "NaN"^^<{XSD}double> {target_graph_ass} .',
                        file=fa)
                else:
                    print(
                        origin_graph_contact_org + f' <{SCHEMA}email> "{self.dictionary["organization"]["L6"]}" {target_graph_ass} .',
                        file=fa)
                # statement
                for criterion in self.dictionary['results_in'].keys():
                    origin_graph_sta = f'<{CAMSSA}{self.dictionary["results_in"][criterion]["statement_id"]}>'
                    print(origin_graph_sta + f' <{RDF}type> <{CAV}Statement> {target_graph_ass} .', file=fa)
                    print(origin_graph_sta + f' <{RDF}type> <{OWL}NamedIndividual> {target_graph_ass} .', file=fa)
                    print(
                        origin_graph_sta + f' <{CAV}judgement> "{self.dictionary["results_in"][criterion]["statement"]}"@en {target_graph_ass} .',
                        file=fa)
                    print(
                        origin_graph_sta + f' <{CAV}refersTo> <{CAMSSA}{self.dictionary["results_in"][criterion]["score_id"]}> {target_graph_ass} .',
                        file=fa)
                # global score
                # Create an instance of the class
                calculator = utils.PunctuationCalculator(self.criteria, self.dictionary)
                # Run the criteria analysis
                ass_punct = calculator.run_criteria()
                # Get the total_overall_score and overall_strength values
                total_overall_score = ass_punct[5][0]  # The total_overall_score is the second to last element
                overall_strength = ass_punct[5][1]  # The overall_strength is the last element
                print(origin_graph_global_sco + f' <{RDF}type> <{CAV}Score> {target_graph_ass} .', file=fa)
                print(origin_graph_global_sco + f' <{RDF}type> <{OWL}NamedIndividual> {target_graph_ass} .', file=fa)
                print(origin_graph_global_sco + f' <{CAV}value> "{round((int(total_overall_score.split("/")[0])/int(total_overall_score.split("/")[1]))*100,2)}%AssessmentScoreAverage"^^<{XSD}string> {target_graph_ass} .', file=fa)
                print(origin_graph_global_sco + f' <{CAV}value> "{round(overall_strength, 2)}%StrengthOfAssessmentScoreAverage"^^<{XSD}string> {target_graph_ass} .', file=fa)
                # score
                for criterion in self.dictionary['results_in'].keys():
                    origin_graph_sco = f'<{CAMSSA}{self.dictionary["results_in"][criterion]["score_id"]}>'
                    print(origin_graph_sco + f' <{RDF}type> <{CAV}Score> {target_graph_ass} .', file=fa)
                    print(origin_graph_sco + f' <{RDF}type> <{OWL}NamedIndividual> {target_graph_ass} .', file=fa)
                    print(
                        origin_graph_sco + f' <{CAV}assignedTo> <{SC}c-{self.dictionary["results_in"][criterion]["criterion_sha_id"]}> {target_graph_ass} .',
                        file=fa)
                    print(
                        origin_graph_sco + f' <{CAV}value> "{self.dictionary["results_in"][criterion]["score"]}"^^<{XSD}string> {target_graph_ass} .',
                        file=fa)  # mirar >int antes >:int

    def create_criteria_graph(self=None):
        origin_graph_cri = f'<{SC}{self.dictionary["contextualised_by"]["scenario_id"]}>'
        target_graph_cri = f'<{SC}>'
        with open('arti/out/crit/nq/' + f'{self.sc}-{self.tool_version}-criteria.nq', 'w') as fc:
            # criteria
            print(origin_graph_cri + f' <{RDF}type> <{CAV}Scenario> {target_graph_cri} .', file=fc)
            print(origin_graph_cri + f' <{RDF}type> <{OWL}NamedIndividual> {target_graph_cri} .', file=fc)
            print(
                origin_graph_cri + f' <{CAV}description> "{self.get_description()}"@en {target_graph_cri} .',
                file=fc)
            for criterion in self.dictionary['results_in'].keys():
                cri_sha_id = self.dictionary["results_in"][criterion]["criterion_sha_id"]
                print(origin_graph_cri + f' <{CAV}includes> <{SC}{cri_sha_id}> {target_graph_cri} .', file=fc)
            print(
                origin_graph_cri + f' <{CAV}purpose> ""@en '
                                   f'{target_graph_cri} .', file=fc)
            # print(
            #     origin_graph_cri + f' <{DCT}title> "{self.dictionary["contextualised_by"]["scenario"]}({self.dictionary["tool_version"]})"@en {target_graph_cri} .',
            #     file=fc)
            print(
                origin_graph_cri + f' <{DCT}title> "{self.dictionary["contextualised_by"]["scenario"]}"@en {target_graph_cri} .',
                file=fc)
            print(
                origin_graph_cri + f' <{OWL}versionInfo> "{self.dictionary["tool_version"]}"@en {target_graph_cri} .',
                file=fc)
            print(
                origin_graph_cri + f' <{DCAT}landingPage> "{self.dictionary["url_eusurvey"]}"^^<{XSD}anyURI> {target_graph_cri} .',
                file=fc)
            for criterion in self.dictionary['results_in'].keys():
                cri_sha_id = self.dictionary["results_in"][criterion]["criterion_sha_id"]
                print(f'<{SC}{cri_sha_id}> <{RDF}type> <{CCCEV}Criterion> {target_graph_cri} .', file=fc)
                print(f'<{SC}{cri_sha_id}> <{RDF}type> <{OWL}NamedIndividual> {target_graph_cri} .', file=fc)
                print(
                    f'<{SC}{cri_sha_id}> <{CCCEV}hasDescription> "{self.dictionary["results_in"][criterion]["criterion_description"]}"@en {target_graph_cri} .',
                    file=fc)

    def create_specs_graph(self=None):
        target_graph_spe = f'<{CSSV_RSC}>'
        files = get_files('arti/out/specs/nq/')
        if f'{self.spec_title}.nq' not in files:
            with open('arti/out/specs/nq/' + f'{self.spec_title}.nq', 'w') as fs:
                # specification ContactPoint
                print(
                    f'<{CSSV_RSC}{self.dictionary["agent"]["uuid"]}> <{RDF}type> <{SCHEMA}ContactPoint> {target_graph_spe} .',
                    file=fs)
                print(
                    f'<{CSSV_RSC}{self.dictionary["agent"]["uuid"]}> <{RDF}type> <{OWL}NamedIndividual> {target_graph_spe} .',
                    file=fs)
                print(
                    f'<{CSSV_RSC}{self.dictionary["agent"]["uuid"]}> <{SCHEMA}contactPoint> <{CSSV_RSC}{self.dictionary["agent"]["sdo_id"]}> {target_graph_spe} .',
                    file=fs)
                if self.dictionary["agent"]["P4"] != self.dictionary["agent"]["P4"]:
                    print(
                        f'<{CSSV_RSC}{self.dictionary["agent"]["uuid"]}> <{SCHEMA}email> "NaN"^^<{XSD}double> {target_graph_spe} .',
                        file=fs)
                else:
                    print(
                        f'<{CSSV_RSC}{self.dictionary["agent"]["uuid"]}> <{SCHEMA}email> "{self.dictionary["agent"]["P4"]}" {target_graph_spe} .',
                        file=fs)
                # specification Standard
                print(
                    f'<{CSSV_RSC}{self.dictionary["title"]["spec_id"]}> <{RDF}type> <{CSSV}{self.dictionary["spec_type"]}> {target_graph_spe} .',
                    file=fs)
                # if self.dictionary["spec_type"] != "Specification":
                #     print(
                #         f'<{CSSV_RSC}{self.dictionary["title"]["spec_id"]}> <{RDF}type> <{CSSV}Specification> {target_graph_spe} .',
                #         file=fs)
                print(
                    f'<{CSSV_RSC}{self.dictionary["title"]["spec_id"]}> <{RDF}type> <{OWL}NamedIndividual> {target_graph_spe} .',
                    file=fs)
                print(
                    f'<{CSSV_RSC}{self.dictionary["title"]["spec_id"]}> <{CSSV}isMaintainedBy> <{CSSV_RSC}{self.dictionary["agent"]["sdo_id"]}> {target_graph_spe} .',
                    file=fs)
                print(
                    f'<{CSSV_RSC}{self.dictionary["title"]["spec_id"]}> <{DCT}title> "{self.dictionary["title"]["P1"]}"@en {target_graph_spe} .',
                    file=fs)
                print(
                    f'<{CSSV_RSC}{self.dictionary["title"]["spec_id"]}> <{DCT}description> "{self.dictionary["title"]["description"]}"@en {target_graph_spe} .',
                    file=fs)
                print(
                    f'<{CSSV_RSC}{self.dictionary["title"]["spec_id"]}> <{PAV}version> "{self.dictionary["title"]["version"]}"@en {target_graph_spe} .',
                    file=fs)
                print(
                    f'<{CSSV_RSC}{self.dictionary["title"]["spec_id"]}> <{DCAT}distribution> <{CSSV_RSC}{self.dictionary["title"]["distribution_id"]}> {target_graph_spe} .',
                    file=fs)
                # specification Distribution
                print(
                    f'<{CSSV_RSC}{self.dictionary["title"]["distribution_id"]}> <{RDF}type> <{OWL}NamedIndividual> {target_graph_spe} .',
                    file=fs)
                print(
                    f'<{CSSV_RSC}{self.dictionary["title"]["distribution_id"]}> <{RDF}type> <{DCAT}Distribution> {target_graph_spe} .',
                    file=fs)
                print(
                    f'<{CSSV_RSC}{self.dictionary["title"]["distribution_id"]}> <{DCAT}downloadURL> "{self.dictionary["title"]["P2"]}"^^<{XSD}anyURI> {target_graph_spe} .',
                    file=fs)
                # specification Organization
                print(
                    f'<{CSSV_RSC}{self.dictionary["agent"]["sdo_id"]}> <{RDF}type> <{OWL}NamedIndividual> {target_graph_spe} .',
                    file=fs)
                print(
                    f'<{CSSV_RSC}{self.dictionary["agent"]["sdo_id"]}> <{RDF}type> <{ORG}Organization> {target_graph_spe} .',
                    file=fs)
                print(
                    f'<{CSSV_RSC}{self.dictionary["agent"]["sdo_id"]}> <{SKOS}prefLabel> "{self.dictionary["agent"]["P3"]}"^^<{XSD}string> {target_graph_spe} .',
                    file=fs)


CAMSS = "http://data.europa.eu/2sa#"
CAMSSA = "http://data.europa.eu/2sa/assessments/"
CAV = "http://data.europa.eu/2sa/cav#"
CCCEV = "http://data.europa.eu/m8g/cccev#"
CSSV = "http://data.europa.eu/2sa/cssv#"
CSSV_RSC = "http://data.europa.eu/2sa/cssv/rsc/"
DCAT = "http://www.w3.org/ns/dcat#"
ORG = "http://www.w3.org/ns/org#"
SC = "http://data.europa.eu/2sa/scenarios#"
SCHEMA = "http://schema.org/"
PAV = "http://purl.org/pav/"
#STATUS = "http://data.europa.eu/2sa/rsc/assessment-status#"
#TOOL = "http://data.europa.eu/2sa/rsc/toolkit-version#"

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
OWL = "http://www.w3.org/2002/07/owl#"
XSD = "http://www.w3.org/2001/XMLSchema#"
DCT = "http://purl.org/dc/terms/"
SKOS = "http://www.w3.org/2004/02/skos/core#"


# Namespaces
def declare_namespace(g):
    CAMSS_ = Namespace("http://data.europa.eu/2sa#")
    CAMSSA_ = Namespace("http://data.europa.eu/2sa/assessments/")
    CAV_ = Namespace("http://data.europa.eu/2sa/cav#")
    CCCEV_ = Namespace("http://data.europa.eu/m8g/cccev#")
    CSSV_ = Namespace("http://data.europa.eu/2sa/cssv#")
    CSSV_RSC_ = Namespace("http://data.europa.eu/2sa/cssv/rsc/")
    SC_ = Namespace("http://data.europa.eu/2sa/scenarios#")
    #STATUS_ = Namespace("http://data.europa.eu/2sa/rsc/assessment-status#")
    #TOOL_ = Namespace("http://data.europa.eu/2sa/rsc/toolkit-version#")
    SCHEMA_ = Namespace("http://schema.org/")
    PAV_ = Namespace("http://purl.org/pav/")
    DCT_ = "http://purl.org/dc/terms/"
    g.bind('camss', CAMSS, replace=True)
    g.bind('cav', CAV_, replace=True)
    g.bind('cssv', CSSV_, replace=True)
    g.bind('camssa', CAMSSA_, replace=True)
    g.bind('cssvrsc', CSSV_RSC_, replace=True)
    #g.bind('status', STATUS_, replace=True)
    #g.bind('tool', TOOL_, replace=True)
    g.bind('sc', SC_, replace=True)
    g.bind('schema', SCHEMA_, replace=True)
    g.bind('pav', PAV_, replace=True)
    g.bind('dct', DCT_, replace=True)
    g.bind('cccev', CCCEV_, replace=True)
    return g


def __merge_graphs__():
    for files_root in ['arti/out/ass/nq/', 'arti/out/crit/nq/', 'arti/out/specs/nq/']:
        # Creating a list of filenames
        filenames = get_files(files_root)
        # Open file3 in write mode
        if files_root == 'arti/out/ass/nq/':
            with open('arti/out/ass/ass-graph.nq', 'w', encoding='utf-8') as outfile:
                # Iterate through list
                for names in filenames:
                    # Open each file in read mode
                    with open(files_root + names, 'r') as infile:
                        # read the data from file1 and
                        # file2 and write it in file3
                        for line in infile:
                            outfile.write(line)
        if files_root == 'arti/out/crit/nq/':
            with open('arti/out/crit/crit-graph.nq', 'w', encoding='utf-8') as outfile:
                # Iterate through list
                for names in filenames:
                    # Open each file in read mode
                    with open(files_root + names, 'r') as infile:
                        # read the data from file1 and
                        # file2 and write it in file3
                        outfile.write(infile.read())
        if files_root == 'arti/out/specs/nq/':
            with open('arti/out/specs/specs-graph.nq', 'w', encoding='utf-8') as outfile:
                # Iterate through list
                for names in filenames:
                    # Open each file in read mode
                    with open(files_root + names, 'r') as infile:
                        # read the data from file1 and
                        # file2 and write it in file3
                        outfile.write(infile.read())
            log(f'Merging CAMSS Assessments Graphs, CAMSS Scenarios and Critera Graphs and Specifications Graphs into (cumulative) NQuads dataset files...',
                nl=False)
            print()
            print("WARNING: this merge action is only covering the CAMSS Assessments you converted in your personal folder...","\n"
                  "... the merge file to be shared with CELLAR should also include the CAMSS Scenario criteria (find in /crit folder")
            print("Done!")


def convert_graph_to(target: str):
    if target.lower() == 'turtle':
        target = 'ttl'
        extension = 'ttl'
    elif target.lower() == 'json-ld':
        target = 'json-ld'
        extension = 'jsonld'
    # try:
    for files_root in ['arti/out/ass/nq/', 'arti/out/crit/nq/', 'arti/out/specs/nq/']:
        # Creating a list of filenames
        filenames = get_files(files_root, exclude=['ttl', 'json-ld'])
        for file in filenames:
            head = file[:-3]
            new_file = files_root.split("/")
            new_file.remove('nq')
            new_file.remove('')
            new_dir = '/'.join(new_file) + f'/{target}/'
            os.makedirs(new_dir, exist_ok=True)
            g = rdflib.ConjunctiveGraph()
            data = open(files_root + file, 'rb')
            g.parse(data, format='nquads')
            if target == 'ttl':
                g = declare_namespace(g)
            g.serialize(format=target, destination=new_dir + head + '.' + extension)
    for files_root in ['arti/out/ass/', 'arti/out/crit/', 'arti/out/specs/']:
        # Creating a list of filenames
        filenames = get_files(files_root, exclude=['nq', 'ttl', 'json-ld', 'ass-graph.jsonld', 'specs-graph.jsonld',
                                                   'crit-graph.jsonld', 'ass-graph.ttl', 'specs-graph.ttl',
                                                   'crit-graph.ttl', 'CAMSS_Ontology_Assessments_graph.ttl'])
        for file in filenames:
            head = file[:-3]
            g = rdflib.ConjunctiveGraph()
            data = open(files_root + file, 'rb')
            g.parse(data, format='nquads')
            print(file)
            if target == 'ttl':
                g = declare_namespace(g)
            g.serialize(format=target, destination=files_root + head + '.' + extension)
    print('Transformation Done!')
    # except:
    #    pass


def log(message: str, nl: bool = True, level: str = 'i'):
    """
    ################
    Origin: camss.py
    ################
    """
    print(message, end='' if not nl else '\n')
    if level == 'i':
        logging.info(message)
    elif level == 'w':
        logging.warning(message)


def xst_file(path: str) -> bool:
    """
    ################
    Origin: camss.py
    ################
    Checks whether a file or directory exists or not.
    :param path:  the path to the dir or file
    :return: the result of the checking
    """
    return os.path.isdir(path) or os.path.isfile(path)


def get_files(root_dir: str, exclude: [] = None) -> (str, str, str):
    """
    ################
    Origin: camss.py
    ################
    Returns lazily and recursively each path file name, the file name, extension and an index number from
    inside the folders of a root folder
    :param root_dir: the initial folder with the directories and files
    :param exclude: list of files or directories to not get into
    :return: file absolute path, file name, extension, and its index number
    """
    exclude = [] if not exclude else exclude
    xst_file(root_dir)
    files = []
    # i = 0 # number of xlsx files to be processed
    for file in glob.iglob(root_dir + '/**', recursive=False):
        xpath = PurePath(file)
        if xpath.name not in exclude:
            files.append(xpath.name)
    return files


def sha256(text: str) -> str:
    """
    ################
    Origin: camss.py
    ################
    Generates a SHA256 hash of a text
    :param text: the text to digest
    :return: the hash as a text
    """
    if text:
        return hashlib.sha256(text.encode()).hexdigest()
    else:
        raise Exception("No sha256-based id generated because no thruty provided.")


def __extract_file_assessments__(root_dir: str, ass_files: list):
    """
    ################
    Origin: camss.py
    ################
    """
    for file in ass_files:
        # log(f"Extracting assessments from '{file}'...", nl=False)
        ass_file = Extractor(root_dir + '/' + file)
        len_ass = len(ass_file.ass_df)
        row = 1
        print(ass_file.scenario + ' Scenario ' + 'v' + ass_file.tool_version)
        while row + 4 <= len_ass:
            # log(f"Extracting data from the {row}º Assessment in '{file}' into a dictionary...",
            # nl=False)
            extractor = Extractor(root_dir + '/' + file, row + 3)
            row += 1
            # print(f"*{extractor.ass_dict['title']['P1']}* specification retrieved!")
            os.makedirs('arti/out', exist_ok=True)
            os.makedirs('arti/out/ass', exist_ok=True)
            os.makedirs('arti/out/ass/nq', exist_ok=True)
            os.makedirs('arti/out/crit', exist_ok=True)
            os.makedirs('arti/out/crit/nq', exist_ok=True)
            os.makedirs('arti/out/specs', exist_ok=True)
            os.makedirs('arti/out/specs/nq', exist_ok=True)
            Graph(extract=extractor)
            Graph(extract=extractor, ass_=ass_file)
            # print(f"*{extractor.ass_dict['title']['P1']}* graph created!")
            # print()
            # progress_bar(file, row, extractor.ass_dict['title']['P1'])

def slash(path) -> str:
    """
    ################
    Origin: camss.py
    ################
    Will add the trailing slash if it's not already there.
    :param path: path file name
    :return: slashed path file name
    """
    return os.path.join(path, '')


def __help__():
    print(
        """
        CAMSS Python utilities
        European Commission, ISA2 Programme, DIGIT
        camss@everis.nttdata.com
        contributor: mailto:enric.staromiejski.torregrosa@everis.nttdata.com
        contributor: mailto:juan.carlos.segura.fernandez.carnicero@everis.nttdata.com
        Licence UPL (https://joinup.ec.europa.eu/collection/eupl/about)
        Build _
        Version _._

        Command-line syntax:
        -------------------

        python camssXLSX2NQ.py <folder_Assessments> <out_Graphs> 
        """)


def run(param: str = 'arti/in/'):
    """
    Use it to run the code from a python console, Jupyter Lab or Notebook, etc.
    """
    __pipeline__(param)
    return


def __pipeline__(input_folder: str):
    """
    ################
    Origin: camss.py
    ################
    """
    for path in glob.iglob(input_folder + '/**', recursive=False):
        if not input_folder or len(input_folder) == 0:
            __help__()
            return
        __extract_file_assessments__(path, get_files(path))
    print()
    log("All graphs successfully created!")
    print()


def main(argv: []):
    """
    ################
    Origin: camss.py
    ################
    Runs the code from console command line
    :param argv: the input folder
    """
    __pipeline__(argv[0])
    return


if __name__ == '__main__':
    '''
    ################
    Origin: camss.py
    ################
    '''
    main(sys.argv[1:])