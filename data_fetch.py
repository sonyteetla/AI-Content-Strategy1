# data_fetch.py
import json
import pandas as pd
from pytrends.request import TrendReq

def get_mock():
    with open("mock_data.json", "r", encoding="utf-8") as f:
        return json.load(f)

def safe_pytrends(keyword="skincare"):
    # returns a pandas Series of last 10 points or raises
    try:
        pytrends = TrendReq(timeout=(10,25))
        kw_list = [keyword]
        pytrends.build_payload(kw_list, timeframe='today 1-m')
        df = pytrends.interest_over_time()
        if df.empty:
            raise ValueError("pytrends returned empty")
        # return last 10 rows (or fewer)
        series = df[keyword].tail(10)
        series.index = range(len(series))  # simplify index for plotting
        return series
    except Exception as e:
        raise

def get_trend_or_mock(keyword="skincare"):
    try:
        series = safe_pytrends(keyword)
        return {"type":"real","data": series}
    except Exception:
        mock = get_mock()
        # construct a fake series from mock topics (numbers)
        vals = [10 + i*3 for i in range(10)]
        s = pd.Series(vals)
        s.index = range(len(s))
        return {"type":"mock","data": s}
