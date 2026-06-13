# AI 종합 데이터 변환 및 분석 툴 (STT_MD)

영상 음성 추출, PDF 마크다운 변환, 주식 강의 교차 분석을 하나의 Streamlit 웹 앱에서 처리하는 통합 도구입니다.

## 주요 기능

| 탭 | 기능 | 사용 API / 도구 |
|---|---|---|
| 🎥 영상 → TXT | 영상 파일에서 음성을 추출해 텍스트로 변환 | OpenAI Whisper API, FFmpeg |
| 📄 PDF → MD | PDF를 고품질 마크다운으로 변환 | LlamaParse (LlamaCloud), PyMuPDF |
| 🧠 AI 강의 분석 | 교재 + 녹취록 교차 분석 리포트 생성 | Anthropic Claude (Sonnet 4.6) |

---

## 프로젝트 구조

```
STT_MD/
├── app1.py              # 메인 앱 (Whisper + LlamaParse + Claude 3단계 분석)
├── app.py               # 이전 버전 (Deepgram + Claude 단일 호출)
├── requirements.txt     # Python 패키지 의존성
├── .env                 # API 키 설정 (Git에 포함하지 않음)
├── .gitignore
└── .streamlit/
    └── config.toml      # Streamlit 설정 (업로드 용량 3GB)
```

---

## 사전 요구 사항

### 1. Python 3.8 이상

### 2. FFmpeg / FFprobe (탭 1 필수)

영상에서 오디오를 추출하고 분할하기 위해 시스템 PATH에 `ffmpeg`, `ffprobe`가 설치되어 있어야 합니다.

- Windows: [FFmpeg 공식 다운로드](https://ffmpeg.org/download.html) 후 PATH 등록
- 설치 확인:
  ```bash
  ffmpeg -version
  ffprobe -version
  ```

### 3. API 키

| 환경 변수 | 용도 | 발급처 |
|---|---|---|
| `OPENAI_API_KEY` | 영상 음성 → 텍스트 (Whisper) | [OpenAI Platform](https://platform.openai.com/) |
| `LLAMA_CLOUD_API_KEY` | PDF → 마크다운 변환 | [LlamaCloud](https://cloud.llamaindex.ai/) |
| `ANTHROPIC_API_KEY` | 주식 강의 AI 분석 | [Anthropic Console](https://console.anthropic.com/) |

---

## 설치 및 실행

### 1. 저장소 클론

```bash
git clone <your-repo-url>
cd STT_MD
```

### 2. 가상 환경 생성 및 패키지 설치 (권장)

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

> `.env` 파일은 `.gitignore`에 포함되어 있으므로 Git에 커밋되지 않습니다.  
> API 키를 `.env`에 넣지 않아도, 앱 실행 후 각 탭에서 직접 입력할 수 있습니다.

### 4. 앱 실행

```bash
streamlit run app1.py
```

브라우저에서 `http://localhost:8501` 이 자동으로 열립니다.

---

## 사용 방법

### 탭 1: 🎥 영상 → TXT 변환

1. OpenAI API Key 입력 (`.env`에 설정했다면 생략 가능)
2. 변환할 **영상 파일의 절대 경로** 입력  
   예: `C:\Users\Username\Videos\Seo_260526.mp4`
3. **안정적인 영상 변환 시작** 버튼 클릭

**처리 흐름**
- FFmpeg로 영상에서 오디오 추출 (16kHz, mono, 32kbps MP3)
- OpenAI Whisper 업로드 제한(25MB)을 고려해 **30분(1800초) 단위**로 분할
- 각 조각을 OpenAI Whisper API(`whisper-1`)로 순차 변환
- 전체 텍스트 병합 후 화면 표시 및 `.txt` 다운로드

**출력 파일명:** `{영상파일명}_변환.txt`

---

### 탭 2: 📄 PDF → MD 변환

1. LlamaCloud API Key 입력
2. 변환할 PDF 파일 업로드
3. **고품질 PDF 변환 시작** 버튼 클릭

**처리 흐름**
- PyMuPDF로 PDF를 **페이지 단위**로 분리
- 각 페이지를 LlamaParse로 마크다운 변환
- 전체 페이지 결과를 하나의 마크다운으로 병합

**출력 파일명:** `{PDF파일명}_변환.md`

---

### 탭 3: 🧠 AI 강의 종합 분석 (3단계 세분할)

교재(PDF/MD)와 강의 녹취록(TXT)을 교차 검증하여 주식 강의 심층 분석 리포트를 생성합니다.

**입력 파일**
| 구분 | 형식 |
|---|---|
| 교재 / 강의자료 | `.md` 또는 `.pdf` |
| 강사 녹취록 | `.txt` |

**분석 지침 (5가지)**
1. 종합 핵심 브리핑
2. 교재 + 강사 추가 인사이트 결합
3. [강사 특별 코멘트] 섹션 분리
4. 종목별 심층 뷰 및 밸류에이션 정리
5. 실전 적용 포인트

**3단계 세분할 호출 방식**

토큰 제한을 우회하기 위해 Claude API를 3번 나눠 호출합니다.

| 단계 | 처리 지침 | max_tokens |
|---|---|---|
| 1단계 | 지침 1, 2, 3 | 8,192 |
| 2단계 | 지침 4 (종목 분석) | 8,192 |
| 3단계 | 지침 5 (실전 포인트) | 8,192 |

각 단계 결과가 실시간으로 화면에 누적 표시되며, 완료 후 통합 `.md` 리포트를 다운로드할 수 있습니다.

**출력 파일명:** `주식강의_3단계_심층분석_리포트.md`

**사용 모델:** `claude-sonnet-4-6`

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
openai          # app1.py 탭 1에서 사용 (requirements.txt에 미포함 — 아래 참고)
```

> `app1.py`의 Whisper 탭은 `openai` 패키지를 사용합니다.  
> `requirements.txt`에 없다면 별도로 설치하세요:
> ```bash
> pip install openai
> ```

---

## Streamlit 설정

`.streamlit/config.toml`:

```toml
[server]
maxUploadSize = 3072   # 최대 업로드 3GB (MB 단위)
```

---

## app.py vs app1.py

| 항목 | app.py (이전) | app1.py (현재) |
|---|---|---|
| 영상 STT | Deepgram API | OpenAI Whisper API |
| PDF 변환 | LlamaParse | LlamaParse (동일) |
| AI 분석 | Claude 단일 호출 | Claude 3단계 세분할 호출 |
| 분석 모델 | Claude 3.5 Sonnet | Claude Sonnet 4.6 |

**권장:** `app1.py`를 메인으로 사용하세요.

---

## 주의 사항

- **API 비용:** Whisper, LlamaParse, Claude API 모두 사용량에 따라 과금됩니다.
- **영상 경로:** 탭 1은 파일 업로드가 아닌 **로컬 절대 경로** 입력 방식입니다.
- **긴 영상:** 30분 단위 분할 후 순차 처리하므로 영상 길이에 비례해 시간이 소요됩니다.
- **PDF 품질:** LlamaParse는 페이지별 호출이므로 페이지 수가 많을수록 API 호출 횟수와 비용이 증가합니다.
- **API 키 보안:** `.env` 파일을 Git에 커밋하지 마세요.

---

## 라이선스

개인 프로젝트 — 용도에 맞게 자유롭게 사용·수정하세요.
