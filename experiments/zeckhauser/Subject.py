import json

class Subject:
    def __init__(self, score, view):
        self.score = score
        self.view = view

    def toJSON(self):
        return {'score':self.score, 'view':self.view}
    
    def __repr__(self):
        return json.dumps(dict({'score':self.score, 'view':self.view}))

