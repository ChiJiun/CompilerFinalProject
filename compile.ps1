Write-Host "Compiling Bison..."
bison -d parser.y

Write-Host "Compiling Flex..."
flex scanner.l

Write-Host "Compiling C++..."
g++ -o minilisp.exe interpreter.cpp parser.tab.c lex.yy.c -std=c++11 -Wno-write-strings

if ($?) {
    Write-Host "Build Successful! Run ./minilisp.exe <file.lsp>"
} else {
    Write-Host "Build Failed."
}
