"""
코드: https://cafe.naver.com/songspread/7631
"""

import backtrader as bt
import pandas as pd
from datetime import datetime

# 1. Backtrader 전략 정의


class RSIStrategy(bt.Strategy):
    params = (
        ("rsi_period", 14),
        ("rsi_lower", 30),
        ("rsi_upper", 70),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)

    def next(self):
        if not self.position:  # Not in the market
            if self.rsi[-1] < self.p.rsi_lower and self.rsi[0] >= self.p.rsi_lower:
                self._log("BUY CREATE, %.2f" % self.data.close[0])
                self.buy()
        else:  # In the market
            if self.rsi[-1] > self.p.rsi_upper and self.rsi[0] <= self.p.rsi_upper:
                self._log("SELL CREATE, %.2f" % self.data.close[0])
                self.sell()

    def _log(self, txt, dt=None):
        dt = dt or self.data.datetime.date(0)
        print("%s, %s" % (dt.isoformat(), txt))


# 2. Cerebro 엔진 설정 및 데이터 로드

if __name__ == "__main__":
    cerebro = bt.Cerebro()
    cerebro.addstrategy(RSIStrategy)

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

    # 강의에서는 무위험 이자율(risk-free rate)을 따로 설정 안 함. 그러면 1%가 기본 값임.
    # 이 경우 평균 초과수익이 거의 없거나 변동성이 커서 Sharpe가 크게 음수로 떨어짐.
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")

    # 기간 계산
    start_date = datetime(2011, 1, 1)
    end_date = datetime(2020, 12, 31)
    years = (end_date - start_date).days / 365.25

    # 백테스트 실행
    results = cerebro.run()
    cerebro.plot()
    exit()

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
        # 위에서 키가 없으면 0을 반환하지만, 키는 항상 존재함.
        # 그러나 키에 해당하는 값이 None인 경우가 있음. 이걸 처리 안 하면 출력문에서 에러 남.
        sharpe = 0.0 if sharpe_value is None else sharpe_value

        fast_length = strat.p.fast_length
        slow_length = strat.p.slow_length
        print(
            f"fast_length={fast_length}, slow_length={slow_length} | CAGR={cagr:.2f}%, MDD={mdd:.2f}%, Calmar={calmar:.2f}, Sharpe={sharpe:.2f}"
        )
