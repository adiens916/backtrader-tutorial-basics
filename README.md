# Backtrader-Tutorial

Backtrader (주식 백테스팅 프레임워크) 강의 따라해보기.

다음 강의의 흐름을 참고했음.
- 제목: A.I.에게 배우는 Python을 이용한 매매전략 백테스트
- 저자: 인터스텔라
- 링크: https://cafe.naver.com/songspread/7394

강의에 나온 프롬프트를 AI에 입력하여, 스스로 어디까지 만들 수 있나 실험해봄.


## 설치
필요 라이브러리
```bash
pip install backtrader pandas matplotlib
```


## 폴더 구조
```
backtrader-tutorial/
├── src/ # 강의 실습 코드
├── data/ # 데이터 등
```


##  팁
### 2강: 주식 데이터 다운로드
- yfinance로 다운 받는 방법으로 작성.
- 다운 받은 파일 열어서 **헤더 정리 필요**
- `auto_adjust=False`, 확장자는 `.csv`가 좋음. 구분자(sep)은 쉼표가 좋음.

### 3~4강: 기본 구조
- 직접 AI 돌린 버젼 v0와 강의에 나온 버젼 v1이 있음.
- **되도록 강의에 나온 버젼 (v1)을 참고**하기. 
  - 더 구조적이고 기본에 충실함.
  - 로그가 풍부해서 처음에 파악하기 좋음.
- 데이터 불러올 때 **경로와 구분자 주의**

### 5강: 종가
- 종가 구매 시엔 `cerebro.broker.set_coc(True)` 필요
- 데이터 소수 자리가 너무 길면 계산 틀릴 수 있으니,  
**2자리까지 반올림 처리** 필요.
- 전날 가격을 구하려면 `[-1]` 인덱스 참조.

### 6강: 패러미터 최적화
- 최적화: 지표들을 조금씩 바꿔서, 가장 좋은 수익률을 만드는 최적의 지표를 찾을 수 있음.
- `cerebro.optstrategy()`에 전략과 패러미터 목록을 넣고,  
`results = cerebro.run()`에서 results를 순회하면 됨.  
그 후 전략에 저장된 값을 불러와서 비교 가능.
```python
for result in results:
    strat = result[0]
    strat.params.fast_length  # 20일선
    strat.params.slow_length  # 50일선
```

### 7강: 성과 평가 지표
- 평가 지표는 `cerebro.addanalyzer()`에 분석기 추가 가능.  
이때 `_name` 인자에 저장된 이름으로, 추후 `strat`에서 불러올 수 있음.
```python
cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")

# (중략)

rets = strat.analyzers.returns.get_analysis()
current_return = (rets["rtot"] * 100 if "rtot" in rets else 0)  # 총 수익률 (%)
```

- CAGR은 8강 참고하기. 그쪽에서 훨씬 간결하게 작성함.
- SharpeRatio 분석기 추가할 때 **`riskfreerate`** 값 설정 주의. 결과 크게 달라짐.
- 값 불러올 때 `sharperatio` 키는 있는데 값은 None인 경우가 있음. 따로 처리해줘야 함.
```python
sharpe_value = sharpe_analysis.get("sharperatio", 0.0)
# 위에서 키가 없으면 0을 반환하지만, 키는 항상 존재함.
# 그러나 키에 해당하는 값이 None인 경우가 있음. 이걸 처리 안 하면 출력문에서 에러 남.
sharpe = 0.0 if sharpe_value is None else sharpe_value
```

### 8강: 다양한 전략
각 파일들 참고. 사실상 Strategy 클래스만 바꿔 끼면 된다.