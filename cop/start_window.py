"""Start window for the operator: language and, only if data are saved, patient ID, session and folder."""

import ctypes
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, font, ttk

from cop import config, screen


def ask_start_settings() -> dict | None:
    # Returns None if the window is closed without starting
    # Same call as in screen.open_window: it must come before the first window, and this window comes first
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    root = tk.Tk()
    root.title("Center-out task")
    font.nametofont("TkDefaultFont").configure(size=config.START_WINDOW_FONT_SIZE)
    language = tk.StringVar(value=next(iter(screen.TEXTS)))
    save_data = tk.BooleanVar(value=False)
    patient_id = tk.StringVar()
    session = tk.StringVar()
    save_folder = tk.StringVar(value=str(config.SAVE_DIR))
    message = tk.StringVar()
    settings = {}

    # One column of rows; each row with more than one widget has its own frame
    main_frame = ttk.Frame(root, padding=20)
    main_frame.grid()
    language_frame = ttk.Frame(main_frame)
    language_frame.grid(row=0, column=0, sticky="w")
    ttk.Label(language_frame, text="Language / 语言").grid(row=0, column=0)
    for column, language_code in enumerate(screen.TEXTS, start=1):
        ttk.Radiobutton(language_frame, text=screen.TEXTS[language_code]["language_name"], variable=language,
                        value=language_code).grid(row=0, column=column, padx=(15, 0))

    # Fields shown only when the box is checked
    save_frame = ttk.Frame(main_frame)
    ttk.Label(save_frame, text="Patient ID (study code, not the name) / 患者编号（研究编号，不要用姓名）").grid(
        row=0, column=0, columnspan=2, sticky="w")
    ttk.Entry(save_frame, textvariable=patient_id, width=30).grid(row=1, column=0, sticky="w", pady=(0, 10))
    ttk.Label(save_frame, text="Session / 场次").grid(row=2, column=0, columnspan=2, sticky="w")
    ttk.Entry(save_frame, textvariable=session, width=30).grid(row=3, column=0, sticky="w", pady=(0, 10))
    ttk.Label(save_frame, text="Folder / 文件夹").grid(row=4, column=0, columnspan=2, sticky="w")
    ttk.Entry(save_frame, textvariable=save_folder, width=50).grid(row=5, column=0, sticky="we")

    def browse():
        chosen_folder = filedialog.askdirectory(initialdir=save_folder.get(), mustexist=False)
        if chosen_folder:
            save_folder.set(chosen_folder)

    ttk.Button(save_frame, text="Browse / 浏览", command=browse).grid(row=5, column=1, padx=(10, 0))

    def show_save_fields():
        if save_data.get():
            save_frame.grid(row=2, column=0, sticky="w", pady=(10, 0))
        else:
            save_frame.grid_remove()

    ttk.Checkbutton(main_frame, text="Save data / 保存数据", variable=save_data, command=show_save_fields).grid(
        row=1, column=0, sticky="w", pady=(15, 0))

    def start():
        if save_data.get():
            names = [patient_id.get(), session.get()]
            names_ok = all(
                0 < len(name) <= config.NAME_MAX_LENGTH and all(character in config.NAME_CHARACTERS for character in name)
                for name in names
            )
            if not names_ok:
                message.set(f"Patient ID and session: 1 to {config.NAME_MAX_LENGTH} letters, digits, _ or -\n"
                            f"患者编号和场次：1 到 {config.NAME_MAX_LENGTH} 个字母、数字、_ 或 -")
                return
            try:
                Path(save_folder.get()).mkdir(parents=True, exist_ok=True)
            except OSError:
                message.set("The folder cannot be created / 无法创建文件夹")
                return
        settings.update(language=language.get(), save_data=save_data.get(), patient_id=patient_id.get(),
                        session=session.get(), save_folder=Path(save_folder.get()))
        root.destroy()

    ttk.Label(main_frame, textvariable=message, foreground="red").grid(row=3, column=0, sticky="w", pady=(10, 0))
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=4, column=0, sticky="w", pady=(15, 0))
    ttk.Button(button_frame, text="Start / 开始", command=start).grid(row=0, column=0)
    ttk.Button(button_frame, text="Quit / 退出", command=root.destroy).grid(row=0, column=1, padx=(10, 0))
    root.bind("<Return>", lambda event: start())
    root.bind("<Escape>", lambda event: root.destroy())
    root.eval("tk::PlaceWindow . center")
    root.mainloop()
    return settings or None