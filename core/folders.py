def pick_folder(initial_dir: str | None = None) -> str | None:
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        kwargs = {}
        if initial_dir:
            kwargs["initialdir"] = initial_dir
        return filedialog.askdirectory(**kwargs) or None
    finally:
        root.destroy()
