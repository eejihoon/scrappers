# 광고 라이브러리 스크래퍼

페이스북 광고 라이브러리에서 광고 데이터를 수집하는 다중 플랫폼 스크래퍼입니다. 모듈화된 구조로 설계되어 향후 구글, 틱톡 등 다른 플랫폼으로 확장 가능합니다.

## 프로젝트 이해하기

### 빠른 시작 (5분)
1. **설치 및 실행**: [설치 및 설정](#설치-및-설정) → [기본 사용법](#기본-사용법)
2. **첫 실행**: `python main.py --page-id 119546338123785 --country KR --max-ads 5`
3. **결과 확인**: `output/csv_files/ad_data.csv` 파일 열기

### 코드 구조 이해하기 (15분)

#### 1단계: 진입점 파악
- **`main.py`**: 전체 프로그램의 시작점, 명령행 인자 처리 및 워크플로우 조정
- **`config.py`**: 모든 설정값 관리 (URL, 타임아웃, 경로 등)

#### 2단계: 핵심 로직 이해
- **`scrapers/base.py`**: 모든 스크래퍼의 공통 기능 (Selenium 설정, 스크롤링, 오류 처리)
- **`scrapers/facebook_scraper.py`**: 페이스북 특화 스크래핑 로직 (광고 카드 찾기, 데이터 추출)

#### 3단계: 데이터 처리 흐름
- **`ad_selectors.py`**: CSS/XPath 선택자 정의 (UI 변경에 대응하는 견고한 선택자)
- **`storage/csv_storage.py`**: 수집된 데이터를 CSV로 저장하는 로직

### 심화 이해 (30분)

#### 아키텍처 패턴
```
사용자 입력 (main.py) 
    ↓
스크래퍼 선택 및 초기화 (base.py)
    ↓
페이지 네비게이션 및 요소 탐색 (facebook_scraper.py + ad_selectors.py)
    ↓
데이터 추출 및 검증 (facebook_scraper.py)
    ↓
저장소에 데이터 저장 (csv_storage.py)
```

#### 핵심 설계 원칙
1. **모듈화**: 각 플랫폼별로 독립적인 스크래퍼 클래스
2. **확장성**: 새로운 플랫폼 추가 시 기존 코드 수정 최소화
3. **견고성**: UI 변경에 대응하는 다층 선택자 전략
4. **안정성**: 중복 제거, 오류 처리, 재시도 메커니즘

### 개발자를 위한 가이드

#### 새로운 플랫폼 추가하기
1. `ad_selectors.py`에 새 플랫폼 선택자 클래스 추가
2. `scrapers/` 디렉토리에 새 스크래퍼 클래스 생성 (`base.py` 상속)
3. `config.py`에 플랫폼별 설정 추가
4. `main.py`의 플랫폼 매핑에 추가

#### 선택자 전략 이해하기
```python
# 나쁜 예: CSS 클래스명 의존 (자주 변경됨)
".ad-card-container"

# 좋은 예: 텍스트 기반 검색 (변경 적음)
"//div[contains(., '라이브러리 ID:')]"
```

#### 데이터 추출 로직
1. **컨테이너 찾기**: 광고 카드 전체 영역 식별
2. **정보 추출**: 각 필드별 정규식 패턴 매칭
3. **데이터 정제**: 공백 제거, 형식 통일
4. **중복 검사**: Library ID 기반 중복 제거

## 주요 기능

- 페이스북 광고 라이브러리 스크래핑
- 특정 페이지 ID 기반 광고 수집
- 광고 라이브러리 ID, 시작일, 플랫폼, 썸네일, 더보기 링크 추출
- CSV 형태로 데이터 저장
- HTML 아카이브 자동 저장
- 중복 제거 및 오류 처리
- 안티 탐지 기능 내장

## 설치 및 설정

### 필수 조건

- Python 3.8 이상
- Chrome 브라우저

### 패키지 설치

```bash
pip install -r requirements.txt
```

## 사용법

### 기본 사용법

```bash
# 기본 페이지 광고 수집
python main.py --page-id "119546338123785"

# 한국 페이지 광고 수집
python main.py --page-id "119546338123785" --country KR

# 최대 광고 수 제한
python main.py --page-id "119546338123785" --max-ads 50

# 헤드리스 모드 비활성화 (브라우저 창 표시)
python main.py --page-id "119546338123785" --no-headless
```

### 옵션 설명

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--page-id` | **필수** 페이스북 페이지 ID | - |
| `--platform` | 플랫폼 선택 (facebook, google, tiktok) | facebook |
| `--country` | 국가 코드 (KR, US, JP 등) | US |
| `--media-type` | 미디어 타입 (all, image, video, text) | all |
| `--active-status` | 광고 상태 (all, active, inactive) | active |
| `--max-ads` | 최대 수집 광고 수 | 무제한 |
| `--headless` | 헤드리스 모드 활성화 | True |
| `--no-headless` | 헤드리스 모드 비활성화 | - |
| `--timeout` | 페이지 로드 대기 시간 (초) | 30 |
| `--output-dir` | 출력 디렉토리 | output |
| `--output-file` | CSV 파일명 | ad_data.csv |
| `--no-archive` | HTML 아카이브 저장 비활성화 | False |
| `--debug` | 디버그 로깅 활성화 | False |

### 사용 예시

#### 1. 무신사 페이지 광고 수집
```bash
python main.py --page-id "119546338123785" --country KR --max-ads 20
```

#### 2. 미국 페이지 광고 수집
```bash
python main.py --page-id "123456789" --country US --max-ads 50
```

#### 3. 디버그 모드로 실행
```bash
python main.py --page-id "119546338123785" --debug --no-headless
```

### 페이지 ID 찾는 방법

페이스북 페이지의 Page ID를 찾으려면:
1. 페이스북 페이지에 접속
2. 페이지 소스 보기 (Ctrl+U)
3. "page_id" 검색하여 숫자 확인
4. 또는 페이스북 개발자 도구나 외부 도구 사용

## 출력 데이터

### CSV 파일 구조

| 컬럼 | 설명 | 예시 |
|------|------|------|
| library_id | 광고 라이브러리 ID | 1477742293401772 |
| start_date | 광고 시작일 | 2025. 7. 3.에 게재 시작함 |
| platforms | 게재 플랫폼 | ["Instagram", "Facebook"] |
| thumbnail_url | 썸네일 이미지 URL | https://scontent-icn2-1.xx.fbcdn.net/... |
| learn_more_url | 더보기 링크 URL | https://l.facebook.com/l.php?u=... |
| multiple_versions_images | 다중 버전 이미지 URL 목록 | [] |
| scraped_at | 수집 시간 | 2025-07-03T21:27:55.471838 |
| platform | 플랫폼명 | facebook |
| additional_data | 추가 데이터 | {} |

### 파일 저장 위치

```
output/
├── csv_files/
│   ├── ad_data.csv          # 광고 데이터
│   └── html_archives/       # HTML 아카이브
└── logs/
    └── scraper.log          # 로그 파일
```

## 프로젝트 구조

```
ads/
├── main.py                  # 메인 실행 파일
├── config.py               # 설정 관리
├── ad_selectors.py         # CSS/XPath 선택자
├── scrapers/               # 스크래퍼 모듈
│   ├── __init__.py
│   ├── base.py            # 기본 스크래퍼 클래스
│   └── facebook_scraper.py # 페이스북 스크래퍼
├── storage/                # 저장소 모듈
│   ├── __init__.py
│   ├── base.py            # 기본 저장소 클래스
│   └── csv_storage.py     # CSV 저장소
├── requirements.txt        # 필수 패키지
└── README.md              # 사용법 안내
```

## 주의사항

### 속도 제한
- 페이스북 광고 라이브러리는 요청 속도를 제한합니다
- 과도한 요청 시 일시적으로 접근이 차단될 수 있습니다
- 적절한 지연시간을 두고 사용하는 것을 권장합니다

### 법적 고지
- 이 도구는 공개된 페이스북 광고 라이브러리 데이터만 수집합니다
- 수집된 데이터의 사용은 관련 법규와 플랫폼 정책을 준수해야 합니다
- 상업적 사용 시 해당 플랫폼의 이용약관을 확인하시기 바랍니다

### 기술적 제한
- 페이스북의 UI 변경 시 일부 기능이 작동하지 않을 수 있습니다
- Chrome 브라우저와 ChromeDriver가 필요합니다
- 네트워크 환경에 따라 성능이 달라질 수 있습니다

## 문제 해결

### 일반적인 오류

#### ChromeDriver 오류
```bash
# ChromeDriver 자동 다운로드되지 않는 경우
# Chrome 버전 확인 후 수동 설치 필요
```

#### 광고를 찾을 수 없는 경우
- 페이지 ID가 올바른지 확인
- 해당 페이지에 광고가 실제로 있는지 확인
- 국가 설정 확인
- 네트워크 연결 상태 확인

#### CSV 파일이 생성되지 않는 경우
- 출력 디렉토리 권한 확인
- 디스크 용량 확인
- `--debug` 옵션으로 자세한 로그 확인

### 로그 확인
```bash
# 실행 로그 확인
tail -f scraper.log

# 디버그 모드로 상세 로그 출력
python main.py --page-id "119546338123785" --debug
```

## 라이선스

이 프로젝트는 교육 및 연구 목적으로 제작되었습니다. 사용 시 관련 법규와 플랫폼 정책을 준수하시기 바랍니다.