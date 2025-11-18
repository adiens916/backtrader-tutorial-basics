import backtrader as bt
import pandas as pd
from datetime import datetime


# 1. Backtrader 볼린저 밴드 전략 정의


class BollingerBandsStrategy(bt.Strategy):
    params = (
        ("bb_period", 20),  # 볼린저 밴드 기간
        ("bb_devfactor", 2.0),  # 표준편차 배수
    )

    def __init__(self):
        # 볼린저 밴드 지표 생성
        self.bband = bt.indicators.BollingerBands(
            self.data.close, period=self.p.bb_period, devfactor=self.p.bb_devfactor
        )
        # 각 밴드 참조
        self.top_band = self.bband.top
        self.mid_band = self.bband.mid
        self.bot_band = self.bband.bot

    def next(self):
        if not self.position:  # 포지션이 없을 때
            # 가격이 하단 밴드 아래로 내려갔다가 다시 위로 올라오면 매수
            if (
                self.data.close[-1] < self.bot_band[-1]
                and self.data.close[0] >= self.bot_band[0]
            ):
                self._log("BUY CREATE, %.2f" % self.data.close[0])
                self.buy()
        else:  # 포지션이 있을 때
            # 가격이 상단 밴드 위로 올라갔다가 다시 아래로 내려오면 매도
            if (
                self.data.close[-1] > self.top_band[-1]
                and self.data.close[0] <= self.top_band[0]
            ):
                self._log("SELL CREATE, %.2f" % self.data.close[0])
                self.sell()

    def _log(self, txt, dt=None):
        dt = dt or self.data.datetime.date(0)
        print("%s, %s" % (dt.isoformat(), txt))


# 2. Cerebro 엔진 설정 및 데이터 로드

if __name__ == "__main__":
    cerebro = bt.Cerebro()
    cerebro.addstrategy(BollingerBandsStrategy)

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

    # 기간 계산
    start_date = datetime(2011, 1, 1)
    end_date = datetime(2020, 12, 31)
    years = (end_date - start_date).days / 365.25

    # 초기 자본 출력
    print(f"초기 자본: {cerebro.broker.getvalue():.2f}")

    # 백테스트 실행
    results = cerebro.run()

    # 최종 자본 출력
    final_value = cerebro.broker.getvalue()
    print(f"최종 자본: {final_value:.2f}")

    # 성과 지표 분석
    strat = results[0]

    # CAGR 계산
    returns_analysis = strat.analyzers.returns.get_analysis()
    rtot = returns_analysis.get("rtot", 0.0)
    cagr = ((1 + rtot) ** (1 / years) - 1) * 100

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
    print("볼린저 밴드 전략 백테스트 결과")
    print("=" * 60)
    print(
        f"파라미터: bb_period={strat.p.bb_period}, bb_devfactor={strat.p.bb_devfactor}"
    )
    print(f"총 수익률: {rtot*100:.2f}%")
    print(f"CAGR: {cagr:.2f}%")
    print(f"MDD: {mdd:.2f}%")
    print(f"Calmar Ratio: {calmar:.2f}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print("=" * 60)

    # 차트 출력
    cerebro.plot()
