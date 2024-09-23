import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton

def create_window():
    app = QApplication(sys.argv)

    # 메인 윈도우 생성
    window = QWidget()
    window.setWindowTitle("System Output")
    
    # 레이아웃 설정
    layout = QVBoxLayout()
    window.setLayout(layout)
    
    # 텍스트 위젯
    text = QTextEdit()
    text.setReadOnly(True)  # 텍스트 편집 불가로 설정
    text.setFixedHeight(200)  # 텍스트 위젯의 높이 설정
    text.append("If you want to save changes, press a button below.\n")
    layout.addWidget(text)
    
    # 버튼 클릭 시 호출되는 함수
    def on_save_and_quit():
        text.append("Successfully Saved Changes!\n")
        window.close()
        window.result = True

    def on_dont_save_and_quit():
        text.append("Changes were not saved.\n")
        window.close()
        window.result = False
    
    # 버튼 레이아웃 생성
    button_layout = QHBoxLayout()

    # Save and Quit 버튼 생성 및 배치
    save_button = QPushButton("Save and Quit")
    save_button.clicked.connect(on_save_and_quit)
    button_layout.addWidget(save_button)

    # Don't Save and Quit 버튼 생성 및 배치
    dont_save_button = QPushButton("Don't Save and Quit")
    dont_save_button.clicked.connect(on_dont_save_and_quit)
    button_layout.addWidget(dont_save_button)

    # 버튼 레이아웃을 메인 레이아웃에 추가
    layout.addLayout(button_layout)
    
    # 창 크기 조정
    window.setGeometry(100, 100, 400, 300)
    
    # 창을 화면에 표시
    window.show()
    
    # 이벤트 루프 시작
    app.exec_()
    
    # 결과 반환
    return window.result if hasattr(window, 'result') else None
