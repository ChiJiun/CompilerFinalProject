# Mini-LISP Interpreter

這是一個使用 C++, Flex 和 Bison 實作的 Mini-LISP 直譯器。

## 功能列表

此直譯器支援所有 **Basic Features** 與 **Bonus Features**：

1.  **基本運算**: 加減乘除、取餘數 (`+`, `-`, `*`, `/`, `mod`)
2.  **邏輯運算**: `and`, `or`, `not`, `>`, `<`, `=`
3.  **流程控制**: `if` 表達式
4.  **變數定義**: `define`
5.  **函式功能**: 匿名函式 `fun` 與命名函式
6.  **輸出**: `print-num`, `print-bool`
7.  **遞迴 (Recursion)** (Bonus)
8.  **型別檢查 (Type Checking)** (Bonus)
9.  **巢狀函式 (Nested Function / Static Scope)** (Bonus)
10. **一級函式 (First-class Function / Closure)** (Bonus)

## 編譯方式

請確認已安裝 `flex`, `bison` 和 `g++` (MinGW)。

### 使用 PowerShell 腳本 (推薦)
在專案根目錄執行：
```powershell
.\compile.ps1
```

### 手動編譯
```bash
bison -d parser.y
flex scanner.l
g++ -o minilisp.exe interpreter.cpp parser.tab.c lex.yy.c -std=c++11
```

## 執行方式

**注意**：PowerShell 不支援 `<` 重新導向符號。請將檔案路徑作為參數傳遞。

### 正確用法
```powershell
.\minilisp.exe public_test_data\02_1.lsp
```

### 錯誤用法 (會導致 RedirectionNotSupported 錯誤)
```powershell
# 請勿使用這種方式
.\minilisp.exe < public_test_data\02_1.lsp
```

## 測試指令

您可以直接執行 `run_tests.ps1` 腳本來一次跑完所有測試資料：

```powershell
.\run_tests.ps1
```

## 程式碼結構說明

本專案由以下核心檔案組成：

*   **`ast.h` (Abstract Syntax Tree Header)**
    *   定義抽象語法樹 (AST) 的節點結構 (如 `NumberNode`, `IfNode`, `FunNode` 等)。
    *   定義 `Value` (數值/布林/函式型別) 與 `Environment` (變數 Scope 管理)。
*   **`scanner.l` (Lexical Analyzer)**
    *   使用 Flex 撰寫。負責將輸入的字串切割成 Token (如 `LPAREN`, `NUMBER`, `PLUS`)。
*   **`parser.y` (Syntax Analyzer)**
    *   使用 Bison 撰寫。定義文法規則 (Grammar)，並將 Token 組合成 AST。
*   **`interpreter.cpp` (Interpreter Core)**
    *   實作 AST 節點的 `eval()` 運算邏輯。
    *   包含型別檢查 (Type Checking) 與主程式進入點 (Main Function)。
*   **`compile.ps1`**: 自動化編譯腳本 (PowerShell)。
*   **`run_tests.ps1`**: 自動化測試腳本，執行所有公開測資。
