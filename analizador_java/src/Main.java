import java.io.FileReader;

public class Main {
    public static void main(String[] args) {
        if (args.length == 0) {
            System.err.println("Uso: java Main <archivo.jvg>");
            return;
        }

        try {
            FileReader reader = new FileReader(args[0]);
            Lexer lexer = new Lexer(reader);
            parser sintactico = new parser(lexer);

            sintactico.parse();

            if (sintactico.huboErrores()) {
                System.out.println("Análisis finalizado con errores.");
            } else {
                System.out.println("Análisis sintáctico correcto.");
            }

        } catch (Exception e) {
            System.err.println("Error durante el análisis:");
            System.err.println(e.getMessage());
        }
    }
}