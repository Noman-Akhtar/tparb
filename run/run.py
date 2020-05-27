import ccxt
import redis

from cryptofeed.exchanges import Huobi as Exchange

from config import config
from modules.traingle import Triangle

fee = 0.0 / 100
r = 2
coin_a = 'BTC'
coin_b = 'USDT'
tri_coins = [
    'BTC', 'HT', 'XRP', 'TRX', 'LINK',
    'LTC', 'MTL', 'HOT', 'VET', 'ADA',
    'ENJ', 'ETC', 'WAVES', 'NEO', 'XLM',
    'RLC', 'DASH', 'XMR', 'QTUM', 'IOTA',
    'DENT', 'ZIL', 'NPXS', 'ICX', 'ZEC'
]


redis_obj = redis.Redis(
    host=config.R_HOST,
    password=config.R_PASSWORD,
    port=config.R_PORT,
    db=config.R_DB,
    decode_responses=True
)


if __name__ == '__main__':

    hbi = ccxt.huobipro()
    tickers = hbi.fetch_tickers()
    symbols = list(tickers.keys())

    [redis_obj.delete(key) for key in redis_obj.keys()]

    triangle = Triangle(coin_a, coin_b, tri_coins, fee, redis_obj, Exchange)
    triangle.build()
