import tkinter as tk
from tkinter import messagebox

def create_window():
    # 메인 윈도우 생성
    root = tk.Tk()
    root.title("System Output")

    # 레이아웃 설정
    main_frame = tk.Frame(root)
    main_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

    # 텍스트 위젯
    text = tk.Text(main_frame, height=10, wrap=tk.WORD)
    text.config(state=tk.NORMAL)
    text.insert(tk.END, "If you want to save changes, press a button below.\n")
    text.config(state=tk.DISABLED)
    text.pack(fill=tk.BOTH, expand=True)

    # 버튼 클릭 시 호출되는 함수
    def on_save_and_quit():
        text.config(state=tk.NORMAL)
        text.insert(tk.END, "Successfully Saved Changes!\n")
        text.config(state=tk.DISABLED)
        root.result = True
        root.quit()

    def on_dont_save_and_quit():
        text.config(state=tk.NORMAL)
        text.insert(tk.END, "Changes were not saved.\n")
        text.config(state=tk.DISABLED)
        root.result = False
        root.quit()

    # 버튼 프레임 생성
    button_frame = tk.Frame(main_frame)
    button_frame.pack(pady=10)

    # Save and Quit 버튼 생성 및 배치
    save_button = tk.Button(button_frame, text="Save and Quit", command=on_save_and_quit)
    save_button.pack(side=tk.LEFT, padx=5)

    # Don't Save and Quit 버튼 생성 및 배치
    dont_save_button = tk.Button(button_frame, text="Don't Save and Quit", command=on_dont_save_and_quit)
    dont_save_button.pack(side=tk.LEFT, padx=5)

    # 창 크기 조정
    root.geometry("400x300")

    # 창을 화면에 표시
    root.mainloop()

    # 결과 반환
    return root.result if hasattr(root, 'result') else None