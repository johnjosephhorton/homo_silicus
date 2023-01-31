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

from threading import Thread

openai.api_key = os.getenv('OPENAI_API_KEY')

MAX_FAILURES = 4

scenarios = dict({
    "Berk29": ((400, 400), (750, 400)),
    "Barc2": ((400, 400), (750, 375)),
    "Berk23": ((800, 200), (0, 0)),
    "Barc8": ((300, 600), (700, 500)),
    "Berk15": ((200, 700), (600, 600)),
    "Berk26":((0, 800), (400, 400))
})

def create_prompt(scenario, personality):
    left_a, left_b = scenario[0]
    right_a, right_b = scenario[1]
    return f"""You are deciding on allocation for yourself and another person, Person A. 
{personality}

    Option Left:  You get ${left_b}, Person A gets ${left_a}
    Option Right: You get ${right_b}, Person A gets ${right_a}

    What do you choose, with one word [Left, Right]?"""


def get_decision(scenario, personality, scenario_name, model):
    prompt = create_prompt(scenario, personality)
    failure_count = 0
    while True and failure_count < MAX_FAILURES:
        try:
            choice_raw = openai.Completion.create(
                model= model,
                prompt = prompt,
                max_tokens=150,
                temperature=0
            )
            choice_text = choice_raw['choices'][0]['text'].strip()
            break
        except openai.error.ServiceUnavailableError as e:
            print(f"Experiment error: {e}")
            failure_count += 1 
            time.sleep(30)          

    return dict({"choice_raw": choice_raw,
                 "choice_text": choice_text,
                 "choice": "Left" if "left" in choice_text.lower() else "Right", 
                 "scenario": scenario,
                 "personality":personality,
                 "model":model,
                 "scenario_name":scenario_name,
                 "prompt":prompt})

class GetDictatorChoiceThread(Thread):

    def __init__(self, scenario, personality, scenario_name, model):
        super().__init__()
        self.scenario = scenario
        self.personality = personality
        self.scenario_name = scenario_name
        self.model = model

    def run(self):
        self.decision = get_decision(scenario = self.scenario, personality = self.personality, scenario_name = self.scenario_name, model = self.model)

models_described = dict({
    "text-davinci-003": ("Most capable GPT-3 model. Can do any task the other models can do, often with higher quality, longer output and better instruction-following. Also supports inserting completions within text.",
                         "4,000 tokens",
                         "Up to Jun 2021"),
    "text-curie-001": ("Very capable, but faster and lower cost than Davinci.",
                       "2,048 tokens",
                       "Up to Oct 2019"), 
    "text-babbage-001": ("Capable of straightforward tasks, very fast, and lower cost.",
                         "2,048 tokens",
                         "Up to Oct 2019"),
    "text-ada-001": ("Capable of very simple tasks, usually the fastest model in the GPT-3 series, and lowest cost.",
                     "2,048 tokens",
                     "Up to Oct 2019")}
)

models = models_described.keys()
personalities = [
    "",
    "You only care about fairness between players",
    "You only care about your own pay-off",
    "You only care about the total pay-off of both players"]
 
threads = []
for model in models:
    for personality in personalities:
        for scenario_name, scenario in scenarios.items():
            thread = GetDictatorChoiceThread(scenario = scenario, personality = personality, scenario_name = scenario_name, model = model)
            thread.start()
            threads.append(thread)
    
observations = []
for thread in threads:
    thread.join()
    observations.append(thread.decision)

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



write_data("../../data/charness_rabin.db", observations, flush = False)
