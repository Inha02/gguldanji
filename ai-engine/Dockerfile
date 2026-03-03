FROM python:3.12-slim

WORKDIR /app

# XGBoost/LightGBM에 필요한 시스템 라이브러리
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드
COPY api/ api/
COPY crawler/ crawler/

# 학습된 모델 + RAG 인덱스 + 설정
COPY crawler/data/models/ crawler/data/models/
COPY crawler/data/chroma_db/ crawler/data/chroma_db/
COPY crawler/data/final/ crawler/data/final/
COPY crawler/data/config/ crawler/data/config/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]