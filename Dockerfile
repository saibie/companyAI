# 1. 가장 무난하고 가벼운 공식 파이썬 이미지
FROM python:3.12-slim-bookworm

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 환경 변수 설정
# PYTHONDONTWRITEBYTECODE: .pyc 파일 생성 방지 (Docker에서 불필요)
# PYTHONUNBUFFERED: 로그가 버퍼링 없이 즉시 출력되게 함 (중요!)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 4. 시스템 패키지 설치 (Postgres, Curl 등)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 5. 의존성 파일 복사
COPY requirements.txt .

# 6. 패키지 설치 (pip 사용)
# --no-cache-dir: 이미지 용량 줄이기
# 시스템 파이썬(/usr/local/lib/...)에 직접 설치되므로 볼륨 마운트 영향 안 받음!
RUN pip install --no-cache-dir -r requirements.txt

# 7. 소스 코드 복사
COPY . .