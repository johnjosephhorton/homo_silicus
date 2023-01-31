import os

import dotenv
import json
import re
import time
import sqlite3
import json
import random
import time
import pprint

from collections import Counter

import openai
from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')
    
from Scenario import Scenario
from Subject import Subject
from Experiment import Experiment
from Views import Views
from Views import View

def flatten(lst):
    result = []
    for i in lst:
        if isinstance(i, list):
            result.extend(flatten(i))
        else:
            result.append(i)
    return result

print("Creating views")
views = Views()
views.create_views(100)

print(views.tally())

print("Creating subjects")
subjects = [Subject(score = v.score, view = v.view) for v in views]

options = (70, 30, 60, 50)
scenarios = [Scenario(options, status_quo) for status_quo in list(options) + [None]]
experiment = Experiment(subjects, scenarios, "text-ada-001")

print("Running the experiment")
experiment.run_all()

print("Writing data")
experiment.write_data("../data/zeckhauser_modular.db")
