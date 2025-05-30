"""
Claude OCR 모듈
Anthropic Claude API를 사용하여 이미지에서 텍스트를 추출하는 클래스
"""

import base64
import time
import logging
from typing import List, Dict, Optional, Callable
from pathlib import Path
import anthropic
from anthropic import Anthropic


class ClaudeOCR:
    """Claude API를 사용한 OCR 처리 클래스"""
    
    def __init__(self, api_key: str):
        """
        Claude OCR 초기화
        
        Args:
            api_key: Anthropic API 키
        """
        self.client = Anthropic(api_key=api_key)
        self.logger = logging.getLogger(__name__)
        
    def image_to_base64(self, image_path: str) -> str:
        """
        이미지 파일을 base64로 인코딩
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            base64 인코딩된 이미지 문자열
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            self.logger.error(f"이미지 인코딩 실패: {image_path}, 오류: {e}")
            raise
    
    def get_ocr_prompt(self, document_type: str = "general") -> str:
        """
        문서 유형에 따른 OCR 프롬프트 생성
        
        Args:
            document_type: 문서 유형 (general, table, handwritten, form)
            
        Returns:
            OCR 프롬프트 문자열
        """
        prompts = {
            "general": """이 이미지에 포함된 모든 텍스트를 정확히 추출해 주세요.
다음 사항을 지켜주세요:
- 원본의 줄바꿈과 단락 구조를 최대한 유지해 주세요
- 제목, 소제목 등의 계층구조를 보존해 주세요
- 특수문자나 기호도 정확히 포함해 주세요
- 표가 있다면 표 형태로 정리해 주세요
- 한글과 영어가 섞여 있어도 모두 정확히 추출해 주세요""",
            
            "table": """이 이미지의 표를 정확히 추출해 주세요.
- 행과 열 구조를 명확히 구분해 주세요
- 셀 병합이 있다면 표시해 주세요
- 숫자 데이터는 정확히 보존해 주세요
- 표의 헤더와 내용을 구분해 주세요""",
            
            "handwritten": """이 손글씨 문서의 텍스트를 추출해 주세요.
- 읽기 어려운 부분은 [불명확] 표시해 주세요
- 추정되는 단어는 [추정: 단어] 형태로 표시해 주세요
- 가능한 한 정확하게 읽어주세요""",
            
            "form": """이 양식/폼의 모든 텍스트를 추출해 주세요.
- 필드명과 입력된 값을 구분해 주세요
- 체크박스나 선택 항목의 상태도 표시해 주세요
- 양식의 구조를 유지해 주세요"""
        }
        return prompts.get(document_type, prompts["general"])
    
    def extract_text_from_image(self, image_path: str, document_type: str = "general") -> str:
        """
        이미지에서 텍스트 추출
        
        Args:
            image_path: 이미지 파일 경로
            document_type: 문서 유형
            
        Returns:
            추출된 텍스트
        """
        try:
            # 이미지를 base64로 인코딩
            base64_image = self.image_to_base64(image_path)
            
            # 파일 확장자에 따른 MIME 타입 결정
            file_extension = Path(image_path).suffix.lower()
            mime_type_map = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            mime_type = mime_type_map.get(file_extension, 'image/png')
            
            # Claude API 호출
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": base64_image,
                                },
                            },
                            {
                                "type": "text",
                                "text": self.get_ocr_prompt(document_type)
                            }
                        ],
                    }
                ],
            )
            
            # 응답에서 텍스트 추출
            if message.content and len(message.content) > 0:
                return message.content[0].text
            else:
                return "텍스트를 추출할 수 없습니다."
                
        except Exception as e:
            self.logger.error(f"OCR 처리 실패: {image_path}, 오류: {e}")
            return f"오류 발생: {str(e)}"
    
    def extract_text_batch(
        self, 
        image_paths: List[str], 
        document_type: str = "general",
        delay: float = 1.0,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[int, Dict[str, str]]:
        """
        여러 이미지에서 배치로 텍스트 추출
        
        Args:
            image_paths: 이미지 파일 경로 리스트
            document_type: 문서 유형
            delay: API 호출 간 지연 시간 (초)
            progress_callback: 진행률 콜백 함수
            
        Returns:
            {페이지번호: {"text": 텍스트, "status": 상태}} 형태의 딕셔너리
        """
        results = {}
        total = len(image_paths)
        
        self.logger.info(f"배치 OCR 시작: {total}개 이미지")
        
        for i, image_path in enumerate(image_paths):
            try:
                # 텍스트 추출
                text = self.extract_text_from_image(image_path, document_type)
                
                results[i] = {
                    'page': i + 1,
                    'text': text,
                    'status': 'success',
                    'image_path': image_path
                }
                
                self.logger.info(f"페이지 {i+1}/{total} 처리 완료")
                
                # 진행률 콜백 호출
                if progress_callback:
                    progress_callback(i + 1, total)
                
                # API 레이트 리미트을 위한 지연
                if i < total - 1:
                    time.sleep(delay)
                    
            except Exception as e:
                self.logger.error(f"페이지 {i+1} 처리 실패: {e}")
                results[i] = {
                    'page': i + 1,
                    'text': f"오류 발생: {str(e)}",
                    'status': 'error',
                    'image_path': image_path
                }
        
        self.logger.info(f"배치 OCR 완료: {len(results)}개 결과")
        return results
    
    def extract_with_retry(
        self, 
        image_path: str, 
        document_type: str = "general",
        max_retries: int = 3
    ) -> str:
        """
        재시도 로직이 포함된 텍스트 추출
        
        Args:
            image_path: 이미지 파일 경로
            document_type: 문서 유형
            max_retries: 최대 재시도 횟수
            
        Returns:
            추출된 텍스트
        """
        for attempt in range(max_retries):
            try:
                return self.extract_text_from_image(image_path, document_type)
            except Exception as e:
                if attempt == max_retries - 1:
                    self.logger.error(f"최대 재시도 횟수 초과: {image_path}")
                    raise e
                
                wait_time = 2 ** attempt  # 지수 백오프
                self.logger.warning(f"재시도 {attempt + 1}/{max_retries}, {wait_time}초 대기: {e}")
                time.sleep(wait_time)
