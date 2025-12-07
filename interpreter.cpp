#include <iostream>
#include <vector>
#include <numeric>
#include "ast.h"
#include "parser.tab.h"

extern std::vector<Node*> program;
extern "C" FILE* yyin;
extern "C" int yyparse();

// Helper for Type Checking
void typeError(const std::string& expect, const std::string& got) {
    std::cout << "Type Error: Expect '" << expect << "' but got '" << got << "'." << std::endl;
    exit(0);
}

void checkNumber(const Value& v) {
    if (v.type != ValType::NUMBER) {
        std::string got = (v.type == ValType::BOOLEAN) ? "boolean" : "function"; // Simple mapping
        typeError("number", got);
    }
}

void checkBool(const Value& v) {
    if (v.type != ValType::BOOLEAN) {
        std::string got = (v.type == ValType::NUMBER) ? "number" : "function";
        typeError("boolean", got);
    }
}

// Implementations

Value BinaryOpNode::eval(Environment* env) {
    std::vector<Value> evaluatedArgs;
    for (Node* arg : args) {
        evaluatedArgs.push_back(arg->eval(env));
    }

    if (op == "+") {
        int sum = 0;
        for (const auto& v : evaluatedArgs) {
            checkNumber(v);
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
            // Division by zero behavior not specified, but assume crash or error
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
        // "return #t if all EXPs are equal"
        // Can be numbers only based on spec table? 
        // Table says "Number(s)" for input.
        // Actually example (= (+ 1 1) 2 (/ 6 3)) => #t implies multiple args
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
            if (!v.boolVal) return Value(false);
        }
        return Value(true);
    } else if (op == "or") {
        for (const auto& v : evaluatedArgs) {
            checkBool(v);
            if (v.boolVal) return Value(true);
        }
        return Value(false);
    } else if (op == "not") {
        checkBool(evaluatedArgs[0]);
        return Value(!evaluatedArgs[0].boolVal);
    }
    return Value();
}

Value IfNode::eval(Environment* env) {
    Value test = testExp->eval(env);
    checkBool(test);
    if (test.boolVal) {
        return thenExp->eval(env);
    } else {
        return elseExp->eval(env);
    }
}

Value PrintNode::eval(Environment* env) {
    Value v = exp->eval(env);
    if (isNum) {
        checkNumber(v);
        std::cout << v.numVal << std::endl;
    } else {
        checkBool(v);
        std::cout << (v.boolVal ? "#t" : "#f") << std::endl;
    }
    return Value(); // Return nothing relevant
}

Value DefineNode::eval(Environment* env) {
    Value v = exp->eval(env);
    // "Redefining is not allowed" - Basic feature check
    // Logic: check current env only? Or all? Spec: "Note: Redefining is not allowed."
    // We'll check current scope.
    if (env->bindings.find(name) != env->bindings.end()) {
        std::cerr << "Error: Redefining " << name << " is not allowed." << std::endl;
        exit(1);
    }
    env->define(name, v);
    return Value();
}

Value BlockNode::eval(Environment* env) {
    Value last;
    for (Node* stmt : stmts) {
        last = stmt->eval(env);
    }
    return last;
}

Value FunNode::eval(Environment* env) {
    Value v;
    v.type = ValType::FUNCTION;
    // Capture environment (Closure)
    v.funcVal = new FuncData(params, body, env); 
    return v;
}

Value CallNode::eval(Environment* env) {
    Value func = funcExp->eval(env);
    if (func.type != ValType::FUNCTION) {
        // Bonus: Type checking for function call?
        // Spec says "Function call" Parameter Type "Any", Output "Depend...".
        // But if it's not a function we can't call it.
        std::cout << "Type Error: Expect 'function' but got '" 
                  << (func.type == ValType::NUMBER ? "number" : "boolean") << "'." << std::endl;
        exit(0);
    }

    FuncData* fData = func.funcVal;

    // Check arg count
    if (args.size() != fData->params.size()) {
         std::cerr << "Error: Need " << fData->params.size() << " arguments, but got " << args.size() << "." << std::endl;
         exit(0); // Match behavior of 01_1.lsp?
    }

    // Evaluate arguments in CURRENT environment
    std::vector<Value> argValues;
    for (Node* arg : args) {
        argValues.push_back(arg->eval(env));
    }

    // Create new environment for function execution
    // Parent should be the CAPTURED environment (Static Scope)
    Environment* newEnv = new Environment(fData->env);

    // Bind parameters
    for (size_t i = 0; i < args.size(); ++i) {
        newEnv->define(fData->params[i], argValues[i]);
    }

    // Execute body
    // "Variables used in FUN-BODY should be bound to PARAMs"
    // The parser stores BODY as an EXP.
    return fData->body->eval(newEnv);
}

int main(int argc, char** argv) {
    /* 
       Wait, the user wants to run the interpreter on a file.
       ./smli example.lsp
       So we need to accept a filename.
    */
    if (argc > 1) {
        FILE* file = fopen(argv[1], "r");
        if (!file) {
            std::cerr << "Could not open file " << argv[1] << std::endl;
            return 1;
        }
        yyin = file;
    }

    yyparse(); // Builds 'program' vector

    Environment* globalEnv = new Environment();

    for (Node* stmt : program) {
        stmt->eval(globalEnv);
    }

    return 0;
}
