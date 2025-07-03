프로젝트: 다중 플랫폼 광고 라이브러리 스크래퍼
1. 프로젝트 개요 (Overview)
본 프로젝트는 페이스북(Meta), 구글, 틱톡 등 주요 온라인 광고 플랫폼의 투명성 라이브러리에서 광고 데이터를 수집하는 자동화 스크래퍼를 개발하는 것을 목표로 한다.
초기 버전(MVP)은 페이스북 광고 라이브러리를 대상으로 하며, **셀레니움(Selenium)**을 사용하여 동적으로 로딩되는 웹 콘텐츠를 안정적으로 수집한다. 수집된 데이터는 CSV 파일로 저장하고, 데이터 수집의 근거를 남기기 위해 원본 페이지는 HTML 파일로 아카이빙한다.
프로젝트의 핵심은 확장성과 유지보수성이다. 각 플랫폼별 스크래퍼와 데이터 저장 로직을 모듈화하여, 향후 다른 광고 플랫폼을 추가하거나 데이터 저장 방식을 **구글 시트(Google Sheets)**로 변경하는 작업을 용이하게 설계해야 한다.
2. 핵심 요구사항 (Core Requirements)
기술 스택: Python, Selenium
스크래핑 대상:
1차 목표: 페이스북 광고 라이브러리
확장 목표: 구글 광고 투명성 센터, 틱톡 크리에이티브 센터 등
수집 데이터 명세:
Library ID: 광고 고유 ID
Started running on: 광고 시작일
Platforms: 광고 노출 플랫폼 (Facebook, Instagram 등)
Thumbnail Image URL: 목록 페이지의 대표 이미지 URL
Learn More Link: 광고 랜딩 페이지 URL
Multiple Versions Images: 'See ad details' 클릭 시 나타나는 모든 하위 버전의 이미지 URL 배열
데이터 출력:
수집된 모든 데이터는 CSV 파일로 저장한다.
데이터를 수집한 페이지의 전체 소스는 HTML 파일로 저장한다.
3. 아키텍처 및 설계 전략 (Architecture & Design)
가. 모듈화 설계
scrapers 모듈:
플랫폼별 스크래핑 로직을 별도의 클래스(FacebookScraper, GoogleScraper 등)로 분리한다.
모든 스크래퍼는 공통 인터페이스를 따르도록 추상 기본 클래스(ABC)를 활용할 수 있다.
storage 모듈:
데이터 저장 방식을 클래스(CsvStorage, GoogleSheetsStorage 등)로 분리한다.
이를 통해 main 코드 변경 없이 저장 방식을 교체할 수 있다.
config 모듈 / selectors.py:
스크래핑 대상 URL, 저장 경로, 그리고 가장 중요한 HTML 선택자(Selector) 등 변하기 쉬운 값들을 별도의 설정 파일로 분리하여 유지보수성을 극대화한다.
나. 견고한 선택자(Robust Selector) 전략
페이스북의 HTML 클래스 이름은 수시로 변경되므로, 이를 직접 사용하는 것을 엄격히 금지한다. 대신 아래와 같은 견고한 선택자 전략을 사용한다.
기능 기반 속성 우선 사용:
data-testid, data-pagelet 등 테스트용 ID를 최우선으로 사용한다.
role (예: role="button"), aria-label 등 웹 접근성 관련 속성을 차선으로 활용한다.
상대적 경로(XPath) 활용:
'Sponsored' 와 같이 내용이 잘 바뀌지 않는 텍스트를 포함한 요소를 기준점(Anchor)으로 삼는다.
ancestor::, following-sibling:: 등 XPath의 축(axis)을 사용하여 기준점으로부터 원하는 요소까지의 상대적 경로를 지정한다.
선택자 외부 파일 분리:
위 전략으로 찾은 XPath나 CSS Selector들을 모두 selectors.py 파일에 상수로 정의한다.
수정 사유: HTML 구조 변경 시, 코드 로직이 아닌 selectors.py 파일만 수정하면 되므로 대응이 매우 빨라진다.
4. 스크래핑 작업 흐름 (Scraping Workflow)
초기화: 설정 파일(config.py)에서 대상 URL과 선택자(selectors.py) 정보를 로드한다.
페이지 로드 및 스크롤:
셀레니움으로 타겟 URL에 접속한다.
페이지 맨 아래까지 반복적으로 스크롤하여 모든 광고 카드가 로딩되도록 한다.
광고 카드 순회:
페이지에 로드된 모든 광고 카드 컨테이너를 찾는다.
각 광고 카드를 순회하며 아래 작업을 반복한다.
1차 정보 수집 (메인 목록):
현재 카드 내에서 Library ID, Started running on, Platforms, Thumbnail Image URL, Learn More Link를 추출한다.
2차 정보 수집 (상세 보기):
카드 내의 'See ad details' 버튼을 클릭한다.
WebDriverWait를 사용해 상세 정보 팝업이 나타날 때까지 명시적으로 대기한다.
'This ad has multiple versions' 섹션을 찾아 그 안의 모든 이미지 URL을 리스트로 수집한다. (해당 섹션이 없는 경우를 대비해 try-except 처리)
데이터 저장 및 정리:
1, 2차 수집 데이터를 취합한다.
CsvStorage 모듈을 호출하여 데이터를 CSV에 추가한다.
상세 보기 팝업을 닫아 다음 카드 스크래핑을 준비한다.
종료: 모든 카드 순회가 끝나면, 수집된 전체 페이지 소스를 HTML 파일로 저장하고 브라우저를 종료한다.

