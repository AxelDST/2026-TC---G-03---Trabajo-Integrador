"""
editor.py — Editor de código con resaltado de sintaxis Javaguayo,
numeración de líneas y marcado de errores.
"""
from __future__ import annotations

import re
import tkinter as tk
from tkinter import font as tkfont
from typing import List

from . import theme

# ── Patrones de resaltado de sintaxis ─────────────────────────────
_COMMENT   = re.compile(r'//[^\n]*')
_LIT_STR   = re.compile(r'"[^"\n]*(?:"|\n|$)')
_LIT_CHAR  = re.compile(r"'[^'\n](?:'|$)")
_KEYWORD   = re.compile(r'\b(clase|retornar|si|sino|mientras|repetir|nuevo|imprimir|inicio)\b')
_TYPE_KW   = re.compile(r'\b(int|decimal|string|objeto|bool|void|char)\b')
_BOOL_NULL = re.compile(r'\b(true|false|null)\b')
_CLASS_NM  = re.compile(r'\b[A-Z][a-zA-Z0-9]*\b')
_LIT_NUM   = re.compile(r'(?<![a-zA-Z_])(-?\d+\.?\d*)\b')
_OPERATOR  = re.compile(r'==|!=|<=|>=|[<>=+\-*/]')


class LineNumbers(tk.Canvas):
    """Canvas lateral que muestra los números de línea sincronizados con el editor."""

    def __init__(self, parent: tk.Widget, editor: "CodeEditor") -> None:
        super().__init__(
            parent,
            width=48,
            bg=theme.BG_LINE_NUMS,
            highlightthickness=0,
            bd=0,
        )
        self._editor = editor
        self.bind("<Configure>", self._redraw)

    def redraw(self, event=None) -> None:
        self._redraw()

    def _redraw(self, event=None) -> None:
        self.delete("all")
        txt = self._editor.text

        # Primer y último índice visible
        top_idx = txt.index("@0,0")
        bot_idx = txt.index(f"@0,{txt.winfo_height()}")

        first_line = int(top_idx.split(".")[0])
        last_line  = int(bot_idx.split(".")[0])

        for lineno in range(first_line, last_line + 1):
            # Posición Y del inicio de esa línea en el widget Text
            dline = txt.dlineinfo(f"{lineno}.0")
            if dline is None:
                continue
            y = dline[1] + dline[3] // 2  # centro vertical de la línea
            self.create_text(
                42, y,
                anchor="e",
                text=str(lineno),
                fill=theme.TEXT_MUTED,
                font=theme.FONT_MONO_SM,
            )


class CodeEditor(tk.Frame):
    """
    Widget editor de código con:
    - Números de línea sincronizados
    - Resaltado de sintaxis Javaguayo en tiempo real
    - Marcado visual de líneas con errores léxicos/sintácticos
    - Auto-indentado al presionar Enter
    - Ctrl+Z / Ctrl+Y para deshacer/rehacer
    """

    def __init__(self, parent: tk.Widget, **kwargs) -> None:
        super().__init__(parent, bg=theme.BG_EDITOR, **kwargs)
        self._highlight_job: str | None = None
        self._build_widgets()
        self._configure_tags()
        self._bind_events()

    # ── Construcción ──────────────────────────────────────────────
    def _build_widgets(self) -> None:
        # Scrollbars
        self._vscroll = tk.Scrollbar(
            self, orient="vertical",
            bg=theme.BG_HOVER, troughcolor=theme.BG_PANEL,
            relief="flat", bd=0, width=10,
        )
        self._hscroll = tk.Scrollbar(
            self, orient="horizontal",
            bg=theme.BG_HOVER, troughcolor=theme.BG_PANEL,
            relief="flat", bd=0, width=10,
        )
        self._hscroll.pack(side="bottom", fill="x")
        self._vscroll.pack(side="right",  fill="y")

        # Números de línea
        self._line_nums_frame = tk.Frame(self, bg=theme.BG_LINE_NUMS, width=52)
        self._line_nums_frame.pack(side="left", fill="y")
        self._line_nums_frame.pack_propagate(False)

        # Widget Text principal
        self.text = tk.Text(
            self,
            bg=theme.BG_EDITOR,
            fg=theme.TEXT_PRIMARY,
            insertbackground=theme.ACCENT_BLUE,
            selectbackground=theme.BG_SELECTED,
            selectforeground=theme.TEXT_PRIMARY,
            font=theme.FONT_MONO,
            relief="flat", bd=0,
            padx=14, pady=10,
            undo=True, maxundo=200,
            wrap="none",
            yscrollcommand=self._on_yscroll,
            xscrollcommand=self._hscroll.set,
            tabs=("28",),  # 4 espacios aprox.
            spacing1=2,
            spacing3=2,
        )
        self.text.pack(side="left", fill="both", expand=True)

        # Separador derecho de números de línea
        tk.Frame(self._line_nums_frame, width=1, bg=theme.BORDER).pack(
            side="right", fill="y"
        )

        # Canvas de números
        self._line_nums = LineNumbers(self._line_nums_frame, self)
        self._line_nums.pack(fill="both", expand=True)

        # Conectar scrollbars
        self._vscroll.config(command=self._on_vscroll_cmd)
        self._hscroll.config(command=self.text.xview)

    def _on_yscroll(self, *args) -> None:
        self._vscroll.set(*args)
        self._line_nums.redraw()

    def _on_vscroll_cmd(self, *args) -> None:
        self.text.yview(*args)
        self._line_nums.redraw()

    # ── Tags de sintaxis ──────────────────────────────────────────
    def _configure_tags(self) -> None:
        t = self.text
        t.tag_configure("comment",   foreground=theme.SYN_COMMENT,
                         font=(theme.FONT_MONO[0], theme.FONT_MONO[1], "italic"))
        t.tag_configure("lit_str",   foreground=theme.SYN_STRING)
        t.tag_configure("lit_char",  foreground=theme.SYN_STRING)
        t.tag_configure("keyword",   foreground=theme.SYN_KEYWORD,
                         font=(theme.FONT_MONO[0], theme.FONT_MONO[1], "bold"))
        t.tag_configure("type_kw",   foreground=theme.SYN_TYPE)
        t.tag_configure("bool_null", foreground=theme.SYN_LITERAL)
        t.tag_configure("class_nm",  foreground=theme.SYN_CLASS_NAME)
        t.tag_configure("lit_num",   foreground=theme.SYN_LITERAL)

        # Error marks
        t.tag_configure("error_lex",  background="#3d1515", underline=True)
        t.tag_configure("error_sint", background="#2d2200")
        t.tag_configure("curr_line",  background="#1c2128")

        # Prioridades (mayor = más visible)
        for tag in ("error_lex", "error_sint", "curr_line"):
            t.tag_raise(tag)

    # ── Eventos ───────────────────────────────────────────────────
    def _bind_events(self) -> None:
        t = self.text
        t.bind("<KeyRelease>",    self._on_key_release)
        t.bind("<ButtonRelease>", self._on_click)
        t.bind("<Return>",        self._on_return, add=True)
        t.bind("<Configure>",     lambda e: self._line_nums.redraw())
        t.bind("<MouseWheel>",    self._on_mousewheel)
        t.bind("<<Modified>>",    self._on_modified)

    def _on_key_release(self, event=None) -> None:
        self._line_nums.redraw()
        self._update_curr_line()
        self._schedule_highlight()

    def _on_click(self, event=None) -> None:
        self._update_curr_line()
        self._line_nums.redraw()

    def _on_mousewheel(self, event=None) -> None:
        self.after(10, self._line_nums.redraw)

    def _on_modified(self, event=None) -> None:
        self.text.edit_modified(False)

    def _on_return(self, event=None) -> None:
        """Auto-indentado al presionar Enter."""
        line = self.text.get("insert linestart", "insert")
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if line.rstrip().endswith("{"):
            indent += 4
        self.text.insert("insert", "\n" + " " * indent)
        self._line_nums.redraw()
        return "break"

    # ── Resaltado de sintaxis ─────────────────────────────────────
    def _schedule_highlight(self) -> None:
        if self._highlight_job:
            self.after_cancel(self._highlight_job)
        self._highlight_job = self.after(250, self._apply_highlighting)

    def _apply_highlighting(self) -> None:
        t = self.text
        content = t.get("1.0", "end-1c")

        # Limpiar tags de sintaxis (no los de errores)
        for tag in ("comment", "lit_str", "lit_char", "keyword",
                    "type_kw", "bool_null", "class_nm", "lit_num"):
            t.tag_remove(tag, "1.0", "end")

        def apply(pattern: re.Pattern, tag: str) -> None:
            for m in pattern.finditer(content):
                s = f"1.0 + {m.start()} chars"
                e = f"1.0 + {m.end()} chars"
                t.tag_add(tag, s, e)

        # Orden importa: comentarios y strings primero para que tapen keywords
        apply(_COMMENT,   "comment")
        apply(_LIT_STR,   "lit_str")
        apply(_LIT_CHAR,  "lit_char")
        apply(_KEYWORD,   "keyword")
        apply(_TYPE_KW,   "type_kw")
        apply(_BOOL_NULL, "bool_null")
        apply(_CLASS_NM,  "class_nm")
        apply(_LIT_NUM,   "lit_num")

    def _update_curr_line(self) -> None:
        t = self.text
        t.tag_remove("curr_line", "1.0", "end")
        line = t.index("insert").split(".")[0]
        t.tag_add("curr_line", f"{line}.0", f"{int(line)+1}.0")

    # ── API pública ───────────────────────────────────────────────
    def get_code(self) -> str:
        """Retorna el contenido actual del editor."""
        return self.text.get("1.0", "end-1c")

    def set_code(self, code: str) -> None:
        """Reemplaza el contenido del editor."""
        t = self.text
        t.config(state="normal")
        t.delete("1.0", "end")
        t.insert("1.0", code)
        self.clear_error_marks()
        self._apply_highlighting()
        self._line_nums.redraw()
        self._update_curr_line()

    def clear_error_marks(self) -> None:
        """Elimina todos los marcados de errores."""
        self.text.tag_remove("error_lex",  "1.0", "end")
        self.text.tag_remove("error_sint", "1.0", "end")

    def mark_error_lines(
        self,
        lex_lines:  List[int],
        sint_lines: List[int],
    ) -> None:
        """Marca visualmente las líneas con errores en el editor."""
        self.clear_error_marks()
        for ln in lex_lines:
            try:
                self.text.tag_add("error_lex", f"{ln}.0", f"{ln}.end+1c")
            except tk.TclError:
                pass
        for ln in sint_lines:
            try:
                self.text.tag_add("error_sint", f"{ln}.0", f"{ln}.end+1c")
            except tk.TclError:
                pass

    def goto_line(self, line: int) -> None:
        """Desplaza la vista al número de línea dado y mueve el cursor."""
        t = self.text
        idx = f"{line}.0"
        t.see(idx)
        t.mark_set("insert", idx)
        t.focus_set()
        self._update_curr_line()
        self._line_nums.redraw()

    def get_cursor_pos(self) -> tuple[int, int]:
        """Retorna (línea, columna) actual del cursor (1-indexed)."""
        pos = self.text.index("insert")
        ln, col = pos.split(".")
        return int(ln), int(col) + 1
