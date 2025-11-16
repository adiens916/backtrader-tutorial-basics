"""
https://cafe.naver.com/songspread/7458

위 링크에서 제시한 프롬프트를, 직접 Grok4에 돌려서 얻은 코드.
불필요한 출력문 삭제
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


# 2. Cerebro 엔진 설정 및 데이터 로드
if __name__ == "__main__":
    cerebro = bt.Cerebro()

    # 최적화 전략 추가 (fast_length: 5~30 step 5, slow_length: 20~100 step 10)
    cerebro.optstrategy(
        SMACrossover, fast_length=range(5, 31, 5), slow_length=range(20, 101, 10)
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

    # 성과 분석기 추가 (총 수익률 등)
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    cerebro.addanalyzer(
        bt.analyzers.SharpeRatio, _name="sharpe", timeframe=bt.TimeFrame.Days
    )

    # 백테스트 시작 전 초기 자본 출력
    print(f"Starting Portfolio Value: {cerebro.broker.getvalue():.2f}")

    # 백테스트 실행 (최적화 결과 반환)
    results = cerebro.run()

    # 결과 분석: 최고 성과 조합 찾기 (OptReturn 객체 처리)
    best_return = -float("inf")
    best_sharpe = -float("inf")
    best_params = None
    for run in results:  # OptReturn 리스트
        for strat in run:  # 각 run 내 전략 리스트 (보통 [strat])
            # fast_length < slow_length 확인 (유효 조합만)
            if strat.params.fast_length >= strat.params.slow_length:
                continue

            # OptReturn 객체로 결과가 반환되므로, 루프에서 analyzers 접근
            rets = strat.analyzers.returns.get_analysis()
            current_return = (
                rets["rtot"] * 100 if "rtot" in rets else 0
            )  # 총 수익률 (%)

            sharpe_analysis = strat.analyzers.sharpe.get_analysis()
            current_sharpe = (
                sharpe_analysis["sharperatio"]
                if "sharperatio" in sharpe_analysis
                else 0
            )

            fast = strat.params.fast_length
            slow = strat.params.slow_length

            print(
                f"Params: fast={fast}, slow={slow}, Return: {current_return:.2f}%, Sharpe: {current_sharpe:.2f}"
            )

            # 총 수익률 기준으로 최고 선택 (샤프 비율도 고려 가능)
            if current_return > best_return:
                best_return = current_return
                best_sharpe = current_sharpe
                best_params = (fast, slow)

    if best_params:
        print(
            f"Best combination: fast_length={best_params[0]}, slow_length={best_params[1]}, Total Return: {best_return:.2f}%, Sharpe Ratio: {best_sharpe:.2f}"
        )
    else:
        print("No valid parameter combinations found.")

    # 최적 조합으로 다시 실행하여 최종 포트폴리오 가치 출력
    if best_params:
        cerebro = bt.Cerebro()
        cerebro.addstrategy(
            SMACrossover,
            fast_length=best_params[0],
            slow_length=best_params[1],
        )
        cerebro.adddata(data)
        cerebro.addsizer(bt.sizers.FixedSize, stake=20)
        cerebro.broker.set_coc(True)
        cerebro.broker.setcash(100000.0)
        cerebro.broker.setcommission(commission=0.001)
        cerebro.run()
        print(f"Final Portfolio Value: {cerebro.broker.getvalue():.2f}")
        cerebro.plot()
