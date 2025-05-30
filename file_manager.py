"""
파일 관리 모듈
텍스트를 TXT 또는 PDF 파일로 저장하는 기능을 제공
"""

import os
import logging
from typing import Dict, List, Optional
from pathlib import Path
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False
    FPDF = None
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class FileManager:
    """텍스트 파일 저장 관리 클래스"""
    
    def __init__(self):
        """파일 매니저 초기화"""
        self.logger = logging.getLogger(__name__)
        self.setup_fonts()
    
    def setup_fonts(self):
        """PDF 생성을 위한 폰트 설정"""
        try:
            # 한글 폰트 등록 시도
            font_paths = [
                "C:/Windows/Fonts/malgun.ttf",  # Windows
                "/System/Library/Fonts/AppleGothic.ttf",  # macOS
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"  # Linux CJK
            ]
            
            self.korean_font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('Korean', font_path))
                        self.korean_font = 'Korean'
                        self.logger.info(f"한글 폰트 등록 성공: {font_path}")
                        break
                    except Exception as e:
                        self.logger.debug(f"폰트 등록 실패: {font_path}, {e}")
                        continue
            
            if not self.korean_font:
                self.logger.warning("한글 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")
                
        except Exception as e:
            self.logger.warning(f"폰트 설정 실패: {e}")
    
    def save_as_txt(
        self, 
        ocr_results: Dict[int, Dict[str, str]], 
        output_path: str,
        include_page_numbers: bool = True,
        page_separator: str = "\n" + "="*50 + "\n"
    ) -> bool:
        """
        OCR 결과를 TXT 파일로 저장
        
        Args:
            ocr_results: OCR 결과 딕셔너리
            output_path: 출력 파일 경로
            include_page_numbers: 페이지 번호 포함 여부
            page_separator: 페이지 구분자
            
        Returns:
            저장 성공 여부
        """
        try:
            self.logger.info(f"TXT 파일 저장 시작: {output_path}")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                # 파일 헤더 작성
                f.write("PDF OCR 결과\n")
                f.write("="*50 + "\n")
                f.write(f"총 페이지 수: {len(ocr_results)}\n")
                f.write("="*50 + "\n\n")
                
                # 페이지별 텍스트 저장
                for i in sorted(ocr_results.keys()):
                    result = ocr_results[i]
                    
                    if include_page_numbers:
                        f.write(f"페이지 {result['page']}\n")
                        f.write("-" * 20 + "\n")
                    
                    # 상태가 성공인 경우만 텍스트 저장
                    if result.get('status') == 'success':
                        f.write(result['text'])
                    else:
                        f.write(f"[오류] {result['text']}")
                    
                    # 마지막 페이지가 아니면 구분자 추가
                    if i < max(ocr_results.keys()):
                        f.write(page_separator)
                
                # 파일 푸터
                f.write("\n\n" + "="*50)
                f.write(f"\n처리 완료: {len(ocr_results)}페이지")
            
            self.logger.info(f"TXT 파일 저장 완료: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"TXT 파일 저장 실패: {e}")
            return False
    
    def save_as_pdf_fpdf(
        self, 
        ocr_results: Dict[int, Dict[str, str]], 
        output_path: str,
        include_page_numbers: bool = True
    ) -> bool:
        """
        FPDF를 사용하여 OCR 결과를 PDF 파일로 저장
        
        Args:
            ocr_results: OCR 결과 딕셔너리
            output_path: 출력 파일 경로
            include_page_numbers: 페이지 번호 포함 여부
            
        Returns:
            저장 성공 여부
        """
        try:
            if not FPDF_AVAILABLE:
                self.logger.warning("FPDF 라이브러리가 설치되지 않았습니다. ReportLab으로 대체하여 저장합니다.")
                return self.save_as_pdf_reportlab(ocr_results, output_path, include_page_numbers)
                
            self.logger.info(f"PDF 파일 저장 시작 (FPDF): {output_path}")
            
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            # 한글 폰트 설정 (FPDF용)
            try:
                # DejaVu 폰트 사용
                pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
                font_name = 'DejaVu'
            except:
                # 기본 폰트 사용
                font_name = 'Arial'
                self.logger.warning("유니코드 폰트 로드 실패, 기본 폰트 사용")
            
            # 페이지별 처리
            for i in sorted(ocr_results.keys()):
                result = ocr_results[i]
                
                pdf.add_page()
                pdf.set_font(font_name, size=12)
                
                if include_page_numbers:
                    pdf.set_font(font_name, 'B', 14)
                    pdf.cell(0, 10, f'페이지 {result["page"]}', ln=True, align='C')
                    pdf.ln(5)
                
                pdf.set_font(font_name, size=10)
                
                # 텍스트 내용 추가
                text_content = result['text'] if result.get('status') == 'success' else f"[오류] {result['text']}"
                
                # 긴 텍스트를 여러 줄로 분할
                lines = text_content.split('\n')
                for line in lines:
                    if line.strip():
                        # FPDF의 멀티셀 사용
                        try:
                            pdf.multi_cell(0, 8, line, align='L')
                        except:
                            # 유니코드 문제가 있으면 ASCII만 출력
                            ascii_line = line.encode('ascii', 'ignore').decode('ascii')
                            pdf.multi_cell(0, 8, ascii_line, align='L')
                    pdf.ln(2)
            
            pdf.output(output_path)
            self.logger.info(f"PDF 파일 저장 완료: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"PDF 파일 저장 실패 (FPDF): {e}")
            return False
    
    def save_as_pdf_reportlab(
        self, 
        ocr_results: Dict[int, Dict[str, str]], 
        output_path: str,
        include_page_numbers: bool = True
    ) -> bool:
        """
        ReportLab을 사용하여 OCR 결과를 PDF 파일로 저장
        
        Args:
            ocr_results: OCR 결과 딕셔너리
            output_path: 출력 파일 경로
            include_page_numbers: 페이지 번호 포함 여부
            
        Returns:
            저장 성공 여부
        """
        try:
            self.logger.info(f"PDF 파일 저장 시작 (ReportLab): {output_path}")
            
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet()
            
            # 한글 스타일 설정
            if self.korean_font:
                korean_style = ParagraphStyle(
                    'Korean',
                    parent=styles['Normal'],
                    fontName=self.korean_font,
                    fontSize=10,
                    leading=14,
                    spaceAfter=6
                )
                title_style = ParagraphStyle(
                    'KoreanTitle',
                    parent=styles['Heading1'],
                    fontName=self.korean_font,
                    fontSize=14,
                    leading=18,
                    spaceAfter=12,
                    alignment=1  # 중앙 정렬
                )
            else:
                korean_style = styles['Normal']
                title_style = styles['Heading1']
            
            story = []
            
            # 문서 제목
            story.append(Paragraph("PDF OCR 결과", title_style))
            story.append(Spacer(1, 12))
            
            # 페이지별 처리
            for i in sorted(ocr_results.keys()):
                result = ocr_results[i]
                
                if include_page_numbers:
                    story.append(Paragraph(f"페이지 {result['page']}", title_style))
                    story.append(Spacer(1, 8))
                
                # 텍스트 내용 처리
                text_content = result['text'] if result.get('status') == 'success' else f"[오류] {result['text']}"
                
                # HTML 특수문자 이스케이프
                text_content = text_content.replace('&', '&amp;')
                text_content = text_content.replace('<', '&lt;')
                text_content = text_content.replace('>', '&gt;')
                
                # 줄바꿈을 <br/>로 변환
                text_content = text_content.replace('\n', '<br/>')
                
                story.append(Paragraph(text_content, korean_style))
                story.append(Spacer(1, 20))
            
            doc.build(story)
            self.logger.info(f"PDF 파일 저장 완료: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"PDF 파일 저장 실패 (ReportLab): {e}")
            return False