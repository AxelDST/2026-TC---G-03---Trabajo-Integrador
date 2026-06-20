"""
main.py — Punto de entrada del Mini IDE Javaguayo.

Uso:
    python main.py
"""
import tkinter as tk
from ide.app import JavaguayoIDE


def main() -> None:
    root = tk.Tk()
    root.withdraw()  # Ocultar mientras carga

    # DPI awareness en Windows (pantallas HiDPI)
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = JavaguayoIDE(root)
    root.deiconify()  # Mostrar ventana ya construida
    root.mainloop()


if __name__ == "__main__":
    main()
