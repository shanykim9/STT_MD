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

# 웹 브라우저 탭 및 레이아웃 설정
st.set_page_config(page_title="AI 종합 데이터 변환 및 분석 툴", page_icon="🛠️", layout="wide")

st.title("🛠️ AI 종합 데이터 변환 및 분석 툴")
st.markdown("영상 음성 추출, 고품질 PDF 복원, 그리고 **Claude 기반의 주식 강의 심층 교차 분석(3단계 세분할)**을 통합 제공합니다.")

tab1, tab2, tab3 = st.tabs(["🎥 영상 -> TXT 변환", "📄 PDF -> MD 변환 (LlamaParse)", "🧠 AI 강의 종합 분석 (3단계 세분할)"])

# ==========================================
# 탭 1: 영상 음성 텍스트 변환 (OpenAI Whisper 안정화 버전)
# ==========================================
with tab1:
    st.header("🎥 영상 음성 -> 텍스트 변환 (OpenAI Whisper)")
    st.markdown("네트워크 오류(10054)가 없는 가장 안정적인 **OpenAI Whisper API**를 사용하여 텍스트를 추출합니다.")
    
    import glob
    from openai import OpenAI
    
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not openai_api_key:
        openai_api_key = st.text_input("OpenAI API Key를 입력하세요:", type="password", key="vid_key").strip()
        
    video_path_input = st.text_input("영상 파일의 절대 경로를 입력하세요:", placeholder="예: C:\\Users\\Username\\Videos\\Seo_260526.mp4")

    if st.button("🚀 안정적인 영상 변환 시작", key="btn_vid"):
        video_path = video_path_input.strip('"').strip("'")
        if not openai_api_key or not video_path or not os.path.exists(video_path):
            st.error("API 키와 올바른 영상 경로를 확인해 주세요.")
        else:
            base_filename = os.path.splitext(os.path.basename(video_path))[0]
            output_txt_filename = f"{base_filename}_변환.txt"

            try:
                # OpenAI 클라이언트 초기화
                client = OpenAI(api_key=openai_api_key)
                
                duration_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path]
                total_duration = float(subprocess.run(duration_cmd, stdout=subprocess.PIPE, text=True).stdout.strip())

                st.write("### ⏳ 오디오 추출 및 변환 진행 상태")
                progress_text = st.empty()
                progress_bar = st.progress(0.0)

                with tempfile.TemporaryDirectory() as temp_dir:
                    chunk_pattern = os.path.join(temp_dir, "chunk_%03d.mp3")
                    
                    # 💡 OpenAI Whisper의 최대 업로드 용량(25MB)을 넉넉하게 통과하도록 30분(1800초) 단위로 안전하게 분할합니다.
                    command = [
                        "ffmpeg", "-y", "-i", video_path, "-vn", 
                        "-acodec", "libmp3lame", "-ac", "1", "-ar", "16000", "-b:a", "32k",
                        "-f", "segment", "-segment_time", "1800", 
                        chunk_pattern
                    ]
                    process = subprocess.Popen(command, stderr=subprocess.PIPE, universal_newlines=True, encoding='utf-8')
                    
                    time_regex = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})")
                    for line in process.stderr:
                        match = time_regex.search(line)
                        if match:
                            h, m, s = match.groups()
                            current_time = int(h) * 3600 + int(m) * 60 + float(s)
                            percent = min(1.0, current_time / total_duration)
                            progress_bar.progress(percent)
                            progress_text.text(f"1단계: OpenAI 규격에 맞춘 30분 단위 오디오 분할 중... ({int(percent * 100)}%)")
                    
                    process.wait()
                    progress_bar.progress(1.0)
                    progress_text.text("1단계 완료: 오디오 분할 추출 완료")

                    chunks = sorted(glob.glob(os.path.join(temp_dir, "chunk_*.mp3")))
                    total_chunks = len(chunks)
                    
                    full_transcript = ""
                    has_error = False

                    # 서버 전송 및 텍스트 변환 단계
                    for idx, chunk_file in enumerate(chunks):
                        progress_text.text(f"2단계: OpenAI Whisper로 음성 인식 중... (총 {total_chunks}개 조각 중 {idx+1}번째 처리 중 🔄)")
                        progress_bar.progress(idx / total_chunks)
                        
                        try:
                            with open(chunk_file, "rb") as audio_file:
                                # OpenAI 공식 API 호출 (네트워크 단절에 가장 강력하게 대응하도록 설계됨)
                                transcript = client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=audio_file,
                                    response_format="text"  # json이 아닌 텍스트로 바로 받기
                                )
                            full_transcript += transcript + "\n\n"
                        except Exception as e:
                            st.error(f"오류: {idx+1}번째 조각 처리 중 에러 발생: {str(e)}")
                            has_error = True
                            break

                    if not has_error:
                        progress_bar.progress(1.0)
                        progress_text.text(f"✅ 2단계 완료: 총 {total_chunks}개의 조각을 완벽하게 병합했습니다!")
                        st.success("✅ 영상 텍스트 변환이 완벽하게 완료되었습니다!")
                        st.text_area("영상 변환 결과", full_transcript, height=250)
                        st.download_button("📄 텍스트 다운로드", full_transcript, file_name=output_txt_filename, mime="text/plain")

            except Exception as e:
                st.error(f"오류 발생: {str(e)}")

# ==========================================
# 탭 2: PDF 마크다운 변환 (LlamaParse)
# ==========================================
with tab2:
    st.header("📄 고품질 PDF -> 마크다운(.md) 변환")
    llama_api_key = os.getenv("LLAMA_CLOUD_API_KEY", "").strip()
    if not llama_api_key:
        llama_api_key = st.text_input("LlamaCloud API Key:", type="password", key="pdf_key").strip()

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
# 탭 3: AI 종합 분석 (3단계 세분할 호출)
# ==========================================
with tab3:
    st.header("🧠 주식 강의 무제한 심층 분석 (3단계 세분할 호출)")
    st.markdown("토큰 제한을 완전히 부수기 위해 AI가 **1~3번**, **4번**, **5번** 지침을 각각 별도로 심층 분석하고 실시간으로 화면에 누적 결합합니다.")

    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not anthropic_api_key:
        anthropic_api_key = st.text_input("Anthropic API Key를 입력하세요:", type="password", key="claude_key").strip()

    # --- 1. 화면 내 지침(Rule) 편집 영역 ---
    # 선생님이 요청하신 최종 수정 지침 완벽 반영 (정확한 문구 유지)
    default_rules = """[주식 강의 교차 분석 및 맞춤형 요약 시스템 Rule / Skill]

지금 2개의 자료(주식 강의 교재 PDF 파일 1개이거나 PDF 파일을 텍스트로 변환한 md 파일과 해당 강의의 녹취록 TXT 파일 1개)를 업로드합니다. 
이 두 자료를 교차 검증하여, 아래의 5가지 지침과 출력 형식에 맞춰 이번 주의 핵심 내용을 빠짐없이 심층 정리해 주세요.

**[분석 및 출력 지침]**
1. 종합 핵심 브리핑 (유연한 핵심 포인트 도출 및 요약 서술):
- 교재(PDF/MD)의 목차 흐름을 기본 뼈대로 하되, 강사가 녹취록(TXT)에서 특별히 시간을 많이 할애하여 열변을 토하거나 중요하다고 강조한 내용을 최우선 순위로 삼아 이번 주 최우선 핵심 포인트를 도출해 주세요.
- 핵심 포인트 개수는 기본 3가지로 하되, 강사가 강조한 내용이 많을 경우 5가지 혹은 그 이상으로 유연하게 모두 정리해 주세요. (적다면 1~2가지도 좋습니다.)
- (중요) 단순하고 짧은 요약을 지양하고, 강사가 강조한 핵심 배경과 이유를 이해할 수 있도록 요약해서 서술해 주세요.

2. 교재 + 강사의 추가 인사이트 결합:
- 교재에 있는 딱딱한 전문 용어나 개념 중, 강사가 녹취록에서 초보자도 이해하기 쉽게 비유를 들었거나 부연 설명한 부분을 적극적으로 찾아내어 그 설명 방식을 그대로 반영해 요약해서 정리해 주세요.

3. [강사 특별 코멘트] 섹션 분리:
- 교재에는 명시되어 있지 않으나 강사가 강의 중에 추가로 언급한 시장의 최신 동향, 거시경제(매크로) 노이즈에 대한 경고, 특정 섹터에 대한 개인적인 견해 및 주의사항이 있다면 [강사 특별 코멘트]라는 제목 아래 별도로 눈에 띄게 정리해 주세요. 배경 설명을 생략하지 말고 요약해서 기재해 주세요.

4. 종목별 심층 뷰(View) 및 밸류에이션 정리 (선택과 집중):
- 교재에 언급된 모든 종목을 다루되, 강사가 가장 강조한 상위 5~7개(강조한 내용이 많을 경우 5~7가지 이상으로 유연하게 모두 정리해 주세요. 적다면 1~2가지도 좋습니다.)
 핵심 종목만 아래 3가지 요소(A, B, C)를 포함하여 깊이 있게 작성해 주세요.
  A. 음성(TXT)에서 추가로 강조된 해당 종목의 핵심 모멘텀 및 이슈 (생략된 경우 해당 사실 기재)
  B. 해당 종목의 PER 수치 (교재와 녹취록에 언급된 수치 모두 기재, 없으면 '언급 없음' 기재)
  C. 담쌤(강사)의 명확한 매매 뷰 (예: 적극 분할 매수, 눌림목 대기, 관망 등)와 판단한 구체적인 이유 서술.
- 나머지 단순 언급되거나 패스한 종목들은 글자 수(토큰) 확보를 위해 서술형이 아닌 '요약 표(Table)' 형식(종목명, PER, 매매 뷰 3가지 컬럼)으로 압축해서 한 번에 정리해 주세요.

5. 실전 적용 포인트:
- 종합된 분석 내용을 바탕으로, 투자자가 이번 주 실전 투자나 추가 공부 시 가장 집중해야 할 구체적인 전략이나 결론을 2~3가지 요약해 주세요.
- 담쌤(강사)의 강의한 알짜를 맨 먼저 기재하고, 각 종목별 매매뷰를 간략히 핵심만 요약해서 표로 정리해주세요. (예: '26년 6월 1일(강의일), 삼성전자 적극매수, SK하이닉스 적극매수, 삼성전기 조정기다림 등')"""

    st.subheader("⚙️ AI 분석 지침 (프롬프트)")
    user_rules = st.text_area("이 지침을 바탕으로 AI가 두 문서를 교차 검증합니다:", value=default_rules, height=350)

    st.markdown("---")

    # --- 2. 데이터 업로드 영역 ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📁 1. 교재 / 강의자료")
        material_file = st.file_uploader("교재 업로드 (MD 또는 PDF)", type=["md", "pdf"])
    with col2:
        st.subheader("📁 2. 강사 녹취록")
        transcript_file = st.file_uploader("녹취록 업로드 (TXT)", type=["txt"])

    if st.button("🚀 무제한 3단계 세분할 분석 시작 (리포트 생성)", type="primary"):
        if not anthropic_api_key:
            st.error("Anthropic API Key가 필요합니다.")
        elif not material_file or not transcript_file:
            st.error("교재 파일과 녹취록 파일을 모두 업로드해 주세요.")
        else:
            try:
                with st.spinner("파일 텍스트 추출 중..."):
                    material_text = ""
                    if material_file.name.endswith(".pdf"):
                        doc = fitz.open(stream=material_file.read(), filetype="pdf")
                        for page in doc:
                            material_text += page.get_text() + "\n"
                        doc.close()
                    else:
                        material_text = material_file.read().decode("utf-8")
                    transcript_text = transcript_file.read().decode("utf-8")

                client = anthropic.Anthropic(api_key=anthropic_api_key)
                
                # 시각적 연출을 위한 3개의 컨테이너 (결과가 나오는 즉시 차례대로 화면에 뿌려줌)
                st.markdown("### 📊 분석 결과 리포트")
                st.markdown("---")
                part1_container = st.empty()
                part2_container = st.empty()
                part3_container = st.empty()
                
                # ==========================================
                # [1단계 호출] 지침 1, 2, 3 처리
                # ==========================================
                with st.spinner("🔄 파트 1 분석 중: 지침 1~3번(핵심 브리핑 및 인사이트)을 작성 중입니다..."):
                    system_prompt_1 = "당신은 세계 최고의 주식 강의 분석가입니다. 사용자가 제공하는 <instructions> 안의 지침 중 [1번, 2번, 3번]에 해당하는 내용만 완벽하게 작성하십시오. 4번과 5번은 절대 출력하지 마십시오."
                    
                    user_message_1 = f"""
<instructions>
{user_rules}

[중요 출력 규칙]
- 답변 생성 시 반드시 지침에 명시된 1, 2, 3번 목차 번호와 제목을 그대로 사용하십시오.
- 4번과 5번은 이 단계에서 절대로 출력하지 마십시오.
</instructions>

<material>
{material_text}
</material>

<transcript>
{transcript_text}
</transcript>
"""
                    response_1 = client.messages.create(
                        model="claude-sonnet-4-6", 
                        max_tokens=8192,
                        temperature=0.3,
                        system=system_prompt_1,
                        messages=[{"role": "user", "content": user_message_1}]
                    )
                    part1_result = response_1.content[0].text
                    part1_container.markdown(part1_result)

                # ==========================================
                # [2단계 호출] 지침 4 처리 (종목 분석 전담)
                # ==========================================
                with st.spinner("🔄 파트 2 분석 중: 지침 4번(모든 종목 심층 뷰 및 표 정리)을 집중 분석 중입니다... (가장 오래 걸립니다)"):
                    system_prompt_2 = "당신은 세계 최고의 주식 강의 분석가입니다. 오직 <instructions> 안의 지침 중 [4번]에 해당하는 내용만 집중적으로 작성하십시오."
                    
                    user_message_2 = f"""
<instructions>
{user_rules}

[중요 출력 규칙]
- 답변 생성 시 반드시 지침에 명시된 4번 목차 번호와 제목('4. 종목별 심층 뷰(View) 및 밸류에이션 정리')을 그대로 사용하십시오.
- (핵심) 오직 4번 지침만 수행하십시오. 8,192 토큰을 전부 종목 분석에만 사용해도 좋습니다. 절대로 1, 2, 3번이나 5번 내용을 출력하지 마십시오.
</instructions>

<material>
{material_text}
</material>

<transcript>
{transcript_text}
</transcript>
"""
                    response_2 = client.messages.create(
                        model="claude-sonnet-4-6", 
                        max_tokens=8192,
                        temperature=0.3,
                        system=system_prompt_2,
                        messages=[{"role": "user", "content": user_message_2}]
                    )
                    part2_result = response_2.content[0].text
                    part2_container.markdown(part2_result)

                # ==========================================
                # [3단계 호출] 지침 5 처리 (실전 적용 포인트 전담)
                # ==========================================
                with st.spinner("🔄 파트 3 분석 중: 지침 5번(실전 적용 포인트 및 매매뷰 요약 표)을 마무리 중입니다..."):
                    system_prompt_3 = "당신은 세계 최고의 주식 강의 분석가입니다. 오직 <instructions> 안의 지침 중 [5번]에 해당하는 내용만 작성하십시오."
                    
                    user_message_3 = f"""
앞서 당신이 작성한 1~4번의 분석 결과와 원본 데이터를 바탕으로, 마지막 [5번] 지침을 완벽하게 수행하십시오.

<instructions>
{user_rules}

[중요 출력 규칙]
- 답변 생성 시 반드시 지침에 명시된 5번 목차 번호와 제목('5. 실전 적용 포인트')을 그대로 사용하십시오.
- 오직 5번 지침에 대해서만 답변하십시오. 
</instructions>

<material>
{material_text}
</material>

<transcript>
{transcript_text}
</transcript>

<previous_analysis>
{part1_result}
{part2_result}
</previous_analysis>
"""
                    response_3 = client.messages.create(
                        model="claude-sonnet-4-6", 
                        max_tokens=8192,
                        temperature=0.3,
                        system=system_prompt_3,
                        messages=[{"role": "user", "content": user_message_3}]
                    )
                    part3_result = response_3.content[0].text
                    part3_container.markdown(part3_result)

                st.success("✅ 3단계에 걸친 모든 지침(1~5번)의 심층 분석이 누락 없이 완벽하게 완료되었습니다!")
                
                # 최종 다운로드용 파일 결합
                full_report = part1_result + "\n\n" + part2_result + "\n\n" + part3_result
                st.download_button(
                    label="📥 최종 통합 분석 리포트 다운로드 (.md)",
                    data=full_report,
                    file_name="주식강의_3단계_심층분석_리포트.md",
                    mime="text/markdown",
                    type="primary"
                )

            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {str(e)}")