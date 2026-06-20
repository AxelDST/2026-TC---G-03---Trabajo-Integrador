import java.io.*;
import java.util.*;

/**
 * IDEAnalyzer — Analizador para el Mini IDE de Javaguayo.
 *
 * Ejecuta el analizador léxico y/o sintáctico sobre un archivo .jvg
 * y emite los resultados como JSON por stdout.
 *
 * Uso:
 *   java -cp bin;lib/java-cup-runtime.jar IDEAnalyzer <archivo.jvg>
 *   java -cp bin;lib/java-cup-runtime.jar IDEAnalyzer <archivo.jvg> --lexico
 */
public class IDEAnalyzer {

    public static void main(String[] args) {
        // Forzar UTF-8 en stdout
        try {
            System.setOut(new PrintStream(System.out, true, "UTF-8"));
        } catch (Exception ignored) {}

        if (args.length < 1) {
            System.out.println("{\"error\": \"No se especifico archivo\"}");
            return;
        }

        String archivo = args[0];
        boolean lexicoOnly = args.length > 1 && "--lexico".equals(args[1]);
        PrintStream originalErr = System.err;

        // ============================================================
        // PASO 1: Solo léxico — recolección de tokens y errores léxicos
        // ============================================================
        List<String[]> tokens = new ArrayList<>();
        List<String> erroresLex = new ArrayList<>();

        try {
            // Suprimir stderr directo del lexer (usamos listaErrores)
            System.setErr(new PrintStream(new ByteArrayOutputStream()));

            Lexer lexer1 = new Lexer(new FileReader(archivo));

            java_cup.runtime.Symbol tok;
            while (true) {
                tok = lexer1.next_token();
                if (tok.sym == sym.EOF) break;

                int id = tok.sym;
                String tipo = (id >= 0 && id < sym.terminalNames.length)
                    ? sym.terminalNames[id] : "TOKEN_" + id;
                String valor = (tok.value != null) ? tok.value.toString() : "";
                tokens.add(new String[]{
                    tipo,
                    valor,
                    String.valueOf(tok.left),
                    String.valueOf(tok.right)
                });
            }

            erroresLex.addAll(lexer1.getErrores());

        } catch (Exception e) {
            erroresLex.add("Error al ejecutar el analizador lexico: " +
                (e.getMessage() != null ? e.getMessage() : e.getClass().getName()));
        } finally {
            System.setErr(originalErr);
        }

        // ============================================================
        // PASO 2: Análisis sintáctico (si no es modo léxico)
        // ============================================================
        List<String> erroresSint = new ArrayList<>();
        boolean huboErroresSintax = false;

        if (!lexicoOnly) {
            ByteArrayOutputStream errBuf = new ByteArrayOutputStream();
            try {
                System.setErr(new PrintStream(errBuf, true, "UTF-8"));

                Lexer lexer2 = new Lexer(new FileReader(archivo));
                parser p = new parser(lexer2);
                p.parse();
                huboErroresSintax = p.huboErrores();

            } catch (Exception e) {
                huboErroresSintax = true;
                if (e.getMessage() != null && !e.getMessage().isEmpty()) {
                    erroresSint.add("Error sintactico no recuperable: " + e.getMessage());
                }
            } finally {
                System.setErr(originalErr);
            }

            // Extraer mensajes sintácticos del stderr capturado
            try {
                String errOutput = errBuf.toString("UTF-8");
                for (String line : errOutput.split("\\r?\\n")) {
                    line = line.trim();
                    if (!line.isEmpty() && (
                        line.contains("Error sint") ||
                        line.contains("Se recuper")
                    )) {
                        erroresSint.add(line);
                    }
                }
            } catch (Exception ignored) {}
        }

        // ============================================================
        // Determinar estado final
        // ============================================================
        boolean hasLex  = !erroresLex.isEmpty();
        boolean hasSint = huboErroresSintax || !erroresSint.isEmpty();

        String estado;
        if (!hasLex && !hasSint)       estado = "OK";
        else if (hasLex && hasSint)    estado = "ERROR_AMBOS";
        else if (hasLex)               estado = "ERROR_LEXICO";
        else                           estado = "ERROR_SINTACTICO";

        // ============================================================
        // Construir JSON de salida
        // ============================================================
        StringBuilder sb = new StringBuilder();
        sb.append("{\n");

        // tokens
        sb.append("  \"tokens\": [\n");
        for (int i = 0; i < tokens.size(); i++) {
            String[] t = tokens.get(i);
            sb.append("    {")
              .append("\"tipo\": ").append(js(t[0])).append(", ")
              .append("\"valor\": ").append(js(t[1])).append(", ")
              .append("\"linea\": ").append(t[2]).append(", ")
              .append("\"columna\": ").append(t[3])
              .append("}");
            if (i < tokens.size() - 1) sb.append(",");
            sb.append("\n");
        }
        sb.append("  ],\n");

        sb.append("  \"totalTokens\": ").append(tokens.size()).append(",\n");

        // errores léxicos
        sb.append("  \"erroresLexicos\": [\n");
        for (int i = 0; i < erroresLex.size(); i++) {
            sb.append("    ").append(js(erroresLex.get(i)));
            if (i < erroresLex.size() - 1) sb.append(",");
            sb.append("\n");
        }
        sb.append("  ],\n");

        // errores sintácticos
        sb.append("  \"erroresSintacticos\": [\n");
        for (int i = 0; i < erroresSint.size(); i++) {
            sb.append("    ").append(js(erroresSint.get(i)));
            if (i < erroresSint.size() - 1) sb.append(",");
            sb.append("\n");
        }
        sb.append("  ],\n");

        sb.append("  \"estado\": ").append(js(estado)).append("\n");
        sb.append("}");

        System.out.println(sb.toString());
    }

    /** Escapa un String para JSON. */
    private static String js(String s) {
        if (s == null) return "\"\"";
        StringBuilder sb = new StringBuilder("\"");
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '"':  sb.append("\\\""); break;
                case '\\': sb.append("\\\\"); break;
                case '\n': sb.append("\\n");  break;
                case '\r': sb.append("\\r");  break;
                case '\t': sb.append("\\t");  break;
                default:
                    if (c < 32) sb.append(String.format("\\u%04x", (int) c));
                    else        sb.append(c);
            }
        }
        sb.append("\"");
        return sb.toString();
    }
}
