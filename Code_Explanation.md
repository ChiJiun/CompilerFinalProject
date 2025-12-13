# Mini-LISP Python 實作詳解 (Code Explanation)

這份文件將帶您深入了解 `minilisp.py` 的實作細節。本專案採用了標準的直譯器架構：**Tokenizer -> Parser -> AST -> Interpreter**，並利用 Python 的動態特性實現了極高的開發效率。

---

## 1. 架構總覽

程式碼主要分為三個階段：

1.  **Parsing (解析)**: 將原始碼字串轉換為抽象語法樹 (AST)。
    *   `tokenize()`: 使用正規表達式 (Regex) 將字串切割成 Token 列表。
    *   `read_sexp()`: 將 Token 列表組裝成巢狀的 List 結構 (S-Expression)。
    *   `parse_exp()`: 將 S-Expression 轉換為 Python 的物件 (AST Nodes)。
2.  **AST (抽象語法樹)**: 定義了程式的結構。
    *   使用 Python 的 `class` 來代表不同的語法結構 (如 `Val`, `If`, `Call`, `Op` 等)。
3.  **Evaluation (求值)**: 執行程式邏輯。
    *   每個 AST 節點都有一個 `eval(env)` 方法，傳入當前的環境 `Env`，回傳計算結果。

---

## 2. 核心元件詳解

### A. 環境 (Environment) - `class Env`

這是實作 **變數作用域 (Scope)** 的關鍵。

```python
class Env(dict):
    def __init__(self, par=None):
        self.par = par  # Parent Environment
```

*   **繼承自 `dict`**: 利用 Python 的字典來儲存變數名稱與數值的對應。
*   **`par` (Parent)**: 指向「上一層」的環境。
*   **`find(n)`**: 查找變數時，先找自己，找不到就往 `par` 找。這實現了 **Static Scope (靜態作用域)**，讓函式可以存取定義時外部的變數。

### B. 閉包 (Closure) - `class Closure`

這是實作 **First-class Function** 與 **Nested Function** 的核心。

```python
class Closure:
    def __init__(self, args, body, env): ...
```

*   當直譯器執行到 `(fun ...)` 時，它不會只存程式碼，還會把 **當下的環境 (`env`)** 存起來。
*   這使得函式即使被傳遞到其他地方執行，依然能「記得」它出生時的環境。

### C. 語法樹節點 (AST Nodes)

每個語法結構都對應一個類別：

*   **`Val`**: 數值或布林常數。
*   **`Var`**: 變數 (例如 `x`)。
*   **`If`**: 條件判斷。
*   **`Def`**: 變數定義 (檢查了重複定義錯誤)。
*   **`Op`**: 基礎運算 (`+`, `-`, `and` 等)。
    *   **Runtime Arity Check**: 在 `eval` 時檢查參數數量，若不符則報錯 (例如 `Error: Need 2 arguments...`)。
    *   **Mod 運算**: 使用 `math.fmod` 確保負數運算行為與 C++ 一致。
*   **`Call`**: 函式呼叫。
    *   **執行流程**:
        1.  求值函式本體 (得到 `Closure`)。
        2.  檢查參數數量。
        3.  **建立新環境**: `new_e = Env(fn.env)`。注意 Parent 是 `Closure` 捕捉的環境，而非呼叫者的環境。
        4.  綁定參數並執行。

### D. 解析器 (Parser)

我們使用了一個兩階段的解析策略，這比傳統的 Recursive Descent 更適合 LISP。

1.  **`tokenize`**: 
    ```python
    re.findall(r'\(|\)|#t|#f|0|-?[1-9]\d*|...', s)
    ```
    一行 Regex 搞定所有斷詞工作。

2.  **`read_sexp`**:
    這是一個簡單的遞迴函數。遇到 `(` 就開始遞迴讀取直到 `)`，將其打包成 Python List。
    *   輸入: `(+ 1 2)`
    *   輸出: `['+', 1, 2]` (Python List)

3.  **`parse_exp`**:
    將 List 轉換為 AST Node。
    *   如果是 `['+', 1, 2]` -> 轉換為 `Op('+', [Val(1), Val(2)])`。
    *   如果是 `['if', ...]` -> 轉換為 `If(...)`。
    *   如果是 `['fun', ...]` -> 轉換為 `Fun(...)`。

---

## 3. 錯誤處理策略

專案區分了兩種錯誤類型，以符合題目與測試資料的要求：

1.  **Syntax Error (語法錯誤)**:
    *   例如：括號不匹配、運算子結構錯誤 (如 `01_2.lsp` 的 `unexpected '-'`)。
    *   處理：由 `error_syntax()` 拋出，輸出格式為 `syntax error` 或 `syntax error, unexpected 'TOKEN'`。

2.  **Runtime Error (執行期錯誤)**:
    *   例如：型別錯誤、除以零、變數未定義、參數數量不符。
    *   處理：由 `error_runtime()` 拋出，輸出詳細錯誤原因 (例如 `Type Error: Expect 'number' but got 'boolean'.`)。

---

## 4. 總結

這份實作展示了 Python 在編譯器領域的強大能力。透過利用 Python 的動態特性 (List, Dict, Class)，我們用極少的程式碼量 (約 160 行) 就完成了一個符合嚴格規格的 LISP 直譯器，且具備高度的可讀性與擴充性。
