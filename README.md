# Mini-LISP Interpreter (Python Version)

這是一個極致精簡、功能完備的 Mini-LISP 直譯器，使用 Python 實作。

## 特色 (Features)

*   **零依賴 (Zero Dependency)**: 僅使用 Python 標準庫 (`sys`, `re`, `math`)，無需安裝任何外部套件。
*   **極致精簡 (Minimalist)**: 核心程式碼約 160 行，邏輯清晰，易於閱讀與維護。
*   **完整功能 (Full Compliance)**: 支援 PDF 規格中的所有 **Basic Features** 與 **Bonus Features**。
*   **精確錯誤報告 (Precise Error Reporting)**: 區分語法錯誤 (Syntax Error) 與執行期錯誤 (Runtime Error)，並提供詳細的錯誤原因。

## 功能列表

1.  **基本運算**: `+`, `-`, `*`, `/`, `mod`
2.  **邏輯運算**: `and`, `or`, `not`, `>`, `<`, `=`
3.  **流程控制**: `if` 表達式
4.  **變數定義**: `define`
5.  **函式功能**: 匿名函式 `fun` 與命名函式
6.  **輸出功能**: `print-num`, `print-bool`
7.  **遞迴 (Recursion)** (Bonus)
8.  **型別檢查 (Type Checking)** (Bonus)
9.  **巢狀函式 (Nested Function / Static Scope)** (Bonus)
10. **一級函式 (First-class Function / Closure)** (Bonus)

## 執行方式

### 前置需求
*   Python 3.x

### 執行單一檔案
```bash
python minilisp.py <file.lsp>
```
例如：
```bash
python minilisp.py public_test_data/b1_1.lsp
```

### 執行測試腳本
專案附帶了一個測試腳本，可自動執行 `public_test_data` 目錄下的所有測試：
```bash
python run_python_tests.py
```

## 檔案結構

*   `minilisp.py`: 直譯器主程式。
*   `run_python_tests.py`: 自動化測試腳本。
*   `public_test_data/`: 測試資料集。
*   `Code_Explanation.md`: 程式碼詳細解說文件。