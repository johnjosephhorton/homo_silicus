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

def create_prompt(new_price, politics, neutral):
    if neutral:
        store_action = "changes the price to"
    else:
        store_action = "raises the price to"
    prompt = f"""A hardware store has been selling snow shovels for $15. The morning after a large snowstorm, the store {store_action} ${new_price}. 

Please rate this action as:
1) Completely Fair 
2) Acceptable
3) Unfair 
4) Very Unfair

You are a {politics}.
What is your choice [1, 2, 3, or 4]:"""
    return prompt
    
openai.api_key = os.getenv('OPENAI_API_KEY')

MAX_FAILURES = 4


def get_decision(new_price, politics, neutral, model = "text-davinci-003"):
    prompt = create_prompt(new_price, politics, neutral)
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
                 "choice": choice_text, 
                 "new_price": new_price,
                 "neutral": neutral,
                 "politics":politics,
                 "model":model,
                 "prompt":prompt})

class GetKKTChoiceThread(Thread):

    def __init__(self, new_price, politics, neutral, model):
        super().__init__()
        self.new_price = new_price
        self.politics = politics
        self.neutral = netural
        self.model = model

    def run(self):
        self.decision = get_decision(new_price = self.new_price, politics = self.politics, neutral = self.neutral, model = self.model)

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

models = ["text-davinci-003"]

political_views = [
    "socialist",
    "leftist",
    "liberal",
    "moderate",
    "liberterian", 
    "conservative",
]

new_prices = [16, 20, 40, 100]

threads = []
for model in models:
    for new_price in new_prices:
        for politics in political_views:
            for netural in [True, False]:
                thread = GetKKTChoiceThread(new_price = new_price, politics = politics, neutral = netural, model = model)
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


write_data("../../data/kkt.db", observations, flush = False)
