"""
PDF 변환 모듈
PDF 파일을 이미지로 변환하는 기능을 제공
"""

import os
import tempfile
import logging
from typing import List, Optional, Callable
from pathlib import Path
from pdf2image import convert_from_path
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)
from PIL import Image, ImageEnhance


class PDFConverter:
    """PDF를 이미지로 변환하는 클래스"""
    
    def __init__(self):
        """PDF 변환기 초기화"""
        self.logger = logging.getLogger(__name__)
        
    def check_poppler_installation(self) -> bool:
        """
        Poppler 설치 여부 확인
        
        Returns:
            설치 여부 (True/False)
        """
        try:
            # pdf2image import 테스트
            from pdf2image import convert_from_path
            
            # 간단한 테스트로 poppler 설치 확인
            import subprocess
            
            # Windows에서는 pdftoppm, Linux에서는 pdftoppm 확인
            commands_to_try = ['pdftoppm', 'pdftocairo']
            
            for cmd in commands_to_try:
                try:
                    result = subprocess.run([cmd, '-h'], 
                                          capture_output=True, 
                                          text=True, 
                                          timeout=5)
                    if result.returncode == 0:
                        return True
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            return False
            
        except (ImportError, subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            self.logger.warning(f"Poppler 확인 실패: {e}")
            return False
    
    def get_pdf_page_count(self, pdf_path: str) -> int:
        """
        PDF 파일의 페이지 수 확인
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            페이지 수
        """
        try:
            from pdf2image import pdfinfo_from_path
            info = pdfinfo_from_path(pdf_path)
            return info.get('Pages', 0)
        except Exception as e:
            self.logger.warning(f"페이지 수 확인 실패: {e}")
            # 대안: 실제 변환해서 개수 확인
            try:
                images = convert_from_path(pdf_path, first_page=1, last_page=1)
                if images:
                    return len(convert_from_path(pdf_path))
                return 0
            except Exception:
                return 0
    
    def optimize_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """
        OCR을 위한 이미지 최적화
        
        Args:
            image: PIL 이미지 객체
            
        Returns:
            최적화된 이미지
        """
        try:
            # 이미지 크기가 너무 작으면 확대
            width, height = image.size
            if width < 1000 or height < 1000:
                scale_factor = max(1000 / width, 1000 / height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 컬러 이미지를 RGB로 변환 (RGBA에서 알파 채널 제거)
            if image.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    background.paste(image, mask=image.split()[-1])
                else:
                    background.paste(image, mask=image.split()[-1])
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 대비 향상
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            # 선명도 향상
            sharpness_enhancer = ImageEnhance.Sharpness(image)
            image = sharpness_enhancer.enhance(1.1)
            
            return image
            
        except Exception as e:
            self.logger.warning(f"이미지 최적화 실패: {e}")
            return image
    
    def convert_pdf_to_images(
        self,
        pdf_path: str,
        output_folder: Optional[str] = None,
        dpi: int = 300,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[str]:
        """
        PDF를 이미지 파일들로 변환
        
        Args:
            pdf_path: PDF 파일 경로
            output_folder: 출력 폴더 (None이면 임시 폴더 사용)
            dpi: 이미지 해상도 (기본값: 300)
            first_page: 시작 페이지 (1부터 시작)
            last_page: 끝 페이지
            progress_callback: 진행률 콜백 함수
            
        Returns:
            생성된 이미지 파일 경로 리스트
        """
        try:
            # Poppler 설치 확인
            if not self.check_poppler_installation():
                raise PDFInfoNotInstalledError(
                    "Poppler이 설치되지 않았습니다. 설치 가이드를 확인해주세요."
                )
            
            # 출력 폴더 설정
            if output_folder is None:
                output_folder = tempfile.mkdtemp()
            else:
                os.makedirs(output_folder, exist_ok=True)
            
            self.logger.info(f"PDF 변환 시작: {pdf_path}")
            self.logger.info(f"출력 폴더: {output_folder}")
            self.logger.info(f"DPI: {dpi}")
            
            # PDF를 이미지로 변환
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                first_page=first_page,
                last_page=last_page,
                fmt='PNG',
                thread_count=1,  # 안정성을 위해 단일 스레드 사용
                grayscale=False,  # 컬러 유지
                transparent=False  # 투명도 제거
            )
            
            image_paths = []
            total_pages = len(images)
            
            self.logger.info(f"총 {total_pages}페이지 변환 중...")
            
            for i, image in enumerate(images):
                try:
                    # 이미지 최적화
                    optimized_image = self.optimize_image_for_ocr(image)
                    
                    # 파일명 생성
                    page_num = (first_page or 1) + i
                    image_filename = f"page_{page_num:04d}.png"
                    image_path = os.path.join(output_folder, image_filename)
                    
                    # 이미지 저장
                    optimized_image.save(image_path, 'PNG', optimize=False)
                    image_paths.append(image_path)
                    
                    self.logger.debug(f"페이지 {page_num} 저장 완료: {image_path}")
                    
                    # 진행률 콜백 호출
                    if progress_callback:
                        progress_callback(i + 1, total_pages)
                        
                except Exception as e:
                    self.logger.error(f"페이지 {page_num} 저장 실패: {e}")
                    continue
            
            self.logger.info(f"PDF 변환 완료: {len(image_paths)}개 이미지 생성")
            return image_paths
            
        except PDFInfoNotInstalledError:
            raise
        except PDFSyntaxError as e:
            self.logger.error(f"PDF 파일 구문 오류: {e}")
            raise ValueError(f"PDF 파일이 손상되었거나 올바르지 않습니다: {e}")
        except Exception as e:
            self.logger.error(f"PDF 변환 실패: {e}")
            raise
    
    def convert_single_page(self, pdf_path: str, page_number: int, output_path: str, dpi: int = 300) -> str:
        """
        PDF의 특정 페이지 하나만 이미지로 변환
        
        Args:
            pdf_path: PDF 파일 경로
            page_number: 페이지 번호 (1부터 시작)
            output_path: 출력 이미지 파일 경로
            dpi: 이미지 해상도
            
        Returns:
            생성된 이미지 파일 경로
        """
        try:
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                first_page=page_number,
                last_page=page_number
            )
            
            if images:
                optimized_image = self.optimize_image_for_ocr(images[0])
                optimized_image.save(output_path, 'PNG')
                return output_path
            else:
                raise ValueError(f"페이지 {page_number}를 변환할 수 없습니다")
                
        except Exception as e:
            self.logger.error(f"단일 페이지 변환 실패: {e}")
            raise
    
    def cleanup_temp_files(self, image_paths: List[str]) -> None:
        """
        임시 이미지 파일들 정리
        
        Args:
            image_paths: 삭제할 이미지 파일 경로 리스트
        """
        for image_path in image_paths:
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
                    self.logger.debug(f"임시 파일 삭제: {image_path}")
            except Exception as e:
                self.logger.warning(f"임시 파일 삭제 실패: {image_path}, 오류: {e}")
    
    def get_installation_guide(self) -> str:
        """
        Poppler 설치 가이드 반환
        
        Returns:
            설치 가이드 문자열
        """
        return """
Poppler 설치 가이드:

[Windows]
1. https://poppler.freedesktop.org/에서 Windows용 바이너리 다운로드
2. 압축 해제 후 bin 폴더를 PATH에 추가

[macOS]
brew install poppler

[Ubuntu/Debian]
sudo apt-get install poppler-utils

[CentOS/RHEL]
sudo yum install poppler-utils

[Arch Linux]
sudo pacman -S poppler
"""