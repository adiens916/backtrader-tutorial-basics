"""
코드: https://cafe.naver.com/songspread/7411
설명: https://cafe.naver.com/songspread/7419
"""

import backtrader as bt
import pandas as pd
from datetime import datetime


# 1. Backtrader 전략 정의
class SMACrossover(bt.Strategy):
    params = (
        ("fast_length", 10),
        ("slow_length", 30),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None

        # 이동평균선 지표 생성
        self.fast_sma = bt.indicators.SMA(self.dataclose, period=self.p.fast_length)
        self.slow_sma = bt.indicators.SMA(self.dataclose, period=self.p.slow_length)

        # 이동평균선 교차 지표 생성
        self.crossover = bt.indicators.CrossOver(self.fast_sma, self.slow_sma)

    def next(self):
        if self.order:
            return

        # 매수/매도 로직
        if not self.position:  # 포지션이 없을 때
            # 단기 이동평균선이 장기 이동평균선을 상향 돌파 (골든 크로스)
            if self.crossover > 0:
                self.order = self.buy()
        # 포지션이 있을 때
        else:
            # 단기 이동평균선이 장기 이동평균선을 하향 돌파 (데드 크로스)
            if self.crossover < 0:
                self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                print(
                    f"BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}"
                )
            elif order.issell():
                print(
                    f"SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}"
                )

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print("Order Canceled/Margin/Rejected")

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        print(f"OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}")


# 2. Cerebro 엔진 설정 및 데이터 로드
if __name__ == "__main__":
    cerebro = bt.Cerebro()

    # 전략 추가
    cerebro.addstrategy(SMACrossover)

    # Pandas를 이용하여 SOXL.txt 파일 읽기
    df = pd.read_csv("data/SOXL.txt", index_col="Date", parse_dates=True, sep="\t")

    # Backtrader용 데이터 피드 생성
    data = bt.feeds.PandasData(
        dataname=df,
        fromdate=datetime(2011, 1, 1),
        todate=datetime(2020, 12, 31),
        timeframe=bt.TimeFrame.Days,
    )

    # 데이터 피드 추가
    cerebro.adddata(data)

    # 초기 자본 설정
    cerebro.broker.setcash(100000.0)

    # 수수료 설정 (0.1% 예시)
    cerebro.broker.setcommission(commission=0.001)

    # 백테스트 시작 전 초기 자본 출력
    print(f"Starting Portfolio Value: {cerebro.broker.getvalue():.2f}")

    # 백테스트 실행
    cerebro.run()

    # 백테스트 종료 후 최종 자본 출력
    print(f"Final Portfolio Value: {cerebro.broker.getvalue():.2f}")

    # 결과 플로팅
    cerebro.plot()
