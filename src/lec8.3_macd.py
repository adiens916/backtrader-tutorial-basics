import backtrader as bt
import pandas as pd
from datetime import datetime


class MACDStrategy(bt.Strategy):
    params = (
        ("fast_period", 12),  # 빠른 EMA
        ("slow_period", 26),  # 느린 EMA
        ("signal_period", 9),  # 시그널 라인 기간
    )

    def __init__(self):
        # MACD 지표 생성
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.p.fast_period,
            period_me2=self.p.slow_period,
            period_signal=self.p.signal_period,
        )

        # MACD 라인과 시그널 라인 참조
        self.macd_line = self.macd.macd
        self.signal_line = self.macd.signal

        # 크로스오버 감지용 (1 = 골든크로스, -1 = 데드크로스)
        self.crossover = bt.indicators.CrossOver(self.macd_line, self.signal_line)

    def next(self):
        # 포지션이 없을 때 → 골든크로스 시 매수
        if not self.position:
            if self.crossover > 0:  # MACD가 시그널 위로 교차
                self._log(f"BUY CREATE, 가격: {self.data.close[0]:.2f}")
                self.buy()

        # 포지션이 있을 때 → 데드크로스 시 청산
        else:
            if self.crossover < 0:  # MACD가 시그널 아래로 교차
                self._log(f"SELL CREATE, 가격: {self.data.close[0]:.2f}")
                self.sell()

    def _log(self, txt, dt=None):
        dt = dt or self.data.datetime.date(0)
        print("%s, %s" % (dt.isoformat(), txt))


# 2. Cerebro 엔진 설정 및 데이터 로드

if __name__ == "__main__":
    cerebro = bt.Cerebro()
    cerebro.addstrategy(MACDStrategy)

    # Pandas를 이용하여 SOXL.txt 파일 읽기
    df = pd.read_csv("data/SOXL.txt", index_col="Date", parse_dates=True, sep="\t")
    # 실수형 컬럼들을 소수점 아래 둘째 자리에서 반올림
    for col in ["Open", "High", "Low", "Close", "Adj Close"]:
        if col in df.columns:
            df[col] = df[col].round(2)

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
    # 수수료 설정 (0.1%)
    cerebro.broker.setcommission(commission=0.001)

    # Analyzer 추가
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")

    # 초기 자본 출력
    print(f"초기 자본: {cerebro.broker.getvalue():.2f}")

    # 백테스트 실행
    results = cerebro.run()

    # 최종 자본 출력
    final_value = cerebro.broker.getvalue()
    print(f"최종 자본: {final_value:.2f}")

    # 성과 지표 분석
    strat = results[0]

    # 1. CAGR (%) - Returns 분석기의 rnorm100 (연환산 복리 수익률)
    returns_analysis = strat.analyzers.returns.get_analysis()
    cagr = returns_analysis.get("rnorm100", 0.0)  # 기본값 0.0으로 안전 처리

    # MDD (Maximum Drawdown)
    drawdown_analysis = strat.analyzers.drawdown.get_analysis()
    mdd = drawdown_analysis.get("max", {}).get("drawdown", 0.0) or 0.0

    # Calmar Ratio
    calmar = cagr / mdd if mdd > 0 else 0.0

    # Sharpe Ratio
    sharpe_analysis = strat.analyzers.sharpe.get_analysis()
    sharpe_value = sharpe_analysis.get("sharperatio", 0.0)
    sharpe = 0.0 if sharpe_value is None else sharpe_value

    # 결과 출력
    print("\n" + "=" * 60)
    print("MACD 전략 백테스트 결과")
    print("=" * 60)
    # print(f"총 수익률: {rtot*100:.2f}%")
    print(f"CAGR: {cagr:.2f}%")
    print(f"MDD: {mdd:.2f}%")
    print(f"Calmar Ratio: {calmar:.2f}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print("=" * 60)

    # 차트 출력
    cerebro.plot()
