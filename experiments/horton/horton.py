import os

import dotenv
import json
import re
import openai
import time
import sqlite3
import json
import random
import copy

from dotenv import load_dotenv
load_dotenv()

MAX_FAILURES = 3 
openai.api_key = os.getenv('OPENAI_API_KEY')


import json

def exclude_non_serializable_entries(dictionary):
    new_dictionary = {}
    for key, value in dictionary.items():
        try:
            json.dumps(value)
            new_dictionary[key] = value
        except TypeError:
            pass
    return new_dictionary


###############
## Create a job
###############

class Job:

    def __init__(self, role, budget_language):
        self.role = role
        self.budget_language = budget_language
        self.ats = []
        self.record_id = None

    def toJSON(self):
        return exclude_non_serializable_entries(self.__dict__)
 
    def add_applicants(self, applicants):
        counter = 1 
        for applicant in applicants:
            self.ats.extend([f"Person {counter}: {applicant.description}"])
            counter += 1
        self.num_candidates = len(self.ats)
        
    def create_prompt(self):
        candidate_list = "\n".join(self.ats)
        prompt = f"""
You are hiring for the role "{self.role}."
{self.budget_language}
You have {self.num_candidates} candidates.

{candidate_list}

Who would you hire? You have to pick one.
        """
        return prompt
    

class Worker:

    def __init__(self, education, experience, wage_ask):
        self.education = education
        self.experience = experience
        self.wage_ask = wage_ask

    def toJSON(self):
        return exclude_non_serializable_entries(self.__dict__)
                        
    @property
    def description(self):
        return f"Has {self.experience} year(s) of experience in this role. Requests ${self.wage_ask}/hour."
  
        
class Scenario:

    def __init__(self, job, applicants, min_wage, pair_index):
        self.job = job
        self.applicants = applicants
        self.min_wage = min_wage
        self.job.add_applicants(self.applicants)
        self.applications_json = [a.toJSON() for a in applicants]
        self.job_json = job.toJSON()
        self.pair_index = pair_index
        
    def toJSON(self):
        return exclude_non_serializable_entries(self.__dict__)

class Decision:

    def __init__(self, scenario):
        self.scenario = scenario
        self.prompt = scenario.job.create_prompt()

    def toJSON(self):
        return exclude_non_serializable_entries(self.__dict__)
    
    def get_decision(self):
        failure_count = 0
        while True and failure_count < MAX_FAILURES:
            try:
                self.choice_raw = openai.Completion.create(
                    model="text-davinci-003",
                    prompt = self.prompt,
                    max_tokens=150,
                    temperature=0
                )
                self.choice = self.choice_raw['choices'][0]['text'].strip()
                break
            except openai.error.ServiceUnavailableError as e:
                print(f"Experiment error: {e}")
                failure_count += 1 
                time.sleep(30)          

        self.hired_person_raw  = openai.Completion.create(
            model="text-davinci-003",
            prompt = "In this text find who was hired: " + self.choice + "Person: ",
            max_tokens=150,
            temperature=0)
        self.hired_person = self.hired_person_raw['choices'][0]['text'].strip()
        return dict({"choice_raw": self.choice_raw,
                     "choice":self.choice,
                     "hired_person_raw": self.hired_person_raw,
                     "hired_person" : self.hired_person
        })


## Construct workers

experience_levels = [0, 1]
education_levels = ["high school graduate"]
jobs = ["Dishwasher", "Custodian", "Home Health Aide", "Waiter", "Laborer", "Parking Lot Attendant"]

wage_asks = [12, 13, 14, 15, 16, 17, 18, 19, 20]
min_wages = [0, 15]

workers = []

for education in education_levels:
    for wage_ask in wage_asks:
        for experience in experience_levels:
            w = Worker(education = education, experience = experience, wage_ask = wage_ask)
            workers.append(w)

from threading import Thread

class GetDecisionThread(Thread):

    def __init__(self, scenario):
        super().__init__()
        self.scenario = scenario

    def run(self):
        self.decision_obj = Decision(self.scenario)
        while True:
            try:
                self.decision = self.decision_obj.get_decision()
                break
            except:
                time.sleep(3)
        self.result = dict({"scenario": self.scenario.toJSON(),
                            "decision_obj": self.decision_obj.toJSON(),
                            "decision":self.decision})


def write_data(database_string, observations, flush = False):
    conn = sqlite3.connect(database_string)
    cursor = conn.cursor()
    if flush:
        cursor.execute("DROP TABLE IF EXISTS responses")
        cursor.execute("DROP TABLE IF EXISTS experiments")
    cursor.execute("CREATE TABLE IF NOT EXISTS experiments (note TEXT)")
    cursor.execute("INSERT INTO experiments VALUES (?)", (f"Experiment:{time.time()}",))
    experiment_id = cursor.lastrowid
    cursor.execute("CREATE TABLE IF NOT EXISTS responses (experiment_id INTEGER, observation TEXT, FOREIGN KEY(experiment_id) REFERENCES experiments(id))")        
    for obs in observations:
        cursor.execute("INSERT INTO responses VALUES (?,?)", (experiment_id, json.dumps(obs)))
        conn.commit()

if False:
    job = "Dishwasher"
    min_wage = 0
    pair_index = 1
    J = Job(job, "The typical hourly rate for this role is $12/hour.")
    a = random.choice(workers)
    b = random.choice(workers)
    applicants = [a,b]
    s = Scenario(job = J, applicants = applicants, min_wage = min_wage, pair_index = pair_index)
    print(s.job.create_prompt())


    
max_attempts = 5
num_hiring_scenarios = 30
threads = []
pair_index = -1
for wage_ask in [12, 13, 14, 15, 16, 17]:
    job = "Dishwasher"
    for _ in range(num_hiring_scenarios):
        J = Job(job, "The typical wage for this job is $12/hour.")
        a_base = Worker(education = "", experience = 1, wage_ask = wage_ask)
        b_base = Worker(education = "", experience = 0, wage_ask = 13)
        pair_index += 1 
        for min_wage in min_wages:
            a = copy.deepcopy(a_base)
            b = copy.deepcopy(b_base)
            if a.wage_ask < min_wage:
                a.wage_ask = min_wage
            if b.wage_ask < min_wage:
                b.wage_ask = min_wage
            applicants = [a,b]
            s = Scenario(job = J, applicants = applicants, min_wage = min_wage, pair_index = pair_index)
            wait = 1
            attempts = 0
            while True and attempts < max_attempts:
                try:
                    thread = GetDecisionThread(s)
                    thread.start()
                    break
                except Exception as e:
                    print("Rate limit")
                    time.sleep(wait)
                    wait = 2 * wait 
                    attempts += 1 
            threads.append(thread)
            
observations = []

for thread in threads:
    thread.join()
    observations.append(thread.result)


write_data("../../data/horton.db", observations, flush = False)
                   



