%{
#include <string>
#include <vector>
#include "ast.h"
#include "parser.tab.h"
extern "C" int yylex();
%}
%option noyywrap
%%
[ \t\n\r]+ { /* ignore */ }
"(" { return LPAREN; }
")" { return RPAREN; }
"+" { return PLUS; }
"-" { return MINUS; }
"*" { return MULTIPLY; }
"/" { return DIVIDE; }
"mod" { return MODULUS; }
">" { return GREATER; }
"<" { return SMALLER; }
"=" { return EQUAL; }
"and" { return AND; }
"or" { return OR; }
"not" { return NOT; }
"define" { return DEFINE; }
"fun" { return FUN; }
"if" { return IF; }
"print-num" { return PRINT_NUM; }
"print-bool" { return PRINT_BOOL; }
"#t" { yylval.bval = true; return BOOL_VAL; }
"#f" { yylval.bval = false; return BOOL_VAL; }
0|[1-9][0-9]*|-[1-9][0-9]* { yylval.ival = std::stoi(yytext); return NUMBER; }
[a-z]([a-z0-9]|"-")* { yylval.sval = new std::string(yytext); return ID; }
. { /* ignore */ }
%%

