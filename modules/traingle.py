import time

from cryptofeed import FeedHandler

from modules.redis_tree import RedisTree


class Triangle:

    def __init__(self, coin_a: str, coin_b: str, tri_coins: list, fee, redis_obj, Exchange):
        self.coin_a = coin_a
        self.coin_b = coin_b
        self.tri_coins = tri_coins
        self.redis_obj = redis_obj
        self.Exchange = Exchange

        self.sep = '-'
        self.root = self.coin_a + self.sep + self.coin_b
        self.redis_tree = RedisTree(
            coin_a=self.coin_a,
            coin_b=self.coin_b,
            tri_coins=self.tri_coins,
            fee=fee,
            redis_obj=self.redis_obj
        )
        self.all_symbols = self._prepare_symbols()
        self.feed = FeedHandler()

    def _prepare_symbols(self):
        all_symbols = [self.coin_a + self.sep + self.coin_b]
        for coin in self.tri_coins:
            all_symbols.extend(
                [coin + self.sep + self.coin_a, coin + self.sep + self.coin_b]
            )
        return all_symbols

    def _process_feed(self, pair, bid, bid_size, ask, ask_size, bid_feed, ask_feed):
        coin_a, coin_b = pair.split(self.sep)

        if pair == self.root:
            print('Updating Root   | {} | {}'.format(pair, ask))
            self.redis_tree.update_root(bid, bid_size, ask, ask_size, time.time_ns())
        else:
            print('Updating Branch | {} | {}'.format(pair, bid))
            self.redis_tree.update_branch(coin_a, coin_b, bid, bid_size, ask, ask_size, time.time_ns())

    def build(self):
        self.redis_tree.prepare_tree()
        
        self.feed.add_nbbo(
            [self.Exchange],
            self.all_symbols,
            self._process_feed
        )

        self.feed.run()
