# 2026-TC---G-03---Trabajo-Integrador

# Javaguayo IDE

Mini IDE para el lenguaje de programación **Javaguayo**, desarrollado para la cátedra Teoría de la Computación.


**Grupo 03:** 
- Dos Santos Axel Joan
- Mittelstedt Gabriel Leonardo
- Escalada Leandro Ezequiel
---

## Tabla de contenidos

1. [¿Qué es Javaguayo?](#qué-es-javaguayo)
2. [Arquitectura del proyecto](#arquitectura-del-proyecto)
3. [Tokens del lenguaje](#tokens-del-lenguaje)
4. [Requisitos](#requisitos)
5. [Ejecución](#ejecución)
6. [Funcionalidades del IDE](#funcionalidades-del-ide)
7. [Comandos de generación y prueba](#comandos-de-generación-y-prueba)
8. [Orden completo recomendado](#orden-completo-recomendado)

---

## ¿Qué es Javaguayo?

Javaguayo es un mini-lenguaje orientado a objetos con sintaxis inspirada en Java, diseñado con fines académicos para explorar los fundamentos formales de los lenguajes de programación:

- **Análisis léxico** mediante autómatas finitos deterministas (AFD)
- **Análisis sintáctico** mediante gramáticas libres de contexto (GLC)
- **Interpretación** del bloque `inicio()` con soporte a operaciones básicas e impresión por pantalla

Los archivos fuente Javaguayo usan la extensión **`.jvg`**.

---

## Arquitectura del proyecto

```text
2026-TC---G-03---Trabajo-Integrador/
│
├── main.py                    # Punto de entrada del IDE
├── requirements.txt           # Dependencias Python (solo stdlib)
│
├── ide/                       # Interfaz gráfica (Python / Tkinter)
│   ├── app.py                 # Ventana principal y lógica del IDE
│   ├── editor.py              # Widget de editor de código
│   ├── results_panel.py       # Panel de salida / tokens / errores
│   ├── analyzer.py            # Puente Python ↔ analizador Java
│   └── theme.py               # Paleta de colores y estilos
│
├── analizador_java/           # Núcleo del analizador (Java)
│   ├── src/
│   │   ├── Lexer.flex         # Especificación léxica (JFlex)
│   │   ├── Parser.cup         # Gramática sintáctica (Java CUP)
│   │   ├── IDEAnalyzer.java   # Interfaz de análisis para el IDE
│   │   └── Main.java          # Punto de entrada CLI del analizador
│   ├── generated/             # Código Java generado (Lexer.java, parser.java, sym.java)
│   ├── bin/                   # Clases compiladas (.class)
│   └── lib/
│       ├── jflex.jar
│       ├── java-cup.jar
│       └── java-cup-runtime.jar
│
└── ejemplos/                  # Programas .jvg de prueba
    ├── correcto_01.jvg … correcto_03.jvg
    ├── error_lexico_01.jvg … error_lexico_03.jvg
    └── error_sintactico_01.jvg … error_sintactico_03.jvg
```

---

## Tokens del lenguaje

| Categoría | Ejemplos |
|---|---|
| Palabras reservadas | `clase`, `si`, `sino`, `mientras`, `repetir`, `nuevo`, `imprimir`, `retornar`, `inicio` |
| Tipos de dato | `int`, `decimal`, `string`, `bool`, `char`, `objeto`, `void` |
| Operadores matemáticos | `+`, `-`, `*`, `/` |
| Operadores relacionales | `==`, `!=`, `<`, `>`, `<=`, `>=` |
| Operadores lógicos | `and`, `or` |
| Operador de asignación | `=` |
| Literales | `42`, `-3.14`, `"texto"`, `'c'`, `true`, `false`, `null` |
| Nombre de clase | `MiClase`, `Calculadora`, `Animal` _(inicia con mayúscula)_ |
| Identificadores | `miMetodo`, `miVariable`, `x` _(inicia con minúscula)_ |
| Símbolos especiales | `(`, `)`, `{`, `}`, `;`, `,`, `.` |
| Comentarios | `// comentario de línea` _(ignorados por el analizador)_ |

---

## Requisitos

### Software necesario

| Herramienta | Versión mínima |
|---|---|
| Python | 3.x (Tkinter incluido) |
| Java JDK | 11 o superior |
| JFlex | 1.9.1 |
| Java CUP | v0.11b 20160615 |

> **Nota:** Python no requiere paquetes externos. La interfaz utiliza únicamente `tkinter`, que viene incluido en la instalación estándar de Python.

### Librerías Java (`.jar`)

Las librerías del analizador se encuentran en `analizador_java/lib/`:

```text
analizador_java/lib/
├── jflex.jar
├── java-cup.jar
└── java-cup-runtime.jar
```

---

## Ejecución

Antes de ejecutar el IDE, asegurarse de haber completado los pasos de [Comandos de generación y prueba](#comandos-de-generación-y-prueba) al menos una vez (generar y compilar el analizador Java).

Una vez que el analizador está compilado, iniciar el IDE con:

```powershell
python main.py
```

Esto abre la ventana principal del IDE Javaguayo. Desde allí se puede:

- Escribir código Javaguayo directamente en el editor
- Abrir un archivo `.jvg` existente con el botón **Abrir**
- Cargar un ejemplo predefinido con el botón **Ejemplo**
- Ejecutar o analizar el código con los botones de la barra de herramientas

---

## Funcionalidades del IDE

### Barra de herramientas

| Botón | Acción |
|---|---|
| **Ejecutar** | Interpreta el bloque `inicio()` y muestra la salida |
| **Analizar** | Corre el analizador léxico y muestra la tabla de tokens |
| **Abrir** | Carga un archivo `.jvg` desde disco |
| **Guardar** | Guarda el código actual en un archivo `.jvg` |
| **Limpiar** | Limpia el editor y todos los paneles |
| **Ejemplo** | Carga un programa de ejemplo predefinido |

### Pestañas del panel derecho

| Pestaña | Contenido |
|---|---|
| **Salida** | Resultado de la ejecución del programa |
| **Tokens** | Tabla con cada token reconocido: línea, columna, tipo y valor |
| **Errores** | Lista de errores léxicos y sintácticos detectados |

---

## Comandos de generación y prueba

Todos los comandos deben ejecutarse desde la raíz del proyecto.

### Instalación de Java CUP

Desde la raíz del proyecto se descargaron las dependencias de CUP con PowerShell:

```powershell
Invoke-WebRequest -Uri "https://repo1.maven.org/maven2/com/github/vbmacher/java-cup/11b-20160615-3/java-cup-11b-20160615-3.jar" -OutFile "analizador_java\lib\java-cup.jar"

Invoke-WebRequest -Uri "https://repo1.maven.org/maven2/com/github/vbmacher/java-cup-runtime/11b-20160615-3/java-cup-runtime-11b-20160615-3.jar" -OutFile "analizador_java\lib\java-cup-runtime.jar"
```

### 1. Verificar JFlex

```powershell
java -jar analizador_java\lib\jflex.jar --version
```

Salida esperada:

```text
This is JFlex 1.9.1
```

### 2. Verificar CUP

```powershell
java -cp "analizador_java\lib\java-cup.jar;analizador_java\lib\java-cup-runtime.jar" java_cup.Main -version
```

Salida esperada:

```text
CUP v0.11b 20160615
```

### 3. Generar el analizador sintáctico con CUP

```powershell
java -cp "analizador_java\lib\java-cup.jar;analizador_java\lib\java-cup-runtime.jar" java_cup.Main -parser parser -symbols sym -destdir analizador_java\generated analizador_java\src\Parser.cup
```

Este comando genera:

```text
analizador_java/generated/parser.java
analizador_java/generated/sym.java
```

### 4. Generar el analizador léxico con JFlex

```powershell
java -jar analizador_java\lib\jflex.jar -d analizador_java\generated analizador_java\src\Lexer.flex
```

Este comando genera:

```text
analizador_java/generated/Lexer.java
```

### 5. Compilar los archivos Java

```powershell
javac -encoding UTF-8 -cp "analizador_java\lib\java-cup-runtime.jar;analizador_java\generated;analizador_java\src" -d analizador_java\bin analizador_java\src\Main.java analizador_java\generated\*.java
```

Este comando genera los archivos `.class` en:

```text
analizador_java/bin/
```

### 6. Ejecutar casos correctos

```powershell
java -cp "analizador_java\bin;analizador_java\lib\java-cup-runtime.jar" Main ejemplos\correcto_01.jvg

java -cp "analizador_java\bin;analizador_java\lib\java-cup-runtime.jar" Main ejemplos\correcto_02.jvg

java -cp "analizador_java\bin;analizador_java\lib\java-cup-runtime.jar" Main ejemplos\correcto_03.jvg
```

Salida esperada:

```text
Análisis sintáctico correcto.
```

### 7. Ejecutar casos con error léxico

```powershell
java -cp "analizador_java\bin;analizador_java\lib\java-cup-runtime.jar" Main ejemplos\error_lexico_01.jvg

java -cp "analizador_java\bin;analizador_java\lib\java-cup-runtime.jar" Main ejemplos\error_lexico_02.jvg

java -cp "analizador_java\bin;analizador_java\lib\java-cup-runtime.jar" Main ejemplos\error_lexico_03.jvg
```

Salida esperada:

```text
Error léxico ...
Análisis finalizado con errores.
```

### 8. Ejecutar casos con error sintáctico

```powershell
java -cp "analizador_java\bin;analizador_java\lib\java-cup-runtime.jar" Main ejemplos\error_sintactico_01.jvg

java -cp "analizador_java\bin;analizador_java\lib\java-cup-runtime.jar" Main ejemplos\error_sintactico_02.jvg

java -cp "analizador_java\bin;analizador_java\lib\java-cup-runtime.jar" Main ejemplos\error_sintactico_03.jvg
```

Salida esperada:

```text
Error sintáctico ...
Análisis finalizado con errores.
```

---

## Orden completo recomendado

Cada vez que se modifique `Lexer.flex` o `Parser.cup`, ejecutar:

```powershell
java -cp "analizador_java\lib\java-cup.jar;analizador_java\lib\java-cup-runtime.jar" java_cup.Main -parser parser -symbols sym -destdir analizador_java\generated analizador_java\src\Parser.cup

java -jar analizador_java\lib\jflex.jar -d analizador_java\generated analizador_java\src\Lexer.flex

javac -encoding UTF-8 -cp "analizador_java\lib\java-cup-runtime.jar;analizador_java\generated;analizador_java\src" -d analizador_java\bin analizador_java\src\Main.java analizador_java\generated\*.java
```

Luego probar con:

```powershell
java -cp "analizador_java\bin;analizador_java\lib\java-cup-runtime.jar" Main ejemplos\correcto_01.jvg
```
