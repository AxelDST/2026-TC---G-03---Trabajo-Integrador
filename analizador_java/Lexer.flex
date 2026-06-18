import java_cup.runtime.*;
import java.util.ArrayList;
import java.util.List;

%%

%public
%class Lexer
%unicode
%cup
%line
%column

%{
    // Lista prevista para almacenar errores léxicos y permitir su consulta desde la interfaz.
    private List<String> listaErrores = new ArrayList<>();

    public List<String> getErrores() {
        return listaErrores;
    }

    private Symbol simbolo(int tipo) {
        return new Symbol(tipo, yyline + 1, yycolumn + 1, yytext());
    }

    private Symbol simbolo(int tipo, Object valor) {
        return new Symbol(tipo, yyline + 1, yycolumn + 1, valor);
    }

    private void registrarError(String mensaje) {
        String msg = "Error léxico (línea " + (yyline + 1) + ", columna " + (yycolumn + 1) + "): " + mensaje;
        listaErrores.add(msg);
        System.err.println(msg);
    }
%}

%eofval{
    return simbolo(sym.EOF);
%eofval}


/* ---- Macros léxicas ---- */
LineTerminator   = \r\n|\r|\n
Espacio          = [ \t\f]
WS               = ({Espacio}|{LineTerminator})+
Comentario       = "//"[^\r\n]*

Digito           = [0-9]
LIT_INT          = -?{Digito}+
LIT_DEC          = -?{Digito}+"."{Digito}+
LIT_STR          = \"([^\"\r\n])*\"
LIT_CHAR         = \'[^\'\r\n]\'

NombreClase      = [A-Z][a-zA-Z0-9]*
Identificador    = [a-z][a-zA-Z0-9_]*

%%

<YYINITIAL> {

    /* ---- Comentarios y espacios ---- */
    {Comentario}        { /* se descarta */ }
    {WS}                { /* se descarta */ }

    /* ---- Literal booleano y null ---- */
    "true"              { return simbolo(sym.LIT_BOOL, Boolean.TRUE); }
    "false"             { return simbolo(sym.LIT_BOOL, Boolean.FALSE); }
    "null"              { return simbolo(sym.LIT_NULL, null); }

    /* ---- Palabras reservadas ---- */
    "clase"             { return simbolo(sym.CLASE); }
    "retornar"          { return simbolo(sym.RETORNAR); }
    "si"                { return simbolo(sym.SI); }
    "sino"              { return simbolo(sym.SINO); }
    "mientras"          { return simbolo(sym.MIENTRAS); }
    "repetir"           { return simbolo(sym.REPETIR); }
    "nuevo"             { return simbolo(sym.NUEVO); }
    "imprimir"          { return simbolo(sym.IMPRIMIR); }
    "inicio"            { return simbolo(sym.INICIO); }

    /* ---- Tipos de dato ---- */
    "int"               { return simbolo(sym.INT); }
    "decimal"           { return simbolo(sym.DECIMAL); }
    "string"            { return simbolo(sym.STRING); }
    "objeto"            { return simbolo(sym.OBJETO); }
    "bool"              { return simbolo(sym.BOOL); }
    "void"              { return simbolo(sym.VOID); }
    "char"              { return simbolo(sym.CHAR); }

    /* ---- Operadores lógicos ---- */
    "and"               { return simbolo(sym.AND); }
    "or"                { return simbolo(sym.OR); }

    /* ---- Operadores relacionales ---- */
    "=="                { return simbolo(sym.IGUAL); }
    "!="                { return simbolo(sym.DISTINTO); }
    "<="                { return simbolo(sym.MENOR_IGUAL); }
    ">="                { return simbolo(sym.MAYOR_IGUAL); }
    "<"                 { return simbolo(sym.MENOR); }
    ">"                 { return simbolo(sym.MAYOR); }

    /* ---- Operador de asignación ---- */
    "="                 { return simbolo(sym.ASIGNAR); }

    /* ---- Operadores matemáticos ---- */
    "+"                 { return simbolo(sym.MAS); }
    "-"                 { return simbolo(sym.MENOS); }
    "*"                 { return simbolo(sym.POR); }
    "/"                 { return simbolo(sym.DIV); }

    /* ---- Símbolos especiales ---- */
    "("                 { return simbolo(sym.LPAREN); }
    ")"                 { return simbolo(sym.RPAREN); }
    "{"                 { return simbolo(sym.LBRACE); }
    "}"                 { return simbolo(sym.RBRACE); }
    ";"                 { return simbolo(sym.PUNTOYCOMA); }
    ","                 { return simbolo(sym.COMA); }
    "."                 { return simbolo(sym.PUNTO); }

    /* ---- Literales numéricos y de texto ---- */
    {LIT_DEC}           { return simbolo(sym.LIT_DEC, Double.parseDouble(yytext())); }
    {LIT_INT}           { return simbolo(sym.LIT_INT, Integer.parseInt(yytext())); }
    {LIT_STR}           { return simbolo(sym.LIT_STR, yytext().substring(1, yytext().length() - 1)); }
    {LIT_CHAR}          { return simbolo(sym.LIT_CHAR, Character.valueOf(yytext().charAt(1))); }

    /* ---- Identificadores ---- */
    {NombreClase}       { return simbolo(sym.NOMBRE_CLASE, yytext()); }
    {Identificador}     { return simbolo(sym.IDENTIFICADOR, yytext()); }

    /* ---- Captura de Errores Específicos ---- */
    \"                  { registrarError("cadena de texto sin comilla de cierre"); }
    \'                  { registrarError("carácter sin comilla de cierre"); }
    
    /* ---- Caracter no reconocido genérico ---- */
    [^]                 { registrarError("carácter no reconocido '" + yytext() + "'"); }
}