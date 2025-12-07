%{
#include <iostream>
#include <vector>
#include <string>
#include "ast.h"

extern "C" int yylex();
extern "C" int yyparse();
extern "C" FILE* yyin;
void yyerror(const char* s);

// Global list of statements to execute
std::vector<Node*> program;
%}

%union {
    int ival;
    bool bval;
    std::string* sval;
    Node* node;
    std::vector<Node*>* nodes;
    std::vector<std::string>* ids;
}

%token <ival> NUMBER
%token <bval> BOOL_VAL
%token <sval> ID
%token PRINT_NUM PRINT_BOOL
%token PLUS MINUS MULTIPLY DIVIDE MODULUS GREATER SMALLER EQUAL
%token AND OR NOT
%token DEFINE FUN IF
%token LPAREN RPAREN

%type <node> EXP STMT PRINT_STMT DEF_STMT NUM_OP LOGICAL_OP FUN_EXP FUN_CALL IF_EXP FUN_BODY
%type <nodes> EXPS PARAM DEF_STMTS
%type <ids> FUN_IDS IDS

%%

PROGRAM : STMTS
        ;

STMTS : STMT { program.push_back($1); }
      | STMTS STMT { program.push_back($2); }
      ;

STMT : EXP
     | DEF_STMT
     | PRINT_STMT
     ;

PRINT_STMT : LPAREN PRINT_NUM EXP RPAREN { $$ = new PrintNode(true, $3); }
           | LPAREN PRINT_BOOL EXP RPAREN { $$ = new PrintNode(false, $3); }
           ;

EXP : BOOL_VAL { $$ = new BoolNode($1); }
    | NUMBER { $$ = new NumberNode($1); }
    | ID { $$ = new VariableNode(*$1); delete $1; }
    | NUM_OP
    | LOGICAL_OP
    | FUN_EXP
    | FUN_CALL
    | IF_EXP
    ;

NUM_OP : LPAREN PLUS EXPS RPAREN { $$ = new BinaryOpNode("+", *$3); delete $3; }
       | LPAREN MINUS EXP EXP RPAREN { 
            std::vector<Node*> args; args.push_back($3); args.push_back($4);
            $$ = new BinaryOpNode("-", args); 
       }
       | LPAREN MULTIPLY EXPS RPAREN { $$ = new BinaryOpNode("*", *$3); delete $3; }
       | LPAREN DIVIDE EXP EXP RPAREN { 
            std::vector<Node*> args; args.push_back($3); args.push_back($4);
            $$ = new BinaryOpNode("/", args); 
       }
       | LPAREN MODULUS EXP EXP RPAREN { 
            std::vector<Node*> args; args.push_back($3); args.push_back($4);
            $$ = new BinaryOpNode("mod", args); 
       }
       | LPAREN GREATER EXP EXP RPAREN { 
            std::vector<Node*> args; args.push_back($3); args.push_back($4);
            $$ = new BinaryOpNode(">", args); 
       }
       | LPAREN SMALLER EXP EXP RPAREN { 
            std::vector<Node*> args; args.push_back($3); args.push_back($4);
            $$ = new BinaryOpNode("<", args); 
       }
       | LPAREN EQUAL EXPS RPAREN { $$ = new BinaryOpNode("=", *$3); delete $3; }
       ;

LOGICAL_OP : LPAREN AND EXPS RPAREN { $$ = new BinaryOpNode("and", *$3); delete $3; }
           | LPAREN OR EXPS RPAREN { $$ = new BinaryOpNode("or", *$3); delete $3; }
           | LPAREN NOT EXP RPAREN { 
                std::vector<Node*> args; args.push_back($3);
                $$ = new BinaryOpNode("not", args); 
           }
           ;

DEF_STMT : LPAREN DEFINE ID EXP RPAREN { $$ = new DefineNode(*$3, $4); delete $3; }
         ;

FUN_EXP : LPAREN FUN FUN_IDS FUN_BODY RPAREN { $$ = new FunNode(*$3, $4); delete $3; }
        ;

FUN_IDS : LPAREN RPAREN { $$ = new std::vector<std::string>(); }
        | LPAREN IDS RPAREN { $$ = $2; }
        ;

IDS : ID { $$ = new std::vector<std::string>(); $$->push_back(*$1); delete $1; }
    | IDS ID { $$ = $1; $$->push_back(*$2); delete $2; }
    ;

FUN_BODY : EXP { $$ = $1; }
         | DEF_STMTS EXP { 
             $1->push_back($2); 
             $$ = new BlockNode(*$1); 
             delete $1; 
         }
         ;

DEF_STMTS : DEF_STMT { $$ = new std::vector<Node*>(); $$->push_back($1); }
          | DEF_STMTS DEF_STMT { $$ = $1; $$->push_back($2); }
          ;

FUN_CALL : LPAREN FUN_EXP PARAM RPAREN { 
             $$ = new CallNode($2, *$3); delete $3; 
         }
         | LPAREN ID PARAM RPAREN {
             $$ = new CallNode(new VariableNode(*$2), *$3); delete $3; delete $2;
         }
         ;

PARAM : { $$ = new std::vector<Node*>(); }
      | EXPS { $$ = $1; }
      ;

IF_EXP : LPAREN IF EXP EXP EXP RPAREN { $$ = new IfNode($3, $4, $5); }
       ;

EXPS : EXP { $$ = new std::vector<Node*>(); $$->push_back($1); }
     | EXPS EXP { $$ = $1; $$->push_back($2); }
     ;

%%

void yyerror(const char* s) {
    std::cout << "syntax error" << std::endl;
    exit(0);
}