from flask import Flask, jsonify
from flask_caching import Cache
import time
import requests
import numpy as np
import talib

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/adx')
def get_adx_data():
    symbols = ["ETHUSDT", "BTCUSDT", "BNBUSDT", "RSRUSDT", "LUNAUSDT", "BUSDUSDT", "SHIBUSDT", "CHZUSDT", "ADAUSDT", "SUNUSDT", "LITUSDT", "ATOMUSDT", "XRPUSDT"]
    intervals = ['15m', '30m', '1h', '4h', '1d']
    limit = 31

    result = {}

    for symbol in symbols:
        for interval in intervals:
            response = requests.get(f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}")
            if response.status_code != 200:
                continue

            data = response.json()

            high_prices = [float(item[2]) for item in data]
            low_prices = [float(item[3]) for item in data]
            close_prices = [float(item[4]) for item in data]

            high_prices_np = np.array(high_prices)
            low_prices_np = np.array(low_prices)
            close_prices_np = np.array(close_prices)

            adx = talib.ADX(high_prices_np, low_prices_np, close_prices_np)

            current_adx = adx[-1]

            timestamp = int(time.time() * 1000)

            if symbol not in result:
                result[symbol] = {}
            result[symbol]= {
                'coin': symbol,
                'adx': current_adx,
                'date': timestamp,
                'interval': interval
            }

    cache.set('adx_data', result, timeout=3600)
    return jsonify(result)

@app.route('/adx/<string:interval>')
def get_adx_interval(interval):
    data = cache.get('adx_data')
    if data is None:
        return jsonify({'error': 'ADX data not available'})

    result = {symbol: data[symbol] for symbol in data if data[symbol]['interval'] == interval}
    cache.set('adx_data_interval', result, timeout=3600)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
