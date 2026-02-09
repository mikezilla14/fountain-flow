from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ast_nodes import (
    ScriptNode, ScriptAST, FrontmatterNode, SceneHeadingNode, SectionHeadingNode,
    ActionNode, DialogueNode, AssetNode, StateChangeNode, LogicNode,
    DecisionNode, ChoiceNode, JumpNode
)

class BaseTranspiler(ABC):
    def transpile(self, ast: ScriptAST) -> str:
        output = []
        for node in ast:
            output.append(self.visit(node))
        return "\n".join(filter(None, output))

    def visit(self, node: ScriptNode) -> str:
        method_name = f'visit_{node.__class__.__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ScriptNode) -> str:
        return ""

class TweeTranspiler(BaseTranspiler):
    """Transpiles to Twine (SugarCube format)."""

    def __init__(self):
        self.last_was_section = False

    def visit(self, node: ScriptNode) -> str:
        # Override visit to track state
        # We need to capture result, then update state
        # But specifically we care if PREVIOUS was section
        # So we update state AFTER visit? 
        # No, we need the state DURING the visit of the CURRENT node, based on PREVIOUS.
        
        # Actually visitor pattern usually dispatches.
        # Let's hook into the specific visit methods or just manage state here?
        # Simpler: In transpile() loop?
        # But transpile is in BaseTranspiler.
        # Let's override transpile or just update state in specific methods.
        # Problem: 'visit' calls 'visit_Node'.
        # Easier to just set the flag in visit_SectionHeading and clear in others.
        # But we need to know if we 'cleared' it in the *current* step vs *previous*.
        
        # Let's simple check:
        # If I am SceneHeading, check flag.
        # If I am SectionHeading, set flag=True (for next).
        # Else, set flag=False.
        
        # But I need to invoke the super().visit or specific logic.
        result = super().visit(node)
        
        # Update flag for NEXT node
        if isinstance(node, SectionHeadingNode):
            self.last_was_section = True
        elif isinstance(node, (SceneHeadingNode, FrontmatterNode)):
            # SceneHeading consumes the flag (handled inside visit_SceneHeadingNode)
            pass
        else:
            # Any other node clears the flag (content, logic, etc)
            # What if there's a comment? (Not in AST)
            self.last_was_section = False
            
        return result

    def visit_FrontmatterNode(self, node: FrontmatterNode) -> str:
        lines = [":: StoryInit"]
        for k, v in node.variables.items():
            lines.append(f"<<set ${k} to {v}>>")
        self.last_was_section = False # Explicit reset
        return "\n".join(lines) + "\n"

    def visit_SceneHeadingNode(self, node: SceneHeadingNode) -> str:
        text = f"**{node.text}**\n"
        if self.last_was_section:
            # We are already in a labeled passage (from SectionHeading).
            # Do NOT start a new passage. Just output the header.
            self.last_was_section = False # Consumed
            return f"\n{text}"
        else:
            # Start new passage
            self.last_was_section = False
            safe_id = node.text.replace(" ", "_").replace(".", "")
            return f"\n:: {safe_id}\n{text}"

    def visit_SectionHeadingNode(self, node: SectionHeadingNode) -> str:
        # Explicit anchor
        # Sets flag for next node via visit() override or we can set it here if we assume execution order
        # But visit() wraps this.
        # We'll rely on visit() or set it here?
        # If we set it here, it applies to *next* node? 
        # 'visit' calls this, then returns. 
        # So setting it here is fine.
        return f"\n:: {node.anchor}\n"

    def visit_ActionNode(self, node: ActionNode) -> str:
        return f"{node.text}\n"

    def visit_DialogueNode(self, node: DialogueNode) -> str:
        # Character: "Line"
        # Or just bold character?
        # **CHARACTER**: Line
        if node.parenthetical:
            return f"**{node.character}** ({node.parenthetical}): {node.text}\n"
        return f"**{node.character}**: {node.text}\n"

    def visit_AssetNode(self, node: AssetNode) -> str:
        # Twee/SugarCube doesn't have standard BG/SHOW macros.
        # Use HTML/CSS injection or comments.
        if node.asset_type == "BG":
           return f'<script>$("body").css("background-image", "url(\'{node.data}.jpg\')");</script>\n' 
        if node.asset_type == "SHOW":
           return f'<!-- SHOW: {node.data} -->\n'
        return f"<!-- Asset: {node.asset_type} {node.data} -->\n"

    def visit_StateChangeNode(self, node: StateChangeNode) -> str:
        # ~ VAR = VAL -> <<set $VAR to VAL>>
        expr = node.expression
        # Simple heuristic: word at start is var
        parts = expr.split(' ', 1)
        if parts:
             var = parts[0]
             rest = parts[1] if len(parts) > 1 else ""
             # Basic check to avoid double $ if user wrote $VAR
             if not var.startswith("$"):
                 var = "$" + var
             return f"<<set {var} {rest}>>\n"
        return f"<<set {expr}>>\n"

    def visit_LogicNode(self, node: LogicNode) -> str:
        if node.start_condition:
            cond = node.start_condition
            # Helper to add $ to vars in condition?
            # Ideally parser/AST handles this, but for now assumption:
            # Users write "VAR > 10". Twine needs "$VAR > 10".
            # Minimal replacement heuristic for common vars
            # Split by space and if token is identifier (and not keyword/number), add $
            tokens = cond.split()
            new_tokens = []
            for t in tokens:
                if t.isidentifier() and t not in ["true", "false", "and", "or", "not"]:
                    new_tokens.append(f"${t}")
                else:
                    new_tokens.append(t)
            cond = " ".join(new_tokens)
            return f"<<if {cond}>>"
        if node.is_else:
            return "<<else>>"
        if node.is_end:
            return "<<endif>>\n"
        return ""

    def visit_DecisionNode(self, node: DecisionNode) -> str:
        return f"\n{node.text}\n"

    def visit_ChoiceNode(self, node: ChoiceNode) -> str:
        # + [Label] Text -> #Target
        # [[Label|Target]]
        # In FFlow, logic indented under choice is meant to run IF chosen.
        # But in a flat list AST, the logic comes AFTER the choice in the passage.
        # This renders the logic check immediately.
        # To fix this properly requires hierarchical AST.
        # For now, we output the choice link.
        # If target exists, standard link: [[Label|Target]]
        # If no target (inline logic), we might need a "next" passage or link macro.
        
        target = node.target if node.target else ""
        text = node.text if node.text else node.label
        
        if target:
            return f"[[{text}|{target}]]\n"
        else:
            # Inline logic case (detective.fflow style)
            # We can't easily wrap the *next* nodes without lookahead.
            # Fallback: Render a link that does nothing? Or breaks?
            # Using a setter link: <<link "Label">>...<</link>> is best but we need to capture the body.
            # Given limitations, we output a comment warning.
            return f"<!-- Choice '{node.label}' has inline logic which is not fully supported in flat Twee export yet. -->\n[[{text}|NEXT_STEP]]\n"

    def visit_JumpNode(self, node: JumpNode) -> str:
        return f"<<goto \"{node.target}\">>\n"


class RenPyTranspiler(BaseTranspiler):
    """Transpiles to Ren'Py script."""
    
    def __init__(self):
        self.indent_level = 0

    def indent(self, s: str) -> str:
        return "    " * self.indent_level + s

    def visit_FrontmatterNode(self, node: FrontmatterNode) -> str:
        lines = ["label start:"]
        self.indent_level += 1
        for k, v in node.variables.items():
            lines.append(self.indent(f"$ {k} = {v}"))
        return "\n".join(lines) + "\n"

    def visit_SceneHeadingNode(self, node: SceneHeadingNode) -> str:
        # RenPy uses labels for flow, but scene headings are visual.
        # scene bg name
        # We might not make it a label unless it's a jump target.
        # But we need new labels for flow.
        # Let's map Scene Headings to labels?
        # Or just "scene bg" if we have asset.
        # For now, treat as comment or scene statement
        return self.indent(f"# {node.text}\n")

    def visit_SectionHeadingNode(self, node: SectionHeadingNode) -> str:
        # This IS a label
        self.indent_level = 0 # Reset indent for labels
        s = f"label {node.anchor}:\n"
        self.indent_level = 1
        return s

    def visit_ActionNode(self, node: ActionNode) -> str:
        return self.indent(f"\"{node.text}\"\n")

    def visit_DialogueNode(self, node: DialogueNode) -> str:
        # char "text"
        # Need to define chars? For now use string literal for char name
        char_id = node.character.title().replace(" ", "")
        return self.indent(f'{char_id} "{node.text}"\n')

    def visit_AssetNode(self, node: AssetNode) -> str:
        if node.asset_type == "BG":
            return self.indent(f"scene {node.data}\n")
        if node.asset_type == "SHOW":
            return self.indent(f"show {node.data}\n")
        if node.asset_type == "MUSIC":
             return self.indent(f"play music \"{node.data}\"\n")
        return self.indent(f"# Asset: {node.asset_type} {node.data}\n")

    def visit_StateChangeNode(self, node: StateChangeNode) -> str:
        return self.indent(f"$ {node.expression}\n")

    def visit_LogicNode(self, node: LogicNode) -> str:
        
        # Rethink: LogicNode(IF) returns string, then we indent future lines.
        if node.start_condition:
            s = self.indent(f"if {node.start_condition}:\n")
            self.indent_level += 1
            return s
        
        if node.is_else:
            self.indent_level -= 1
            s = self.indent("else:\n")
            self.indent_level += 1
            return s
            
        if node.is_end:
            self.indent_level -= 1
            return ""
        return ""

    def visit_DecisionNode(self, node: DecisionNode) -> str:
        # RenPy menu
        s = self.indent(f"menu:\n")
        self.indent_level += 1
        s += self.indent(f"\"{node.text}\"\n")
        return s

    def visit_ChoiceNode(self, node: ChoiceNode) -> str:
        # In menu block
        # "Label":
        #    jump Target
        s = self.indent(f"\"{node.label}\":\n")
        self.indent_level += 1
        if node.text:
             s += self.indent(f"\"{node.text}\"\n")
        s += self.indent(f"jump {node.target}\n")
        self.indent_level -= 1
        return s

    def visit_JumpNode(self, node: JumpNode) -> str:
        return self.indent(f"jump {node.target}\n")

class FFlowTranspiler(BaseTranspiler):
    """Transpiles back to .fflow format."""

    def visit_FrontmatterNode(self, node: FrontmatterNode) -> str:
        lines = ["$ " + k + ": " + str(v) for k, v in node.variables.items()]
        return "\n".join(lines) + "\n===\n"

    def visit_SceneHeadingNode(self, node: SceneHeadingNode) -> str:
        return f"\n{node.text}\n"

    def visit_SectionHeadingNode(self, node: SectionHeadingNode) -> str:
        return f"\n# {node.anchor}\n"

    def visit_ActionNode(self, node: ActionNode) -> str:
        return f"{node.text}\n"

    def visit_DialogueNode(self, node: DialogueNode) -> str:
        s = f"\n{node.character}\n"
        if node.parenthetical:
            s += f"{node.parenthetical}\n"
        s += f"{node.text}\n"
        return s

    def visit_AssetNode(self, node: AssetNode) -> str:
        return f"! {node.asset_type}: {node.data}\n"

    def visit_StateChangeNode(self, node: StateChangeNode) -> str:
        return f"~ {node.expression}\n"

    def visit_LogicNode(self, node: LogicNode) -> str:
        if node.start_condition:
            return f"(IF: {node.start_condition})\n"
        if node.is_else:
            return "(ELSE)\n"
        if node.is_end:
            return "(END)\n"
        return ""

    def visit_DecisionNode(self, node: DecisionNode) -> str:
        return f"\n? {node.text}\n"

    def visit_ChoiceNode(self, node: ChoiceNode) -> str:
        # + [Label] Text -> #Target
        target = f" -> #{node.target}" if node.target else ""
        return f"+ [{node.label}] {node.text}{target}\n"

    def visit_JumpNode(self, node: JumpNode) -> str:
        return f"-> #{node.target}\n"
