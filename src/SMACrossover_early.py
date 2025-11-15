"""
https://cafe.naver.com/songspread/7411
"""

import pandas as pd
import backtrader as bt
from datetime import datetime
import backtrader.feeds as btfeeds

# 1. 데이터 읽기 및 필터링
# SOXL.txt 파일이 OHLCV 형식(날짜, Open, High, Low, Close, Volume)으로 되어 있다고 가정
df = pd.read_csv("data/SOXL.txt", parse_dates=["Date"], index_col="Date", sep="\t")

# 2011-01-01 ~ 2020-12-31 데이터 필터링 (인덱스가 Date 컬럼이라고 가정)
start_date = datetime(2011, 1, 1)
end_date = datetime(2020, 12, 31)
df = df[(df.index >= start_date) & (df.index <= end_date)]

# 컬럼 확인 및 재정렬 (표준 OHLCV 형식으로 맞춤, 필요 시 컬럼명 조정)
df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()

print(f"필터링된 데이터 개수: {len(df)}")
print(df.head())


# 2. 이동평균선 교차 전략 정의
class SMACrossStrategy(bt.Strategy):
    params = (
        ("short_period", 20),  # 단기 이동평균 기간
        ("long_period", 50),  # 장기 이동평균 기간
    )

    def __init__(self):
        # 이동평균선 인디케이터 생성
        self.sma_short = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.short_period
        )
        self.sma_long = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.long_period
        )

        # 교차 신호 생성
        self.crossover = bt.indicators.CrossOver(self.sma_short, self.sma_long)

    def next(self):
        # 포지션이 없을 때만 신호 확인 (장기 포지션 유지)
        if not self.position:
            if self.crossover > 0:  # 단기 > 장기 (상향 교차)
                self.buy()
                print(
                    f"매수 신호: {self.data.datetime.date(0)} - 가격: {self.data.close[0]:.2f}"
                )
        else:
            if self.crossover < 0:  # 단기 < 장기 (하향 교차)
                self.sell()
                print(
                    f"매도 신호: {self.data.datetime.date(0)} - 가격: {self.data.close[0]:.2f}"
                )


# 3. 백테스트 실행 엔진 설정
cerebro = bt.Cerebro()

# 전략 추가
cerebro.addstrategy(SMACrossStrategy)

# Pandas 데이터 피드 생성 및 추가
data_feed = btfeeds.PandasData(dataname=df)
cerebro.adddata(data_feed)

# 초기 자본 및 수수료 설정
cerebro.broker.setcash(100000.0)  # 초기 자본 100,000
cerebro.broker.setcommission(commission=0.001)  # 0.1% 수수료

# 데이터 범위 설정 (필터링된 데이터와 일치)
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")

print("초기 포트폴리오 가치: %.2f" % cerebro.broker.getvalue())

# 4. 백테스트 실행
results = cerebro.run()

# 결과 출력
final_value = cerebro.broker.getvalue()
print("최종 포트폴리오 가치: %.2f" % final_value)
print("총 수익률: %.2f%%" % (100 * (final_value - 100000) / 100000))

# 분석기 결과
strat = results[0]
print("샤프 비율:", strat.analyzers.sharpe.get_analysis())
print("총 수익률:", strat.analyzers.returns.get_analysis())
print("최대 드로다운:", strat.analyzers.drawdown.get_analysis())

# 5. 차트 플롯 (matplotlib 필요)
cerebro.plot(style="candlestick")  # 주석 해제 시 차트 표시
