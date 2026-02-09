import sys
import os
sys.path.insert(0, os.path.abspath('src'))
from core_parser import parse
from transpiler import RenPyTranspiler

script = """
INT. START
(IF: x > 1)
    "True"
(ELSE)
    "False"
(END)
Done.
"""
ast = parse(script.strip())
transpiler = RenPyTranspiler()
output = transpiler.transpile(ast)

with open("debug_output.txt", "w") as f:
    f.write(output)
    f.write("\n--- LINES ---\n")
    lines = [l for l in output.split('\n') if l.strip()]
    f.write(str(lines))
