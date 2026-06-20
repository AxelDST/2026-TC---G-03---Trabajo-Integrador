"""
theme.py — Paleta de colores y estilos del Mini IDE Javaguayo.
Inspirado en GitHub Dark + VS Code.
"""
import tkinter as tk
from tkinter import ttk

# ── Paleta principal ──────────────────────────────────────────────
BG_MAIN       = "#0d1117"   # fondo global
BG_EDITOR     = "#0d1117"   # fondo editor
BG_PANEL      = "#161b22"   # paneles secundarios
BG_WIDGET     = "#21262d"   # widgets (treeview, text)
BG_HOVER      = "#30363d"   # hover buttons
BG_SELECTED   = "#1f4a7a"   # selección
BG_LINE_NUMS  = "#161b22"   # números de línea

ACCENT_BLUE   = "#58a6ff"
ACCENT_GREEN  = "#3fb950"
ACCENT_RED    = "#f85149"
ACCENT_YELLOW = "#d29922"
ACCENT_PURPLE = "#bc8cff"
ACCENT_ORANGE = "#ffa657"
ACCENT_CYAN   = "#39d353"

TEXT_PRIMARY   = "#e6edf3"
TEXT_SECONDARY = "#8b949e"
TEXT_MUTED     = "#484f58"

BORDER         = "#30363d"
BORDER_LIGHT   = "#444c56"

# ── Colores de sintaxis ───────────────────────────────────────────
SYN_KEYWORD    = "#ff7b72"   # palabras reservadas
SYN_TYPE       = "#ffa657"   # tipos de dato
SYN_LITERAL    = "#79c0ff"   # literales numéricos / bool / null
SYN_STRING     = "#a5d6ff"   # cadenas de texto
SYN_COMMENT    = "#8b949e"   # comentarios
SYN_CLASS_NAME = "#f0883e"   # nombres de clase (PascalCase)

# ── Fuentes ───────────────────────────────────────────────────────
FONT_MONO      = ("Consolas", 11)
FONT_MONO_SM   = ("Consolas", 10)
FONT_UI        = ("Segoe UI", 10)
FONT_UI_BOLD   = ("Segoe UI", 10, "bold")
FONT_UI_LG     = ("Segoe UI", 12, "bold")
FONT_SMALL     = ("Segoe UI", 9)
FONT_TITLE     = ("Segoe UI", 11, "bold")

# ── Colores por tipo de token (para la tabla) ─────────────────────
TOKEN_COLORS = {
    # Palabras reservadas
    "CLASE":       "#ff7b72",
    "SI":          "#ff7b72",
    "SINO":        "#ff7b72",
    "MIENTRAS":    "#ff7b72",
    "REPETIR":     "#ff7b72",
    "NUEVO":       "#ff7b72",
    "IMPRIMIR":    "#ff7b72",
    "INICIO":      "#ff7b72",
    "RETORNAR":    "#ff7b72",
    # Tipos
    "INT":         "#ffa657",
    "DECIMAL":     "#ffa657",
    "STRING":      "#ffa657",
    "OBJETO":      "#ffa657",
    "BOOL":        "#ffa657",
    "VOID":        "#ffa657",
    "CHAR":        "#ffa657",
    # Literales
    "LIT_INT":     "#79c0ff",
    "LIT_DEC":     "#79c0ff",
    "LIT_STR":     "#a5d6ff",
    "LIT_CHAR":    "#a5d6ff",
    "LIT_BOOL":    "#79c0ff",
    "LIT_NULL":    "#79c0ff",
    # Identificadores
    "NOMBRE_CLASE":  "#f0883e",
    "IDENTIFICADOR": "#e6edf3",
    # Operadores
    "AND":         "#f78166",
    "OR":          "#f78166",
    "IGUAL":       "#f78166",
    "DISTINTO":    "#f78166",
    "MENOR":       "#f78166",
    "MAYOR":       "#f78166",
    "MENOR_IGUAL": "#f78166",
    "MAYOR_IGUAL": "#f78166",
    "ASIGNAR":     "#f78166",
    "MAS":         "#f78166",
    "MENOS":       "#f78166",
    "POR":         "#f78166",
    "DIV":         "#f78166",
    # Símbolos
    "LPAREN":      "#c9d1d9",
    "RPAREN":      "#c9d1d9",
    "LBRACE":      "#c9d1d9",
    "RBRACE":      "#c9d1d9",
    "PUNTOYCOMA":  "#8b949e",
    "COMA":        "#8b949e",
    "PUNTO":       "#8b949e",
}

# Categorías de tokens (para el badge en la tabla)
TOKEN_CATEGORY = {
    "CLASE": "KW", "SI": "KW", "SINO": "KW", "MIENTRAS": "KW",
    "REPETIR": "KW", "NUEVO": "KW", "IMPRIMIR": "KW", "INICIO": "KW",
    "RETORNAR": "KW",
    "INT": "TIPO", "DECIMAL": "TIPO", "STRING": "TIPO", "OBJETO": "TIPO",
    "BOOL": "TIPO", "VOID": "TIPO", "CHAR": "TIPO",
    "LIT_INT": "LIT", "LIT_DEC": "LIT", "LIT_STR": "LIT",
    "LIT_CHAR": "LIT", "LIT_BOOL": "LIT", "LIT_NULL": "LIT",
    "NOMBRE_CLASE": "ID", "IDENTIFICADOR": "ID",
    "AND": "OP", "OR": "OP", "IGUAL": "OP", "DISTINTO": "OP",
    "MENOR": "OP", "MAYOR": "OP", "MENOR_IGUAL": "OP", "MAYOR_IGUAL": "OP",
    "ASIGNAR": "OP", "MAS": "OP", "MENOS": "OP", "POR": "OP", "DIV": "OP",
    "LPAREN": "SYM", "RPAREN": "SYM", "LBRACE": "SYM", "RBRACE": "SYM",
    "PUNTOYCOMA": "SYM", "COMA": "SYM", "PUNTO": "SYM",
}


def setup_styles(root: tk.Tk) -> None:
    """Configura los estilos ttk para el tema oscuro."""
    style = ttk.Style(root)
    style.theme_use("default")

    # ── Notebook ──
    style.configure(
        "Dark.TNotebook",
        background=BG_PANEL,
        borderwidth=0,
        tabmargins=[0, 0, 0, 0],
    )
    style.configure(
        "Dark.TNotebook.Tab",
        background=BG_WIDGET,
        foreground=TEXT_SECONDARY,
        padding=[14, 7],
        font=FONT_UI,
        borderwidth=0,
    )
    style.map(
        "Dark.TNotebook.Tab",
        background=[("selected", BG_PANEL), ("active", BG_HOVER)],
        foreground=[("selected", TEXT_PRIMARY), ("active", TEXT_PRIMARY)],
    )

    # ── Treeview ──
    style.configure(
        "Dark.Treeview",
        background=BG_WIDGET,
        foreground=TEXT_PRIMARY,
        fieldbackground=BG_WIDGET,
        borderwidth=0,
        rowheight=26,
        font=FONT_MONO_SM,
    )
    style.configure(
        "Dark.Treeview.Heading",
        background=BG_PANEL,
        foreground=TEXT_SECONDARY,
        font=FONT_UI_BOLD,
        borderwidth=0,
        relief="flat",
        padding=[8, 6],
    )
    style.map(
        "Dark.Treeview",
        background=[("selected", BG_SELECTED)],
        foreground=[("selected", TEXT_PRIMARY)],
    )
    style.map(
        "Dark.Treeview.Heading",
        background=[("active", BG_HOVER)],
    )

    # ── Scrollbar ──
    style.configure(
        "Dark.Vertical.TScrollbar",
        background=BG_HOVER,
        troughcolor=BG_PANEL,
        borderwidth=0,
        relief="flat",
        arrowcolor=TEXT_SECONDARY,
        width=10,
    )
    style.configure(
        "Dark.Horizontal.TScrollbar",
        background=BG_HOVER,
        troughcolor=BG_PANEL,
        borderwidth=0,
        relief="flat",
        arrowcolor=TEXT_SECONDARY,
        width=10,
    )
    style.map(
        "Dark.Vertical.TScrollbar",
        background=[("active", ACCENT_BLUE)],
    )

    # ── PanedWindow ──
    style.configure("Dark.TPanedwindow", background=BORDER)
