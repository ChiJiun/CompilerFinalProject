# Mini-LISP 直譯器專案詳解 (Code Walkthrough)

這份文件包含了 Mini-LISP 直譯器的所有原始程式碼。我已在程式碼中加入**詳細的教學註解**，並在每個檔案前加上了觀念導讀。閱讀此文件可以幫助你從零理解編譯器/直譯器的運作原理。

---

## 系統架構圖

直譯器的運作流程如下：

1.  **Source Code (`.lsp`)**：純文字檔案。
2.  **Lexical Analysis (`scanner.l`)**：將文字切成有意義的單字 (Token)。
3.  **Syntax Analysis (`parser.y`)**：分析單字排列是否符合文法，並建立 **AST (抽象語法樹)**。
4.  **Semantic Analysis & Execution (`ast.h`, `interpreter.cpp`)**：走訪 AST，檢查型別，執行運算，管理變數環境。

---

## 1. 資料結構定義 (`ast.h`)

這是整個專案的「地基」。它定義了兩件最重要的事情：
1.  **資料型別 (`Value`)**：程式執行時數值長什麼樣子？(數字、布林、還是函式？)
2.  **語法樹節點 (`Node`)**：程式碼被轉成樹狀結構後長什麼樣子？
3.  **環境 (`Environment`)**：變數存在哪裡？如何實作 Scope (作用域)？

```cpp
#ifndef AST_H
#define AST_H

#include <string>
#include <vector>
#include <iostream>
#include <map>
#include <memory>
#include <functional>

// 預先宣告，因為 Node 和 Environment 會互相參照
struct Node;
class Environment;

// === 1. 數值系統 (Value System) ===
// 定義 Mini-LISP 支援的資料型別
enum class ValType {
    NUMBER,   // 整數
    BOOLEAN,  // 布林 (#t, #f)
    FUNCTION, // 函式 (支援 Closure)
    NONE      // 用於沒有回傳值的語句 (如 define)
};

// 這是直譯器運算時傳遞的「數值物件」
struct Value {
    ValType type;
    int numVal = 0;       // 儲存數字
    bool boolVal = false; // 儲存布林
    
    // 儲存函式資訊 (實作 Closure 的關鍵)
    // 當 type 為 FUNCTION 時，這裡會指嚮函式的定義與當下的環境
    struct FuncData* funcVal = nullptr;

    Value() : type(ValType::NONE) {}
    Value(int v) : type(ValType::NUMBER), numVal(v) {}
    Value(bool v) : type(ValType::BOOLEAN), boolVal(v) {}
};

// === 2. AST 節點基類 (Base Node) ===
// 所有的語法結構 (數字、加法、if、函式定義) 都繼承自此類別
struct Node {
    // 虛擬解構子：確保刪除物件時能正確釋放記憶體
    virtual ~Node() = default;
    
    // 核心函式：eval (求值)
    // 每個節點都知道如何「計算自己」並回傳一個 Value
    // env 參數代表「當前的變數環境」
    virtual Value eval(Environment* env) = 0;
};

// === 3. 環境與變數作用域 (Environment & Scope) ===
// 這是實作變數存取與 Closure 的核心類別
class Environment {
public:
    // 指向「上一層環境」的指標
    // 這是實作 Static Scope (靜態作用域) 的關鍵鏈結
    Environment* parent;
    
    // 當前環境內的變數儲存區 (變數名 -> 數值)
    std::map<std::string, Value> bindings;

    // 建構子：可以指定 parent (創造新的 Scope)
    Environment(Environment* p = nullptr) : parent(p) {}

    // 定義變數 (在當前 Scope)
    void define(const std::string& name, Value val) {
        bindings[name] = val;
    }

    // 查找變數 (遞迴往上層找)
    Value* lookup(const std::string& name) {
        // 1. 先找自己這層
        auto it = bindings.find(name);
        if (it != bindings.end()) {
            return &it->second;
        }
        // 2. 找不到，如果還有上一層，就往上一層找
        if (parent) {
            return parent->lookup(name);
        }
        // 3. 真的找不到，回傳 nullptr
        return nullptr;
    }
};

// 用來儲存函式本體的結構
// 這就是所謂的 "Closure" (閉包) 的資料結構：程式碼 + 環境
struct FuncData {
    std::vector<std::string> params; // 參數名稱列表 (如 x, y)
    Node* body;                      // 函式執行的程式碼 (AST)
    Environment* env;                // **關鍵**：函式被定義時的環境

    FuncData(const std::vector<std::string>& p, Node* b, Environment* e) 
        : params(p), body(b), env(e) {}
};

// === 4. 各種 AST 節點實作 ===

// 數字節點 (例如: 123)
struct NumberNode : Node {
    int val;
    NumberNode(int v) : val(v) {}
    Value eval(Environment* env) override { return Value(val); }
};

// 布林節點 (例如: #t)
struct BoolNode : Node {
    bool val;
    BoolNode(bool v) : val(v) {}
    Value eval(Environment* env) override { return Value(val); }
};

// 變數節點 (例如: x)
struct VariableNode : Node {
    std::string name;
    VariableNode(const std::string& n) : name(n) {}
    Value eval(Environment* env) override {
        Value* v = env->lookup(name);
        if (!v) {
            std::cerr << "Error: Variable " << name << " not defined." << std::endl;
            exit(1);
        }
        return *v;
    }
};

// 二元/多元運算節點 (例如: +, -, and, >)
struct BinaryOpNode : Node {
    std::string op;          // 運算子字串
    std::vector<Node*> args; // 參數列表 (因為 + 可以有很多參數)

    BinaryOpNode(const std::string& o, const std::vector<Node*>& a) : op(o), args(a) {}
    ~BinaryOpNode() { for(auto a : args) delete a; }
    
    // 實作定義在 interpreter.cpp
    Value eval(Environment* env) override;
};

// If 節點
struct IfNode : Node {
    Node *testExp, *thenExp, *elseExp;
    IfNode(Node* t, Node* th, Node* el) : testExp(t), thenExp(th), elseExp(el) {}
    ~IfNode() { delete testExp; delete thenExp; delete elseExp; }
    Value eval(Environment* env) override;
};

// Print 節點
struct PrintNode : Node {
    bool isNum; // 區分 print-num 還是 print-bool
    Node* exp;
    PrintNode(bool num, Node* e) : isNum(num), exp(e) {}
    ~PrintNode() { delete exp; }
    Value eval(Environment* env) override;
};

// Define 節點 (變數定義)
struct DefineNode : Node {
    std::string name;
    Node* exp;
    DefineNode(const std::string& n, Node* e) : name(n), exp(e) {}
    ~DefineNode() { delete exp; }
    Value eval(Environment* env) override;
};

// Block 節點 (函式本體可能包含多行語句)
struct BlockNode : Node {
    std::vector<Node*> stmts;
    BlockNode(const std::vector<Node*>& s) : stmts(s) {}
    ~BlockNode() { for(auto s : stmts) delete s; }
    Value eval(Environment* env) override;
};

// Function Definition 節點 (fun (x) ...)
struct FunNode : Node {
    std::vector<std::string> params;
    Node* body;
    FunNode(const std::vector<std::string>& p, Node* b) : params(p), body(b) {}
    ~FunNode() { delete body; }
    Value eval(Environment* env) override;
};

// Function Call 節點 (呼叫函式)
struct CallNode : Node {
    Node* funcExp; // 函式本身 (可能是一個變數名，也可能直接是一個 fun 定義)
    std::vector<Node*> args; // 傳入的參數值
    CallNode(Node* f, const std::vector<Node*>& a) : funcExp(f), args(a) {}
    ~CallNode() { delete funcExp; for(auto a : args) delete a; }
    Value eval(Environment* env) override;
};

#endif
```

---

## 2. 詞法分析器 (`scanner.l`)

這是 **Flex** 的原始檔。它的工作是將原始字串 (Character Stream) 轉換成 Token Stream。

**核心觀念**：
*   **Regex (正規表達式)**：左邊定義規則。
*   **Action (動作)**：右邊定義抓到規則後要做什麼。
*   **`yylval`**：這是一個全域變數 (Union)，用來把 Token 的「值」(例如數字是多少、變數名字是什麼) 傳給 Parser。

```lex
%{ 
#include <string>
#include <vector>
#include "ast.h"
// 引入 Parser 定義的 Token 代號 (由 Bison 自動產生)
#include "parser.tab.h"
extern "C" int yylex();
%}
%option noyywrap

%%
[ \t\n\r]+ { /* 忽略所有空白、換行、Tab */ }

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

    /* 處理整數：包含 0, 正整數, 負整數 */
    /* yytext 是 Flex 抓到的當前字串 */
    /* std::stoi 將字串轉為 int 存入 yylval.ival */
0|[1-9][0-9]*|-[1-9][0-9]* { yylval.ival = std::stoi(yytext); return NUMBER; }

    /* 處理 ID (變數名) */
    /* 規則：小寫字母開頭，後面可以是小寫字母、數字或連字號 */
    /* 注意：這裡 new 了一個 string，Parser 用完後要記得 delete */
[a-z]([a-z0-9]|"-")* { yylval.sval = new std::string(yytext); return ID; }

. { /* 忽略其他未定義字元 */ }
%%
```

---

## 3. 語法分析器 (`parser.y`)

這是 **Bison** 的原始檔。它的工作是定義文法 (Grammar) 並建立 AST。

**核心觀念**：
*   **`%union`**：定義 Token 可以攜帶哪些類型的資料 (對應 C++ 的 Union)。
*   **BNF Grammar**：定義語言結構 (例如 `EXP : NUMBER | ID | ...`)。
*   **建樹邏輯 (`$$ = ...`)**：
    *   `$$` 代表冒號左邊規則的結果。
    *   `$1`, `$2`... 代表冒號右邊第幾個元件的值。
    *   例如 `PLUS EXPS` -> `$$ = new BinaryOpNode("+", *$2)` 就是把加法運算子和參數包成一個節點。

```yacc
%{ 
#include <iostream>
#include <vector>
#include <string>
#include "ast.h"

extern "C" int yylex();
extern "C" int yyparse();
extern "C" FILE* yyin;
void yyerror(const char* s);

// 全域變數：用來儲存分析完的所有語句，Interpreter 會執行這些語句
std::vector<Node*> program;
%}

/* 定義 yylval 的型別集合 */
%union {
    int ival;                 // 用於 NUMBER
    bool bval;                // 用於 BOOL_VAL
    std::string* sval;        // 用於 ID
    Node* node;               // 用於各種 AST 節點
    std::vector<Node*>* nodes;// 用於參數列表 (EXPS)
    std::vector<std::string>* ids; // 用於函式參數名列表
}

/* 定義 Token 及其對應的 union 型別 */
%token <ival> NUMBER
%token <bval> BOOL_VAL
%token <sval> ID
%token PRINT_NUM PRINT_BOOL
%token PLUS MINUS MULTIPLY DIVIDE MODULUS GREATER SMALLER EQUAL
%token AND OR NOT
%token DEFINE FUN IF
%token LPAREN RPAREN

/* 定義非終結符號 (Non-terminal) 的型別 (對應 AST 節點) */
%type <node> EXP STMT PRINT_STMT DEF_STMT NUM_OP LOGICAL_OP FUN_EXP FUN_CALL IF_EXP FUN_BODY
%type <nodes> EXPS PARAM DEF_STMTS
%type <ids> FUN_IDS IDS

%%

/* === 文法規則區 === */

/* 程式由一個或多個 STMT (語句) 組成 */
PROGRAM : STMTS
        ;

STMTS : STMT { program.push_back($1); }
      | STMTS STMT { program.push_back($2); }
      ;

STMT : EXP
     | DEF_STMT
     | PRINT_STMT
     ;

/* 輸出語句 */
PRINT_STMT : LPAREN PRINT_NUM EXP RPAREN { $$ = new PrintNode(true, $3); }
           | LPAREN PRINT_BOOL EXP RPAREN { $$ = new PrintNode(false, $3); }
           ;

/* 表達式：可以是值、變數、運算、函式定義或呼叫 */
EXP : BOOL_VAL { $$ = new BoolNode($1); }
    | NUMBER { $$ = new NumberNode($1); }
    | ID { $$ = new VariableNode(*$1); delete $1; } // ID 用完要刪除 string 指標
    | NUM_OP
    | LOGICAL_OP
    | FUN_EXP
    | FUN_CALL
    | IF_EXP
    ;

/* 數值運算 */
NUM_OP : LPAREN PLUS EXPS RPAREN { $$ = new BinaryOpNode("+", *$3); delete $3; }
       | LPAREN MINUS EXP EXP RPAREN { 
            std::vector<Node*> args;
            args.push_back($3);
            args.push_back($4);
            $$ = new BinaryOpNode("-", args);
       }
       | LPAREN MULTIPLY EXPS RPAREN { $$ = new BinaryOpNode("*", *$3); delete $3; }
       | LPAREN DIVIDE EXP EXP RPAREN { 
            std::vector<Node*> args;
            args.push_back($3);
            args.push_back($4);
            $$ = new BinaryOpNode("/", args);
       }
       | LPAREN MODULUS EXP EXP RPAREN { 
            std::vector<Node*> args;
            args.push_back($3);
            args.push_back($4);
            $$ = new BinaryOpNode("mod", args);
       }
       | LPAREN GREATER EXP EXP RPAREN { 
            std::vector<Node*> args;
            args.push_back($3);
            args.push_back($4);
            $$ = new BinaryOpNode(">", args);
       }
       | LPAREN SMALLER EXP EXP RPAREN { 
            std::vector<Node*> args;
            args.push_back($3);
            args.push_back($4);
            $$ = new BinaryOpNode("<", args);
       }
       | LPAREN EQUAL EXPS RPAREN { $$ = new BinaryOpNode("=", *$3); delete $3; }
       ;

/* 邏輯運算 */
LOGICAL_OP : LPAREN AND EXPS RPAREN { $$ = new BinaryOpNode("and", *$3); delete $3; }
           | LPAREN OR EXPS RPAREN { $$ = new BinaryOpNode("or", *$3); delete $3; }
           | LPAREN NOT EXP RPAREN { 
                std::vector<Node*> args;
                args.push_back($3);
                $$ = new BinaryOpNode("not", args);
           }
           ;

/* 變數定義：(define x 10) */
DEF_STMT : LPAREN DEFINE ID EXP RPAREN { $$ = new DefineNode(*$3, $4); delete $3; }
         ;

/* 函式定義：(fun (x y) (+ x y)) */
FUN_EXP : LPAREN FUN FUN_IDS FUN_BODY RPAREN { $$ = new FunNode(*$3, $4); delete $3; }
        ;

/* 函式參數列：() 或 (x y z) */
FUN_IDS : LPAREN RPAREN { $$ = new std::vector<std::string>(); }
        | LPAREN IDS RPAREN { $$ = $2; }
        ;

/* 遞迴解析多個 ID */
IDS : ID { $$ = new std::vector<std::string>(); $$->push_back(*$1); delete $1; }
    | IDS ID { $$ = $1; $$->push_back(*$2); delete $2; }
    ;

/* 函式本體：可以是單一 EXP，或是內部定義變數後接 EXP (巢狀結構) */
FUN_BODY : EXP { $$ = $1; }
         | DEF_STMTS EXP { 
             $1->push_back($2); // 把最後的 EXP 加入語句列表
             $$ = new BlockNode(*$1); 
             delete $1; 
         }
         ;

DEF_STMTS : DEF_STMT { $$ = new std::vector<Node*>(); $$->push_back($1); }
          | DEF_STMTS DEF_STMT { $$ = $1; $$->push_back($2); }
          ;

/* 函式呼叫：(func 1 2) 或 ((fun ...) 1 2) */
FUN_CALL : LPAREN FUN_EXP PARAM RPAREN { 
             $$ = new CallNode($2, *$3); delete $3; 
         }
         | LPAREN ID PARAM RPAREN {
             $$ = new CallNode(new VariableNode(*$2), *$3); delete $3; delete $2;
         }
         ;

PARAM : { $$ = new std::vector<Node*>(); } // 空參數
      | EXPS { $$ = $1; }
      ;

/* If 表達式 */
IF_EXP : LPAREN IF EXP EXP EXP RPAREN { $$ = new IfNode($3, $4, $5); }
       ;

/* 遞迴解析多個 Expression */
EXPS : EXP { $$ = new std::vector<Node*>(); $$->push_back($1); }
     | EXPS EXP { $$ = $1; $$->push_back($2); }
     ;

%%

void yyerror(const char* s) {
    std::cout << "syntax error" << std::endl;
    exit(0);
}
```

---

## 4. 直譯器邏輯 (`interpreter.cpp`)

這是程式的大腦。它包含了 `main` 函式以及所有 AST 節點的 `eval` 實作。

**核心重點**：
1.  **Type Checking (型別檢查)**：在運算前檢查是否為 Number 或 Boolean。
2.  **`FunNode::eval`**：創造 Closure，**捕捉當前環境**。
3.  **`CallNode::eval`**：執行函式，建立新環境 (Parent 指向被捕捉的環境，而非呼叫者的環境)，這是 **Static Scope** 的關鍵。

```cpp
#include <iostream>
#include <vector>
#include <numeric>
#include "ast.h"
#include "parser.tab.h"

extern std::vector<Node*> program;
extern "C" FILE* yyin;
extern "C" int yyparse();

// === Helper Functions: 型別檢查 ===

// 錯誤處理：印出 Type Error 並結束程式
void typeError(const std::string& expect, const std::string& got) {
    std::cout << "Type Error: Expect '" << expect << "' but got '" << got << "'." << std::endl;
    exit(0);
}

// 確保數值是 Number
void checkNumber(const Value& v) {
    if (v.type != ValType::NUMBER) {
        std::string got = (v.type == ValType::BOOLEAN) ? "boolean" : "function";
        typeError("number", got);
    }
}

// 確保數值是 Boolean
void checkBool(const Value& v) {
    if (v.type != ValType::BOOLEAN) {
        std::string got = (v.type == ValType::NUMBER) ? "number" : "function";
        typeError("boolean", got);
    }
}

// === Node Implementations (AST 節點邏輯) ===

// 1. 二元運算求值
Value BinaryOpNode::eval(Environment* env) {
    std::vector<Value> evaluatedArgs;
    // 先計算所有參數的值
    for (Node* arg : args) {
        evaluatedArgs.push_back(arg->eval(env));
    }

    if (op == "+") {
        int sum = 0;
        for (const auto& v : evaluatedArgs) {
            checkNumber(v); // 型別檢查
            sum += v.numVal;
        }
        return Value(sum);
    } else if (op == "-") {
        checkNumber(evaluatedArgs[0]);
        checkNumber(evaluatedArgs[1]);
        return Value(evaluatedArgs[0].numVal - evaluatedArgs[1].numVal);
    } else if (op == "*") {
        int prod = 1;
        for (const auto& v : evaluatedArgs) {
            checkNumber(v);
            prod *= v.numVal;
        }
        return Value(prod);
    } else if (op == "/") {
        checkNumber(evaluatedArgs[0]);
        checkNumber(evaluatedArgs[1]);
        if (evaluatedArgs[1].numVal == 0) {
             std::cerr << "Error: Division by zero" << std::endl; exit(1);
        }
        return Value(evaluatedArgs[0].numVal / evaluatedArgs[1].numVal);
    } else if (op == "mod") {
        checkNumber(evaluatedArgs[0]);
        checkNumber(evaluatedArgs[1]);
        return Value(evaluatedArgs[0].numVal % evaluatedArgs[1].numVal);
    } else if (op == ">") {
        checkNumber(evaluatedArgs[0]);
        checkNumber(evaluatedArgs[1]);
        return Value(evaluatedArgs[0].numVal > evaluatedArgs[1].numVal);
    } else if (op == "<") {
        checkNumber(evaluatedArgs[0]);
        checkNumber(evaluatedArgs[1]);
        return Value(evaluatedArgs[0].numVal < evaluatedArgs[1].numVal);
    } else if (op == "=") {
        // 等號檢查：所有參數數值必須相等
        if (evaluatedArgs.empty()) return Value(true);
        checkNumber(evaluatedArgs[0]);
        int first = evaluatedArgs[0].numVal;
        for (size_t i = 1; i < evaluatedArgs.size(); ++i) {
            checkNumber(evaluatedArgs[i]);
            if (evaluatedArgs[i].numVal != first) return Value(false);
        }
        return Value(true);
    } else if (op == "and") {
        for (const auto& v : evaluatedArgs) {
            checkBool(v);
            if (!v.boolVal) return Value(false); // 短路邏輯：遇到 #f 即回傳 #f
        }
        return Value(true);
    } else if (op == "or") {
        for (const auto& v : evaluatedArgs) {
            checkBool(v);
            if (v.boolVal) return Value(true); // 短路邏輯：遇到 #t 即回傳 #t
        }
        return Value(false);
    } else if (op == "not") {
        checkBool(evaluatedArgs[0]);
        return Value(!evaluatedArgs[0].boolVal);
    }
    return Value();
}

// 2. If 判斷式求值
Value IfNode::eval(Environment* env) {
    Value test = testExp->eval(env);
    checkBool(test); // 檢查條件必須是 Boolean
    if (test.boolVal) {
        return thenExp->eval(env);
    } else {
        return elseExp->eval(env);
    }
}

// 3. Print 求值
Value PrintNode::eval(Environment* env) {
    Value v = exp->eval(env);
    if (isNum) {
        checkNumber(v);
        std::cout << v.numVal << std::endl;
    } else {
        checkBool(v);
        std::cout << (v.boolVal ? "#t" : "#f") << std::endl;
    }
    return Value(); // Print 沒有回傳值
}

// 4. Define 變數定義
Value DefineNode::eval(Environment* env) {
    Value v = exp->eval(env);
    // 檢查是否重複定義 (基本功能要求)
    if (env->bindings.find(name) != env->bindings.end()) {
        std::cerr << "Error: Redefining " << name << " is not allowed." << std::endl;
        exit(1);
    }
    env->define(name, v);
    return Value();
}

// 5. Block 區塊求值 (用於函式本體)
Value BlockNode::eval(Environment* env) {
    Value last;
    for (Node* stmt : stmts) {
        last = stmt->eval(env); // 依序執行
    }
    return last; // 回傳最後一個語句的結果
}

// 6. 函式定義 (Function Definition) - 實作 Closure
Value FunNode::eval(Environment* env) {
    Value v;
    v.type = ValType::FUNCTION;
    // **關鍵**：將 `env` (當下的環境) 存入 FuncData
    // 這使得函式可以記得它被定義時的變數 (Static Scope)
    v.funcVal = new FuncData(params, body, env); 
    return v;
}

// 7. 函式呼叫 (Function Call)
Value CallNode::eval(Environment* env) {
    // 1. 取得函式物件
    Value func = funcExp->eval(env);
    if (func.type != ValType::FUNCTION) {
        std::cout << "Type Error: Expect 'function' but got '" 
                  << (func.type == ValType::NUMBER ? "number" : "boolean") << "'." << std::endl;
        exit(0);
    }

    FuncData* fData = func.funcVal;

    // 2. 檢查參數數量
    if (args.size() != fData->params.size()) {
         std::cerr << "Error: Need " << fData->params.size() << " arguments, but got " << args.size() << "." << std::endl;
         exit(0);
    }

    // 3. 計算參數值 (在**呼叫者**的環境下計算)
    std::vector<Value> argValues;
    for (Node* arg : args) {
        argValues.push_back(arg->eval(env));
    }

    // 4. 建立函式執行環境
    // **重要**：Parent 是 `fData->env` (函式定義時的環境)，而不是現在的 `env`
    // 這確保了函式內部讀取變數時，是依照定義時的 Scope，而非呼叫時的 Scope (Static Scope)
    Environment* newEnv = new Environment(fData->env);

    // 5. 將參數綁定到新環境
    for (size_t i = 0; i < args.size(); ++i) {
        newEnv->define(fData->params[i], argValues[i]);
    }

    // 6. 執行函式本體
    return fData->body->eval(newEnv);
}

// === Main Function ===
int main(int argc, char** argv) {
    // 處理檔案輸入
    if (argc > 1) {
        FILE* file = fopen(argv[1], "r");
        if (!file) {
            std::cerr << "Could not open file " << argv[1] << std::endl;
            return 1;
        }
        yyin = file;
    }

    // 1. 呼叫 Parser 建樹
    yyparse(); 

    // 2. 建立全域環境 (Global Environment)
    Environment* globalEnv = new Environment();

    // 3. 走訪 AST 執行程式
    for (Node* stmt : program) {
        stmt->eval(globalEnv);
    }

    return 0;
}
```

---

## 如何自行編譯

若您安裝了 Flex, Bison 和 G++ (Windows 下建議使用 MinGW)，可以使用以下指令編譯：

```bash
# 1. 產生 Parser C++ 程式碼 (parser.tab.c, parser.tab.h)
bison -d parser.y

# 2. 產生 Lexer C++ 程式碼 (lex.yy.c)
flex scanner.l

# 3. 編譯並連結所有檔案
g++ -o minilisp.exe interpreter.cpp parser.tab.c lex.yy.c -std=c++11
```
