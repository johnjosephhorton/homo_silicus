import openai
import sqlite3
import time
import json
import os

from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

from threading import Thread

def get_topics(n):
    messages=[{"role": "user", "content": f"Get a list of policy areas. For example transportation, medical devices, national defense, and so on. Return {n} such topics in a JSON list, with a single key 'policy_areas'"}]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        max_tokens=500,
        temperature=0.2,
        messages = messages)
    return response


def get_new_example(example, policy_area, model = "gpt-3.5-turbo"):
    messages=[{"role": "user", "content": f"Create a new scenario with the structure as this one, but about {policy_area}. Keep JSON formatting: {json.dumps(example)}"}]
    response = openai.ChatCompletion.create(
        model= model, #"gpt-4",
        max_tokens=100,
        temperature=0.2,
        messages = messages)
    return response

if __name__ == "__main__":
    example = dict({
        "body":"The National Highway Safety Commission",
        "option1":"improving automobile safety (bumpers, body, gas tank configurations, seatbelts) ",
        "option1_short":"auto safety",
        "option2":"improving the safety of interstate highways (guard rails, grading, highway interchanges, and implementing selective reduced speed limits)",
        "option2_short":"highway safety"
    })
    # R = get_new_example(example, "national defense")
    # outcome = R['choices'][0]['message']['content']
    # print(outcome)

    # R = get_new_example(example, "medical devices")
   
    scenarios = []
    raw_topics = get_topics(10)['choices'][0]['message']['content']
    topics = json.loads(raw_topics)
    print(topics)
    for topic in topics['policy_areas']:
        print(topic)
        R = get_new_example(example, topic)
        scenarios.append(R)
        outcome = R['choices'][0]['message']['content']
        print(outcome)
     
        
                        
                    
