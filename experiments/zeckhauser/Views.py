import random
import openai
from Scenario import Scenario
from Subject import Subject
from Experiment import Experiment
import os
import openai
from dotenv import load_dotenv
load_dotenv()
from threading import Thread

from collections import Counter

attitude_adjustments = [
    "Make this view more extreme",
    "Make this view more netural",
    "Take the opposite position of this view"
]

def adjust_view(adjust, current_view):
    prompt = f"{adjust}: {current_view}"
    raw = openai.Completion.create(
                model="text-davinci-003",
                prompt = prompt,
                max_tokens=150,
                temperature=0
    )
    answer = raw['choices'][0]['text'].strip()
    return answer


def get_result(prompt):
    while True:
        try:
            raw = openai.Completion.create(
                model="text-davinci-003",
                prompt=f"{prompt}:",
                max_tokens=150,
                temperature=0
            )
            answer=raw['choices'][0]['text'].strip()
            break
        except openai.error.ServiceUnavailableError as e:
            print(f"Service unavailable:{e}")
            time.sleep(30)          
    return answer


class View:
    def __init__(self, view, prompt = None, target_auto = None):
        self.view = view
        self.prompt = prompt
        self.target_score = target_auto
        self.score = self.get_score()

    def __repr__(self):
        return f"<View: \"{self.view}\", Score: {self.score}>"

    def get_score(self, options = (90, 75, 25, 10)):
        scenario = Scenario(options, None)
        subject = Subject(1, self.view)
        r = Experiment._run(subject, scenario)
        answer = r['answer'].lower()
        d = scenario.letters_to_budget_shares()
        if answer in d.keys():
           return d[answer]
        else:
           print(f"Could not determine score, response is:\"{answer}\"")
           return None

def gen_view():
    heads = random.choice([True, False])
    if heads:
        option1, option2 = "car", "highway"
    else:
        option1, option2 = "highway", "car"
    options = [
        f"{option1} safety is the most important thing.",
        f"{option1} safety is a terrible waste of money; we should only fund {option2} safety.",
        f"{option1} safety is all that matters. We should not fund {option2} safety.",
        f"{option1} safety and {option2} safety are equally important",
        f"{option1} safety is slightly more important thatn {option2} safety",
        f"I don't really care about {option1} safety or {option2} safety"
    ]
    return View(random.choice(options))

def gen_view_advanced(auto = None):
    modifiers = ["horrifying", "abysmal", "terrible", "poor", "mediocre", "ok", "good",
                 "excellent", "superb", "impeccable", "glorious"]
    modifiers.reverse()
    if not auto:
        auto = random.choice(list(range(0,110,10)))
    car_adjective = modifiers[auto // 10]
    highway_adjective = modifiers[10 - auto // 10]
    coin_flip = random.choice([True, False])
    if coin_flip:
        prompt = f"""Imagine a person thinks that {100-auto}% of funding should go towards creating safer highways and {auto}% to safer cars. Create a viewpoint that person might have, as that person. One sentence."""        
        new_view = View(view = get_result(prompt), prompt = prompt, target_auto = auto)
    else:
        new_view = View(f"Car safety in this country is {car_adjective} while highway safety is {highway_adjective}")
    return new_view

class GetView(Thread):
    def __init__(self):
        super().__init__()
   
    def run(self):
        self.view = gen_view()

class Views(list):

    def mean_score(self):
        return sum([s.score for s in self]) / len(self)

    def tally(self):
        return Counter([s.score for s in self])

    def create_views(self, num_views):
        threads = []
        for _ in range(num_views):
            print(f"Creating view: {_}")
            thread = GetView()
            thread.start()
            threads.append(thread)
   
        for thread in threads:
            thread.join()
            self.append(thread.view)
        print("Completed")
