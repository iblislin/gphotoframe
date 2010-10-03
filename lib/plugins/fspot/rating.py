from __future__ import division

from ...utils.wrandom import WeightedRandom

class RateList(list):

    def __init__(self, photolist, db_class):
        super(RateList, self).__init__()

        self.raw_list = []
        self.photolist = photolist
        self.sql = photolist.sql
        options = photolist.options
        db = db_class()

        if not db.is_accessible:
            self.total = 0
            return

        self.rate_min = options.get('rate_min', 0)
        self.rate_max = options.get('rate_max', 5)
        weight = options.get('rate_weight', 2)

        sql = self.sql.get_statement(
            'rating, COUNT(*)', None,
            self.rate_min, self.rate_max) + ' GROUP BY rating'
        count_list = db.fetchall(sql)
        db.close()
        self.total = sum(x[1] for x in count_list)

        # initialize all rate couter as 0
        count_dic = dict([(x, 0) for x in xrange(6)])
        count_dic.update(dict(count_list))

        for rate, total_in_this in count_dic.items():
            rate_info = FSpotRate(rate, total_in_this, weight)
            self.raw_list.append(rate_info)

        self._set_random_weight()

    def update_rate(self, old, new):
        for rate in self.raw_list:
            rate.total += 1 if rate.name == new \
                else -1 if rate.name == old else 0
        self._set_random_weight()

    def _set_random_weight(self):
        del self[0:]

        for rate in self.raw_list:
            if rate.total > 0 and self.rate_min <= rate.name <= self.rate_max:
                self.append(rate)

        self.random = WeightedRandom(self)

    def get_random_weight(self):
        rate = self.random()
        return rate

class FSpotRate(object):

    def __init__(self, name, total, option=None):
        self.name = name
        self.total = total
        self.option = option

    def _get_weight(self):
        weight_mag = self.option or 2
        weight = self.total * (self.name * weight_mag + 1)
        return weight

    weight = property(_get_weight, None)
