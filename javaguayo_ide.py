"""
Javaguayo Mini IDE
==================
Mini IDE para el lenguaje Javaguayo - Trabajo Integrador 2026
FCEQyN Módulo Apóstoles - UNaM
Grupo 03: Dos Santos Axel, Mittelstedt Gabriel, Escalada Leandro
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import re
import os

# ──────────────────────────────────────────────
#  TOKENS Y EXPRESIONES REGULARES
# ──────────────────────────────────────────────

PALABRAS_RESERVADAS = {
    "clase", "retornar", "si", "sino", "mientras",
    "repetir", "nuevo", "imprimir", "inicio"
}

TIPOS = {"int", "decimal", "string", "bool", "char", "objeto", "void", "null"}

LITERALES_BOOL = {"true", "false"}

TOKEN_SPEC = [
    ("COMENTARIO",    r"//[^\n]*"),
    ("LIT_DEC",       r"-?\d+\.\d+"),
    ("LIT_INT",       r"-?\d+"),
    ("LIT_STR",       r'"[^"\n]*"'),
    ("LIT_CHAR",      r"'[^'\n]'"),
    ("LIT_BOOL",      r"\b(true|false)\b"),
    ("OP_REL",        r"==|!=|<=|>=|<|>"),
    ("OP_ASIGN",      r"(?<!=)=(?!=)"),
    ("OP_SUMA",       r"[+\-]"),
    ("OP_MULT",       r"[*/]"),
    ("LPAREN",        r"\("),
    ("RPAREN",        r"\)"),
    ("LBRACE",        r"\{"),
    ("RBRACE",        r"\}"),
    ("SEMICOLON",     r";"),
    ("COMMA",         r","),
    ("DOT",           r"\."),
    ("PALABRA_RES",   r"\b(?:clase|retornar|si|sino|mientras|repetir|nuevo|imprimir|inicio)\b"),
    ("TIPO",          r"\b(?:int|decimal|string|bool|char|objeto|void|null)\b"),
    ("AND_OR",        r"\b(?:and|or)\b"),
    ("NOMBRE_CLASE",  r"\b[A-Z][a-zA-Z0-9]*\b"),
    ("IDENTIFICADOR", r"\b[a-z][a-zA-Z0-9_]*\b"),
    ("WS",            r"[ \t\n\r]+"),
    ("DESCONOCIDO",   r"."),
]

MASTER_PATTERN = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC)
)

# ──────────────────────────────────────────────
#  ANALIZADOR LÉXICO
# ──────────────────────────────────────────────

def tokenizar(codigo):
    """Retorna lista de (tipo, valor, posicion)."""
    tokens = []
    for m in MASTER_PATTERN.finditer(codigo):
        tipo = m.lastgroup
        valor = m.group()
        pos = m.start()
        if tipo == "WS":
            continue
        tokens.append((tipo, valor, pos))
    return tokens

def analizar_lexico(codigo):
    """Devuelve tabla de tokens y lista de errores."""
    tokens = tokenizar(codigo)
    linea = 1
    col = 1
    tabla = []
    pos_actual = 0
    for tipo, valor, pos in tokens:
        # contar líneas hasta pos
        fragmento = codigo[:pos]
        linea = fragmento.count("\n") + 1
        ultimo_nl = fragmento.rfind("\n")
        col = pos - ultimo_nl if ultimo_nl >= 0 else pos + 1
        tabla.append((linea, col, tipo, valor))
    return tabla

# ──────────────────────────────────────────────
#  ANALIZADOR SINTÁCTICO (validación básica)
# ──────────────────────────────────────────────

def validar_sintaxis(codigo):
    """Validaciones sintácticas básicas. Retorna lista de mensajes."""
    errores = []
    tokens = tokenizar(codigo)
    tipos_tok = [t for t, v, p in tokens]
    valores_tok = [v for t, v, p in tokens]
    posiciones_tok = [p for t, v, p in tokens]

    # 1. Llaves balanceadas
    llaves = 0
    for t, v, p in tokens:
        if t == "LBRACE":
            llaves += 1
        elif t == "RBRACE":
            llaves -= 1
        if llaves < 0:
            linea = codigo[:p].count("\n") + 1
            errores.append(f"[Línea {linea}] Error: '}}' sin '{{' correspondiente.")
            llaves = 0
    if llaves > 0:
        errores.append(f"Error: Falta(n) {llaves} llave(s) de cierre '}}'.")

    # 2. Paréntesis balanceados
    paren = 0
    for t, v, p in tokens:
        if t == "LPAREN":
            paren += 1
        elif t == "RPAREN":
            paren -= 1
        if paren < 0:
            linea = codigo[:p].count("\n") + 1
            errores.append(f"[Línea {linea}] Error: ')' sin '(' correspondiente.")
            paren = 0
    if paren > 0:
        errores.append(f"Error: Falta(n) {paren} paréntesis de cierre ')'.")

    # 3. Debe haber al menos una clase
    if "clase" not in valores_tok:
        errores.append("Error: El programa debe contener al menos una declaración 'clase'.")

    # 4. Debe haber bloque inicio
    if "inicio" not in valores_tok:
        errores.append("Advertencia: No se encontró el bloque 'inicio' (punto de entrada).")

    # 5. Sentencias deben terminar con ;
    sent_tokens = {"IDENTIFICADOR", "NOMBRE_CLASE", "LIT_INT", "LIT_DEC",
                   "LIT_STR", "LIT_BOOL", "LIT_CHAR", "RPAREN"}
    for i, (t, v, p) in enumerate(tokens):
        if t == "RBRACE":
            # la sentencia anterior al } debería terminar en ; o }
            if i > 0:
                pt, pv, pp = tokens[i-1]
                if pt in {"IDENTIFICADOR", "LIT_INT", "LIT_DEC", "LIT_STR",
                          "LIT_BOOL", "LIT_CHAR", "RPAREN"}:
                    linea = codigo[:p].count("\n") + 1
                    errores.append(
                        f"[Línea {linea}] Advertencia: posible ';' faltante antes de '}}'.")

    # 6. Tokens desconocidos
    for t, v, p in tokens:
        if t == "DESCONOCIDO":
            linea = codigo[:p].count("\n") + 1
            errores.append(f"[Línea {linea}] Error léxico: carácter desconocido '{v}'.")

    return errores

# ──────────────────────────────────────────────
#  INTÉRPRETE / EJECUTOR BÁSICO
# ──────────────────────────────────────────────

MAX_ITERACIONES = 10000

def _get_var(entorno, nombre):
    actual = entorno
    while isinstance(actual, dict):
        if nombre in actual:
            return True, actual[nombre]
        actual = actual.get("__parent__")
    return False, None


def _set_var(entorno, nombre, valor):
    actual = entorno
    while isinstance(actual, dict):
        if nombre in actual:
            actual[nombre] = valor
            return
        actual = actual.get("__parent__")
    entorno[nombre] = valor


def _es_instancia(valor):
    return isinstance(valor, dict) and "__class__" in valor


def _siguiente_no_comentario(tokens, idx):
    while idx < len(tokens) and tokens[idx][0] == "COMENTARIO":
        idx += 1
    return idx


def _buscar_bloque_inicio_tokens(tokens):
    i = 0
    while i < len(tokens):
        t, v, p = tokens[i]
        if t == "PALABRA_RES" and v == "inicio":
            j = _siguiente_no_comentario(tokens, i + 1)
            if j < len(tokens) and tokens[j][0] == "LPAREN":
                j = _siguiente_no_comentario(tokens, j + 1)
                if j < len(tokens) and tokens[j][0] == "RPAREN":
                    j = _siguiente_no_comentario(tokens, j + 1)
                    if j < len(tokens) and tokens[j][0] == "LBRACE":
                        nivel = 1
                        j += 1
                        inicio = j
                        while j < len(tokens) and nivel > 0:
                            if tokens[j][0] == "LBRACE":
                                nivel += 1
                            elif tokens[j][0] == "RBRACE":
                                nivel -= 1
                            j += 1
                        if nivel == 0:
                            return tokens[inicio:j - 1]
                        return None
        i += 1
    return None


def _tokens_a_texto(tokens):
    return " ".join(valor for _, valor, _ in tokens).strip()


def _extraer_parentesis_expr(tokens, idx, output_fn, contexto):
    i = _siguiente_no_comentario(tokens, idx)
    if i >= len(tokens) or tokens[i][0] != "LPAREN":
        output_fn(f"[Error] Sintaxis invalida en {contexto}: falta '('.\n")
        return [], i, False

    i += 1
    expr_tokens = []
    paren = 1
    while i < len(tokens) and paren > 0:
        t, v, p = tokens[i]
        if t == "LPAREN":
            paren += 1
        elif t == "RPAREN":
            paren -= 1
            if paren == 0:
                i += 1
                break
        if paren > 0 and t != "COMENTARIO":
            expr_tokens.append(tokens[i])
        i += 1
    if paren > 0:
        output_fn(f"[Error] Sintaxis invalida en {contexto}: falta ')'.\n")
        return [], i, False

    return expr_tokens, i, True


def _extraer_bloque(tokens, idx, output_fn, contexto):
    i = _siguiente_no_comentario(tokens, idx)
    if i >= len(tokens) or tokens[i][0] != "LBRACE":
        output_fn(f"[Error] Sintaxis invalida en {contexto}: falta '{{'.\n")
        return [], i, False

    i += 1
    bloque_tokens = []
    llaves = 1
    while i < len(tokens) and llaves > 0:
        t, v, p = tokens[i]
        if t == "LBRACE":
            llaves += 1
        elif t == "RBRACE":
            llaves -= 1
            if llaves == 0:
                i += 1
                break
        if llaves > 0:
            bloque_tokens.append(tokens[i])
        i += 1
    if llaves > 0:
        output_fn(f"[Error] Sintaxis invalida en {contexto}: falta '}}'.\n")
        return [], i, False

    return bloque_tokens, i, True


def _separar_argumentos(tokens):
    if not tokens:
        return []
    args = []
    actual = []
    paren = 0
    for t, v, p in tokens:
        if t == "LPAREN":
            paren += 1
        elif t == "RPAREN":
            paren -= 1
        if t == "COMMA" and paren == 0:
            args.append(actual)
            actual = []
            continue
        if t != "COMENTARIO":
            actual.append((t, v, p))
    if actual:
        args.append(actual)
    return args


def _construir_clases(tokens):
    clases = {}
    i = 0
    while i < len(tokens):
        t, v, p = tokens[i]
        if t == "PALABRA_RES" and v == "clase":
            i = _siguiente_no_comentario(tokens, i + 1)
            if i >= len(tokens) or tokens[i][0] != "NOMBRE_CLASE":
                continue
            nombre_clase = tokens[i][1]
            clase_def = {"methods": {}, "attrs": []}
            clases[nombre_clase] = clase_def

            i = _siguiente_no_comentario(tokens, i + 1)
            if i >= len(tokens) or tokens[i][0] != "LBRACE":
                continue
            i += 1
            nivel = 1
            while i < len(tokens) and nivel > 0:
                t, v, p = tokens[i]
                if t == "LBRACE":
                    nivel += 1
                    i += 1
                    continue
                if t == "RBRACE":
                    nivel -= 1
                    i += 1
                    continue
                if nivel == 1:
                    if t in ("TIPO", "NOMBRE_CLASE"):
                        j = _siguiente_no_comentario(tokens, i + 1)
                        if j < len(tokens) and tokens[j][0] == "IDENTIFICADOR":
                            nombre_miembro = tokens[j][1]
                            k = _siguiente_no_comentario(tokens, j + 1)
                            if k < len(tokens) and tokens[k][0] == "LPAREN":
                                params_tokens, k2, ok = _extraer_parentesis_expr(
                                    tokens, k, lambda msg: None, "metodo")
                                if not ok:
                                    i = k2
                                    continue
                                params = []
                                p_idx = 0
                                while p_idx < len(params_tokens):
                                    t2, v2, _ = params_tokens[p_idx]
                                    if t2 in ("TIPO", "NOMBRE_CLASE"):
                                        n_idx = _siguiente_no_comentario(params_tokens, p_idx + 1)
                                        if n_idx < len(params_tokens) and params_tokens[n_idx][0] == "IDENTIFICADOR":
                                            params.append(params_tokens[n_idx][1])
                                            p_idx = n_idx + 1
                                            continue
                                    p_idx += 1
                                cuerpo_tokens, k3, ok = _extraer_bloque(
                                    tokens, k2, lambda msg: None, "metodo")
                                if ok:
                                    clase_def["methods"][nombre_miembro] = {
                                        "params": params,
                                        "body": cuerpo_tokens,
                                    }
                                    i = k3
                                    continue
                                i = k3
                                continue
                            else:
                                if nombre_miembro not in clase_def["attrs"]:
                                    clase_def["attrs"].append(nombre_miembro)
                                while i < len(tokens) and tokens[i][0] != "SEMICOLON":
                                    i += 1
                                if i < len(tokens) and tokens[i][0] == "SEMICOLON":
                                    i += 1
                                continue
                i += 1
            continue
        i += 1
    return clases


def _buscar_inicio_clase(clases):
    for clase_def in clases.values():
        metodo = clase_def["methods"].get("inicio")
        if metodo and len(metodo["params"]) == 0:
            return metodo["body"]
    return None


def _crear_instancia(nombre_clase, clases):
    clase_def = clases.get(nombre_clase)
    if not clase_def:
        return None
    campos = {nombre: None for nombre in clase_def.get("attrs", [])}
    return {"__class__": nombre_clase, "__fields__": campos}


def _ejecutar_sentencia(stmt_tokens, entorno, output_fn, clases):
    if not stmt_tokens:
        return
    linea = _tokens_a_texto(stmt_tokens)
    if not linea:
        return

    # instanciacion: NombreClase nombre = nuevo NombreClase()
    if len(stmt_tokens) >= 7:
        t0, v0, _ = stmt_tokens[0]
        t1, v1, _ = stmt_tokens[1]
        t2, v2, _ = stmt_tokens[2]
        t3, v3, _ = stmt_tokens[3]
        t4, v4, _ = stmt_tokens[4]
        t5, v5, _ = stmt_tokens[5]
        t6, v6, _ = stmt_tokens[6]
        if (t0 == "NOMBRE_CLASE" and t1 == "IDENTIFICADOR" and t2 == "OP_ASIGN" and
                t3 == "PALABRA_RES" and v3 == "nuevo" and t4 == "NOMBRE_CLASE" and
                t5 == "LPAREN" and t6 == "RPAREN"):
            instancia = _crear_instancia(v4, clases)
            if instancia is None:
                output_fn(f"[Error] Clase desconocida: {v4}.\n")
                return
            entorno[v1] = instancia
            return

    # invocacion: nombreObjeto.metodo(args)
    if len(stmt_tokens) >= 4:
        t0, v0, _ = stmt_tokens[0]
        t1, v1, _ = stmt_tokens[1]
        t2, v2, _ = stmt_tokens[2]
        t3, v3, _ = stmt_tokens[3]
        if t0 == "IDENTIFICADOR" and t1 == "DOT" and t2 == "IDENTIFICADOR" and t3 == "LPAREN":
            i = 4
            args_tokens = []
            paren = 1
            while i < len(stmt_tokens) and paren > 0:
                t, v, p = stmt_tokens[i]
                if t == "LPAREN":
                    paren += 1
                elif t == "RPAREN":
                    paren -= 1
                    if paren == 0:
                        i += 1
                        break
                if paren > 0 and t != "COMENTARIO":
                    args_tokens.append(stmt_tokens[i])
                i += 1
            if paren > 0:
                output_fn("[Error] Sintaxis invalida en invocacion de metodo: falta ')'.\n")
                return
            if i < len(stmt_tokens):
                output_fn("[Error] Sintaxis invalida en invocacion de metodo.\n")
                return

            encontrado, obj = _get_var(entorno, v0)
            if not encontrado:
                output_fn(f"[Error] Variable '{v0}' no definida.\n")
                return
            if not _es_instancia(obj):
                output_fn(f"[Error] '{v0}' no es un objeto.\n")
                return

            arg_list = _separar_argumentos(args_tokens)
            valores = []
            for arg_tokens in arg_list:
                expr = _tokens_a_texto(arg_tokens)
                val = evaluar_expr(expr, entorno, output_fn)
                if isinstance(val, str) and val.startswith("[Error"):
                    output_fn(str(val) + "\n")
                    return
                valores.append(val)

            _ejecutar_metodo(obj, v2, valores, clases, output_fn)
            return

    # imprimir(expr)
    m_imp = re.match(r"^imprimir\s*\((.+)\)$", linea)
    if m_imp:
        expr = m_imp.group(1).strip()
        resultado = evaluar_expr(expr, entorno, output_fn)
        output_fn(str(resultado) + "\n")
        return

    # declaracion con asignacion: tipo nombre = expr
    m_decl = re.match(
        r"^(int|decimal|string|bool|char)\s+([a-z][a-zA-Z0-9_]*)\s*=\s*(.+)$", linea)
    if m_decl:
        tipo_v, nombre, expr = m_decl.groups()
        val = evaluar_expr(expr.strip(), entorno, output_fn)
        entorno[nombre] = val
        return

    m_decl_simple = re.match(
        r"^(int|decimal|string|bool|char)\s+([a-z][a-zA-Z0-9_]*)$", linea)
    if m_decl_simple:
        _, nombre = m_decl_simple.groups()
        entorno[nombre] = None
        return

    # asignacion: nombre = expr
    m_asig = re.match(r"^([a-z][a-zA-Z0-9_]*)\s*=\s*(.+)$", linea)
    if m_asig:
        nombre, expr = m_asig.groups()
        _set_var(entorno, nombre, evaluar_expr(expr.strip(), entorno, output_fn))
        return


def _ejecutar_repetir(tokens, idx, entorno, output_fn, clases):
    expr_tokens, i, ok = _extraer_parentesis_expr(tokens, idx + 1, output_fn, "repetir")
    if not ok:
        return i

    bloque_tokens, i, ok = _extraer_bloque(tokens, i, output_fn, "repetir")
    if not ok:
        return i

    expr_texto = _tokens_a_texto(expr_tokens)
    veces = evaluar_expr(expr_texto, entorno, output_fn)
    if isinstance(veces, str) and veces.startswith("[Error"):
        output_fn(str(veces) + "\n")
        return i
    if isinstance(veces, bool) or not isinstance(veces, (int, float)):
        output_fn("[Error] repetir espera un numero entero.\n")
        return i
    if isinstance(veces, float) and not veces.is_integer():
        output_fn("[Error] repetir espera un numero entero.\n")
        return i
    veces_int = int(veces)
    if veces_int < 0:
        output_fn("[Error] repetir no acepta valores negativos.\n")
        return i

    for _ in range(veces_int):
        _ejecutar_bloque(bloque_tokens, entorno, output_fn, clases)
    return i


def _ejecutar_si(tokens, idx, entorno, output_fn, clases):
    expr_tokens, i, ok = _extraer_parentesis_expr(tokens, idx + 1, output_fn, "si")
    if not ok:
        return i

    bloque_true, i, ok = _extraer_bloque(tokens, i, output_fn, "si")
    if not ok:
        return i

    i = _siguiente_no_comentario(tokens, i)
    bloque_false = []
    tiene_sino = False
    if i < len(tokens) and tokens[i][0] == "PALABRA_RES" and tokens[i][1] == "sino":
        bloque_false, i, ok = _extraer_bloque(tokens, i + 1, output_fn, "sino")
        if not ok:
            return i
        tiene_sino = True

    expr_texto = _tokens_a_texto(expr_tokens)
    condicion = evaluar_expr(expr_texto, entorno, output_fn)
    if isinstance(condicion, str) and condicion.startswith("[Error"):
        output_fn(str(condicion) + "\n")
        return i
    if not isinstance(condicion, bool):
        output_fn("[Error] si espera una expresion booleana.\n")
        return i

    if condicion:
        _ejecutar_bloque(bloque_true, entorno, output_fn, clases)
    elif tiene_sino:
        _ejecutar_bloque(bloque_false, entorno, output_fn, clases)
    return i


def _ejecutar_mientras(tokens, idx, entorno, output_fn, clases):
    expr_tokens, i, ok = _extraer_parentesis_expr(tokens, idx + 1, output_fn, "mientras")
    if not ok:
        return i

    bloque_tokens, i, ok = _extraer_bloque(tokens, i, output_fn, "mientras")
    if not ok:
        return i

    expr_texto = _tokens_a_texto(expr_tokens)
    iteraciones = 0
    while True:
        condicion = evaluar_expr(expr_texto, entorno, output_fn)
        if isinstance(condicion, str) and condicion.startswith("[Error"):
            output_fn(str(condicion) + "\n")
            break
        if not isinstance(condicion, bool):
            output_fn("[Error] mientras espera una expresion booleana.\n")
            break
        if not condicion:
            break
        _ejecutar_bloque(bloque_tokens, entorno, output_fn, clases)
        iteraciones += 1
        if iteraciones >= MAX_ITERACIONES:
            output_fn("[Advertencia] Se alcanzo el limite de iteraciones en mientras.\n")
            break
    return i


def _ejecutar_metodo(instancia, nombre_metodo, argumentos, clases, output_fn):
    nombre_clase = instancia.get("__class__")
    clase_def = clases.get(nombre_clase)
    if not clase_def:
        output_fn(f"[Error] Clase desconocida: {nombre_clase}.\n")
        return
    metodo = clase_def["methods"].get(nombre_metodo)
    if not metodo:
        output_fn(f"[Error] Metodo '{nombre_metodo}' no existe en {nombre_clase}.\n")
        return
    params = metodo["params"]
    if len(argumentos) != len(params):
        output_fn(
            f"[Error] Metodo '{nombre_metodo}' espera {len(params)} argumento(s).\n")
        return

    entorno_local = {"__parent__": instancia.get("__fields__", {})}
    for nombre, valor in zip(params, argumentos):
        entorno_local[nombre] = valor
    _ejecutar_bloque(metodo["body"], entorno_local, output_fn, clases)


def _ejecutar_bloque(tokens, entorno, output_fn, clases):
    i = 0
    while i < len(tokens):
        t, v, p = tokens[i]
        if t == "COMENTARIO":
            i += 1
            continue
        if t == "PALABRA_RES":
            if v == "repetir":
                i = _ejecutar_repetir(tokens, i, entorno, output_fn, clases)
                continue
            if v == "si":
                i = _ejecutar_si(tokens, i, entorno, output_fn, clases)
                continue
            if v == "mientras":
                i = _ejecutar_mientras(tokens, i, entorno, output_fn, clases)
                continue
            if v == "sino":
                output_fn("[Error] 'sino' sin 'si' correspondiente.\n")
                bloque_ign, i, ok = _extraer_bloque(tokens, i + 1, output_fn, "sino")
                if ok:
                    continue

        stmt_tokens = []
        while i < len(tokens) and tokens[i][0] != "SEMICOLON":
            if tokens[i][0] != "COMENTARIO":
                stmt_tokens.append(tokens[i])
            i += 1
        if i < len(tokens) and tokens[i][0] == "SEMICOLON":
            i += 1
        _ejecutar_sentencia(stmt_tokens, entorno, output_fn, clases)


def ejecutar(codigo, output_fn):
    """
    Intérprete simplificado: ejecuta llamadas a imprimir()
    y expresiones aritméticas básicas dentro del bloque inicio.
    """
    output_fn("=== Ejecución Javaguayo ===\n")

    errores = validar_sintaxis(codigo)
    if any(e.startswith("[") and "Error" in e for e in errores):
        for e in errores:
            output_fn(e + "\n")
        output_fn("\n[Ejecución abortada por errores sintácticos]\n")
        return

    tokens = tokenizar(codigo)
    clases = _construir_clases(tokens)
    bloque_tokens = _buscar_inicio_clase(clases)
    if bloque_tokens is None:
        bloque_tokens = _buscar_bloque_inicio_tokens(tokens)
    if bloque_tokens is None:
        output_fn("[Error] No se encontró el bloque 'inicio()'.\n")
        return

    # Variables del entorno (solo tipos primitivos)
    entorno = {}
    _ejecutar_bloque(bloque_tokens, entorno, output_fn, clases)

    output_fn("\n=== Fin de ejecución ===\n")


def evaluar_expr(expr, entorno, output_fn):
    """Evalúa expresiones aritméticas y de cadenas básicas."""
    # Reemplazar variables conocidas
    def repl_var(m):
        nombre = m.group(0)
        encontrado, v = _get_var(entorno, nombre)
        if encontrado:
            if isinstance(v, str):
                return repr(v)
            return str(v)
        return nombre

    expr_eval = re.sub(r"\b[a-z][a-zA-Z0-9_]*\b", repl_var, expr)

    # Reemplazar operadores lógicos
    expr_eval = re.sub(r"\band\b", " and ", expr_eval)
    expr_eval = re.sub(r"\bor\b", " or ", expr_eval)
    expr_eval = expr_eval.replace("true", "True").replace("false", "False")
    expr_eval = expr_eval.replace("null", "None")

    try:
        resultado = eval(expr_eval, {"__builtins__": {}}, {})
        return resultado
    except Exception as e:
        return f"[Error al evaluar '{expr}': {e}]"


# ──────────────────────────────────────────────
#  CÓDIGO DE EJEMPLO
# ──────────────────────────────────────────────

CODIGO_EJEMPLO = """\
// Ejemplo de programa en Javaguayo
// Grupo 03 - FCEQyN UNaM - 2026

clase Calculadora {

    int resultado;

    int sumar(int a, int b) {
        retornar a + b;
    }

    void inicio() {
        int x = 10;
        int y = 25;
        int suma = x + y;
        decimal pi = 3.14;
        string mensaje = "Hola desde Javaguayo";
        bool activo = true;

        imprimir("=== Calculadora Javaguayo ===");
        imprimir(mensaje);
        imprimir(suma);
        imprimir(pi);
        imprimir(activo);
    }
}
"""

# ──────────────────────────────────────────────
#  INTERFAZ GRÁFICA
# ──────────────────────────────────────────────

class JavaguayoIDE:
    COLORES = {
        "bg":          "#1E1E2E",
        "panel":       "#181825",
        "barra":       "#11111B",
        "texto":       "#CDD6F4",
        "cursor":      "#F5C2E7",
        "lineas_bg":   "#181825",
        "lineas_fg":   "#585B70",
        "res":         "#CBA6F7",   # palabras reservadas
        "tipo":        "#89B4FA",   # tipos
        "literal":     "#A6E3A1",   # literales
        "str_color":   "#A6E3A1",
        "comentario":  "#585B70",
        "operador":    "#89DCEB",
        "nombre_cls":  "#FAB387",
        "identificad": "#CDD6F4",
        "btn_run":     "#A6E3A1",
        "btn_anl":     "#89B4FA",
        "btn_open":    "#CBA6F7",
        "btn_save":    "#F38BA8",
        "btn_clear":   "#FAB387",
        "btn_fg":      "#1E1E2E",
        "error":       "#F38BA8",
        "ok":          "#A6E3A1",
        "linea_act":   "#313244",
    }

    FUENTE_EDITOR = ("Consolas", 12)
    FUENTE_SALIDA = ("Consolas", 11)
    FUENTE_TITULO = ("Segoe UI", 10, "bold")

    def __init__(self, root):
        self.root = root
        self.root.title("Javaguayo IDE  |  Grupo 03 - FCEQyN UNaM 2026")
        self.root.configure(bg=self.COLORES["bg"])
        self.root.geometry("1200x750")
        self.archivo_actual = None
        self._construir_ui()
        self._cargar_ejemplo()

    # ── CONSTRUCCIÓN DE LA UI ──

    def _construir_ui(self):
        c = self.COLORES

        # ── Barra superior ──
        barra = tk.Frame(self.root, bg=c["barra"], height=44, pady=6)
        barra.pack(fill="x", side="top")

        # Logo
        tk.Label(barra, text="⟨/⟩ Javaguayo IDE",
                 bg=c["barra"], fg=c["res"],
                 font=("Segoe UI", 13, "bold")).pack(side="left", padx=14)

        # Botones
        btns = [
            ("▶  Ejecutar",   c["btn_run"],   self.ejecutar_codigo),
            ("🔍 Analizar",   c["btn_anl"],   self.analizar_codigo),
            ("📂 Abrir",      c["btn_open"],  self.abrir_archivo),
            ("💾 Guardar",    c["btn_save"],  self.guardar_archivo),
            ("🗑  Limpiar",   c["btn_clear"], self.limpiar_todo),
            ("📋 Ejemplo",    c["tipo"],      self._cargar_ejemplo),
        ]
        for texto, color, cmd in btns:
            tk.Button(
                barra, text=texto, bg=color, fg=c["btn_fg"],
                font=self.FUENTE_TITULO, relief="flat",
                padx=10, pady=2, cursor="hand2",
                activebackground=color, command=cmd
            ).pack(side="left", padx=4)

        # Archivo actual
        self.lbl_archivo = tk.Label(
            barra, text="Sin archivo", bg=c["barra"], fg=c["lineas_fg"],
            font=("Segoe UI", 9))
        self.lbl_archivo.pack(side="right", padx=12)

        # ── Panel principal (editor + salida) ──
        panel = tk.Frame(self.root, bg=c["bg"])
        panel.pack(fill="both", expand=True, padx=0, pady=0)

        # PanedWindow horizontal
        paned = tk.PanedWindow(panel, orient="horizontal",
                               bg=c["barra"], sashwidth=4, relief="flat")
        paned.pack(fill="both", expand=True)

        # ── Panel izquierdo: editor ──
        frame_ed = tk.Frame(paned, bg=c["panel"])
        paned.add(frame_ed, width=720)

        tk.Label(frame_ed, text="  EDITOR  —  Javaguayo",
                 bg=c["barra"], fg=c["res"],
                 font=("Segoe UI", 9, "bold"),
                 anchor="w").pack(fill="x")

        ed_cont = tk.Frame(frame_ed, bg=c["panel"])
        ed_cont.pack(fill="both", expand=True)

        # Números de línea
        self.lineas = tk.Text(
            ed_cont, width=4, bg=c["lineas_bg"], fg=c["lineas_fg"],
            font=self.FUENTE_EDITOR, state="disabled",
            relief="flat", bd=0, highlightthickness=0,
            padx=4, pady=6, cursor="arrow"
        )
        self.lineas.pack(side="left", fill="y")

        # Editor principal
        self.editor = tk.Text(
            ed_cont, bg=c["panel"], fg=c["texto"],
            insertbackground=c["cursor"],
            font=self.FUENTE_EDITOR, relief="flat", bd=0,
            highlightthickness=0, padx=10, pady=6,
            undo=True, wrap="none",
            selectbackground="#313244"
        )
        self.editor.pack(side="left", fill="both", expand=True)

        scroll_ed = ttk.Scrollbar(ed_cont, command=self._scroll_sync)
        scroll_ed.pack(side="right", fill="y")
        self.editor.config(yscrollcommand=scroll_ed.set)

        # Scrollbar horizontal
        scroll_h = ttk.Scrollbar(frame_ed, orient="horizontal",
                                 command=self.editor.xview)
        scroll_h.pack(fill="x")
        self.editor.config(xscrollcommand=scroll_h.set)

        # Barra de estado
        self.lbl_status = tk.Label(
            frame_ed, text="Listo", bg=c["barra"], fg=c["ok"],
            font=("Segoe UI", 9), anchor="w", padx=8)
        self.lbl_status.pack(fill="x")

        # ── Panel derecho: pestañas ──
        frame_der = tk.Frame(paned, bg=c["panel"])
        paned.add(frame_der, width=460)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.TNotebook", background=c["barra"], borderwidth=0)
        style.configure("Dark.TNotebook.Tab",
                        background=c["barra"], foreground=c["lineas_fg"],
                        padding=[10, 4], font=("Segoe UI", 9, "bold"))
        style.map("Dark.TNotebook.Tab",
                  background=[("selected", c["panel"])],
                  foreground=[("selected", c["texto"])])

        nb = ttk.Notebook(frame_der, style="Dark.TNotebook")
        nb.pack(fill="both", expand=True)

        # Pestaña: Salida
        tab_sal = tk.Frame(nb, bg=c["panel"])
        nb.add(tab_sal, text="  Salida  ")
        self.salida = scrolledtext.ScrolledText(
            tab_sal, bg=c["panel"], fg=c["ok"],
            font=self.FUENTE_SALIDA, relief="flat", bd=0,
            state="disabled", padx=10, pady=6,
            highlightthickness=0
        )
        self.salida.pack(fill="both", expand=True)

        # Pestaña: Tokens
        tab_tok = tk.Frame(nb, bg=c["panel"])
        nb.add(tab_tok, text="  Tokens  ")

        cols = ("Línea", "Col", "Tipo", "Valor")
        self.tabla_tokens = ttk.Treeview(
            tab_tok, columns=cols, show="headings", height=30)
        style.configure("Treeview",
                        background=c["panel"], foreground=c["texto"],
                        fieldbackground=c["panel"], rowheight=22,
                        font=("Consolas", 10))
        style.configure("Treeview.Heading",
                        background=c["barra"], foreground=c["res"],
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", "#313244")])

        ancho = {"Línea": 55, "Col": 50, "Tipo": 160, "Valor": 180}
        for col in cols:
            self.tabla_tokens.heading(col, text=col)
            self.tabla_tokens.column(col, width=ancho[col], anchor="center")
        sb_tok = ttk.Scrollbar(tab_tok, command=self.tabla_tokens.yview)
        self.tabla_tokens.configure(yscrollcommand=sb_tok.set)
        sb_tok.pack(side="right", fill="y")
        self.tabla_tokens.pack(fill="both", expand=True)

        # Pestaña: Errores
        tab_err = tk.Frame(nb, bg=c["panel"])
        nb.add(tab_err, text="  Errores  ")
        self.errores = scrolledtext.ScrolledText(
            tab_err, bg=c["panel"], fg=c["error"],
            font=self.FUENTE_SALIDA, relief="flat", bd=0,
            state="disabled", padx=10, pady=6,
            highlightthickness=0
        )
        self.errores.pack(fill="both", expand=True)

        # Eventos
        self.editor.bind("<KeyRelease>", self._on_key)
        self.editor.bind("<ButtonRelease>", self._on_key)
        self.editor.bind("<MouseWheel>", self._on_scroll)
        self._definir_tags()
        self._actualizar_lineas()

    def _definir_tags(self):
        c = self.COLORES
        self.editor.tag_configure("res",        foreground=c["res"],       font=("Consolas", 12, "bold"))
        self.editor.tag_configure("tipo",       foreground=c["tipo"],      font=("Consolas", 12, "bold"))
        self.editor.tag_configure("literal",    foreground=c["literal"])
        self.editor.tag_configure("str_color",  foreground=c["str_color"])
        self.editor.tag_configure("comentario", foreground=c["comentario"], font=("Consolas", 12, "italic"))
        self.editor.tag_configure("operador",   foreground=c["operador"])
        self.editor.tag_configure("nombre_cls", foreground=c["nombre_cls"])
        self.editor.tag_configure("linea_act",  background=c["linea_act"])

    # ── SINCRONIZACIÓN ──

    def _scroll_sync(self, *args):
        self.editor.yview(*args)
        self.lineas.yview(*args)

    def _on_scroll(self, event=None):
        self.lineas.yview_moveto(self.editor.yview()[0])

    def _on_key(self, event=None):
        self._actualizar_lineas()
        self._resaltar_sintaxis()
        self._resaltar_linea_actual()

    def _actualizar_lineas(self):
        contenido = self.editor.get("1.0", "end-1c")
        num_lineas = contenido.count("\n") + 1
        self.lineas.config(state="normal")
        self.lineas.delete("1.0", "end")
        self.lineas.insert("1.0", "\n".join(str(i) for i in range(1, num_lineas + 1)))
        self.lineas.config(state="disabled")

    def _resaltar_linea_actual(self):
        self.editor.tag_remove("linea_act", "1.0", "end")
        linea = self.editor.index("insert").split(".")[0]
        self.editor.tag_add("linea_act", f"{linea}.0", f"{linea}.end+1c")

    def _resaltar_sintaxis(self):
        """Resaltado de sintaxis por expresiones regulares."""
        for tag in ["res", "tipo", "literal", "str_color", "comentario",
                    "operador", "nombre_cls"]:
            self.editor.tag_remove(tag, "1.0", "end")

        codigo = self.editor.get("1.0", "end-1c")

        reglas = [
            ("comentario", r"//[^\n]*"),
            ("str_color",  r'"[^"\n]*"'),
            ("str_color",  r"'[^'\n]'"),
            ("res",        r"\b(?:clase|retornar|si|sino|mientras|repetir|nuevo|imprimir|inicio|and|or)\b"),
            ("tipo",       r"\b(?:int|decimal|string|bool|char|objeto|void|null|true|false)\b"),
            ("literal",    r"\b-?\d+\.?\d*\b"),
            ("nombre_cls", r"\b[A-Z][a-zA-Z0-9]*\b"),
            ("operador",   r"==|!=|<=|>=|[+\-*/=<>]"),
        ]

        for tag, patron in reglas:
            for m in re.finditer(patron, codigo):
                inicio = f"1.0+{m.start()}c"
                fin    = f"1.0+{m.end()}c"
                self.editor.tag_add(tag, inicio, fin)

    # ── ACCIONES ──

    def ejecutar_codigo(self):
        codigo = self.editor.get("1.0", "end-1c")
        self._limpiar_salida()
        ejecutar(codigo, self._salida_append)
        self.lbl_status.config(text="Ejecutado", fg=self.COLORES["ok"])

    def analizar_codigo(self):
        codigo = self.editor.get("1.0", "end-1c")

        # Tabla de tokens
        for item in self.tabla_tokens.get_children():
            self.tabla_tokens.delete(item)
        tabla = analizar_lexico(codigo)
        for linea, col, tipo, valor in tabla:
            tag = ""
            if tipo == "COMENTARIO":
                tag = "comentario"
            elif tipo in ("PALABRA_RES", "AND_OR"):
                tag = "keyword"
            self.tabla_tokens.insert("", "end", values=(linea, col, tipo, valor))

        # Errores
        errores = validar_sintaxis(codigo)
        self.errores.config(state="normal")
        self.errores.delete("1.0", "end")
        if errores:
            for e in errores:
                self.errores.insert("end", e + "\n")
            self.lbl_status.config(
                text=f"{len(errores)} problema(s) encontrado(s)",
                fg=self.COLORES["error"])
        else:
            self.errores.insert("end", "✔ Sin errores sintácticos detectados.\n")
            self.lbl_status.config(text="Análisis OK", fg=self.COLORES["ok"])
        self.errores.config(state="disabled")

    def abrir_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Abrir archivo Javaguayo",
            filetypes=[("Javaguayo", "*.jvg"), ("Texto", "*.txt"), ("Todos", "*.*")]
        )
        if ruta:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", contenido)
            self.archivo_actual = ruta
            self.lbl_archivo.config(text=os.path.basename(ruta))
            self._on_key()

    def guardar_archivo(self):
        if not self.archivo_actual:
            ruta = filedialog.asksaveasfilename(
                title="Guardar archivo Javaguayo",
                defaultextension=".jvg",
                filetypes=[("Javaguayo", "*.jvg"), ("Texto", "*.txt")]
            )
            if not ruta:
                return
            self.archivo_actual = ruta
        with open(self.archivo_actual, "w", encoding="utf-8") as f:
            f.write(self.editor.get("1.0", "end-1c"))
        self.lbl_archivo.config(text=os.path.basename(self.archivo_actual))
        self.lbl_status.config(text="Guardado", fg=self.COLORES["ok"])

    def limpiar_todo(self):
        self.editor.delete("1.0", "end")
        self._limpiar_salida()
        for item in self.tabla_tokens.get_children():
            self.tabla_tokens.delete(item)
        self.errores.config(state="normal")
        self.errores.delete("1.0", "end")
        self.errores.config(state="disabled")
        self.lbl_status.config(text="Listo", fg=self.COLORES["ok"])
        self._actualizar_lineas()

    def _cargar_ejemplo(self):
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", CODIGO_EJEMPLO)
        self._on_key()
        self.lbl_status.config(text="Ejemplo cargado", fg=self.COLORES["ok"])

    def _limpiar_salida(self):
        self.salida.config(state="normal")
        self.salida.delete("1.0", "end")
        self.salida.config(state="disabled")

    def _salida_append(self, texto):
        self.salida.config(state="normal")
        self.salida.insert("end", texto)
        self.salida.see("end")
        self.salida.config(state="disabled")


# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app = JavaguayoIDE(root)
    root.mainloop()
