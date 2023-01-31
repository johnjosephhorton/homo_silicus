import os

import dotenv
import json
import re
import time
import sqlite3
import json
import random
import time

import openai
from dotenv import load_dotenv
load_dotenv()

class Scenario:

    def __init__(self, options, status_quo = None):
        self.options = options
        self.status_quo = status_quo
        self.base_prompt = """The National Highway Safety Commission is deciding how to allocate its budget between two safety research programs: i) improving automobile safety (bumpers, body, gas tank configurations, seatbelts) and ii) improving the safety of interstate highways (guard rails, grading, highway interchanges, and implementing selective reduced speed limits).
"""
        header = "abcdefghijklmnopqrstuvwxyz"
        self.ask = f"Please choose your most preferred option in light of your views {[header[h] for h in range(len(options))]}:"

    def __repr__(self):
        return json.dumps(dict({'options':self.options, 'status_quo':self.status_quo}))

    def toJSON(self):
        return dict({'options':self.options, 'status_quo':self.status_quo})
    
    def create_option(self,auto):
        return f"Allocate {auto}% to auto safety and {100 - auto}% to highway safety"

    def create_option_status_quo(self, auto):
        if self.status_quo > auto:
            return f"Decrease auto program by {self.status_quo - auto}% of budget and raise the highway program by like amount"
        if self.status_quo == auto:
            return f"Maintain present budget amounts for the programs"
        if self.status_quo < auto:
            return f"Decrease the highway program by {auto - self.status_quo}% of budget and raise the auto program by like amount"

    def state_status_quo(self, auto):
        return f"The current budget allocation is {auto}% to auto safety and {100-auto}% to highway safety."

    def letters_to_budget_shares(self):
        headers = "abcdefghijklmnopqrstuvwxyz"
        return dict({headers[i]:o for i,o in enumerate(self.options)})

    def multiple_choice(self, views):
        """Creates the scenario."""
        headers = "abcdefghijklmnopqrstuvwxyz"
        option_text = []
        preamble = ""
        if self.status_quo:
            preamble = self.state_status_quo(self.status_quo) + "\n\n"
            choice_text = [self.create_option_status_quo(o) for o in self.options]
        else:
            choice_text = [self.create_option(o) for o in self.options]
        with_numbers = [h + ") " + choice for h, choice in zip(headers[:len(choice_text)], choice_text)]
        self.prompt = self.base_prompt + "\n\n" + preamble + "\n They are considering the following options:\n\n" + "\n".join(with_numbers) + "\n\n" +  f"Your own views: {views}" + "\n\n" +  self.ask
        return dict({'prompt':self.prompt, 'options':self.options, 'choice_text': choice_text, 'status_quo':self.status_quo})

    def gen_prompt(self, views):
        self.multiple_choice(views)
        return self.prompt


