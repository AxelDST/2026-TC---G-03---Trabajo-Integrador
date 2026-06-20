"""
results_panel.py — Panel de resultados del Mini IDE Javaguayo.

Muestra tres pestañas:
  1. Tokens   — tabla con tipo, valor, línea y columna de cada token.
  2. Errores  — lista de errores léxicos y sintácticos con navegación.
  3. Stats    — tarjetas de estadísticas del último análisis.
"""
from __future__ import annotations

import re
import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Optional

from . import theme
from .analyzer import AnalysisResult


class ResultsPanel(tk.Frame):
    """Panel derecho con las pestañas de resultados."""

    def __init__(
        self,
        parent: tk.Widget,
        on_goto_line: Optional[Callable[[int], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(parent, bg=theme.BG_PANEL, **kwargs)
        self.on_goto_line = on_goto_line
        self._all_tokens: list = []
        self._build_widgets()

    # ── Construcción ──────────────────────────────────────────────
    def _build_widgets(self) -> None:
        # Header
        hdr = tk.Frame(self, bg=theme.BG_PANEL)
        hdr.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(
            hdr,
            text="📊  Resultados del Análisis",
            bg=theme.BG_PANEL, fg=theme.TEXT_PRIMARY,
            font=theme.FONT_TITLE,
        ).pack(side="left")

        # Notebook
        self.notebook = ttk.Notebook(self, style="Dark.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        # Pestaña 1 — Tokens
        self._tab_tokens = tk.Frame(self.notebook, bg=theme.BG_WIDGET)
        self.notebook.add(self._tab_tokens, text="  🔤 Tokens  ")
        self._build_tokens_tab()

        # Pestaña 2 — Errores
        self._tab_errors = tk.Frame(self.notebook, bg=theme.BG_WIDGET)
        self.notebook.add(self._tab_errors, text="  ❌ Errores  ")
        self._build_errors_tab()

        # Pestaña 3 — Estadísticas
        self._tab_stats = tk.Frame(self.notebook, bg=theme.BG_WIDGET)
        self.notebook.add(self._tab_stats, text="  📈 Estadísticas  ")
        self._build_stats_tab()

    # ── Pestaña Tokens ────────────────────────────────────────────
    def _build_tokens_tab(self) -> None:
        frm = self._tab_tokens

        # Barra de búsqueda
        search_row = tk.Frame(frm, bg=theme.BG_WIDGET)
        search_row.pack(fill="x", padx=10, pady=8)

        tk.Label(
            search_row, text="🔍", bg=theme.BG_WIDGET,
            fg=theme.TEXT_SECONDARY, font=theme.FONT_UI,
        ).pack(side="left")

        self._token_search = tk.Entry(
            search_row,
            bg=theme.BG_PANEL, fg=theme.TEXT_PRIMARY,
            insertbackground=theme.ACCENT_BLUE,
            relief="flat", bd=6, font=theme.FONT_UI,
        )
        self._token_search.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self._token_search.bind("<KeyRelease>", self._filter_tokens)

        # Contador de tokens
        self._token_count_lbl = tk.Label(
            frm, text="",
            bg=theme.BG_WIDGET, fg=theme.TEXT_SECONDARY,
            font=theme.FONT_SMALL, anchor="w",
        )
        self._token_count_lbl.pack(fill="x", padx=12)

        # Treeview + scrollbar
        tree_frm = tk.Frame(frm, bg=theme.BG_WIDGET)
        tree_frm.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        cols = ("#", "Tipo", "Categoría", "Valor", "Línea", "Col")
        self.token_tree = ttk.Treeview(
            tree_frm, columns=cols, show="headings",
            style="Dark.Treeview", selectmode="browse",
        )

        col_cfg = [
            ("#",          40,  "center"),
            ("Tipo",      120,  "w"),
            ("Categoría",  70,  "center"),
            ("Valor",     140,  "w"),
            ("Línea",      52,  "center"),
            ("Col",        40,  "center"),
        ]
        for name, width, anchor in col_cfg:
            self.token_tree.heading(name, text=name, anchor=anchor)
            self.token_tree.column(name, width=width, anchor=anchor, minwidth=30, stretch=(name == "Valor"))

        vsb = ttk.Scrollbar(tree_frm, orient="vertical",
                             command=self.token_tree.yview,
                             style="Dark.Vertical.TScrollbar")
        hsb = ttk.Scrollbar(tree_frm, orient="horizontal",
                             command=self.token_tree.xview,
                             style="Dark.Horizontal.TScrollbar")
        self.token_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.token_tree.pack(side="left", fill="both", expand=True)

        self.token_tree.bind("<Double-1>", self._on_token_double_click)
        self.token_tree.bind("<Return>",   self._on_token_double_click)

    # ── Pestaña Errores ───────────────────────────────────────────
    def _build_errors_tab(self) -> None:
        frm = self._tab_errors

        def make_section(parent, title, color):
            """Crea un sub-panel de errores con título y text widget."""
            sec = tk.Frame(parent, bg=theme.BG_WIDGET)
            sec.pack(fill="both", expand=True, padx=8, pady=6)

            hdr = tk.Frame(sec, bg=theme.BG_WIDGET)
            hdr.pack(fill="x")

            lbl = tk.Label(hdr, text=title, bg=theme.BG_WIDGET,
                           fg=color, font=theme.FONT_UI_BOLD)
            lbl.pack(side="left", pady=(6, 2))

            count_lbl = tk.Label(hdr, text="", bg=theme.BG_WIDGET,
                                 fg=theme.TEXT_MUTED, font=theme.FONT_SMALL)
            count_lbl.pack(side="left", padx=6, pady=(6, 2))

            txt_frm = tk.Frame(sec, bg=theme.BG_PANEL, bd=0)
            txt_frm.pack(fill="both", expand=True)

            txt = tk.Text(
                txt_frm,
                bg=theme.BG_PANEL, fg=color,
                font=theme.FONT_MONO_SM,
                relief="flat", bd=6,
                wrap="word",
                state="disabled",
                cursor="arrow",
                selectbackground=theme.BG_SELECTED,
                height=7,
            )
            txt.pack(fill="both", expand=True)
            txt.tag_configure("ok",      foreground=theme.ACCENT_GREEN)
            txt.tag_configure("bullet",  foreground=color)
            txt.tag_configure("clickable", underline=True)
            txt.tag_configure("not_run", foreground=theme.TEXT_MUTED,
                              font=(theme.FONT_MONO_SM[0], theme.FONT_MONO_SM[1], "italic"))

            return lbl, count_lbl, txt

        # Separar en dos secciones
        paned = tk.PanedWindow(frm, orient="vertical",
                               bg=theme.BORDER, sashwidth=4, bd=0)
        paned.pack(fill="both", expand=True)

        top_frm = tk.Frame(paned, bg=theme.BG_WIDGET)
        bot_frm = tk.Frame(paned, bg=theme.BG_WIDGET)
        paned.add(top_frm, minsize=80)
        paned.add(bot_frm, minsize=80)

        self._lex_lbl, self._lex_count, self._lex_txt = \
            make_section(top_frm, "❌  Errores Léxicos", theme.ACCENT_RED)

        self._sint_lbl, self._sint_count, self._sint_txt = \
            make_section(bot_frm, "⚠️  Errores Sintácticos", theme.ACCENT_YELLOW)

        # Bind de clic para navegar al error
        self._lex_txt.bind("<Button-1>",
                           lambda e: self._on_error_click(e, self._lex_txt))
        self._sint_txt.bind("<Button-1>",
                            lambda e: self._on_error_click(e, self._sint_txt))

    # ── Pestaña Estadísticas ──────────────────────────────────────
    def _build_stats_tab(self) -> None:
        frm = self._tab_stats

        inner = tk.Frame(frm, bg=theme.BG_WIDGET)
        inner.pack(fill="both", expand=True, padx=16, pady=16)

        # Variables
        self._sv_tokens   = tk.StringVar(value="—")
        self._sv_lex_err  = tk.StringVar(value="—")
        self._sv_sint_err = tk.StringVar(value="—")
        self._sv_time     = tk.StringVar(value="—")
        self._sv_estado   = tk.StringVar(value="—")
        self._sv_mode     = tk.StringVar(value="—")

        def card(parent, icon, title, var, color, row, col):
            c = tk.Frame(parent, bg=theme.BG_PANEL, padx=16, pady=14)
            c.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
            tk.Label(c, text=f"{icon}  {title}",
                     bg=theme.BG_PANEL, fg=theme.TEXT_SECONDARY,
                     font=theme.FONT_SMALL).pack(anchor="w")
            tk.Label(c, textvariable=var, bg=theme.BG_PANEL,
                     fg=color, font=("Segoe UI", 22, "bold")).pack(anchor="w", pady=(4, 0))
            return c

        card(inner, "🔤", "Total de Tokens",      self._sv_tokens,   theme.ACCENT_BLUE,   0, 0)
        card(inner, "❌", "Errores Léxicos",      self._sv_lex_err,  theme.ACCENT_RED,    0, 1)
        card(inner, "⚠️", "Errores Sintácticos",  self._sv_sint_err, theme.ACCENT_YELLOW, 1, 0)
        card(inner, "⏱️", "Tiempo de Análisis",   self._sv_time,     theme.ACCENT_CYAN,   1, 1)

        inner.columnconfigure(0, weight=1)
        inner.columnconfigure(1, weight=1)

        # Tarjeta de estado (ancho completo)
        estado_card = tk.Frame(inner, bg=theme.BG_PANEL, padx=16, pady=14)
        estado_card.grid(row=2, column=0, columnspan=2, padx=6, pady=6, sticky="ew")
        tk.Label(estado_card, text="📋  Estado del Análisis",
                 bg=theme.BG_PANEL, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_SMALL).pack(anchor="w")
        self._estado_lbl = tk.Label(
            estado_card, textvariable=self._sv_estado,
            bg=theme.BG_PANEL, fg=theme.ACCENT_GREEN,
            font=("Segoe UI", 13, "bold"),
        )
        self._estado_lbl.pack(anchor="w", pady=(4, 0))

        # Modo
        mode_card = tk.Frame(inner, bg=theme.BG_PANEL, padx=16, pady=10)
        mode_card.grid(row=3, column=0, columnspan=2, padx=6, pady=(0, 6), sticky="ew")
        tk.Label(mode_card, text="🔧  Modo de Análisis",
                 bg=theme.BG_PANEL, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_SMALL).pack(anchor="w")
        tk.Label(mode_card, textvariable=self._sv_mode,
                 bg=theme.BG_PANEL, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_UI).pack(anchor="w")

    # ── Actualización de datos ────────────────────────────────────
    def update_results(
        self,
        result: AnalysisResult,
        mode: str = "Léxico + Sintáctico",
        lexico_only: bool = False,
    ) -> None:
        """Actualiza todas las pestañas con los resultados del análisis."""
        self._update_tokens_tab(result)
        self._update_errors_tab(result, lexico_only=lexico_only)
        self._update_stats_tab(result, mode)

    def _update_tokens_tab(self, result: AnalysisResult) -> None:
        self._all_tokens = result.tokens
        self._token_search.delete(0, "end")
        self._render_tokens(result.tokens)

    def _render_tokens(self, tokens) -> None:
        tree = self.token_tree
        tree.delete(*tree.get_children())

        for i, tok in enumerate(tokens):
            tipo  = tok.tipo
            valor = tok.valor
            cat   = theme.TOKEN_CATEGORY.get(tipo, "SYM")
            color = theme.TOKEN_COLORS.get(tipo, theme.TEXT_PRIMARY)

            tag = f"t_{tipo}"
            tree.tag_configure(tag, foreground=color)
            tree.insert(
                "", "end",
                values=(i + 1, tipo, cat, valor, tok.linea, tok.columna),
                tags=(tag,),
            )

        n = len(tokens)
        plural = "s" if n != 1 else ""
        self._token_count_lbl.config(
            text=f"  {n} token{plural} encontrado{plural}"
        )

    def _filter_tokens(self, event=None) -> None:
        q = self._token_search.get().strip().lower()
        if not q:
            self._render_tokens(self._all_tokens)
        else:
            filtered = [
                t for t in self._all_tokens
                if q in t.tipo.lower() or q in t.valor.lower()
            ]
            self._render_tokens(filtered)

    def _update_errors_tab(
        self,
        result: AnalysisResult,
        lexico_only: bool = False,
    ) -> None:
        def fill(widget, errors, ok_msg):
            widget.config(state="normal")
            widget.delete("1.0", "end")
            if errors:
                for err in errors:
                    widget.insert("end", f"  • {err}\n", "bullet")
            else:
                widget.insert("end", f"  {ok_msg}", "ok")
            widget.config(state="disabled")

        n_lex  = len(result.lex_errors)
        n_sint = len(result.sint_errors)

        self._lex_count.config(
            text=f"({n_lex} error{'es' if n_lex != 1 else ''})" if n_lex else ""
        )

        fill(self._lex_txt, result.lex_errors, "✅ Sin errores léxicos")
        self._lex_txt.config(fg=theme.ACCENT_RED if n_lex else theme.ACCENT_GREEN)

        # Panel sintáctico: diferenciar modo
        self._sint_txt.config(state="normal")
        self._sint_txt.delete("1.0", "end")
        if lexico_only:
            # El análisis sintáctico NO se ejecutó
            self._sint_lbl.config(text="⚡  Análisis Sintáctico")
            self._sint_count.config(text="")
            self._sint_txt.insert(
                "end",
                "  ⏭  No ejecutado en modo \u201cSolo Léxico\u201d.\n"
                "  Presioná ▶ Analizar para ejecutar el análisis completo.",
                "not_run",
            )
            self._sint_txt.config(fg=theme.TEXT_MUTED)
        else:
            self._sint_lbl.config(text="⚠️  Errores Sintácticos")
            self._sint_count.config(
                text=f"({n_sint} error{'es' if n_sint != 1 else ''})" if n_sint else ""
            )
            if result.sint_errors:
                for err in result.sint_errors:
                    self._sint_txt.insert("end", f"  • {err}\n", "bullet")
            else:
                self._sint_txt.insert("end", "  ✅ Sin errores sintácticos", "ok")
            self._sint_txt.config(
                fg=theme.ACCENT_YELLOW if n_sint else theme.ACCENT_GREEN
            )
        self._sint_txt.config(state="disabled")

    def _update_stats_tab(self, result: AnalysisResult, mode: str) -> None:
        self._sv_tokens.set(str(result.total_tokens))
        self._sv_lex_err.set(str(len(result.lex_errors)))
        self._sv_sint_err.set(str(len(result.sint_errors)))
        self._sv_time.set(f"{result.elapsed:.3f} s")
        self._sv_mode.set(mode)

        _estado_map = {
            "OK":               ("✅  Análisis correcto — sin errores",         theme.ACCENT_GREEN),
            "ERROR_LEXICO":     ("❌  Errores léxicos detectados",              theme.ACCENT_RED),
            "ERROR_SINTACTICO": ("⚠️  Errores sintácticos detectados",          theme.ACCENT_YELLOW),
            "ERROR_AMBOS":      ("🔴  Errores léxicos y sintácticos detectados", theme.ACCENT_RED),
        }
        txt, color = _estado_map.get(result.estado,
                                     ("❓  Estado desconocido", theme.TEXT_SECONDARY))
        self._sv_estado.set(txt)
        self._estado_lbl.config(fg=color)

    # ── Interacción ───────────────────────────────────────────────
    def _on_token_double_click(self, event=None) -> None:
        sel = self.token_tree.selection()
        if sel and self.on_goto_line:
            vals = self.token_tree.item(sel[0], "values")
            try:
                self.on_goto_line(int(vals[4]))  # índice de "Línea"
            except (IndexError, ValueError):
                pass

    def _on_error_click(self, event, widget: tk.Text) -> None:
        """Al hacer clic en una línea de error, navega a esa línea en el editor."""
        idx = widget.index(f"@{event.x},{event.y}")
        row = idx.split(".")[0]
        line_text = widget.get(f"{row}.0", f"{row}.end")
        m = re.search(r'l[ií]nea\s+(\d+)', line_text, re.IGNORECASE)
        if m and self.on_goto_line:
            self.on_goto_line(int(m.group(1)))

    # ── Limpiar ───────────────────────────────────────────────────
    def clear(self) -> None:
        """Limpia todos los paneles."""
        self.token_tree.delete(*self.token_tree.get_children())
        self._token_count_lbl.config(text="")
        self._all_tokens = []

        for widget in (self._lex_txt, self._sint_txt):
            widget.config(state="normal")
            widget.delete("1.0", "end")
            widget.config(state="disabled")

        self._lex_count.config(text="")
        self._sint_count.config(text="")
        # Restaurar títulos originales
        self._sint_lbl.config(text="⚠️  Errores Sintácticos")


        for var in (self._sv_tokens, self._sv_lex_err,
                    self._sv_sint_err, self._sv_time, self._sv_estado, self._sv_mode):
            var.set("—")
        self._estado_lbl.config(fg=theme.TEXT_SECONDARY)

    def select_tab(self, index: int) -> None:
        self.notebook.select(index)
