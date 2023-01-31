import openai
import sqlite3
import time
import json

from threading import Thread

class RunExperimentThread(Thread):
    def __init__(self, subject, scenario, model = "text-davinci-003"):
        super().__init__()
        self.subject = subject
        self.scenario = scenario
        self.model = model
   
    def run(self):
        results= Experiment._run(self.subject, self.scenario, self.model)
        self.observation = dict({
            'subject':self.subject.toJSON(),
            'scenario':self.scenario.toJSON(),
            'result': results,
        })
        

class Experiment:
    """Can we also set model, temperature & tokens here"""
    def __init__(self, subjects, scenarios, model = "text-davinci-003"):
        self.subjects = subjects
        self.scenarios = scenarios
        self.model = model
        self.observations = [] 

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
                          sort_keys=True, indent=4)
    
    @staticmethod
    def get_response(prompt, temperature = 0.0, model="text-davinci-003", max_tokens = 150):
        choice_raw = openai.Completion.create(
            model = model,
            prompt = prompt,
            max_tokens = max_tokens,
            temperature= temperature
        )
        choice = choice_raw['choices'][0]['text'].strip()
        return dict({"choice_raw": choice_raw, "choice":choice, "model":model, "temperature":temperature, "max_tokens":max_tokens})

    @staticmethod
    def get_answer(prompt):
        """Parses the output to find the choice"""
        choice_raw = openai.Completion.create(
            model="text-davinci-003",
            prompt = f"Response was: \"{prompt}\"  Return single letter for choice that was selected (e.g., a, b, c...):",
            max_tokens=150,
            temperature=0
        )
        return choice_raw['choices'][0]['text'].strip()

    @staticmethod
    def _run(subject, scenario, model = "text-davinci-003"):
        d = scenario.letters_to_budget_shares()
        prompt = scenario.gen_prompt(subject.view)
        while True:
            try:
                results = Experiment.get_response(prompt, temperature = 0.0, model  = model)
                answer = Experiment.get_answer(results['choice']).lower()
                if answer in d.keys():
                    preferred_auto_share = d[answer]
                else:
                    print("Could not parse")
                    preferred_auto_share = -1
                break
            except openai.error.ServiceUnavailableError as e:
                print(f"Experiment error: {e}")
                time.sleep(30)          
        return dict({"results":results, "prompt":prompt, 'answer':answer, 'preferred_auto_share':preferred_auto_share})
        
    def run_all(self, debug = False):
        print(f"Running {len(self.subjects) * len(self.scenarios)} scenarios")
        counter = 0
        threads = []
        for subject in self.subjects:
            for scenario in self.scenarios:
                counter += 1
                if debug:
                    results = "here are some results"
                    answer = 'a'
                else:
                    thread = RunExperimentThread(subject = subject, scenario = scenario, model = self.model)
                    thread.start()
                    threads.append(thread)
        for thread in threads:
            thread.join()
            self.observations.append(thread.observation)

    def write_data(self, database_string, flush = False):
        conn = sqlite3.connect(database_string)
        cursor = conn.cursor()
        if flush:
            cursor.execute("DROP TABLE IF EXISTS responses")
            cursor.execute("DROP TABLE IF EXISTS experiments")
        cursor.execute("CREATE TABLE IF NOT EXISTS experiments (note TEXT)")
        cursor.execute("INSERT INTO experiments VALUES (?)", (f"Experiment:{time.time()}",))
        experiment_id = cursor.lastrowid
        cursor.execute("CREATE TABLE IF NOT EXISTS responses (experiment_id INTEGER, observation TEXT, FOREIGN KEY(experiment_id) REFERENCES experiments(id))")        
        for obs in self.observations:
             cursor.execute("INSERT INTO responses VALUES (?,?)", (experiment_id, json.dumps(obs)))
        conn.commit()
