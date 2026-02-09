import re
from typing import List, Optional, Dict, Any
from ast_nodes import (
    ScriptNode, ScriptAST, FrontmatterNode, SceneHeadingNode, SectionHeadingNode,
    ActionNode, DialogueNode, AssetNode, StateChangeNode, LogicNode,
    DecisionNode, ChoiceNode, JumpNode
)

class FFlowParser:
    # Regex Patterns
    REGEX_ASSET = r'^\s*!\s*(\w+):\s*(.+)'
    REGEX_STATE = r'^\s*~\s*(.+)'
    REGEX_DECISION = r'^\s*\?\s*(.+)'
    # Adjusted Choice Regex to be more flexible with whitespace and content
    REGEX_CHOICE = r'^\s*\+\s*\[(.*?)\]\s*(.*?)\s*(?:->\s*#(\w+))?$' 
    REGEX_CONDITIONAL = r'^\s*\(IF:\s*(.+)\)'
    REGEX_ELSE = r'^\s*\(ELSE\)'
    REGEX_END = r'^\s*\(END\)'
    REGEX_JUMP = r'^\s*->\s*#(\w+)'
    REGEX_SECTION = r'^\s*#\s*(\w+)'
    REGEX_SCENE = r'^(INT\.|EXT\.|EST\.|INT\./EXT\.|I/E)\s*(.+)'
    REGEX_CHARACTER = r'^([A-Z0-9 ]*[A-Z0-9]+)(\s*\(.*\))?$' # Simple character name check
    REGEX_PARENTHETICAL = r'^\s*(\(.*\))\s*$'

    def __init__(self):
        self.nodes: ScriptAST = []
        self.in_frontmatter = False
        self.current_frontmatter = {}

    def parse(self, script_text: str) -> ScriptAST:
        self.nodes = []
        lines = script_text.split('\n')
        
        # Pre-process for frontmatter
        if lines and lines[0].strip() == '$': # Start of generic frontmatter? 
            # The spec says "$ VAR: Value", so maybe it starts directly with definitions on line 1?
            # Spec says "Every .fflow document may optionally begin with a generic YAML-style frontmatter block... Symbol: $ ... Termination: ==="
            # Example shows:
            # $ THEME: Noir
            # $ PLAYER_HP: 100
            # ===
            pass

        idx = 0
        while idx < len(lines):
            line = lines[idx].strip()
            
            # Skip empty lines, but maybe keep them as spacers if needed? 
            # Fountain usually ignores single empty lines but needs them for distinct elements.
            if not line:
                idx += 1
                continue

            # 1. Frontmatter Handling
            if line.startswith('$') and '===' not in line:
                if not self.in_frontmatter:
                     # Check if this is the very first block
                     if not self.nodes:
                         self.in_frontmatter = True
                
                if self.in_frontmatter:
                    # Parse variable
                    parts = line.lstrip('$').split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = parts[1].strip()
                        self.current_frontmatter[key] = val
                    idx += 1
                    continue
            
            if line == '===' and self.in_frontmatter:
                self.in_frontmatter = False
                self.nodes.append(FrontmatterNode(variables=self.current_frontmatter))
                idx += 1
                continue

            # 2. Flow Extensions Check
            
            # Asset
            match = re.match(self.REGEX_ASSET, line)
            if match:
                self.nodes.append(AssetNode(asset_type=match.group(1), data=match.group(2)))
                idx += 1
                continue

            # State Modification
            match = re.match(self.REGEX_STATE, line)
            if match:
                self.nodes.append(StateChangeNode(expression=match.group(1)))
                idx += 1
                continue
                
            # Decision
            match = re.match(self.REGEX_DECISION, line)
            if match:
                self.nodes.append(DecisionNode(text=match.group(1)))
                idx += 1
                continue

            # Choice
            match = re.match(self.REGEX_CHOICE, line)
            if match:
                target = match.group(3) if match.group(3) else ""
                self.nodes.append(ChoiceNode(
                    label=match.group(1),
                    text=match.group(2),
                    target=target
                ))
                idx += 1
                continue

            # Jump
            match = re.match(self.REGEX_JUMP, line)
            if match:
                self.nodes.append(JumpNode(target=match.group(1)))
                idx += 1
                continue
            
            # Logic Blocks
            match = re.match(self.REGEX_CONDITIONAL, line)
            if match:
                self.nodes.append(LogicNode(start_condition=match.group(1)))
                idx += 1
                continue
            
            if re.match(self.REGEX_ELSE, line):
                self.nodes.append(LogicNode(is_else=True))
                idx += 1
                continue
                
            if re.match(self.REGEX_END, line):
                self.nodes.append(LogicNode(is_end=True))
                idx += 1
                continue

            # 3. Standard Fountain Elements
            
            # Section Heading
            match = re.match(self.REGEX_SECTION, line)
            if match:
                self.nodes.append(SectionHeadingNode(text=line, anchor=match.group(1)))
                idx += 1
                continue

            # Scene Heading (INT/EXT)
            match = re.match(self.REGEX_SCENE, line)
            if match:
                self.nodes.append(SceneHeadingNode(scene_id="SCENE", text=line))
                idx += 1
                continue
            
            # Character (All caps, not a scene heading)
            # This is tricky without lookahead for dialogue.
            # Standard Fountain: "Null lines followed by all-caps line followed by text is dialogue"
            if re.match(self.REGEX_CHARACTER, line):
                # Check next line for dialogue
                if idx + 1 < len(lines) and lines[idx+1].strip():
                    character_name = line
                    parenthetical = None
                    dialogue_text = ""
                    
                    next_line_idx = idx + 1
                    next_line = lines[next_line_idx].strip()
                    
                    # Check for parenthetical
                    p_match = re.match(self.REGEX_PARENTHETICAL, next_line)
                    if p_match:
                        parenthetical = p_match.group(1)
                        next_line_idx += 1
                        if next_line_idx < len(lines):
                            next_line = lines[next_line_idx].strip()
                    
                    # Assume rest is dialogue until empty line
                    dialogue_lines = []
                    while next_line_idx < len(lines):
                        d_line = lines[next_line_idx].strip()
                        if not d_line:
                            break
                        dialogue_lines.append(d_line)
                        next_line_idx += 1
                    
                    dialogue_text = " ".join(dialogue_lines)
                    
                    self.nodes.append(DialogueNode(
                        character=character_name,
                        text=dialogue_text,
                        parenthetical=parenthetical
                    ))
                    idx = next_line_idx
                    continue

            # Fallback: Action
            self.nodes.append(ActionNode(text=line))
            idx += 1

        return self.nodes

def parse(script_text: str) -> ScriptAST:
    parser = FFlowParser()
    return parser.parse(script_text)
