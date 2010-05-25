import random
import bisect

class WeightedRandom(object):
    '''Weighted Ramdom'''

    def __init__(self, list):
        self.list = list
        self.weight_list = []
        total_weight = sum(item.weight for item in list)
        # total_weight = sum(item.weight * item.total for item in list)
        accum_weight = 0.0
        for item in list:
            accum_weight += item.weight
            # accum_weight += item.weight * item.total
            self.weight_list.append( accum_weight / total_weight )

    def __call__(self):
        n = random.uniform(0, 1)
        item = bisect.bisect(self.weight_list, n)
        return self.list[item]

class Rate(object):

    def __init__(self, name, total_in_this, total_all=None, option=None):
        self.name = name
        self.total = total_in_this
        self.total_all = total_all
        self.option = option

    def _get_weight(self):
        return self.total

    weight = property(_get_weight, None)
