import streamlit as st
import subprocess
import os
import tempfile
import requests
import re
import fitz  # PyMuPDF
from dotenv import load_dotenv

# LlamaParse 패키지 및 비동기 방어
from llama_parse import LlamaParse
import nest_asyncio
nest_asyncio.apply()

# Anthropic (Claude) 패키지
import anthropic

# .env 파일 로드
load_dotenv()

# 웹 브라우저 탭 및 레이아웃 설정 (더 넓게 보기 위해 wide 모드 적용)
st.set_page_config(page_title="AI 종합 데이터 변환 및 분석 툴", page_icon="🛠️", layout="wide")

st.title("🛠️ AI 종합 데이터 변환 및 분석 툴")
st.markdown("영상 음성 추출, 고품질 PDF 복원, 그리고 **Claude 3.5 Sonnet 기반의 주식 강의 심층 교차 분석**을 통합 제공합니다.")

# 상단 3개 탭 구성
tab1, tab2, tab3 = st.tabs(["🎥 영상 -> TXT 변환", "📄 PDF -> MD 변환 (LlamaParse)", "🧠 AI 강의 종합 분석 (Claude 3.5)"])

# ==========================================
# 탭 1: 영상 음성 텍스트 변환 (Deepgram)
# ==========================================
with tab1:
    st.header("🎥 영상 음성 -> 텍스트 변환")
    # (이전 코드와 완벽히 동일하여 생략 없이 전체 유지)
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        api_key = st.text_input("Deepgram API Key:", type="password", key="vid_key")
        
    video_path_input = st.text_input("영상 파일의 절대 경로를 입력하세요:", placeholder="예: C:\\Users\\Username\\Videos\\Seo_260526.mp4")

    if st.button("🚀 영상 변환 시작", key="btn_vid"):
        video_path = video_path_input.strip('"').strip("'")
        if not api_key or not video_path or not os.path.exists(video_path):
            st.error("API 키와 올바른 영상 경로를 확인해 주세요.")
        else:
            audio_path = ""
            base_filename = os.path.splitext(os.path.basename(video_path))[0]
            output_txt_filename = f"{base_filename}_변환.txt"

            try:
                duration_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path]
                total_duration = float(subprocess.run(duration_cmd, stdout=subprocess.PIPE, text=True).stdout.strip())

                st.write("### ⏳ 오디오 추출 진행 상태")
                progress_text = st.empty()
                progress_bar = st.progress(0.0)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_aud:
                    audio_path = tmp_aud.name
                
                command = ["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "libmp3lame", "-q:a", "2", audio_path]
                process = subprocess.Popen(command, stderr=subprocess.PIPE, universal_newlines=True, encoding='utf-8')
                
                time_regex = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})")
                for line in process.stderr:
                    match = time_regex.search(line)
                    if match:
                        h, m, s = match.groups()
                        current_time = int(h) * 3600 + int(m) * 60 + float(s)
                        percent = min(1.0, current_time / total_duration)
                        progress_bar.progress(percent)
                        progress_text.text(f"1단계: 영상에서 오디오 추출 중... ({int(percent * 100)}%)")
                
                process.wait()
                progress_bar.progress(1.0)
                progress_text.text("1단계 완료")

                with st.spinner("2단계: AI가 음성을 텍스트로 변환 중입니다..."):
                    url = "https://api.deepgram.com/v1/listen?model=nova-2&language=ko&smart_format=true"
                    headers = {"Authorization": f"Token {api_key}", "Content-Type": "audio/mp3"}
                    with open(audio_path, "rb") as audio_file:
                        response = requests.post(url, headers=headers, data=audio_file)
                    
                    if response.status_code == 200:
                        transcript = response.json()['results']['channels'][0]['alternatives'][0]['transcript']
                        st.success("✅ 영상 텍스트 변환 완료!")
                        st.text_area("영상 변환 결과", transcript, height=250)
                        st.download_button("📄 텍스트 다운로드", transcript, file_name=output_txt_filename, mime="text/plain")
                    else:
                        st.error(f"오류: {response.status_code}")
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
            finally:
                if audio_path and os.path.exists(audio_path):
                    try: os.remove(audio_path)
                    except: pass

# ==========================================
# 탭 2: PDF 마크다운 변환 (LlamaParse)
# ==========================================
with tab2:
    st.header("📄 고품질 PDF -> 마크다운(.md) 변환")
    llama_api_key = os.getenv("LLAMA_CLOUD_API_KEY")
    if not llama_api_key:
        llama_api_key = st.text_input("LlamaCloud API Key:", type="password", key="pdf_key")

    uploaded_pdf = st.file_uploader("변환할 PDF 파일을 업로드하세요:", type=["pdf"], key="pdf_upload")

    if st.button("🚀 고품질 PDF 변환 시작", key="btn_pdf"):
        if not llama_api_key or not uploaded_pdf:
            st.error("API Key와 PDF 파일이 필요합니다.")
        else:
            try:
                pdf_base_name = os.path.splitext(uploaded_pdf.name)[0]
                output_md_filename = f"{pdf_base_name}_변환.md"
                
                doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
                total_pages = len(doc)

                st.write("### ⏳ 문서 분석 진행 상태")
                progress_text = st.empty()
                progress_bar = st.progress(0.0)
                
                full_markdown = ""
                parser = LlamaParse(api_key=llama_api_key, result_type="markdown", verbose=False)

                for i in range(total_pages):
                    current_page = i + 1
                    progress_text.text(f"LlamaParse 분석 중... ({current_page}/{total_pages} 페이지)")
                    
                    page_doc = fitz.open()
                    page_doc.insert_pdf(doc, from_page=i, to_page=i)
                    
                    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                    tmp_page_path = tmp_file.name
                    tmp_file.close() 
                    
                    page_doc.save(tmp_page_path)
                    page_doc.close()
                    
                    parsed_docs = parser.load_data(tmp_page_path)
                    if parsed_docs:
                        full_markdown += parsed_docs[0].text + "\n\n"
                    
                    try: os.remove(tmp_page_path)
                    except: pass 

                    progress_bar.progress(current_page / total_pages)

                progress_text.text("✅ PDF 마크다운 변환 완료!")
                doc.close()

                st.text_area("변환 결과", full_markdown, height=300)
                st.download_button("📄 마크다운 다운로드", full_markdown, file_name=output_md_filename, mime="text/markdown")
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")

# ==========================================
# 탭 3: AI 종합 분석 (Claude 3.5 Sonnet)
# ==========================================
with tab3:
    st.header("🧠 주식 강의 심층 교차 분석 (Claude 3.5 Sonnet)")
    st.markdown("교재(MD/PDF)와 강사 녹취록(TXT)을 업로드하면, 지정된 5가지 룰에 따라 AI가 완벽한 맞춤형 요약 리포트를 작성합니다.")

    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        st.warning("⚠️ .env 파일에 ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        anthropic_api_key = st.text_input("Anthropic API Key를 입력하세요:", type="password", key="claude_key")
    else:
        st.success("✅ .env 파일에서 Anthropic API Key를 성공적으로 불러왔습니다.")

    # 두 개의 파일을 나란히 업로드하도록 화면 분할
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. 교재 / 강의자료")
        material_file = st.file_uploader("교재 업로드 (MD 또는 PDF 지원)", type=["md", "pdf"])
    with col2:
        st.subheader("2. 강사 녹취록")
        transcript_file = st.file_uploader("녹취록 업로드 (TXT 파일)", type=["txt"])

    if st.button("🚀 AI 교차 분석 시작 (리포트 생성)", type="primary"):
        if not anthropic_api_key:
            st.error("Anthropic API Key가 필요합니다.")
        elif not material_file or not transcript_file:
            st.error("교재 파일과 녹취록 파일을 모두 업로드해 주세요.")
        else:
            try:
                with st.spinner("파일 텍스트 추출 중..."):
                    # 1. 교재 자료 텍스트 추출
                    material_text = ""
                    if material_file.name.endswith(".pdf"):
                        # PDF일 경우 PyMuPDF로 단순 텍스트 추출 (표/이미지는 제외된 기본 텍스트)
                        doc = fitz.open(stream=material_file.read(), filetype="pdf")
                        for page in doc:
                            material_text += page.get_text() + "\n"
                        doc.close()
                    else:
                        # MD 파일일 경우 그대로 디코딩
                        material_text = material_file.read().decode("utf-8")
                    
                    # 2. 녹취록 텍스트 추출
                    transcript_text = transcript_file.read().decode("utf-8")

                with st.spinner("Claude 3.5 Sonnet이 자료를 교차 검증하며 심층 분석 리포트를 작성 중입니다... (약 30초~1분 소요)"):
                    
                    # 선생님께서 제공해주신 '분석 지침(Rule)'을 시스템 프롬프트로 완벽히 이식
                    system_prompt = """당신은 세계 최고의 주식 강의 분석가이자 투자 전략가입니다.
제공되는 2개의 자료(주식 강의 교재와 해당 강의의 녹취록)를 교차 검증하여, 아래의 5가지 지침과 출력 형식에 맞춰 핵심 내용을 빠짐없이 심층 정리해 주세요.

[분석 및 출력 지침]
1. 종합 핵심 브리핑 (유연한 핵심 포인트 도출 및 상세 서술):
- 교재의 목차 흐름을 기본 뼈대로 하되, 강사가 녹취록에서 특별히 시간을 많이 할애하여 열변을 토하거나 중요하다고 강조한 내용을 최우선 순위로 삼아 이번 주 최우선 핵심 포인트를 도출해 주세요.
- 핵심 포인트 개수는 기본 3가지로 하되, 강사가 강조한 내용이 많을 경우 5가지 혹은 그 이상으로 유연하게 모두 정리해 주세요. (강조된 부분이 적다면 1~2가지도 무방함)
- (중요) 단순하고 짧은 요약을 지양하고, 강사가 강조한 핵심 배경과 이유를 충분히 이해할 수 있도록 상세하고 깊이 있게 서술해 주세요.

2. 교재 + 강사의 추가 인사이트 결합:
- 교재에 있는 딱딱한 전문 용어나 개념 중, 강사가 녹취록에서 초보자도 이해하기 쉽게 비유를 들었거나 부연 설명한 부분을 적극적으로 찾아내어 그 설명 방식을 그대로 반영해 상세히 정리해 주세요.

3. [강사 특별 코멘트] 섹션 분리:
- 교재에는 명시되어 있지 않으나 강사가 강의 중에 추가로 언급한 시장의 최신 동향, 거시경제(매크로) 노이즈에 대한 경고, 특정 섹터에 대한 개인적인 견해 및 주의사항이 있다면 '[강사 특별 코멘트]'라는 제목 아래 별도로 눈에 띄게 정리해 주세요. 이 부분 역시 배경 설명을 생략하지 말고 충분히 기재해 주세요.

4. 종목별 심층 뷰(View) 및 밸류에이션 정리 (모든 종목 포함 및 상세 서술):
- 교재에 기술된 종목 순서를 기준으로 하여, 교재에 언급된 '모든 종목'에 대해 다음 3가지 요소를 반드시 포함해 종목별로 정리해 주세요. 
(단, 강사가 "통째로 지나갑니다" 등으로 생략하거나 별다른 언급 없이 넘어간 종목의 경우에도 절대 제외하지 말고, '통째로 생략됨' 또는 '별다른 언급 없이 넘어감'이라고 명확히 기재하여 모든 종목을 빠짐없이 정리해 주세요.)
- (중요) 출력물이 많아지더라도 각 종목의 주요 핵심과 관련 배경들을 절대 간략하게 생략하지 마세요. 강사가 언급한 상세한 모멘텀, 이슈, 매매 뷰의 이유를 풍부하고 깊이 있게 작성해야 합니다.
  A. 음성(TXT)에서 추가로 강조된 해당 종목의 핵심 모멘텀 및 이슈 (단편적인 요약 금지, 상세한 배경 포함. 생략된 경우 해당 사실 기재)
  B. 해당 종목의 PER 수치 (교재와 녹취록에 언급된 수치 모두 기재, 없으면 '언급 없음' 기재)
  C. 담쌤(강사)의 명확한 매매 뷰 (예: 적극 분할 매수, 눌림목 대기, 관망, 밸류에이션 고평가로 인한 패스 등. 언급이 없는 경우 '뷰 부재 및 패스' 기재)와 그렇게 판단한 구체적인 이유 서술.

5. 실전 적용 포인트:
- 종합된 분석 내용을 바탕으로, 투자자가 이번 주 실전 투자나 추가 공부 시 가장 집중해야 할 구체적인 전략이나 결론을 2~3가지 요약해 주세요.
- 담쌤(강사)의 강의한 알짜를 맨 먼저 기재하고, 각 종목별 매매뷰를 간략히 핵심만 요약해서 정리해주세요. (예: '26년 6월 1일(강의일), 삼성전자 적극매수, SK하이닉스 적극매수, 삼성전기 조정기다림, SK텔레콤 조금씩 매수' 등)"""

                    # 사용자 데이터 세팅
                    user_message = f"다음 두 자료를 바탕으로 지침에 맞게 분석 리포트를 작성해 주세요.\n\n<교재_자료>\n{material_text}\n</교재_자료>\n\n<강사_녹취록>\n{transcript_text}\n</강사_녹취록>"

                    # Claude 3.5 Sonnet API 호출
                    client = anthropic.Anthropic(api_key=anthropic_api_key)
                    response = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=8192,  # 상세 서술을 위해 최대 출력 토큰 확보
                        temperature=0.3,  # 분석의 정확성을 위해 창의성(온도)을 낮춤
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": user_message}
                        ]
                    )

                    analysis_result = response.content[0].text

                    st.success("✅ 맞춤형 심층 분석 리포트가 완성되었습니다!")
                    
                    # 결과를 마크다운 형태로 예쁘게 출력
                    st.markdown("---")
                    st.markdown(analysis_result)
                    st.markdown("---")

                    # 파일 다운로드 제공
                    report_filename = "주식강의_심층분석_리포트.md"
                    st.download_button(
                        label="📥 최종 분석 리포트 다운로드 (.md)",
                        data=analysis_result,
                        file_name=report_filename,
                        mime="text/markdown",
                        type="primary"
                    )

            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {str(e)}")