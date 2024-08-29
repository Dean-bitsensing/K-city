## 코드 구조 설명

### main.py
- 프로그램의 진입점. 어플리케이션을 초기화하고 메인 윈도우 실행

### app/
- 애플리케이션의 주요 코드 위치
- controllers/:
    - main_controller.py : 애플리케이션의 메인 컨트롤러. 모델과 뷰 사이의 중개 역할

- models/:
    - data_model.py : 어플리케이션의 데이터 모델 정의

- viewers/:
    - main_viewer.py : 메인 윈도우와 관련된 뷰 정의

- resources/:
    - icons/ : 아이콘, 이미지 등 리소스 파일 포함.

### config/
- 애플리케이션의 설정 파일 위치
- settings.py : 설정과 관련된 변수 정의

### tests/
- 테스트 코드 포함됨
- test_models.py : 모델 테스트 코드
- test_viewers.py : 뷰어 테스트 코드
- test_controllers.py : 컨트롤러 테스트 코드
