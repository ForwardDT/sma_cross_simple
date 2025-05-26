#!/usr/bin/env python3
"""
SMA Crossover Backtest with Dynamic Percent-of-Portfolio Sizing
Run me as: python sma_cross_1.py
"""
import os
import datetime
import argparse

import backtrader as bt
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt


class SmaCross(bt.Strategy):
    params = dict(
        pfast=10,        # fast MA period
        pslow=30,        # slow MA period
        percent=0.3      # fraction of portfolio to invest (0.3=30%)
    )

    def __init__(self):
        sma_fast = bt.ind.SMA(period=self.p.pfast)
        sma_slow = bt.ind.SMA(period=self.p.pslow)
        self.crossover = bt.ind.CrossOver(sma_fast, sma_slow)

    def next(self):
        price = self.data.close[0]
        equity = self.broker.getvalue()
        size = int((equity * self.p.percent) / price)

        if not self.position and self.crossover > 0:
            if size > 0:
                self.buy(size=size)
                print(f"BUY  {size} @ {price:.2f} "
                      f"(alloc {self.p.percent*100:.0f}% = {equity*self.p.percent:.2f})")

        elif self.position and self.crossover < 0:
            self.sell(size=self.position.size)
            print(f"SELL {self.position.size} @ {price:.2f}")


def run_backtest(
    csv_file: str,
    download: bool,
    start: datetime.datetime,
    end: datetime.datetime,
    pct_to_invest: float,
    cash: float,
    commission: float
):
    # 1) Fetch or load data
    if download or not os.path.exists(csv_file):
        print(f"Downloading TSLA data {start.date()} → {end.date()}…")
        df = yf.download(
            'TSLA',
            start=start, end=end,
            auto_adjust=True,
            progress=False,
            group_by='column',
            multi_level_index=False
        )
        df.to_csv(csv_file)
        print(f"Saved to {csv_file}")
    else:
        print(f"Loading data from {csv_file}")
        df = pd.read_csv(csv_file, parse_dates=True, index_col=0)

    # 2) Set up Cerebro
    cerebro = bt.Cerebro()
    cerebro.addstrategy(SmaCross, percent=pct_to_invest)

    datafeed = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(datafeed)

    cerebro.broker.setcash(cash)
    cerebro.broker.setcommission(commission)

    # 3) Run
    print(f"Starting Portfolio Value: {cerebro.broker.getvalue():,.2f}")
    cerebro.run()
    print(f"Final   Portfolio Value: {cerebro.broker.getvalue():,.2f}")

    # 4) Plot
    cerebro.plot()
    plt.show()


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="SMA Crossover Backtest with dynamic sizing"
    )
    p.add_argument(
        "--csv", default="tsla.csv",
        help="CSV file to read/write TSLA data"
    )
    p.add_argument(
        "--no-download", dest="download", action="store_false",
        help="If set, won't re-download the CSV"
    )
    p.add_argument(
        "--start", type=str, default="2020-01-01",
        help="Start date (YYYY-MM-DD)"
    )
    p.add_argument(
        "--end", type=str, default=None,
        help="End date (YYYY-MM-DD), default today"
    )
    p.add_argument(
        "--pct", type=float, default=0.95,
        help="Fraction of portfolio to invest (e.g. 0.3 = 30%%)"
    )
    p.add_argument(
        "--cash", type=float, default=100000,
        help="Starting cash"
    )
    p.add_argument(
        "--commission", type=float, default=0.001,
        help="Broker commission (e.g. 0.001 = 0.1%%)"
    )
    args = p.parse_args()

    start_dt = datetime.datetime.fromisoformat(args.start)
    end_dt = datetime.datetime.today() if args.end is None else datetime.datetime.fromisoformat(args.end)

    run_backtest(
        csv_file=args.csv,
        download=args.download,
        start=start_dt,
        end=end_dt,
        pct_to_invest=args.pct,
        cash=args.cash,
        commission=args.commission
    )
