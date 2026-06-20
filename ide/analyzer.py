"""
analyzer.py — Bridge Python ↔ Java para el Mini IDE Javaguayo.

Invoca IDEAnalyzer.class vía subprocess, parsea el JSON resultante
y devuelve un objeto AnalysisResult con tokens, errores y estadísticas.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# ── Rutas del proyecto ─────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent.parent
BIN_DIR     = BASE_DIR / "analizador_java" / "bin"
LIB_DIR     = BASE_DIR / "analizador_java" / "lib"
SRC_DIR     = BASE_DIR / "analizador_java" / "src"
GEN_DIR     = BASE_DIR / "analizador_java" / "generated"
RUNTIME_JAR = LIB_DIR / "java-cup-runtime.jar"
JFLEX_JAR   = LIB_DIR / "jflex.jar"
CUP_JAR     = LIB_DIR / "java-cup.jar"

# Separador de classpath según SO
_SEP  = ";" if sys.platform == "win32" else ":"
CLASSPATH = f"{BIN_DIR}{_SEP}{RUNTIME_JAR}"


# ── Modelo de resultados ───────────────────────────────────────────
@dataclass
class TokenInfo:
    tipo: str
    valor: str
    linea: int
    columna: int


@dataclass
class AnalysisResult:
    tokens:       List[TokenInfo]        = field(default_factory=list)
    total_tokens: int                    = 0
    lex_errors:   List[str]              = field(default_factory=list)
    sint_errors:  List[str]             = field(default_factory=list)
    estado:       str                    = "OK"  # OK | ERROR_LEXICO | ERROR_SINTACTICO | ERROR_AMBOS
    elapsed:      float                  = 0.0
    raw_output:   Optional[str]          = None

    @property
    def is_ok(self) -> bool:
        return self.estado == "OK"

    @property
    def has_lex_errors(self) -> bool:
        return bool(self.lex_errors)

    @property
    def has_sint_errors(self) -> bool:
        return bool(self.sint_errors)

    @property
    def total_errors(self) -> int:
        return len(self.lex_errors) + len(self.sint_errors)


# ── Función principal de análisis ─────────────────────────────────
def analyze_code(code: str, lexico_only: bool = False) -> AnalysisResult:
    """
    Analiza el código Javaguayo dado.

    Escribe el código en un archivo temporal .jvg, invoca IDEAnalyzer.class
    y parsea el JSON resultante.

    Args:
        code:        Código fuente en Javaguayo.
        lexico_only: Si True, solo ejecuta el análisis léxico.

    Returns:
        AnalysisResult con tokens, errores y estadísticas.

    Raises:
        RuntimeError: Si Java no está disponible o el analizador falla.
    """
    # Verificar que IDEAnalyzer.class existe; si no, intentar compilar
    ide_class = BIN_DIR / "IDEAnalyzer.class"
    if not ide_class.exists():
        _auto_compile_ide_analyzer()

    # Escribir código en archivo temporal
    tmp_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jvg", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            tmp_path = f.name

        # Construir comando
        cmd = ["java", "-cp", CLASSPATH, "IDEAnalyzer", tmp_path]
        if lexico_only:
            cmd.append("--lexico")

        t0 = time.perf_counter()
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            cwd=str(BASE_DIR),
        )
        elapsed = time.perf_counter() - t0

        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()

        if not stdout:
            detail = f"\nstderr: {stderr[:600]}" if stderr else ""
            raise RuntimeError(
                f"El analizador no produjo ninguna salida.{detail}\n"
                "Verificá que Java esté instalado y que el analizador esté compilado."
            )

        raw_data = json.loads(stdout)
        return _parse_result(raw_data, elapsed, stdout)

    except FileNotFoundError:
        raise RuntimeError(
            "No se encontró el comando 'java'.\n"
            "Asegurate de que Java JDK esté instalado y en el PATH del sistema."
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("El análisis tardó demasiado (timeout 30s). Verificá el código.")
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"El analizador devolvió una respuesta inválida:\n{exc}\n"
            f"Primeras 500 chars: {stdout[:500]}"
        )
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def _parse_result(data: dict, elapsed: float, raw: str) -> AnalysisResult:
    tokens = [
        TokenInfo(
            tipo    = t.get("tipo", "?"),
            valor   = t.get("valor", ""),
            linea   = int(t.get("linea", 0)),
            columna = int(t.get("columna", 0)),
        )
        for t in data.get("tokens", [])
    ]
    return AnalysisResult(
        tokens       = tokens,
        total_tokens = data.get("totalTokens", len(tokens)),
        lex_errors   = data.get("erroresLexicos", []),
        sint_errors  = data.get("erroresSintacticos", []),
        estado       = data.get("estado", "OK"),
        elapsed      = elapsed,
        raw_output   = raw,
    )


def _auto_compile_ide_analyzer() -> None:
    """Intenta compilar IDEAnalyzer.java automáticamente."""
    src = SRC_DIR / "IDEAnalyzer.java"
    if not src.exists():
        raise RuntimeError(
            "No se encontró IDEAnalyzer.class ni IDEAnalyzer.java.\n"
            "El archivo del analizador del IDE está faltando."
        )
    result = subprocess.run(
        [
            "javac", "-encoding", "UTF-8",
            "-cp", f"{BIN_DIR}{_SEP}{RUNTIME_JAR}",
            "-d", str(BIN_DIR),
            str(src),
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Falló la compilación automática:\n{result.stderr}")


# ── Recompilación completa del analizador ─────────────────────────
def compile_analyzer(progress_callback=None) -> List[str]:
    """
    Recompila el analizador léxico y sintáctico completo.

    Pasos:
      1. JFlex sobre Lexer.flex → Lexer.java en generated/
      2. CUP  sobre Parser.cup  → parser.java, sym.java en generated/
      3. javac sobre todos los .java → .class en bin/

    Args:
        progress_callback: Función opcional fn(str) llamada con mensajes de progreso.

    Returns:
        Lista de mensajes de resultado.
    """
    results: List[str] = []
    _log = progress_callback or (lambda m: None)

    def run(cmd: List[str], desc: str) -> None:
        _log(f"⚙️  {desc}...")
        proc = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(BASE_DIR)
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Falló: {desc}\n{proc.stderr.strip()}")
        results.append(f"✅ {desc}")
        _log(f"✅ {desc}")

    # 1. JFlex
    run(
        ["java", "-jar", str(JFLEX_JAR), "--outdir", str(GEN_DIR), str(SRC_DIR / "Lexer.flex")],
        "JFlex — generando Lexer.java",
    )

    # 2. CUP
    run(
        [
            "java", "-jar", str(CUP_JAR),
            "-parser", "parser", "-symbols", "sym",
            "-destdir", str(GEN_DIR),
            str(SRC_DIR / "Parser.cup"),
        ],
        "CUP — generando parser.java y sym.java",
    )

    # 3. javac
    java_files = sorted(GEN_DIR.glob("*.java")) + sorted(SRC_DIR.glob("*.java"))
    run(
        [
            "javac", "-encoding", "UTF-8",
            "-cp", str(RUNTIME_JAR),
            "-d", str(BIN_DIR),
        ] + [str(f) for f in java_files],
        "javac — compilando todas las clases",
    )

    return results


# ── Verificación de entorno ────────────────────────────────────────
def check_java() -> tuple[bool, str]:
    """Verifica si Java está disponible. Retorna (ok, mensaje)."""
    try:
        proc = subprocess.run(
            ["java", "-version"],
            capture_output=True, text=True, timeout=5
        )
        version_line = (proc.stderr or proc.stdout).split("\n")[0].strip()
        return True, version_line
    except FileNotFoundError:
        return False, "Java no encontrado en el PATH"
    except Exception as e:
        return False, str(e)


def check_analyzer() -> tuple[bool, str]:
    """Verifica si IDEAnalyzer.class está compilado."""
    cls = BIN_DIR / "IDEAnalyzer.class"
    if cls.exists():
        return True, f"IDEAnalyzer.class encontrado en {BIN_DIR}"
    return False, f"IDEAnalyzer.class no encontrado en {BIN_DIR}"
