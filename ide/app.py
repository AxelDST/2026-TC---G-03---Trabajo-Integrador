"""
app.py — Ventana principal del Mini IDE Javaguayo.

Integra el editor de código y el panel de resultados,
gestiona archivos .jvg, ejecuta el análisis y muestra
el estado en tiempo real.
"""
from __future__ import annotations

import re
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from . import analyzer as java_analyzer
from . import theme
from .editor import CodeEditor
from .results_panel import ResultsPanel

# ── Rutas ─────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent.parent
EJEMPLOS_DIR = BASE_DIR / "ejemplos"

# ── Catálogo de ejemplos ──────────────────────────────────────────
EJEMPLOS: list[tuple[str, str]] = [
    ("✅  Correcto 01 — Calculadora",            "correcto_01.jvg"),
    ("✅  Correcto 02 — Contador (mientras)",    "correcto_02.jvg"),
    ("✅  Correcto 03 — Instanciación de clase", "correcto_03.jvg"),
    ("❌  Error Léxico 01 — Símbolo @ inválido", "error_lexico_01.jvg"),
    ("❌  Error Léxico 02",                       "error_lexico_02.jvg"),
    ("❌  Error Léxico 03",                       "error_lexico_03.jvg"),
    ("⚠️   Error Sintáctico 01 — Falta ;",        "error_sintactico_01.jvg"),
    ("⚠️   Error Sintáctico 02",                  "error_sintactico_02.jvg"),
    ("⚠️   Error Sintáctico 03",                  "error_sintactico_03.jvg"),
]

# Accesos rápidos para la barra de herramientas
QUICK_EXAMPLES: list[tuple[str, str, str]] = [
    ("✅ C1", "correcto_01.jvg",         theme.ACCENT_GREEN),
    ("✅ C2", "correcto_02.jvg",         theme.ACCENT_GREEN),
    ("✅ C3", "correcto_03.jvg",         theme.ACCENT_GREEN),
    ("❌ L1", "error_lexico_01.jvg",    theme.ACCENT_RED),
    ("❌ L2", "error_lexico_02.jvg",    theme.ACCENT_RED),
    ("❌ L3", "error_lexico_03.jvg",    theme.ACCENT_RED),
    ("⚠ S1", "error_sintactico_01.jvg", theme.ACCENT_YELLOW),
    ("⚠ S2", "error_sintactico_02.jvg", theme.ACCENT_YELLOW),
    ("⚠ S3", "error_sintactico_03.jvg", theme.ACCENT_YELLOW),
]

# Frames del spinner para el status bar
_SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class JavaguayoIDE:
    """Ventana principal del Mini IDE Javaguayo."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self._current_file: Optional[Path] = None
        self._last_saved_content: str = ""   # rastrea cambios sin guardar
        self._is_analyzing  = False
        self._spinner_job:  Optional[str] = None
        self._spinner_idx   = 0

        self._setup_window()
        theme.setup_styles(root)
        self._build_ui()
        self._check_environment()

    # ── Configuración de la ventana ───────────────────────────────
    def _setup_window(self) -> None:
        self.root.title("Javaguayo IDE")
        self.root.geometry("1380x820")
        self.root.minsize(980, 620)
        self.root.configure(bg=theme.BG_MAIN)

    # ── Construcción de la UI ─────────────────────────────────────
    def _build_ui(self) -> None:
        self._build_header()
        self._build_menu()
        self._build_toolbar()
        self._build_main_panel()
        self._build_statusbar()

    def _build_header(self) -> None:
        bar = tk.Frame(self.root, bg=theme.BG_PANEL, height=44)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Logo + título
        tk.Label(
            bar,
            text="⬡",
            bg=theme.BG_PANEL, fg=theme.ACCENT_BLUE,
            font=("Segoe UI", 16, "bold"),
        ).pack(side="left", padx=(14, 4), pady=8)

        tk.Label(
            bar,
            text="Javaguayo IDE",
            bg=theme.BG_PANEL, fg=theme.TEXT_PRIMARY,
            font=("Segoe UI", 12, "bold"),
        ).pack(side="left", pady=8)

        tk.Label(
            bar,
            text="  —  Analizador Léxico & Sintáctico  |  FCEQyN · UNaM  |  Grupo 03",
            bg=theme.BG_PANEL, fg=theme.TEXT_MUTED,
            font=theme.FONT_SMALL,
        ).pack(side="left", pady=8)

        # Nombre del archivo actual
        self._file_lbl = tk.Label(
            bar, text="Sin archivo",
            bg=theme.BG_PANEL, fg=theme.TEXT_SECONDARY,
            font=theme.FONT_SMALL,
        )
        self._file_lbl.pack(side="right", padx=16)

        # Separador inferior
        tk.Frame(self.root, height=1, bg=theme.BORDER).pack(fill="x")

    def _build_menu(self) -> None:
        menu = tk.Menu(
            self.root,
            bg=theme.BG_WIDGET, fg=theme.TEXT_PRIMARY,
            activebackground=theme.BG_SELECTED,
            activeforeground=theme.TEXT_PRIMARY,
            relief="flat", bd=0,
        )
        self.root.config(menu=menu)

        kw = dict(
            tearoff=0,
            bg=theme.BG_WIDGET, fg=theme.TEXT_PRIMARY,
            activebackground=theme.BG_SELECTED,
            activeforeground=theme.TEXT_PRIMARY,
        )

        # ── Archivo ──
        m_file = tk.Menu(menu, **kw)
        menu.add_cascade(label="Archivo", menu=m_file)
        m_file.add_command(label="  📄  Nuevo              Ctrl+N",  command=self._new_file)
        m_file.add_command(label="  📂  Abrir...           Ctrl+O",  command=self._open_file)
        m_file.add_command(label="  💾  Guardar            Ctrl+S",  command=self._save_file)
        m_file.add_command(label="  💾  Guardar como...",            command=self._save_as)
        m_file.add_separator()
        m_file.add_command(label="  🚪  Salir",                      command=self.root.quit)

        # ── Ejemplos ──
        m_ex = tk.Menu(menu, **kw)
        menu.add_cascade(label="Ejemplos", menu=m_ex)
        for name, fname in EJEMPLOS:
            m_ex.add_command(
                label=f"  {name}",
                command=lambda f=fname: self._load_example(f),
            )

        # ── Analizador ──
        m_an = tk.Menu(menu, **kw)
        menu.add_cascade(label="Analizador", menu=m_an)
        m_an.add_command(label="  ▶   Analizar (completo)      F5",  command=self._run_full)
        m_an.add_command(label="  🔤  Solo léxico               F6",  command=self._run_lexico)
        m_an.add_separator()
        m_an.add_command(label="  🔨  Recompilar analizador...",      command=self._recompile_dialog)
        m_an.add_command(label="  🔍  Verificar entorno",             command=self._check_environment_dialog)

        # Atajos de teclado
        self.root.bind("<Control-n>", lambda _: self._new_file())
        self.root.bind("<Control-o>", lambda _: self._open_file())
        self.root.bind("<Control-s>", lambda _: self._save_file())
        self.root.bind("<F5>",        lambda _: self._run_full())
        self.root.bind("<F6>",        lambda _: self._run_lexico())

    def _build_toolbar(self) -> None:
        tb = tk.Frame(self.root, bg=theme.BG_WIDGET, pady=5)
        tb.pack(fill="x")

        def btn(text, cmd, bg_color, *, side="left", padx=3):
            b = tk.Button(
                tb, text=text, command=cmd,
                bg=bg_color, fg="white",
                activebackground=bg_color,
                activeforeground="white",
                relief="flat", bd=0,
                padx=12, pady=6,
                font=theme.FONT_UI_BOLD,
                cursor="hand2",
            )
            b.pack(side=side, padx=padx, pady=2)
            lighter = self._lighten(bg_color)
            b.bind("<Enter>", lambda _, b=b, c=lighter:   b.config(bg=c))
            b.bind("<Leave>", lambda _, b=b, c=bg_color: b.config(bg=c))
            return b

        def sep():
            tk.Frame(tb, width=1, bg=theme.BORDER).pack(side="left", fill="y", padx=8, pady=2)

        tk.Frame(tb, width=6, bg=theme.BG_WIDGET).pack(side="left")

        btn("📂  Abrir",      self._open_file,   theme.BG_HOVER)
        btn("💾  Guardar",    self._save_file,   theme.BG_HOVER)
        btn("🔄  Nuevo",      self._new_file,    theme.BG_HOVER)
        sep()
        self._btn_analyze = btn("▶  Analizar",  self._run_full,   theme.ACCENT_GREEN)
        self._btn_lexico  = btn("🔤  Solo Léxico", self._run_lexico, theme.ACCENT_PURPLE)

        # Ejemplos rápidos
        sep()
        tk.Label(
            tb, text="Ejemplos rápidos:",
            bg=theme.BG_WIDGET, fg=theme.TEXT_SECONDARY,
            font=theme.FONT_SMALL,
        ).pack(side="left", padx=(0, 4))

        for label, fname, color in QUICK_EXAMPLES:
            b = tk.Button(
                tb, text=label,
                command=lambda f=fname: self._load_example(f),
                bg=theme.BG_PANEL, fg=color,
                activebackground=theme.BG_HOVER, activeforeground=color,
                relief="flat", bd=0, padx=8, pady=4,
                font=("Segoe UI", 9), cursor="hand2",
            )
            b.pack(side="left", padx=2, pady=2)

        tk.Frame(tb, width=6, bg=theme.BG_WIDGET).pack(side="right")
        tk.Frame(self.root, height=1, bg=theme.BORDER).pack(fill="x")

    def _build_main_panel(self) -> None:
        self._paned = tk.PanedWindow(
            self.root, orient="horizontal",
            bg=theme.BORDER, sashwidth=5,
            sashrelief="flat", bd=0,
        )
        self._paned.pack(fill="both", expand=True)

        # ── Editor (izquierda) ──
        left = tk.Frame(self._paned, bg=theme.BG_EDITOR)

        left_hdr = tk.Frame(left, bg=theme.BG_PANEL, height=28)
        left_hdr.pack(fill="x")
        left_hdr.pack_propagate(False)
        tk.Label(
            left_hdr,
            text="  📝  Editor  —  Javaguayo  (.jvg)",
            bg=theme.BG_PANEL, fg=theme.TEXT_SECONDARY,
            font=theme.FONT_SMALL, anchor="w",
        ).pack(fill="both", expand=True, padx=8)

        self.editor = CodeEditor(left)
        self.editor.pack(fill="both", expand=True)
        self._paned.add(left, minsize=420)

        # ── Panel de resultados (derecha) ──
        right = tk.Frame(self._paned, bg=theme.BG_PANEL)
        self.results = ResultsPanel(right, on_goto_line=self.editor.goto_line)
        self.results.pack(fill="both", expand=True)
        self._paned.add(right, minsize=400)

        # Posición inicial del separador
        self.root.after(150, lambda: self._paned.sash_place(0, 780, 0))

    def _build_statusbar(self) -> None:
        tk.Frame(self.root, height=1, bg=theme.BORDER).pack(fill="x", side="bottom")
        sb = tk.Frame(self.root, bg=theme.BG_PANEL, height=26)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)

        self._status_var = tk.StringVar(
            value="  ✨ Listo — Escribí código Javaguayo o cargá un ejemplo"
        )
        tk.Label(
            sb, textvariable=self._status_var,
            bg=theme.BG_PANEL, fg=theme.TEXT_SECONDARY,
            font=theme.FONT_SMALL, anchor="w",
        ).pack(side="left", padx=8, fill="y")

        # Indicador de estado (derecha)
        self._state_var = tk.StringVar(value="")
        self._state_lbl = tk.Label(
            sb, textvariable=self._state_var,
            bg=theme.BG_PANEL, fg=theme.ACCENT_BLUE,
            font=theme.FONT_SMALL,
        )
        self._state_lbl.pack(side="right", padx=8)

        # Posición del cursor
        self._cursor_var = tk.StringVar(value="Ln 1, Col 1")
        tk.Label(
            sb, textvariable=self._cursor_var,
            bg=theme.BG_PANEL, fg=theme.TEXT_MUTED,
            font=theme.FONT_SMALL,
        ).pack(side="right", padx=12)

        # Bind cursor
        self.editor.text.bind("<KeyRelease>",    self._update_cursor, "+")
        self.editor.text.bind("<ButtonRelease>", self._update_cursor, "+")

    # ── Helpers ───────────────────────────────────────────────────
    @staticmethod
    def _lighten(hex_color: str, factor: float = 1.25) -> str:
        hex_color = hex_color.lstrip("#")
        r = min(255, int(int(hex_color[0:2], 16) * factor))
        g = min(255, int(int(hex_color[2:4], 16) * factor))
        b = min(255, int(int(hex_color[4:6], 16) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _update_cursor(self, event=None) -> None:
        try:
            ln, col = self.editor.get_cursor_pos()
            self._cursor_var.set(f"Ln {ln}, Col {col}")
        except Exception:
            pass

    def _set_status(self, msg: str, color: str = theme.TEXT_SECONDARY) -> None:
        self._status_var.set(f"  {msg}")

    def _set_state(self, msg: str, color: str = theme.ACCENT_BLUE) -> None:
        self._state_var.set(msg)
        self._state_lbl.config(fg=color)

    def _start_spinner(self) -> None:
        def tick():
            self._spinner_idx = (self._spinner_idx + 1) % len(_SPINNER)
            self._state_var.set(f"{_SPINNER[self._spinner_idx]}  Analizando...")
            self._spinner_job = self.root.after(80, tick)
        self._spinner_job = self.root.after(80, tick)

    def _stop_spinner(self) -> None:
        if self._spinner_job:
            self.root.after_cancel(self._spinner_job)
            self._spinner_job = None

    # ── Gestión de archivos ───────────────────────────────────────
    def _new_file(self) -> None:
        """Nuevo archivo: pide guardar si hay cambios sin guardar."""
        current = self.editor.get_code()
        if current != self._last_saved_content:
            # Hay cambios sin guardar
            if self._current_file:
                prompt = f"'{self._current_file.name}' tiene cambios sin guardar.\n¿Desea guardar antes de continuar?"
            else:
                prompt = "Hay código sin guardar en el editor.\n¿Desea guardarlo antes de continuar?"
            answer = messagebox.askyesnocancel("Cambios sin guardar", prompt)
            if answer is None:        # Cancelar → no hacer nada
                return
            if answer:                # Sí → guardar
                self._save_file()
        # Limpiar
        self._current_file = None
        self._last_saved_content = ""
        self._file_lbl.config(text="Sin archivo")
        self.editor.set_code("")
        self.results.clear()
        self._set_status("📄 Editor listo — escribí código Javaguayo")
        self._set_state("")

    def _open_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Abrir archivo Javaguayo",
            filetypes=[("Javaguayo", "*.jvg"), ("Todos", "*.*")],
            initialdir=str(EJEMPLOS_DIR),
        )
        if path:
            self._load_path(Path(path))

    def _save_file(self) -> None:
        if self._current_file:
            self._write_file(self._current_file)
        else:
            self._save_as()

    def _save_as(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Guardar archivo",
            defaultextension=".jvg",
            filetypes=[("Javaguayo", "*.jvg"), ("Todos", "*.*")],
        )
        if path:
            self._current_file = Path(path)
            self._write_file(self._current_file)

    def _write_file(self, path: Path) -> None:
        try:
            code = self.editor.get_code()
            path.write_text(code, encoding="utf-8")
            self._last_saved_content = code
            self._file_lbl.config(text=f"  💾 {path.name}")
            self._set_status(f"💾 Guardado: {path.name}")
        except OSError as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

    def _load_path(self, path: Path) -> None:
        try:
            code = path.read_text(encoding="utf-8")
            self.editor.set_code(code)
            self._current_file = path
            self._last_saved_content = code
            self._file_lbl.config(text=f"  📄 {path.name}")
            self._set_status(f"📂 Cargado: {path.name}")
            self.results.clear()
            self._set_state("")
        except OSError as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{e}")

    def _load_example(self, filename: str) -> None:
        path = EJEMPLOS_DIR / filename
        if path.exists():
            self._load_path(path)
        else:
            messagebox.showerror("Error", f"No se encontró el ejemplo:\n{path}")

    # _load_template() eliminado — el editor inicia vacío

    # ── Análisis ──────────────────────────────────────────────────
    def _run_full(self) -> None:
        if not self._is_analyzing:
            self._do_analysis(lexico_only=False)

    def _run_lexico(self) -> None:
        if not self._is_analyzing:
            self._do_analysis(lexico_only=True)

    def _do_analysis(self, lexico_only: bool) -> None:
        code = self.editor.get_code().strip()
        if not code:
            messagebox.showwarning("Editor vacío",
                                   "El editor no tiene código. Escribí algo o cargá un ejemplo.")
            return

        self._is_analyzing = True
        self._btn_analyze.config(state="disabled", text="⏳  Analizando...")
        self._btn_lexico.config(state="disabled")
        self.editor.clear_error_marks()
        self.results.clear()

        mode = "Solo Léxico" if lexico_only else "Léxico + Sintáctico"
        self._set_status(f"⚙️ Ejecutando análisis {mode}...")
        self._start_spinner()

        def worker():
            try:
                result = java_analyzer.analyze_code(code, lexico_only=lexico_only)
                self.root.after(0, lambda: self._on_done(result, mode, lexico_only))
            except Exception as exc:
                self.root.after(0, lambda: self._on_error(str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_done(self, result, mode: str, lexico_only: bool = False) -> None:
        self._is_analyzing = False
        self._stop_spinner()
        self._btn_analyze.config(state="normal", text="▶  Analizar")
        self._btn_lexico.config(state="normal")

        # Mostrar resultados
        self.results.update_results(result, mode, lexico_only=lexico_only)

        # Marcar líneas con error en el editor
        lex_lines  = self._extract_lines(result.lex_errors)
        sint_lines = self._extract_lines(result.sint_errors)
        self.editor.mark_error_lines(lex_lines, sint_lines)

        # Actualizar barra de estado
        if result.is_ok:
            self._set_state(f"✅ OK — {result.total_tokens} tokens",
                            theme.ACCENT_GREEN)
            self._set_status(
                f"✅ Análisis correcto — {result.total_tokens} tokens "
                f"en {result.elapsed:.3f}s"
            )
        else:
            n_lex  = len(result.lex_errors)
            n_sint = len(result.sint_errors)
            parts = []
            if n_lex:  parts.append(f"{n_lex} err. léxico{'s' if n_lex>1 else ''}")
            if n_sint: parts.append(f"{n_sint} err. sintáctico{'s' if n_sint>1 else ''}")
            summary = " | ".join(parts)
            self._set_state(f"❌ {summary}", theme.ACCENT_RED)
            self._set_status(
                f"❌ {summary} — {result.total_tokens} tokens en {result.elapsed:.3f}s"
            )

        # Cambiar de pestaña automáticamente
        if result.lex_errors or result.sint_errors:
            self.results.select_tab(1)   # pestaña Errores
        else:
            self.results.select_tab(0)   # pestaña Tokens

    def _on_error(self, msg: str) -> None:
        self._is_analyzing = False
        self._stop_spinner()
        self._btn_analyze.config(state="normal", text="▶  Analizar")
        self._btn_lexico.config(state="normal")
        self._set_state("❗ Error", theme.ACCENT_RED)
        self._set_status("❗ Error al ejecutar el analizador")
        messagebox.showerror("Error del Analizador", msg)

    @staticmethod
    def _extract_lines(error_list: list[str]) -> list[int]:
        lines = []
        for err in error_list:
            m = re.search(r'l[ií]nea\s+(\d+)', err, re.IGNORECASE)
            if m:
                try:
                    lines.append(int(m.group(1)))
                except ValueError:
                    pass
        return lines

    # ── Diálogo de recompilación ───────────────────────────────────
    def _recompile_dialog(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("Recompilar Analizador — Javaguayo IDE")
        win.geometry("560x400")
        win.configure(bg=theme.BG_PANEL)
        win.transient(self.root)
        win.grab_set()
        win.resizable(True, True)

        tk.Label(
            win,
            text="🔨  Recompilar Analizador Javaguayo",
            bg=theme.BG_PANEL, fg=theme.TEXT_PRIMARY,
            font=theme.FONT_UI_LG,
        ).pack(pady=(16, 4))

        tk.Label(
            win,
            text="Ejecuta JFlex, CUP y javac para regenerar el analizador desde los fuentes.",
            bg=theme.BG_PANEL, fg=theme.TEXT_SECONDARY,
            font=theme.FONT_SMALL,
        ).pack(pady=(0, 8))

        out = tk.Text(
            win,
            bg=theme.BG_WIDGET, fg=theme.TEXT_PRIMARY,
            font=theme.FONT_MONO_SM,
            relief="flat", bd=8,
            state="disabled", wrap="word",
        )
        out.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        def log(msg: str) -> None:
            out.config(state="normal")
            out.insert("end", msg + "\n")
            out.see("end")
            out.config(state="disabled")

        btn_frm = tk.Frame(win, bg=theme.BG_PANEL)
        btn_frm.pack(pady=8)

        def do_compile() -> None:
            compile_btn.config(state="disabled", text="⏳  Compilando...")
            out.config(state="normal"); out.delete("1.0", "end"); out.config(state="disabled")

            def worker():
                try:
                    java_analyzer.compile_analyzer(
                        progress_callback=lambda m: win.after(0, log, m)
                    )
                    win.after(0, log, "\n✅  ¡Compilación exitosa!")
                    win.after(0, log, "   Podés usar el analizador actualizado.")
                except Exception as exc:
                    win.after(0, log, f"\n❌  Error: {exc}")
                finally:
                    win.after(0, lambda: compile_btn.config(
                        state="normal", text="🔨  Compilar"
                    ))

            threading.Thread(target=worker, daemon=True).start()

        compile_btn = tk.Button(
            btn_frm, text="🔨  Compilar", command=do_compile,
            bg=theme.ACCENT_ORANGE, fg="white",
            activebackground=theme.ACCENT_ORANGE, activeforeground="white",
            relief="flat", bd=0, padx=16, pady=7,
            font=theme.FONT_UI_BOLD, cursor="hand2",
        )
        compile_btn.pack(side="left", padx=4)

        tk.Button(
            btn_frm, text="Cerrar", command=win.destroy,
            bg=theme.BG_HOVER, fg=theme.TEXT_PRIMARY,
            activebackground=theme.BG_WIDGET, activeforeground=theme.TEXT_PRIMARY,
            relief="flat", bd=0, padx=16, pady=7,
            font=theme.FONT_UI, cursor="hand2",
        ).pack(side="left", padx=4)

    # ── Verificación de entorno ───────────────────────────────────
    def _check_environment(self) -> None:
        """Verifica Java en segundo plano al iniciar (sin diálogo)."""
        def check():
            ok, msg = java_analyzer.check_java()
            if ok:
                self.root.after(0, lambda: self._set_status(
                    f"✅ Java detectado: {msg.split('\"')[1] if '\"' in msg else msg}"
                ))
            else:
                self.root.after(0, lambda: self._set_status(
                    f"⚠️ {msg} — Instalá Java para usar el analizador"
                ))
                self.root.after(500, lambda: messagebox.showwarning(
                    "Java no encontrado",
                    f"No se detectó Java en el PATH.\n\n{msg}\n\n"
                    "Instalá Java JDK y agregalo al PATH para poder ejecutar el analizador."
                ))
        threading.Thread(target=check, daemon=True).start()

    def _check_environment_dialog(self) -> None:
        """Muestra un diálogo con el estado del entorno."""
        win = tk.Toplevel(self.root)
        win.title("Verificar Entorno")
        win.geometry("480x300")
        win.configure(bg=theme.BG_PANEL)
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="🔍  Estado del Entorno",
                 bg=theme.BG_PANEL, fg=theme.TEXT_PRIMARY,
                 font=theme.FONT_UI_LG).pack(pady=(16, 8))

        out = tk.Text(
            win, bg=theme.BG_WIDGET, fg=theme.TEXT_PRIMARY,
            font=theme.FONT_MONO_SM, relief="flat", bd=8,
            state="disabled", wrap="word",
        )
        out.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        def log(msg, color=None):
            out.config(state="normal")
            tag = f"c_{id(msg)}"
            if color:
                out.tag_configure(tag, foreground=color)
                out.insert("end", msg + "\n", tag)
            else:
                out.insert("end", msg + "\n")
            out.config(state="disabled")

        def check():
            ok_j, msg_j = java_analyzer.check_java()
            ok_a, msg_a = java_analyzer.check_analyzer()
            color_j = theme.ACCENT_GREEN if ok_j else theme.ACCENT_RED
            color_a = theme.ACCENT_GREEN if ok_a else theme.ACCENT_YELLOW
            win.after(0, log, f"{'✅' if ok_j else '❌'}  Java: {msg_j}", color_j)
            win.after(0, log, f"{'✅' if ok_a else '⚠️'}  IDEAnalyzer: {msg_a}", color_a)
            win.after(0, log, f"\n📁  Proyecto: {java_analyzer.BASE_DIR}", theme.TEXT_SECONDARY)
            win.after(0, log, f"📁  bin/: {java_analyzer.BIN_DIR}", theme.TEXT_SECONDARY)

        threading.Thread(target=check, daemon=True).start()

        tk.Button(
            win, text="Cerrar", command=win.destroy,
            bg=theme.BG_HOVER, fg=theme.TEXT_PRIMARY,
            relief="flat", bd=0, padx=14, pady=6,
            font=theme.FONT_UI, cursor="hand2",
        ).pack(pady=8)
