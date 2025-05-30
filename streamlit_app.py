"""
PDF Claude OCR - Streamlit 웹앱
브라우저에서 실행되는 OCR 서비스
"""

import streamlit as st
import tempfile
import os
import io
import base64
import threading
import time
from pathlib import Path
import logging

# 페이지 설정
st.set_page_config(
    page_title="PDF Claude OCR",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 로컬 모듈 import
try:
    from claude_ocr import ClaudeOCR
    from pdf_converter import PDFConverter
    from file_manager import FileManager
except ImportError as e:
    st.error(f"모듈 import 오류: {e}")
    st.stop()

# 세션 상태 초기화
if 'claude_ocr' not in st.session_state:
    st.session_state.claude_ocr = None
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'results' not in st.session_state:
    st.session_state.results = None

def init_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def create_download_link(file_content, filename, file_type="txt"):
    """파일 다운로드 링크 생성"""
    if file_type == "txt":
        b64 = base64.b64encode(file_content.encode()).decode()
        mime_type = "text/plain"
    else:
        b64 = base64.b64encode(file_content).decode()
        mime_type = "application/pdf"
    
    href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}">📥 {filename} 다운로드</a>'
    return href

def main():
    """메인 웹앱 함수"""
    init_logging()
    
    # 헤더
    st.title("📄 PDF Claude OCR")
    st.markdown("Claude AI를 사용한 고품질 PDF 텍스트 추출 서비스")
    st.markdown("---")
    
    # 사이드바 - API 설정
    with st.sidebar:
        st.header("🔑 API 설정")
        
        api_key = st.text_input(
            "Claude API 키", 
            type="password",
            help="https://console.anthropic.com에서 발급받은 API 키를 입력하세요"
        )
        
        if api_key:
            if st.button("🧪 API 연결 테스트"):
                with st.spinner("API 연결 확인 중..."):
                    try:
                        test_ocr = ClaudeOCR(api_key)
                        # 간단한 연결 테스트
                        from anthropic import Anthropic
                        client = Anthropic(api_key=api_key)
                        response = client.messages.create(
                            model="claude-3-5-sonnet-20241022",
                            max_tokens=10,
                            messages=[{"role": "user", "content": "Hello"}]
                        )
                        
                        st.session_state.claude_ocr = test_ocr
                        st.success("✅ API 연결 성공!")
                        
                    except Exception as e:
                        st.error(f"❌ API 연결 실패: {e}")
        
        st.markdown("---")
        
        # 처리 옵션
        st.header("⚙️ 처리 옵션")
        
        doc_type = st.selectbox(
            "문서 유형",
            ["general", "table", "handwritten", "form"],
            format_func=lambda x: {
                "general": "📄 일반 문서",
                "table": "📊 표가 많은 문서", 
                "handwritten": "✍️ 손글씨",
                "form": "📋 양식/폼"
            }[x]
        )
        
        output_format = st.selectbox(
            "출력 형식",
            ["txt", "pdf"],
            format_func=lambda x: {"txt": "📝 텍스트 파일", "pdf": "📑 PDF 파일"}[x]
        )
        
        dpi = st.slider("이미지 품질 (DPI)", 150, 600, 300, 50)
        
        include_page_numbers = st.checkbox("페이지 번호 포함", value=True)
    
    # 메인 영역
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📁 PDF 파일 업로드")
        
        uploaded_file = st.file_uploader(
            "PDF 파일을 선택하세요",
            type=['pdf'],
            help="최대 200MB까지 지원됩니다"
        )
        
        if uploaded_file:
            st.success(f"✅ 파일 업로드됨: {uploaded_file.name}")
            
            # 파일 정보 표시
            file_size = len(uploaded_file.getvalue()) / (1024 * 1024)
            st.info(f"📏 파일 크기: {file_size:.1f}MB")
            
            # 처리 시작 버튼
            if st.session_state.claude_ocr and not st.session_state.processing:
                if st.button("🚀 텍스트 추출 시작", type="primary"):
                    st.session_state.processing = True
                    st.rerun()
    
    with col2:
        st.header("🔄 처리 상태")
        
        if st.session_state.processing and uploaded_file:
            # 진행률 표시
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 처리 실행
            process_pdf(
                uploaded_file, 
                doc_type, 
                output_format, 
                dpi, 
                include_page_numbers,
                progress_bar,
                status_text
            )
        
        elif st.session_state.results:
            st.success("✅ 처리 완료!")
            
            # 결과 다운로드
            result_content, filename = st.session_state.results
            
            st.download_button(
                label=f"📥 {filename} 다운로드",
                data=result_content,
                file_name=filename,
                mime="text/plain" if filename.endswith('.txt') else "application/pdf"
            )
            
            # 미리보기 (텍스트 파일인 경우)
            if filename.endswith('.txt'):
                with st.expander("📄 결과 미리보기"):
                    st.text_area(
                        "추출된 텍스트",
                        result_content[:2000] + "..." if len(result_content) > 2000 else result_content,
                        height=300
                    )
        
        else:
            st.info("API 키를 입력하고 PDF 파일을 업로드해주세요.")
    
    # 사용 안내
    st.markdown("---")
    with st.expander("💡 사용 방법 및 주의사항"):
        st.markdown("""
        ### 📖 사용 방법
        1. **API 키 입력**: 사이드바에서 Claude API 키 입력 후 테스트
        2. **파일 업로드**: PDF 파일을 드래그 앤 드롭 또는 선택
        3. **옵션 설정**: 문서 유형과 출력 형식 선택
        4. **처리 시작**: "텍스트 추출 시작" 버튼 클릭
        5. **결과 다운로드**: 완료 후 결과 파일 다운로드
        
        ### ⚠️ 주의사항
        - **비용**: 페이지당 약 $0.01-0.03의 API 비용 발생
        - **시간**: 페이지당 약 10-30초 소요
        - **크기**: 최대 200MB 파일까지 지원
        - **보안**: 업로드된 파일은 처리 후 자동 삭제됨
        
        ### 🔐 개인정보 보호
        - 모든 파일은 서버에 저장되지 않습니다
        - 처리 완료 후 임시 파일은 자동 삭제됩니다
        - API 키는 브라우저 세션에만 저장됩니다
        """)

def process_pdf(uploaded_file, doc_type, output_format, dpi, include_page_numbers, progress_bar, status_text):
    """PDF 처리 함수"""
    try:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            pdf_path = tmp_file.name
        
        # PDF 변환기 초기화
        pdf_converter = PDFConverter()
        
        # Poppler 설치 확인
        if not pdf_converter.check_poppler_installation():
            st.error("😱 Poppler이 설치되지 않았습니다!")
            st.info("""
            **로컬 실행 시:**
            - Windows: `choco install poppler` 또는 수동 설치
            - macOS: `brew install poppler`
            - Ubuntu: `sudo apt-get install poppler-utils`
            
            **Streamlit Cloud 배포 시:**
            - `packages.txt` 파일이 자동으로 설치합니다
            - 배포 후에는 자동으로 작동합니다
            """)
            return
            
        pdf_converter = PDFConverter()
        file_manager = FileManager()
        
        # 1단계: PDF를 이미지로 변환
        status_text.text("📷 PDF를 이미지로 변환 중...")
        progress_bar.progress(10)
        
        temp_folder = tempfile.mkdtemp()
        image_paths = pdf_converter.convert_pdf_to_images(
            pdf_path,
            temp_folder,
            dpi=dpi
        )
        
        if not image_paths:
            st.error("PDF 변환에 실패했습니다.")
            return
        
        progress_bar.progress(30)
        
        # 2단계: OCR 처리
        status_text.text("🤖 Claude AI로 텍스트 추출 중...")
        
        total_pages = len(image_paths)
        ocr_results = {}
        
        for i, image_path in enumerate(image_paths):
            # 페이지별 진행률 업데이트
            page_progress = 30 + (i / total_pages) * 60
            progress_bar.progress(int(page_progress))
            status_text.text(f"🤖 페이지 {i+1}/{total_pages} 처리 중...")
            
            # OCR 처리
            text = st.session_state.claude_ocr.extract_text_from_image(image_path, doc_type)
            
            ocr_results[i] = {
                'page': i + 1,
                'text': text,
                'status': 'success',
                'image_path': image_path
            }
        
        progress_bar.progress(90)
        status_text.text("💾 결과 파일 생성 중...")
        
        # 3단계: 결과 저장
        if output_format == "txt":
            # 텍스트 파일 생성
            result_text = ""
            result_text += "PDF OCR 결과\n"
            result_text += "=" * 50 + "\n"
            result_text += f"총 페이지 수: {len(ocr_results)}\n"
            result_text += "=" * 50 + "\n\n"
            
            for i in sorted(ocr_results.keys()):
                result = ocr_results[i]
                if include_page_numbers:
                    result_text += f"페이지 {result['page']}\n"
                    result_text += "-" * 20 + "\n"
                result_text += result['text'] + "\n\n"
            
            filename = f"{uploaded_file.name.replace('.pdf', '')}_ocr.txt"
            st.session_state.results = (result_text, filename)
            
        else:
            # PDF 파일 생성
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_output:
                output_path = tmp_output.name
            
            file_manager.save_as_pdf_reportlab(ocr_results, output_path, include_page_numbers)
            
            with open(output_path, 'rb') as f:
                pdf_content = f.read()
            
            filename = f"{uploaded_file.name.replace('.pdf', '')}_ocr.pdf"
            st.session_state.results = (pdf_content, filename)
            
            # 임시 파일 정리
            os.unlink(output_path)
        
        progress_bar.progress(100)
        status_text.text("✅ 완료!")
        
        # 임시 파일 정리
        pdf_converter.cleanup_temp_files(image_paths)
        os.unlink(pdf_path)
        
        st.session_state.processing = False
        st.rerun()
        
    except Exception as e:
        st.error(f"처리 중 오류가 발생했습니다: {e}")
        st.session_state.processing = False

if __name__ == "__main__":
    main()