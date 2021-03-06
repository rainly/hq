#!/usr/bin/env python
#-*-coding:utf-8-*-

'''

'''

import json
import sys
import os
import math
import datetime

import pandas as pd
import numpy as np


import click

import time
from functools import wraps


CURDIR = os.path.dirname(os.path.abspath(__file__))

def print_time(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        s = time.time()
        ret = f(*args, **kwds)
        args = [i for i in args if isinstance(i, (int, float, str, unicode))]
        print('Func %s(%s, %s) cost %s seconds' %
              (f.func_name, args, kwds.keys(), time.time() - s))
        return ret
    return wrapper


def _read_csv(csvpath, usecols=[], nrows=None):
    '''
    参数控制只读某些列和前面的n行。
    注意：csv按时间倒序
    '''
    if usecols:
        if 0 not in usecols:
            usecols.insert(0, 0)
        df = pd.read_csv(
            csvpath, index_col=0, header=0, nrows=nrows, usecols=usecols)
    else:
        df = pd.read_csv(csvpath, index_col=0, header=0, nrows=nrows)
    if 'date' in df:
        aday = df['date'].iloc[0]
        if (isinstance(aday, str) or isinstance(aday, unicode)) and len(aday) == len('2016-00-00'):
            FORMAT = '%Y-%m-%d'
        else:
            FORMAT = '%Y%m%d'
        df['date'] = pd.to_datetime(df['date'], format=FORMAT)
    return df


def _ohlc_monthly(filename, ohlc_dir, ohlc_monthly_dir):
    dst = os.path.join(CURDIR, ohlc_monthly_dir, filename)
    src = os.path.join(CURDIR, ohlc_dir, filename)
    if not os.path.exists(src):
        print("%s not exist.." % src)
        return
    if os.path.exists(dst):
        print("%s exist.." % dst)
        return
    df = _read_csv(src)
    if df.shape[0] < 1:
        print("%s empty." % filename)
        return None
    if df.shape[0] > 1:
        assert df.index[0] > df.index[-1]
    code = df.iloc[0]['code']
    data = []
    days = []
    def is_same_month(d1, d2):
        return d1.year == d2.year and d1.month == d2.month

    i = j = df.shape[0] - 1
    startdate = datetime.datetime.strptime(str(df.index[i]), "%Y%m%d")
    while j >= 0:
        enddate = datetime.datetime.strptime(str(df.index[j]), "%Y%m%d")
        if not is_same_month(startdate, enddate):
            tmp_df = df.iloc[j + 1:i + 1]
            idx = df.index[j + 1]
            # 注意df是按时间逆序
            open_price = tmp_df['open'].values[-1]
            high_price = max(tmp_df['high'].values)
            low_price = min(tmp_df['low'].values)
            close_price = tmp_df['close'].values[0]
            days.insert(0, str(idx)[:6])
            data.insert(0, [code, open_price, high_price, low_price, close_price])
            i = j
            startdate = enddate
        j -= 1

    if j == -1:
        tmp_df = df.iloc[j + 1:i + 1]
        idx = df.index[j + 1]
        # 注意df是按时间逆序
        open_price = tmp_df['open'].values[-1]
        high_price = max(tmp_df['high'].values)
        low_price = min(tmp_df['low'].values)
        close_price = tmp_df['close'].values[0]
        days.insert(0, str(idx)[:6])
        data.insert(0, [code, open_price, high_price, low_price, close_price])

    set1 = set(map(lambda i: str(i)[:6], df.index.values))
    set2 = set(days)
    assert set1 == set2, "%s\n%s\n" % (code, set1 - set2)
    df2 = pd.DataFrame(
        data, index=days, columns=['code', 'open', 'high', 'low', 'close'])
    df2.to_csv(dst)
    return df2


@click.command()
@click.option('--filename', default='AAMC.csv', help=u'文件名')
@click.option('--src-dir', default='fix_amex_daily', help=u'ohlc目录')
@click.option('--dest-dir', default='amex_monthly', help='ohlc_monthly目录')
@print_time
def ohlc_monthly(filename, src_dir, dest_dir):
    if filename == 'ALL':
        filenames = os.listdir(os.path.join(CURDIR, src_dir))
    else:
        filenames = [filename]
    for filename in filenames:
        _ohlc_monthly(filename, src_dir, dest_dir)


if __name__ == "__main__":
    ohlc_monthly()

