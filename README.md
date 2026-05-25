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

