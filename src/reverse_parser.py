import re
from typing import List, Optional
from ast_nodes import (
    ScriptNode, ScriptAST, FrontmatterNode, SceneHeadingNode, SectionHeadingNode,
    ActionNode, DialogueNode, AssetNode, StateChangeNode, LogicNode,
    DecisionNode, ChoiceNode, JumpNode
)

class TweeParser:
    """Parses Twee (SugarCube) text into FFlow AST."""
    
    REGEX_PASSAGE = r'^::\s*(.+)'
    REGEX_MACRO_SET = r'<<set\s+\$(\w+)\s*(?:to|=)\s*(.+)>>'
    REGEX_MACRO_IF = r'<<if\s+(.+)>>'
    REGEX_MACRO_ELSE = r'<<else>>'
    REGEX_MACRO_ENDIF = r'<<endif>>' # or <</if>>
    REGEX_LINK = r'\[\[(.*?)(?:\|(.*?))?\]\]' # [[Label|Target]] or [[Target]]
    REGEX_MACRO_GOTO = r'<<goto\s+"(.+)">>'
    REGEX_MACRO_BG = r'<<bg\s+"(.+)">>'
    REGEX_MACRO_SHOW = r'<<show\s+"(.+)">>'

    def parse(self, text: str) -> ScriptAST:
        nodes: ScriptAST = []
        lines = text.split('\n')
        
        current_scene_nodes = []
        
        # Frontmatter collection
        frontmatter_vars = {}
        in_story_init = False

        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Passage Header
            match = re.match(self.REGEX_PASSAGE, line)
            if match:
                passage_name = match.group(1).strip()
                if passage_name == "StoryInit":
                    in_story_init = True
                    continue
                else:
                    in_story_init = False
                    # New Scene/Section
                    # Heuristic: If name starts with "INT." or "EXT.", strictly SceneHeading
                    # Else SectionHeading
                    if passage_name.startswith(("INT.", "EXT.")):
                        nodes.append(SceneHeadingNode(scene_id=passage_name, text=passage_name))
                    else:
                        nodes.append(SectionHeadingNode(text=passage_name, anchor=passage_name))
                continue

            if in_story_init:
                # Expect set macros
                match = re.match(self.REGEX_MACRO_SET, line)
                if match:
                    var = match.group(1)
                    val = match.group(2)
                    frontmatter_vars[var] = val
                # If we detect end of StoryInit block (next passage), we emitted frontmatter?
                # Actually we can emit frontmatter immediately if we collected it first?
                # AST order matters. Frontmatter should be first.
                # If we are in StoryInit, collect vars.
                continue

            # Check logic macros
            match = re.match(self.REGEX_MACRO_IF, line)
            if match:
                nodes.append(LogicNode(start_condition=match.group(1)))
                continue
            
            if re.match(self.REGEX_MACRO_ELSE, line):
                nodes.append(LogicNode(is_else=True))
                continue
                
            if re.match(self.REGEX_MACRO_ENDIF, line) or line == "<</if>>":
                nodes.append(LogicNode(is_end=True))
                continue
            
            match = re.match(self.REGEX_MACRO_SET, line)
            if match:
                nodes.append(StateChangeNode(expression=f"{match.group(1)} = {match.group(2)}"))
                continue

            match = re.match(self.REGEX_MACRO_BG, line)
            if match:
                nodes.append(AssetNode(asset_type="BG", data=match.group(1)))
                continue
                
            match = re.match(self.REGEX_MACRO_SHOW, line)
            if match:
                nodes.append(AssetNode(asset_type="SHOW", data=match.group(1)))
                continue

            match = re.match(self.REGEX_MACRO_GOTO, line)
            if match:
                nodes.append(JumpNode(target=match.group(1)))
                continue

            # Links (Choice)
            # Twee links can be inline. "Text [[Link]]"
            # Fountain-Flow choices are block level + [Label].
            # If line is JUST a link: [[Target]] -> Jump? Or Choice with label=Target?
            # If line has text and link: "Go south [[South|Room]]" -> Choice
            
            link_matches = list(re.finditer(self.REGEX_LINK, line))
            if link_matches:
                # Assume standard Choice syntax if line contains a link
                # Parsing mixed text/links is hard to map perfectly to + [Label] Text
                # Let's simple-case: One link per line = Choice
                for m in link_matches:
                    label = m.group(1)
                    target = m.group(2)
                    
                    if not target: 
                        # [[Target]] -> Label=Target, Target=Target
                        target = label
                    else:
                        # [[Label|Target]]
                        pass
                        
                    # Text before link?
                    pre_text = line[:m.start()].strip()
                    nodes.append(ChoiceNode(label=label, text=pre_text, target=target))
                continue

            # Dialogue vs Action
            # Twee doesn't distinguish. **Char**: Text is common convention I used in Transpiler.
            if line.startswith("**") and "**:" in line:
                parts = line.split("**:", 1)
                char = parts[0].replace("**", "").strip()
                text = parts[1].strip()
                nodes.append(DialogueNode(character=char, text=text))
                continue

            nodes.append(ActionNode(text=line))

        # Prepend frontmatter if collected
        # Prepend frontmatter if collected
        if frontmatter_vars:
            nodes.insert(0, FrontmatterNode(variables=frontmatter_vars))

        return nodes

class RenPyParser:
    """Parses Ren'Py script into FFlow AST."""
    
    REGEX_LABEL = r'^label\s+(\w+):'
    REGEX_VAR = r'^\$\s*(\w+)\s*=\s*(.+)' # $ var = val
    REGEX_SCENE = r'^scene\s+(.+)'
    REGEX_SHOW = r'^show\s+(.+)'
    REGEX_MENU = r'^menu:'
    REGEX_JUMP = r'^jump\s+(\w+)'
    REGEX_IF = r'^if\s+(.+):'
    REGEX_ELSE = r'^else:'
    REGEX_DIALOGUE = r'^(\w+)\s+"(.+)"' # char "text"
    REGEX_ACTION = r'^"(.+)"' # "text"
    
    def parse(self, text: str) -> ScriptAST:
        nodes: ScriptAST = []
        lines = text.split('\n')
        
        frontmatter_vars = {}
        in_menu = False
        current_choice_label = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('#'): continue # Comment
            
            # Label
            match = re.match(self.REGEX_LABEL, line)
            if match:
                label = match.group(1)
                if label == "start":
                    continue # Treat as entry point
                nodes.append(SectionHeadingNode(text=label, anchor=label))
                continue
            
            # Var (Frontmatter or State)
            match = re.match(self.REGEX_VAR, line)
            if match:
                # If at top level or start, maybe frontmatter?
                # For now, treat as StateChangeNode unless we want to be smart
                nodes.append(StateChangeNode(expression=f"{match.group(1)} = {match.group(2)}"))
                continue
                
            # Assets
            match = re.match(self.REGEX_SCENE, line)
            if match:
                nodes.append(AssetNode(asset_type="BG", data=match.group(1)))
                continue
            
            match = re.match(self.REGEX_SHOW, line)
            if match:
                nodes.append(AssetNode(asset_type="SHOW", data=match.group(1)))
                continue
                
            # Menu
            if re.match(self.REGEX_MENU, line):
                in_menu = True
                nodes.append(DecisionNode(text="Choice"))
                continue
                
            # Choice Items (Action regex but inside menu)
            if in_menu:
                # "Choice Label":
                if line.endswith(':'):
                    current_choice_label = line.strip('": ')
                    continue
                
                # Jump inside choice
                match = re.match(self.REGEX_JUMP, line)
                if match and current_choice_label:
                    nodes.append(ChoiceNode(label=current_choice_label, text="", target=match.group(1)))
                    current_choice_label = None
                    continue
                
                # If we hit something else, maybe end of menu?
                # RenPy structure is tricky without indentation tracking.
                # But for simple reverse, let's assume menu ends when we hit non-indented or jump.
                # Actually, standard flow: menu -> choice -> jump.
            
            # Logic
            match = re.match(self.REGEX_IF, line)
            if match:
                nodes.append(LogicNode(start_condition=match.group(1)))
                continue
            
            if re.match(self.REGEX_ELSE, line):
                nodes.append(LogicNode(is_else=True))
                continue

            # Need to detect end of block?
            # Without indentation, we can't reliably detect END.
            # But we can emit it if we see unrelated node?
            # Or reliance on user manual fix up.
            
            # Dialogue
            match = re.match(self.REGEX_DIALOGUE, line)
            if match:
                nodes.append(DialogueNode(character=match.group(1), text=match.group(2)))
                continue
                
            # Action
            match = re.match(self.REGEX_ACTION, line)
            if match:
                nodes.append(ActionNode(text=match.group(1)))
                continue
                
            # Jump (outside menu)
            match = re.match(self.REGEX_JUMP, line)
            if match:
                nodes.append(JumpNode(target=match.group(1)))
                continue

        return nodes
