import simplejson as json
from decimal import Decimal
import time


class RedisTree:

    def __init__(self, coin_a: str, coin_b: str, tri_coins: list, fee: str, redis_obj):
        
        self.coin_a = coin_a
        self.coin_b = coin_b
        self.tri_coins = tri_coins
        
        self.fee_at_buy = Decimal('1') + Decimal(fee)
        self.fee_at_sell = Decimal('1') - Decimal(fee)
        
        self.redis_obj = redis_obj
        
        self.sep = '-'
        self.root = self.coin_a + self.sep + self.coin_b
        self.init_one = Decimal('1')
        self.init_zero = Decimal('0')

    def _on_redis(self, key):
        return self.redis_obj.exists(key)

    def _add_root(self):
        dump = json.dumps([
            self.init_one,  # best bid
            self.init_one,  # bid size
            self.init_one,  # best ask
            self.init_one,  # ask size
            time.time_ns()
        ])
        if not self._on_redis(self.root):
            self.redis_obj.set(self.root, dump)

    def _add_branches(self, coin):
        key = self.coin_a + self.sep + coin
        key_dict = {
            self.coin_a: json.dumps([
                self.init_one,  # best bid
                self.init_one,  # bid size
                self.init_one,  # best ask
                self.init_one,  # ask size
                time.time_ns()
            ]),
            self.coin_b: json.dumps([
                self.init_one,  # best bid
                self.init_one,  # bid size
                self.init_one,  # best ask
                self.init_one,  # ask size
                time.time_ns()
            ]),
            'arb': json.dumps([self.init_one, self.init_one])
        }
        if not self._on_redis(key):
            self.redis_obj.hmset(key, key_dict)

    def prepare_tree(self):
        self._add_root()
        for coin in self.tri_coins:
            self._add_branches(coin)

    def update_root(self, bid, bid_size, ask, ask_size, timestamp):
        dump = json.dumps([
            self.fee_at_sell * bid,
            bid_size,
            self.fee_at_buy * ask,
            ask_size,
            timestamp
        ])
        self.redis_obj.set(self.root, dump)

    def update_branch(self, coin: str, side: str, bid, bid_size, ask, ask_size, timestamp):
        key = self.coin_a + self.sep + coin
        
        branch = self.redis_obj.hgetall(key)
        branch = {i: json.loads(branch[i]) for i in branch}
        branch[side] = [bid, bid_size, ask, ask_size, timestamp]

        branch['arb'] = [
            (Decimal(branch[self.coin_b][2]) * self.fee_at_buy) / (Decimal(branch[self.coin_a][0]) * self.fee_at_sell),  # buying coin_a
            (Decimal(branch[self.coin_b][0]) * self.fee_at_sell) / (Decimal(branch[self.coin_a][2]) * self.fee_at_buy)   # selling coin_a
        ]

        branch = {i: json.dumps(branch[i]) for i in branch}
        self.redis_obj.hmset(key, branch)
