"""
프롬프트: https://cafe.naver.com/songspread/7541
작성: Grok4
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
            self.bar_executed = len(self)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            pass  # 출력 제거
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        pass  # 출력 제거


# 2. Cerebro 엔진 설정 및 데이터 로드

if __name__ == "__main__":
    cerebro = bt.Cerebro()
    # 최적화 전략 추가
    cerebro.optstrategy(
        SMACrossover, fast_length=range(5, 21, 5), slow_length=range(20, 51, 10)
    )

    # Pandas를 이용하여 SOXL.txt 파일 읽기
    df = pd.read_csv("data/SOXL.txt", index_col="Date", parse_dates=True, sep="\t")
    # 실수형 컬럼들을 소수점 아래 둘째 자리에서 반올림
    for col in ["Open", "High", "Low", "Close", "Adj Close"]:
        if col in df.columns:  # 존재하는 컬럼인지 확인
            df[col] = df[col].round(2)  # 소수점 둘째 자리까지 반올림
    # Backtrader용 데이터 피드 생성
    data = bt.feeds.PandasData(
        dataname=df,
        fromdate=datetime(2011, 1, 1),
        todate=datetime(2020, 12, 31),
        timeframe=bt.TimeFrame.Days,
    )

    # 데이터 피드 추가
    cerebro.adddata(data)
    # 고정 수량 매매
    cerebro.addsizer(bt.sizers.FixedSize, stake=20)
    # Cheat-on-close 설정 (종가 체결)
    cerebro.broker.set_coc(True)
    # 초기 자본 설정
    cerebro.broker.setcash(100000.0)
    # 수수료 설정 (0.1% 예시)
    cerebro.broker.setcommission(commission=0.001)
    # Analyzer 추가
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe", riskfreerate=0.0)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")

    # 기간 계산
    start_date = datetime(2011, 1, 1)
    end_date = datetime(2020, 12, 31)
    years = (end_date - start_date).days / 365.25

    # 백테스트 실행
    results = cerebro.run()

    # 각 파라미터별 성과 지표 출력
    for run in results:
        strat = run[0]  # 각 run은 [strategy] 리스트

        # CAGR
        returns_analysis = strat.analyzers.returns.get_analysis()
        rtot = returns_analysis.get("rtot", 0.0)
        cagr = ((1 + rtot) ** (1 / years) - 1) * 100

        # MDD
        drawdown_analysis = strat.analyzers.drawdown.get_analysis()
        mdd = drawdown_analysis.get("max", {}).get("drawdown", 0.0) or 0.0

        # Calmar Ratio
        calmar = cagr / mdd if mdd > 0 else 0.0

        # Sharpe Ratio
        sharpe_analysis = strat.analyzers.sharpe.get_analysis()
        sharpe_value = sharpe_analysis.get("sharperatio", 0.0)
        sharpe = 0.0 if sharpe_value is None else sharpe_value

        fast_length = strat.p.fast_length
        slow_length = strat.p.slow_length
        print(
            f"fast_length={fast_length}, slow_length={slow_length} | CAGR={cagr:.2f}%, MDD={mdd:.2f}%, Calmar={calmar:.2f}, Sharpe={sharpe:.2f}"
        )
