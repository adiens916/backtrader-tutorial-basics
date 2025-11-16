import yfinance as yf
import pandas as pd
from datetime import datetime

# 날짜 범위 설정 (YYYY-MM-DD 형식)
start_date = "2010-01-01"
end_date = "2025-08-31"

# SOXL 티커 데이터 다운로드
ticker = "SOXL"
data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=False)

# 데이터 확인 (선택적: 콘솔에 출력)
print(data.head())
print(f"다운로드된 데이터 기간: {data.index[0]} ~ {data.index[-1]}")
print(f"총 행 수: {len(data)}")

# 'SOXL.txt' 파일로 저장 (CSV 형식, 인덱스 포함)
data.to_csv(
    "SOXL.txt", index=True, sep="\t"
)  # 탭 구분자로 저장하여 텍스트 파일처럼 사용

print("데이터가 'SOXL.txt' 파일로 저장되었습니다.")
