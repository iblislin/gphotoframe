import random
import bisect

class WeightedRandom(object):
    '''Weighted Ramdom'''

    def __init__(self, list):
        self.list = list
        self.weight_list = []
        total_weight = sum(item.weight for item in list)
        accum_weight = 0.0
        for item in list:
            accum_weight += item.weight
            self.weight_list.append( accum_weight / total_weight )

    def __call__(self):
        n = random.uniform(0, 1)
        item = bisect.bisect(self.weight_list, n)
        return self.list[item]
