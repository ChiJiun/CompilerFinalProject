import sys
import re
import math # 用於 fmod 以模擬 C++ 的模數行為

# ==============================================================================
# 1. AST (Abstract Syntax Tree) Nodes & Interpreter Logic
#    這部分定義了語法樹的節點結構，以及每個節點如何「求值」(eval)。
#    這是直譯器的核心，負責實際執行 Mini-LISP 程式碼。
# ==============================================================================

class Env(dict):
    """
    環境 (Environment) 類別，用於儲存變數綁定。
    繼承自 Python 的 dict，可以直接使用 env[name] = value。
    """
    def __init__(self, par=None):
        self.par = par # 指向父級環境，實現靜態作用域 (Static Scope)

    def find(self, n):
        """在當前或父級環境中查找變數值。"""
        if n in self: return self[n]
        if self.par: return self.par.find(n)
        error_runtime(f"Error: Variable {n} not defined") # 如果找不到，則報錯

class Node:
    """所有 AST 節點的基類。"""
    pass

class Val(Node):
    """
    數值節點 (Value Node)：代表一個常數值，如數字或布林值。
    """
    def __init__(self, v): self.v = v
    def eval(self, e): return self.v

class Var(Node):
    """
    變數節點 (Variable Node)：代表一個變數的名稱。
    """
    def __init__(self, n): self.n = n # 變數名稱
    def eval(self, e): return e.find(self.n) # 從環境中查找變數值

class Def(Node):
    """
    定義節點 (Define Node)：代表一個變數定義語句 (define id exp)。
    """
    def __init__(self, n, v): self.n, self.v = n, v # 變數名稱, 表達式
    def eval(self, e):
        # PDF 規定 "Redefining is not allowed."
        if self.n in e: error_runtime(f"Error: Redefining {self.n} is not allowed.")
        e[self.n] = self.v.eval(e) # 在當前環境中定義變數

class If(Node):
    """
    If 節點：代表一個條件表達式 (if test then else)。
    """
    def __init__(self, t, a, b): self.t, self.a, self.b = t, a, b # 測試條件, True分支, False分支
    def eval(self, e):
        # 求值測試條件，並確保它是布林值，然後根據結果求值對應分支
        return self.a.eval(e) if check_bool(self.t.eval(e)) else self.b.eval(e)

class Fun(Node):
    """
    函式定義節點 (Function Definition Node)：代表一個匿名函式 (fun (args...) body...)。
    """
    def __init__(self, args, body): self.args, self.body = args, body # 參數列表, 函式本體(AST列表)
    def eval(self, e): return Closure(self.args, self.body, e) # 回傳一個閉包 (Closure)

class Closure:
    """
    閉包 (Closure)：一個可呼叫的物件，包含了函式定義時的參數、本體和環境。
    這是實現 First-class Function 和 Static Scope 的關鍵。
    """
    def __init__(self, args, body, env): self.args, self.body, self.env = args, body, env

class Call(Node):
    """
    函式呼叫節點 (Function Call Node)：代表一個函式呼叫 (func arg1 arg2...)。
    """
    def __init__(self, f, args): self.f, self.args = f, args # 被呼叫的函式(Fun或Var), 參數列表(AST列表)
    def eval(self, e):
        fn = self.f.eval(e) # 求值函式表達式，得到一個 Closure 物件
        if not isinstance(fn, Closure): error_runtime(f"Type Error: Expect 'function' but got '{typeof(fn)}'.") # 類型檢查
        
        # 函式呼叫的參數數量檢查 (Runtime Error)
        if len(self.args) != len(fn.args): 
            error_runtime(f"Need {len(fn.args)} arguments, but got {len(self.args)}.")

        # 創建新的環境用於函式執行，其父環境是閉包的捕獲環境 (Static Scope)
        new_e = Env(fn.env)
        # 綁定參數：將傳入的實際參數求值後綁定到新環境的形參上
        for n, arg in zip(fn.args, self.args): new_e[n] = arg.eval(e)
        
        # 執行函式本體：本體可能包含多個語句，求值所有語句並回傳最後一個結果
        res = None
        for stmt in fn.body: res = stmt.eval(new_e)
        return res

class Op(Node):
    """
    運算節點 (Operation Node)：代表各種數值或邏輯運算 (+, -, and, or 等)。
    """
    def __init__(self, op, args): self.op, self.args = op, args # 運算符號, 參數列表(AST列表)
    def eval(self, e):
        # --- Runtime Arity Check (執行期參數數量檢查) ---
        cnt = len(self.args)
        if self.op in ['+', '*', '=', 'and', 'or']:
            if cnt < 2: error_runtime(f"Error: Need at least 2 arguments, but got {cnt}.")
        elif self.op in ['-', '/', 'mod', '>', '<']:
            if cnt != 2: error_runtime(f"Error: Need 2 arguments, but got {cnt}.")
        elif self.op == 'not':
            if cnt != 1: error_runtime(f"Error: Need 1 argument, but got {cnt}.")

        # 邏輯運算 (短路求值)
        if self.op == 'and': return all(check_bool(a.eval(e)) for a in self.args)
        if self.op == 'or': return any(check_bool(a.eval(e)) for a in self.args)
        
        # 其他運算：先求值所有參數
        vs = [a.eval(e) for a in self.args]
        
        # 單目運算
        if self.op == 'not': return not check_bool(vs[0])
        
        # 多目運算
        if self.op == '+': return sum(check_num(x) for x in vs)
        if self.op == '*': 
            r=1
            for x in vs: r*=check_num(x)
            return r
        
        # 雙目運算
        v1, v2 = vs[0], vs[1]
        if self.op == '-': return check_num(v1) - check_num(v2)
        if self.op == '/': 
            if check_num(v2)==0: error_runtime("Error: Division by zero") # 除以零檢查
            return int(check_num(v1)/v2) # 整數除法
        if self.op == 'mod': 
            # 使用 math.fmod 並轉 int 以模擬 C++ 的模數行為 (符號與被除數一致)
            return int(math.fmod(check_num(v1), check_num(v2)))
        if self.op == '>': return check_num(v1) > check_num(v2)
        if self.op == '<': return check_num(v1) < check_num(v2)
        if self.op == '=': return all(check_num(x)==check_num(vs[0]) for x in vs) # 等於檢查 (多參數)

class Print(Node):
    """
    Print 節點：代表輸出語句 (print-num exp 或 print-bool exp)。
    """
    def __init__(self, is_n, exp): self.is_n, self.exp = is_n, exp # 是否為 print-num, 要輸出的表達式
    def eval(self, e):
        v = self.exp.eval(e)
        # 根據 is_n 判斷並輸出
        print(check_num(v) if self.is_n else ("#t" if check_bool(v) else "#f"))

# 錯誤處理與類型檢查輔助函數
def error_syntax(unexpected_token=None):
    if unexpected_token:
        print(f"syntax error, unexpected '{unexpected_token}'")
    else:
        print("syntax error")
    sys.exit(0) # 語法錯誤的統一出口

def error_runtime(m): print(m); sys.exit(0) # 執行期錯誤的統一出口 (含 Type Error)

def check_num(v): 
    """檢查值是否為數字，否則報類型錯誤。"""
    if type(v) is not int: error_runtime(f"Type Error: Expect 'number' but got '{typeof(v)}'.")
    return v

def check_bool(v): 
    """檢查值是否為布林，否則報類型錯誤。"""
    if type(v) is not bool: error_runtime(f"Type Error: Expect 'boolean' but got '{typeof(v)}'.")
    return v

def typeof(v): 
    """獲取值的類型字串 (用於錯誤訊息)。"""
    return "number" if type(v) is int else "boolean" if type(v) is bool else "function"

# ==============================================================================
# 2. Parsing (詞法分析 Lexing -> S-Exp Reader -> AST Builder)
#    這部分負責將原始碼字串轉換成可執行語法樹 (AST)。
# ==============================================================================

def tokenize(s):
    """
    詞法分析器 (Lexer)：將原始碼字串分割成 Token 列表。
    使用正則表達式高效匹配各種語言元素。
    """
    # 正則表達式匹配：左括號, 右括號, #t, #f, 數字, 識別符號(含關鍵字和部分運算符), 其他運算符
    return re.findall(r'\(|\)|#t|#f|0|-?[1-9]\d*|[a-z][a-z0-9\-]*|[\+\*/<>=]|mod|and|or|not|-', s)

def read_sexp(tokens):
    """
    S-Expression 讀取器：將 Token 列表轉換為巢狀的 Python 列表/原子 (S-Expression)。
    這是 LISP 語言的核心結構。
    """
    if not tokens: error_syntax() # Token 列表為空，語法錯誤
    t = tokens.pop(0) # 取出第一個 Token
    if t == '(':
        # 如果是左括號，開始讀取列表內容
        L = []
        while tokens and tokens[0] != ')': # 確保 tokens 不為空，避免 IndexError
            L.append(read_sexp(tokens)) # 遞迴讀取子表達式
        if not tokens: error_syntax() # 缺少右括號
        tokens.pop(0) # 讀到右括號，彈出
        return L
    elif t == ')':
        # 意外的右括號，語法錯誤
        error_syntax(t)
    else:
        # 原子 (Atom)：布林值、數字、或識別符號
        if t == '#t': return True
        if t == '#f': return False
        if re.match(r'0|-?[1-9]\d*$', t): return int(t) # 數字轉換
        return t # 識別符號 (ID, 關鍵字, 運算符等)

def parse_prog(tokens):
    """
    程式解析器：解析整個 Mini-LISP 程式的 Token 列表，構建 AST 節點列表。
    """
    nodes = []
    while tokens:
        sexp = read_sexp(tokens) # 讀取一個 S-Expression
        nodes.append(parse_stmt(sexp)) # 將 S-Expression 轉換為 AST 節點
    return nodes

def parse_stmt(s):
    """
    語句解析器：將一個 S-Expression 轉換為 AST 的語句節點。
    支持表達式、定義語句、輸出語句。
    """
    # 判斷是否為列表，並檢查其頭部
    if isinstance(s, list) and s:
        if s[0] == 'define':
            if len(s)!=3: error_syntax(s[0]) # (define id exp)
            return Def(s[1], parse_exp(s[2]))
        if s[0] == 'print-num':
            if len(s)!=2: error_syntax(s[0]) # (print-num exp)
            return Print(True, parse_exp(s[1]))
        if s[0] == 'print-bool':
            if len(s)!=2: error_syntax(s[0]) # (print-bool exp)
            return Print(False, parse_exp(s[1]))
    # 如果不是 define/print，則為一般表達式
    return parse_exp(s)

def parse_exp(s):
    """
    表達式解析器：將一個 S-Expression 轉換為 AST 的表達式節點。
    這是最複雜的部分，需要處理各種運算、if、fun 和函式呼叫。
    """
    if not isinstance(s, list): # 如果是原子 (非列表)
        if type(s) in (int, bool): return Val(s) # 數字或布林值直接包裝
        # 如果是字符串原子，檢查是否為運算符關鍵字，避免將其解析為變數
        if s in ['+', '-', '*', '/', 'mod', '>', '<', '=', 'and', 'or', 'not']: error_syntax(s)
        return Var(s) # 否則視為變數

    # 如果是列表 (S-Expression)
    if not s: error_syntax() # 空列表 () 是語法錯誤
    head = s[0] # 列表的頭部通常是操作符、關鍵字或函式本身
    
    if head == 'if':
        if len(s)!=4: error_syntax(head) # (if test then else)
        return If(parse_exp(s[1]), parse_exp(s[2]), parse_exp(s[3]))
    
    if head == 'fun':
        if len(s)<3: error_syntax(head) # (fun (args...) body...)
        params = s[1] # 參數列表
        if not isinstance(params, list): error_syntax(params) # 參數必須是列表
        # 函式本體 (body) 可以是多個語句 (defs... exp)，我們將它們解析為 AST 節點列表
        body = [parse_stmt(x) for x in s[2:]] 
        return Fun(params, body)
        
    ops_1 = ['not'] # 單目運算符
    ops_2 = ['-','/','mod','>','<'] # 雙目運算符
    ops_n = ['+','*','=','and','or'] # 多目運算符 (>=2個參數)
    
    if head in ops_1 + ops_2 + ops_n:
        # 如果頭部是運算符，則解析後續參數，但不檢查數量 (移至 Runtime)
        args = [parse_exp(x) for x in s[1:]]
        # 移除 Arity Check，直接生成 Op 節點
        return Op(head, args)
    
    # 如果不是上述關鍵字或運算符，則視為函式呼叫
    # 第一個元素是函式本身 (可能是一個 Var 或一個 Fun 表達式)，後續是參數
    return Call(parse_exp(head), [parse_exp(x) for x in s[1:]])

# ==============================================================================
# 3. Main Execution
# ==============================================================================
if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(1) # 檢查命令行參數 (需要一個檔案路徑)
    
    # 1. Parsing Phase (Syntax Check)
    try:
        with open(sys.argv[1]) as f:
            tokens = tokenize(f.read()) # 讀取檔案內容並詞法分析
            nodes = parse_prog(tokens) # 解析 Token 列表，構建 AST
    except Exception as e: # 捕獲任何解析階段的異常作為語法錯誤
        error_syntax() # 不指定錯誤 Token

    # 2. Evaluation Phase (Runtime Check)
    env = Env() # 創建一個全局環境
    for n in nodes: 
        # 執行階段不應捕獲異常並轉為 syntax error
        # 這裡發生的異常 (如 SystemExit) 會直接終止程式，或由 Python Runtime 處理
        n.eval(env) 
