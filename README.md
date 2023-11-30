# 다양성 평가 리포트 웹사이트 백엔드

![CD Status](https://github.com/NewWays-TechForImpactKAIST/backend-python/actions/workflows/build-dev-image.yaml/badge.svg)

FastAPI로 개발되는 다양성 평가 리포트 웹사이트의 백엔드 레포지토리입니다.

## Setup

이 프로젝트를 실행하기 위해서는 Python(v3.9 이상)이 설치되어 있어야 합니다.

## 설치 및 실행 과정

1. 파이썬 가상환경 생성
   - 아래 명령을 실행하여 파이썬 가상환경을 생성합니다.
   ```bash
   cd ~ && virtualenv newways --python=3.10
   ```
2. 가상환경 활성화
   - 아래 명령을 실행하여 가상환경을 활성화합니다.
   ```bash
   source ~/newways/bin/activate
   ```
3. 레포지토리 클론
   - 아래 명령을 실행하여 레포지토리를 클론합니다.
   ```bash
    git clone https://github.com/NewWays-TechForImpactKAIST/backend-python
   ```
4. 필요한 패키지 설치
   - requirements.txt에 명시된 패키지를 설치합니다.
   ```bash
    pip install -r requirements.txt
   ```
5. 환경 변수 설정
   - `.env.example` 파일을 복사하여 `.env` 파일을 생성합니다.
   ```bash
    cp .env.example .env
   ```
   - `.env` 파일을 열어 환경 변수의 값을 필요에 따라 바꾸어줍니다.
6. uvicorn 실행
   - uvicorn을 사용해 fastapi를 실행합니다.
     ```bash
     uvicorn main:app --host HOST --port PORT
     ```
7. Docker build
   - docker image를 빌드합니다.
   ```bash
    docker-compose up -d -build
   ```
