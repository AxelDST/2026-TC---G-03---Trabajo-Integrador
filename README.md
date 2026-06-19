# 2026-TC---G-03---Trabajo-Integrador

# Javaguayo IDE

Mini IDE para el lenguaje de programación **Javaguayo**, desarrollado para la cátedra Teoría de la Computación.


**Grupo 03:** 
- Dos Santos Axel Joan
- Mittelstedt Gabriel Leonardo
- Escalada Leandro Ezequiel

---

## ¿Qué es Javaguayo?

Javaguayo es un mini-lenguaje orientado a objetos con sintaxis inspirada en Java,
diseñado con fines académicos para explorar los fundamentos formales de los
lenguajes de programación: análisis léxico, autómatas finitos y gramáticas libres
de contexto.


---


## Funcionalidades del IDE

| Función | Descripción |
|---|---|
| Ejecutar | Interpreta el bloque `inicio()` y muestra la salida |
| Analizar | Corre el analizador léxico y muestra la tabla de tokens |
|  Abrir | Carga un archivo `.jvg` desde disco |
| Guardar | Guarda el código actual en un archivo `.jvg` |
| Limpiar | Limpia el editor y todos los paneles |
| Ejemplo | Carga un programa de ejemplo predefinido |

### Pestañas del panel derecho

- **Salida** — resultado de la ejecución
- **Tokens** — tabla con cada token reconocido (línea, columna, tipo, valor)
- **Errores** — lista de errores léxicos y sintácticos detectados

---

## Tokens del lenguaje

| Categoría | Ejemplos |
|---|---|
| Palabras reservadas | `clase`, `si`, `sino`, `mientras`, `repetir`, `nuevo`, `imprimir`, `retornar`, `inicio` |
| Tipos de dato | `int`, `decimal`, `string`, `bool`, `char`, `objeto`, `void`, `null` |
| Operadores matemáticos | `+`, `-`, `*`, `/` |
| Operadores relacionales | `==`, `!=`, `<`, `>`, `<=`, `>=` |
| Operadores lógicos | `and`, `or` |
| Literales | `42`, `-3.14`, `"texto"`, `'c'`, `true`, `false` |
| Identificadores | `MiClase`, `miMetodo`, `miVariable` |

## Requisitos del proyecto

Para ejecutar el proyecto se requiere tener instalado:

* Python 3.x
* Java JDK
* JFlex 1.9.1
* Java CUP v0.11b 20160615

Las librerías utilizadas por el analizador se encuentran en:

```text
analizador_java/lib/
├── jflex.jar
├── java-cup.jar
└── java-cup-runtime.jar
```

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

