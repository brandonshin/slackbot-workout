def from_dict(d):
    return Exercise(d['name'], d['min_reps'], d['max_reps'], d['units'], d['info'])

class Exercise(object):
    def __init__(self, name, min_reps, max_reps, units, info):
        self.name = name
        self.min_reps = min_reps
        self.max_reps = max_reps
        self.units = units
        self.info = info

    def __str__(self):
        return self.name
