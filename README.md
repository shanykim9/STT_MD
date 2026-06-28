# AI 종합 데이터 변환 및 분석 툴 (STT_MD)

영상 음성 추출, PDF 마크다운 변환, 주식 강의 AI 교차 분석, 주차별 누적 매매 시뮬레이션을 Streamlit 웹 앱으로 통합 제공하는 프로젝트입니다.

---

## 버전별 앱 파일

프로젝트는 기능이 점진적으로 확장되며 3개의 앱 파일로 구성되어 있습니다.

| 파일 | 탭 수 | 권장 용도 |
|---|---|---|
| `app1.py` | 3탭 | 단일 파일 처리 (초기 버전) |
| `app.py` | 3탭 | 다중 파일 업로드 + 워드 다운로드 |
| **`app2.py`** | **4탭** | **전체 기능 (매매 시뮬레이션 포함) — 최신 권장** |

```bash
# 최신 전체 기능 실행
streamlit run app2.py
```

---

## 주요 기능 요약

| 탭 | 기능 | 사용 API / 도구 |
|---|---|---|
| 🎥 영상 → TXT | 영상 음성을 텍스트로 변환 (다중 파일 일괄 처리) | OpenAI Whisper API, FFmpeg |
| 📄 PDF → MD | PDF를 고품질 마크다운으로 변환 (다중 파일 일괄 처리) | LlamaParse (LlamaCloud), PyMuPDF |
| 🧠 AI 강의 분석 | 교재 + 녹취록 교차 분석 리포트 생성 (MD / DOCX) | Anthropic Claude Sonnet 4.6 |
| 📈 매매 시뮬레이션 | 주차별 매매뷰 기반 포트폴리오 누적 백테스트 | yfinance, python-docx |

---

## 프로젝트 구조

```
STT_MD/
├── app2.py                  # ★ 최신 전체 버전 (4탭, 시뮬레이션 포함)
├── app.py                   # 다중 파일 + 워드 다운로드 버전 (3탭)
├── app1.py                  # 초기 단일 파일 버전 (3탭)
├── portfolio_state.json     # 매매 시뮬레이션 상태 저장 (app2.py 탭 4)
├── requirements.txt         # Python 패키지 의존성
├── .env                     # API 키 설정 (Git에 포함하지 않음)
├── .gitignore
└── .streamlit/
    └── config.toml          # Streamlit 설정 (업로드 용량 3GB)
```

---

## 사전 요구 사항

### 1. Python 3.8 이상

### 2. FFmpeg / FFprobe (탭 1 필수)

영상에서 오디오를 추출하고 분할하기 위해 시스템 PATH에 `ffmpeg`, `ffprobe`가 설치되어 있어야 합니다.

```bash
ffmpeg -version
ffprobe -version
```

- Windows: [FFmpeg 공식 다운로드](https://ffmpeg.org/download.html) 후 PATH 등록

### 3. API 키

| 환경 변수 | 용도 | 발급처 |
|---|---|---|
| `OPENAI_API_KEY` | 영상 음성 → 텍스트 (Whisper) | [OpenAI Platform](https://platform.openai.com/) |
| `LLAMA_CLOUD_API_KEY` | PDF → 마크다운 변환 | [LlamaCloud](https://cloud.llamaindex.ai/) |
| `ANTHROPIC_API_KEY` | 주식 강의 AI 분석 | [Anthropic Console](https://console.anthropic.com/) |

> 탭 4(매매 시뮬레이션)는 별도 API 키 없이 yfinance로 주가 데이터를 조회합니다.

---

## 설치 및 실행

### 1. 저장소 클론

```bash
git clone <your-repo-url>
cd STT_MD
```

### 2. 가상 환경 생성 및 패키지 설치

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성합니다.

```env
OPENAI_API_KEY=sk-...
LLAMA_CLOUD_API_KEY=llx-...
ANTHROPIC_API_KEY=sk-ant-...
```

> `.env`는 `.gitignore`에 포함되어 Git에 커밋되지 않습니다.  
> `.env`에 키를 넣지 않아도 앱 실행 후 각 탭에서 직접 입력할 수 있습니다.

### 4. 앱 실행

```bash
# 최신 전체 기능 (권장)
streamlit run app2.py

# 또는 이전 버전
streamlit run app.py    # 다중 파일 + 워드 다운로드
streamlit run app1.py   # 단일 파일 처리
```

브라우저에서 `http://localhost:8501` 이 자동으로 열립니다.

---

## 탭별 상세 사용법

### 탭 1: 🎥 영상 → TXT 변환

OpenAI Whisper API로 영상 음성을 텍스트로 변환합니다.

**공통 처리 흐름**
1. FFmpeg로 영상에서 오디오 추출 (16kHz, mono, 32kbps MP3)
2. OpenAI Whisper 업로드 제한(25MB)을 고려해 **30분(1800초) 단위**로 분할
3. 각 조각을 `whisper-1` 모델로 순차 변환
4. 결과 병합 후 화면 표시 및 `.txt` 다운로드

| 버전 | 입력 방식 | 출력 |
|---|---|---|
| `app1.py` | 로컬 **절대 경로** 1개 | `{파일명}_변환.txt` |
| `app.py`, `app2.py` | **다중 파일 업로드** (mp4, mkv, avi, mov) | `영상_통합_변환결과.txt` |

---

### 탭 2: 📄 PDF → MD 변환

LlamaParse를 사용해 PDF를 페이지 단위로 고품질 마크다운으로 변환합니다.

**처리 흐름**
1. PyMuPDF로 PDF를 **페이지 단위**로 분리
2. 각 페이지를 LlamaParse API로 마크다운 변환
3. 전체 결과 병합

| 버전 | 입력 방식 | 출력 |
|---|---|---|
| `app1.py` | PDF 1개 업로드 | `{파일명}_변환.md` |
| `app.py`, `app2.py` | PDF **다중 업로드** | `PDF_통합_변환결과.md` |

---

### 탭 3: 🧠 AI 강의 종합 분석 (3단계 세분할)

여러 교재(PDF/MD)와 강의 녹취록(TXT)을 교차 검증하여 주식 강의 심층 분석 리포트를 생성합니다.

**입력 파일**

| 구분 | 형식 | 개수 |
|---|---|---|
| 교재 / 강의자료 | `.md` 또는 `.pdf` | 다중 선택 가능 |
| 강사 녹취록 | `.txt` | 다중 선택 가능 |

| 버전 | 입력 | 다운로드 형식 |
|---|---|---|
| `app1.py` | 각 1개 | `.md` |
| `app.py`, `app2.py` | **각 다중 업로드** | `.md` + **`.docx`** |

**분석 지침 (5가지 — 화면에서 편집 가능)**
1. 종합 핵심 브리핑
2. 교재 + 강사 추가 인사이트 결합
3. [강사 특별 코멘트] 섹션 분리
4. 종목별 심층 뷰 및 밸류에이션 정리
5. 실전 적용 포인트 (종목별 매매뷰 요약 표 포함)

**3단계 세분할 호출 방식**

Claude API 토큰 제한을 우회하기 위해 3번 나눠 호출합니다.

| 단계 | 처리 지침 | max_tokens | 모델 |
|---|---|---|---|
| 1단계 | 지침 1, 2, 3 | 8,192 | claude-sonnet-4-6 |
| 2단계 | 지침 4 (종목 분석) | 8,192 | claude-sonnet-4-6 |
| 3단계 | 지침 5 (실전 포인트, 1~4단계 결과 참조) | 8,192 | claude-sonnet-4-6 |

각 단계 결과가 실시간으로 화면에 누적 표시됩니다.

**워드 다운로드 (`app.py`, `app2.py`)**
- 분석 결과 마크다운 → HTML → `.docx` 변환 (`markdown`, `python-docx`, `htmldocx` 사용)
- 표(table) 형식도 워드 문서에 포함

**출력 파일명**
- `주식강의_다중문서_심층분석_리포트.md`
- `주식강의_다중문서_심층분석_리포트.docx`

---

### 탭 4: 📈 누적형 매매 시뮬레이션 (`app2.py` 전용)

탭 3에서 생성한 **종목별 매매뷰 워드 문서(.docx)** 를 업로드하면, 강의 시그널에 따라 가상 매매를 실행하고 포트폴리오를 **주차별로 누적** 관리합니다.

**핵심 특징**
- 초기 자본금: **1억 원**
- 상태 영속 저장: `portfolio_state.json` (앱 재시작 후에도 이어서 진행)
- 워드 문서에서 강의일(`26년 6월 15일` 형식)과 매매뷰 표 자동 파싱
- 한국/미국 주식 혼합 지원 (환율 USDKRW 반영)
- yfinance로 과거·현재 주가 조회

**사용 방법**
1. 탭 3에서 생성한 매매뷰 `.docx` 파일 업로드
2. **누적 시뮬레이션 실행 및 결과 덮어쓰기** 클릭
3. 포트폴리오 평가, 거래 로그 확인
4. 다음 주차 문서를 업로드하면 기존 잔고·보유량 위에 이어서 진행

**매매뷰 → 액션 매핑**

| 매매뷰 키워드 | 실행 액션 |
|---|---|
| 적극 분할 매수 | 강의일 시가 즉시 매수 (약 300만 원 분량) |
| 분할 매수 | 전일 종가 -2% 목표가 지정가 대기 |
| 눌림목 분할 매수 | 전일 종가 -5% 목표가 지정가 대기 |
| 소량 장기보유 | 시가 1차 매수 + 2·3차 추가 대기 주문 |
| 관망 / 소량보유 / 시큰둥 | 보유 시 1/3 매도 |
| 보수적 관망 | 보유 시 1/2 매도 |
| 삐뽀삐뽀 | 보유 시 전량 매도 |

**지원 종목 (TICKER_MAP)**

SK하이닉스, 삼성전자, 마벨테크놀로지, LIG D&A, GE버노바, 현대모비스, 삼양식품, 엔비디아, TSMC, SK텔레콤, 삼성생명, 삼성증권, 샌디스크, 삼성전기, 한화에어로스페이스, 현대차, 메타, 알파벳, 아마존, 테슬라, 브로드컴, 마이크로소프트, 팔란티어, 이튼, 센트러스에너지 등

**시뮬레이션 초기화**

화면 우측 **잔고 및 시뮬레이션 초기화** 버튼 → `portfolio_state.json` 삭제 후 1억 원부터 재시작

**`portfolio_state.json` 구조**

```json
{
    "cash": 100000000,
    "portfolio": {
        "삼성전자": { "shares": 8, "total_cost": 2740000.0 }
    },
    "pending_orders": [],
    "trade_logs": [],
    "last_lecture_date": "2026-06-15"
}
```

---

## 버전별 기능 비교

| 기능 | app1.py | app.py | app2.py |
|---|---|---|---|
| 영상 STT | Whisper (절대 경로, 단일) | Whisper (다중 업로드) | Whisper (다중 업로드) |
| PDF 변환 | LlamaParse (단일) | LlamaParse (다중) | LlamaParse (다중) |
| AI 분석 | Claude 3단계 (단일 파일) | Claude 3단계 (다중 + 워드) | Claude 3단계 (다중 + 워드) |
| 매매 시뮬레이션 | ❌ | ❌ | ✅ (탭 4) |
| 분석 모델 | claude-sonnet-4-6 | claude-sonnet-4-6 | claude-sonnet-4-6 |

---

## 의존성 패키지

```
streamlit
requests
python-dotenv
pymupdf
llama-parse
nest_asyncio
anthropic
openai
python-docx
markdown
htmldocx
yfinance
pandas
```

| 패키지 | 사용 위치 |
|---|---|
| `openai` | 탭 1 — Whisper STT |
| `llama-parse`, `pymupdf` | 탭 2 — PDF 변환 |
| `anthropic` | 탭 3 — AI 분석 |
| `markdown`, `python-docx`, `htmldocx` | 탭 3 — 워드 다운로드 (`app.py`, `app2.py`) |
| `yfinance`, `pandas` | 탭 4 — 매매 시뮬레이션 (`app2.py`) |

> `llama-parse` 패키지는 deprecated 상태입니다. 현재 앱은 정상 동작하지만, 향후 [LlamaCloud 통합 SDK](https://developers.llamaindex.ai/python/cloud/llamaparse/getting_started/)로 마이그레이션을 권장합니다.

---

## Streamlit 설정

`.streamlit/config.toml`:

```toml
[server]
maxUploadSize = 3072   # 최대 업로드 3GB (MB 단위)
```

---

## 전체 워크플로우 (권장 사용 순서)

```
1. [탭 1] 강의 영상 업로드 → 녹취록 TXT 생성
2. [탭 2] 강의 교재 PDF 업로드 → 마크다운 MD 생성
3. [탭 3] 교재(MD/PDF) + 녹취록(TXT) 업로드 → AI 분석 → 워드(.docx) 다운로드
4. [탭 4] 매매뷰 워드(.docx) 업로드 → 주차별 누적 시뮬레이션 실행
```

---

## 주의 사항

- **API 비용:** Whisper, LlamaParse, Claude API 모두 사용량에 따라 과금됩니다.
- **영상 입력 방식:** `app1.py`는 로컬 절대 경로, `app.py`/`app2.py`는 파일 업로드 방식입니다.
- **긴 영상:** 30분 단위 분할 후 순차 처리하므로 영상 길이와 파일 수에 비례해 시간이 소요됩니다.
- **PDF 변환:** 페이지별 LlamaParse 호출이므로 페이지 수가 많을수록 API 호출 횟수와 비용이 증가합니다.
- **대용량 업로드:** Streamlit 업로드 한도는 3GB로 설정되어 있으나, 실제 처리 시간과 메모리 사용량에 유의하세요.
- **시뮬레이션:** yfinance 데이터는 지연·누락될 수 있으며, 실제 투자 결과를 보장하지 않습니다.
- **상태 파일:** `portfolio_state.json`은 로컬 시뮬레이션 데이터입니다. Git에 올릴지 여부는 사용자 판단에 맡깁니다.
- **API 키 보안:** `.env` 파일을 Git에 커밋하지 마세요.

---

## 라이선스

개인 프로젝트 — 용도에 맞게 자유롭게 사용·수정하세요.
