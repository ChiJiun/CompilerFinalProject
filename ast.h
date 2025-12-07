#ifndef AST_H
#define AST_H

#include <string>
#include <vector>
#include <iostream>
#include <map>
#include <memory>
#include <functional>

// Forward declarations
struct Node;
class Environment;

// Types of values our language supports
enum class ValType {
    NUMBER,
    BOOLEAN,
    FUNCTION,
    NONE // For definitions or statements that don't return a value
};

// A value in the interpreter
struct Value {
    ValType type;
    int numVal = 0;
    bool boolVal = false;
    // For functions (closures), we need to store the function definition and its environment.
    // We'll handle this with a pointer to the AST node and the environment.
    struct FuncData* funcVal = nullptr;

    Value() : type(ValType::NONE) {}
    Value(int v) : type(ValType::NUMBER), numVal(v) {}
    Value(bool v) : type(ValType::BOOLEAN), boolVal(v) {}
};

// Abstract Syntax Tree Node Base
struct Node {
    virtual ~Node() = default;
    virtual Value eval(Environment* env) = 0;
};

// Environment for variable bindings
class Environment {
public:
    Environment* parent;
    std::map<std::string, Value> bindings;

    Environment(Environment* p = nullptr) : parent(p) {}

    void define(const std::string& name, Value val) {
        bindings[name] = val;
    }

    Value* lookup(const std::string& name) {
        auto it = bindings.find(name);
        if (it != bindings.end()) {
            return &it->second;
        }
        if (parent) {
            return parent->lookup(name);
        }
        return nullptr;
    }
};

struct FuncData {
    std::vector<std::string> params;
    Node* body; // Owned by the AST, not here
    Environment* env; // The closure environment

    FuncData(const std::vector<std::string>& p, Node* b, Environment* e) 
        : params(p), body(b), env(e) {}
};

// Implementations of Nodes
struct NumberNode : Node {
    int val;
    NumberNode(int v) : val(v) {}
    Value eval(Environment* env) override { return Value(val); }
};

struct BoolNode : Node {
    bool val;
    BoolNode(bool v) : val(v) {}
    Value eval(Environment* env) override { return Value(val); }
};

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

struct BinaryOpNode : Node {
    std::string op;
    std::vector<Node*> args; // Variable number of arguments for some ops

    BinaryOpNode(const std::string& o, const std::vector<Node*>& a) : op(o), args(a) {}
    ~BinaryOpNode() { for(auto a : args) delete a; }
    
    Value eval(Environment* env) override; // Defined in implementation
};

struct IfNode : Node {
    Node *testExp, *thenExp, *elseExp;
    IfNode(Node* t, Node* th, Node* el) : testExp(t), thenExp(th), elseExp(el) {}
    ~IfNode() { delete testExp; delete thenExp; delete elseExp; }
    Value eval(Environment* env) override;
};

struct PrintNode : Node {
    bool isNum; // true for print-num, false for print-bool
    Node* exp;
    PrintNode(bool num, Node* e) : isNum(num), exp(e) {}
    ~PrintNode() { delete exp; }
    Value eval(Environment* env) override;
};

struct DefineNode : Node {
    std::string name;
    Node* exp;
    DefineNode(const std::string& n, Node* e) : name(n), exp(e) {}
    ~DefineNode() { delete exp; }
    Value eval(Environment* env) override;
};

struct BlockNode : Node {
    std::vector<Node*> stmts;
    BlockNode(const std::vector<Node*>& s) : stmts(s) {}
    ~BlockNode() { for(auto s : stmts) delete s; }
    Value eval(Environment* env) override;
};

struct FunNode : Node {
    std::vector<std::string> params;
    Node* body;
    FunNode(const std::vector<std::string>& p, Node* b) : params(p), body(b) {}
    ~FunNode() { delete body; }
    Value eval(Environment* env) override;
};

struct CallNode : Node {
    Node* funcExp;
    std::vector<Node*> args;
    CallNode(Node* f, const std::vector<Node*>& a) : funcExp(f), args(a) {}
    ~CallNode() { delete funcExp; for(auto a : args) delete a; }
    Value eval(Environment* env) override;
};

#endif
