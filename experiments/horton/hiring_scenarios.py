import os

import dotenv
import json
import re
import openai
import time
import sqlite3
import json

from dotenv import load_dotenv
load_dotenv()

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

    def __init__(self, education, major, experience, wage_ask):
        self.education = education
        self.major = major 
        self.experience = experience
        self.wage_ask = wage_ask

    def toJSON(self):
        return exclude_non_serializable_entries(self.__dict__)
                        
    @property
    def description(self):
        return f"An {self.major} {self.education} graduate. Has {self.experience}. Requests ${self.wage_ask}/hour."
  
        
class Scenario:

    def __init__(self, job, applicants):
        self.job = job
        self.applicants = applicants
        self.job.add_applicants(self.applicants)
        self.applications_json = [a.toJSON() for a in applicants]
        self.job_json = job.toJSON()
        
    def toJSON(self):
        return exclude_non_serializable_entries(self.__dict__)

class Decision:

    def __init__(self, scenario):
        self.scenario = scenario
        self.prompt = scenario.job.create_prompt()

    def toJSON(self):
        return exclude_non_serializable_entries(self.__dict__)
    
    def get_decision(self):
        
        self.choice_raw = openai.Completion.create(
            model="text-davinci-003",
            prompt = self.prompt,
            max_tokens=150,
            temperature=0
        )
        self.choice = self.choice_raw['choices'][0]['text'].strip()
    
        self.hired_person_raw  = openai.Completion.create(
            model="text-davinci-003",
            prompt = "In this text find who was hired: " + self.choice + "Person: ",
            max_tokens=150,
            temperature=0)
        self.hired_person = self.hired_person_raw['choices'][0]['text'].strip()
        return dict({"choice_raw": self.choice_raw,
                     "choice":self.choice,
                     "hired_person_raw": self.hired_person_raw,
                     "hired_person" : self.hired_person})


jobs = ["Dishwasher", "Salesperson"]
more_experienced_wage_offers = [14, 15, 16, 17]

from threading import Thread

class GetDecisionThread(Thread):

    def __init__(self, scenario):
        super().__init__()
        self.scenario = scenario

    def run(self):
        self.decision_obj = Decision(self.scenario)
        self.decision = self.decision_obj.get_decision()
        self.result = dict({"scenario": self.scenario.toJSON(),
                            "decision_obj": self.decision_obj.toJSON(),
                            "decision":self.decision})
        
threads = []
for job in jobs:
    print(job)
    for wage in more_experienced_wage_offers:
        print(wage)
        J = Job(job, "You have a limited budget")
        a = Worker("CS", "MIT", "some labor market experience", 15)
        b = Worker("CS", "MIT", "extensive labor market experience", wage)
        applicants = [a,b]
        s = Scenario(J, applicants)
        thread = GetDecisionThread(s)
        thread.start()
        threads.append(thread)
        #d = Decision(s)
        #d.get_decision()

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
        
observations = []
for thread in threads:
    thread.join()
    observations.append(thread.result)

 
write_data("../data/horton.db", observations, flush = False)
           
        



