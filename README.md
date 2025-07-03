# 광고 라이브러리 스크래퍼

페이스북 광고 라이브러리에서 광고 데이터를 수집하는 다중 플랫폼 스크래퍼입니다. 모듈화된 구조로 설계되어 향후 구글, 틱톡 등 다른 플랫폼으로 확장 가능합니다.

## 주요 기능

- 페이스북 광고 라이브러리 스크래핑
- 키워드 또는 특정 페이지 기반 검색
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
# 키워드로 검색 (한국)
python main.py --country KR --search-terms "무신사"

# 특정 페이지의 모든 광고 검색
python main.py --country KR --page-id "119546338123785"

# 최대 광고 수 제한
python main.py --country KR --search-terms "패션" --max-ads 50

# 헤드리스 모드 비활성화 (브라우저 창 표시)
python main.py --country KR --search-terms "브랜드" --no-headless
```

### 옵션 설명

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--platform` | 플랫폼 선택 (facebook, google, tiktok) | facebook |
| `--country` | 국가 코드 (KR, US, JP 등) | US |
| `--search-terms` | 검색 키워드 | - |
| `--page-id` | 특정 페이지 ID | - |
| `--media-type` | 미디어 타입 (all, image, video, text) | all |
| `--active-status` | 광고 상태 (all, active, inactive) | active |
| `--max-ads` | 최대 수집 광고 수 | 100 |
| `--headless` | 헤드리스 모드 활성화 | True |
| `--no-headless` | 헤드리스 모드 비활성화 | - |
| `--timeout` | 페이지 로드 대기 시간 (초) | 30 |
| `--output-dir` | 출력 디렉토리 | output |
| `--output-file` | CSV 파일명 | ad_data.csv |
| `--no-archive` | HTML 아카이브 저장 비활성화 | False |
| `--debug` | 디버그 로깅 활성화 | False |

### 사용 예시

#### 1. 무신사 키워드 검색
```bash
python main.py --country KR --search-terms "무신사" --max-ads 20
```

#### 2. 특정 페이지의 모든 광고 수집
```bash
python main.py --country KR --page-id "119546338123785" --max-ads 50
```

#### 3. 디버그 모드로 실행
```bash
python main.py --country KR --search-terms "패션" --debug --no-headless
```

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
- 검색 키워드나 페이지 ID 확인
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
python main.py --debug --country KR --search-terms "테스트"
```

## 라이선스

이 프로젝트는 교육 및 연구 목적으로 제작되었습니다. 사용 시 관련 법규와 플랫폼 정책을 준수하시기 바랍니다.