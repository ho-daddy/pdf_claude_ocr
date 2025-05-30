# 📄 PDF Claude OCR - Web App

Claude AI를 사용한 고품질 PDF 텍스트 추출 웹 서비스

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)

## ✨ 주요 기능

- 🤖 **Claude AI 기반** 고정확도 OCR
- 🌐 **웹 브라우저**에서 바로 사용
- 📱 **모바일 지원** 반응형 디자인
- 🔒 **보안 우선** 파일이 서버에 저장되지 않음
- 🌍 **다국어 지원** 한글, 영어, 중국어, 일본어 등
- 📊 **다양한 문서** 일반문서, 표, 손글씨, 양식 등

## 🚀 온라인 사용

웹사이트 접속: **[PDF Claude OCR](https://your-app-url.streamlit.app)**

1. Claude API 키 입력
2. PDF 파일 업로드
3. 옵션 선택 (문서 유형, 출력 형식)
4. 텍스트 추출 시작
5. 결과 다운로드

## 🔑 API 키 준비

1. [Anthropic Console](https://console.anthropic.com) 계정 생성
2. 결제 정보 등록 (최소 $5 크레딧)
3. API 키 발급
4. 웹앱에서 API 키 입력

## 💰 사용 비용

- **A4 페이지 1장**: 약 $0.01-0.03
- **100페이지 문서**: 약 $1-3
- **실시간 계산**: 처리 전 예상 비용 표시

## 🛡️ 개인정보 보호

- ✅ 업로드된 파일은 **서버에 저장되지 않음**
- ✅ 처리 완료 후 **임시 파일 자동 삭제**
- ✅ API 키는 **브라우저 세션에만 저장**
- ✅ **HTTPS 암호화** 통신

## 📱 지원 환경

- **브라우저**: Chrome, Firefox, Safari, Edge
- **기기**: Windows, Mac, Linux, iOS, Android
- **파일 크기**: 최대 200MB
- **페이지 수**: 제한 없음

## 🔧 로컬 실행 (개발자용)

```bash
git clone https://github.com/your-username/pdf-claude-ocr-web.git
cd pdf-claude-ocr-web
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 📋 지원 문서 유형

| 문서 유형 | 설명 | 정확도 |
|-----------|------|--------|
| 📄 일반 문서 | 일반적인 텍스트 문서 | ⭐⭐⭐⭐⭐ |
| 📊 표 문서 | 표가 많은 데이터 문서 | ⭐⭐⭐⭐⭐ |
| ✍️ 손글씨 | 필기체, 손글씨 문서 | ⭐⭐⭐⭐ |
| 📋 양식 | 폼, 설문지, 신청서 | ⭐⭐⭐⭐⭐ |

## 🌟 사용 예시

### 📚 학술 논문
- PDF 논문을 텍스트로 변환
- 인용문 추출
- 연구 노트 작성

### 📊 비즈니스 문서
- 계약서, 보고서 디지털화
- 데이터 분석을 위한 텍스트 추출
- 아카이브 구축

### 📝 개인 문서
- 스캔한 문서 텍스트화
- 오래된 문서 디지털 보관
- 검색 가능한 텍스트 변환

## ⚠️ 사용 시 주의사항

- 🌐 **인터넷 연결** 필수 (Claude API 사용)
- ⏱️ **처리 시간** 페이지당 10-30초 소요
- 💳 **API 비용** Claude API 사용료 발생
- 📄 **파일 형식** PDF 파일만 지원

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 📞 지원 및 문의

- 🐛 **버그 신고**: [Issues](https://github.com/your-username/pdf-claude-ocr-web/issues)
- 💡 **기능 제안**: [Discussions](https://github.com/your-username/pdf-claude-ocr-web/discussions)
- 📧 **이메일**: your-email@example.com

## 🏆 버전 히스토리

- **v1.0.0** - 초기 웹앱 릴리스
- Claude 3.5 Sonnet 지원
- Streamlit Cloud 배포 준비

---

⭐ **이 프로젝트가 유용하다면 Star를 눌러주세요!**