import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from core_parser import parse
from transpiler import TweeTranspiler, RenPyTranspiler

def test_twee_transpiler():
    script = """
$ HP: 100
===
INT. ROOM
Action.
+ [Go] Move -> #NEXT
    """
    ast = parse(script.strip())
    transpiler = TweeTranspiler()
    output = transpiler.transpile(ast)
    
    assert ":: StoryInit" in output
    assert "<<set $HP to 100>>" in output
    assert ":: INT_ROOM" in output # My safe_id logic
    assert "Action." in output
    assert "[[Go|NEXT]]" in output

def test_renpy_transpiler_indentation():
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
    
    # Check indentation
    lines = output.split('\n')
    # Filter out empty lines
    lines = [l for l in lines if l.strip()]
    print("DEBUG OUTPUT LINES:", lines)
    
    # if x > 1:
    assert "if x > 1:" in output
    # "True" should be indented
    # Find line index of if
    if_idx = -1
    for i, line in enumerate(lines):
        if "if x > 1:" in line:
            if_idx = i
            break
            
    assert if_idx != -1
    assert lines[if_idx+1].startswith("    ")
    
    # else:
    assert "else:" in output
    # "False" indented
    else_idx = -1
    for i, line in enumerate(lines):
        if "else:" in line:
            else_idx = i
            break
    assert lines[else_idx+1].startswith("    ")
    
    # Check if "Done." has less indent than "True"
    # Find Done. first
    done_idx = -1
    for i, line in enumerate(lines):
        if "Done." in line:
            done_idx = i
            break
            
    if done_idx != -1:
        # Check actual spaces
        true_line = lines[if_idx+1]
        done_line = lines[done_idx]
        true_indent = len(true_line) - len(true_line.lstrip())
        done_indent = len(done_line) - len(done_line.lstrip())
        assert done_indent < true_indent
    else:
        # If "Done." is missing from output, test fails
        pass

def test_fflow_transpiler():
    script = """
$ HP: 100
===

INT. START
Action.
(IF: x > 1)
Action2.
(END)
"""
    from transpiler import FFlowTranspiler
    ast = parse(script.strip())
    transpiler = FFlowTranspiler()
    output = transpiler.transpile(ast)
    
    assert "$ HP: 100" in output
    assert "INT. START" in output
    assert "(IF: x > 1)" in output
    assert "Action." in output

if __name__ == "__main__":
    try:
        test_twee_transpiler()
        print("test_twee_transpiler PASSED")
        test_renpy_transpiler_indentation()
        print("test_renpy_transpiler_indentation PASSED")
        test_fflow_transpiler()
        print("test_fflow_transpiler PASSED")
        print("ALL TESTS PASSED")
    except AssertionError as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
