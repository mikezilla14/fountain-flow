import argparse
import sys
import os
from core_parser import parse as parse_fflow
from reverse_parser import TweeParser, RenPyParser
from transpiler import TweeTranspiler, RenPyTranspiler, FFlowTranspiler

def main():
    parser = argparse.ArgumentParser(description="Fountain-Flow Compiler/Transpiler")
    parser.add_argument("input_file", help="Input file path (.fflow, .twee, .rpy)")
    parser.add_argument("--to", choices=["twee", "renpy", "fflow"], help="Output format")
    parser.add_argument("--out", help="Output file path (optional)")
    
    args = parser.parse_args()
    
    input_path = args.input_file
    if not os.path.exists(input_path):
        print(f"Error: File '{input_path}' not found.")
        sys.exit(1)
        
    ext = os.path.splitext(input_path)[1].lower()
    
    # 1. Parse Input
    ast = None
    input_format = None
    
    if ext == ".fflow":
        input_format = "fflow"
        with open(input_path, "r", encoding="utf-8") as f:
            ast = parse_fflow(f.read())
    elif ext in [".twee", ".tw"]:
        input_format = "twee"
        with open(input_path, "r", encoding="utf-8") as f:
            ast = TweeParser().parse(f.read())
    elif ext == ".rpy":
        input_format = "renpy"
        with open(input_path, "r", encoding="utf-8") as f:
            ast = RenPyParser().parse(f.read())
    else:
        print(f"Error: Unknown input format '{ext}'. Supported: .fflow, .twee, .rpy")
        sys.exit(1)
        
    print(f"Parsed {len(ast)} nodes from {input_format} source.")

    # 2. Determine Output Format
    target_format = args.to
    if not target_format:
        # Default behavior:
        # fflow -> renpy (arbitrary default, or maybe error?)
        # twee/renpy -> fflow
        if input_format == "fflow":
            print("Please specify --to [twee|renpy]")
            sys.exit(1)
        else:
            target_format = "fflow"
    
    # 3. Transpile
    transpiler = None
    if target_format == "twee":
        transpiler = TweeTranspiler()
    elif target_format == "renpy":
        transpiler = RenPyTranspiler()
    elif target_format == "fflow":
        transpiler = FFlowTranspiler()
        
    output_text = transpiler.transpile(ast)
    
    # 4. Output
    if args.out:
        out_path = args.out
    else:
        # Default: output/<filename>.<ext>
        os.makedirs("output", exist_ok=True)
        filename = os.path.splitext(os.path.basename(input_path))[0]
        ext_map = {"twee": ".twee", "renpy": ".rpy", "fflow": ".fflow"}
        out_ext = ext_map.get(target_format, ".txt")
        out_path = os.path.join("output", f"{filename}{out_ext}")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output_text)
    print(f"Written to {out_path}")

if __name__ == "__main__":
    main()
