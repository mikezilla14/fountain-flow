import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from reverse_parser import TweeParser, RenPyParser
from ast_nodes import (
    ScriptNode, ScriptAST, FrontmatterNode, SceneHeadingNode, SectionHeadingNode,
    ActionNode, DialogueNode, AssetNode, StateChangeNode, LogicNode,
    DecisionNode, ChoiceNode, JumpNode
)

def test_twee_parser():
    script = """
:: StoryInit
<<set $hp to 100>>

:: Start [tag]
Intro text.
**EVE**: Hello.
[[Go North|NorthRoom]]
<<if $hp > 10>>
    Alive.
<<endif>>
"""
    parser = TweeParser()
    nodes = parser.parse(script.strip())
    
    # Check Frontmatter
    assert isinstance(nodes[0], FrontmatterNode)
    assert nodes[0].variables['hp'] == '100'
    
    # Check Scene Heading (Start) - heuristic: if not INT/EXT, it's SectionHeading
    # "Start" -> SectionHeading
    assert isinstance(nodes[1], SectionHeadingNode)
    assert nodes[1].text == "Start [tag]"
    
    # Action
    assert isinstance(nodes[2], ActionNode)
    assert nodes[2].text == "Intro text."
    
    # Dialogue
    assert isinstance(nodes[3], DialogueNode)
    assert nodes[3].character == "EVE"
    assert nodes[3].text == "Hello."
    
    # Link -> Choice
    # [[Go North|NorthRoom]]
    # Node index depends on if there were empty lines skipped
    # My parser skips empty lines.
    
    # Check for ChoiceNode
    choice_node = next((n for n in nodes if isinstance(n, ChoiceNode)), None)
    assert choice_node is not None
    assert choice_node.label == "Go North"
    assert choice_node.target == "NorthRoom"
    
    # Check Logic
    logic_node = next((n for n in nodes if isinstance(n, LogicNode) and n.start_condition), None)
    assert logic_node is not None
    assert "$hp > 10" in logic_node.start_condition

def test_renpy_parser():
    script = """
label start:
    $ hp = 100
    scene bg room
    show e happy
    e "Hello"
    "It is dark."
    menu:
        "Go West":
            jump west_room
    if hp < 0:
        "Dead"
"""
    parser = RenPyParser()
    nodes = parser.parse(script.strip())
    
    # label start skipped? 
    # My code: if label == "start": continue
    
    # $ hp = 100 -> StateChange
    state_node = next((n for n in nodes if isinstance(n, StateChangeNode)), None)
    assert state_node is not None
    assert state_node.expression == "hp = 100"
    
    # scene bg room -> Asset(BG)
    bg_node = next((n for n in nodes if isinstance(n, AssetNode) and n.asset_type == "BG"), None)
    assert bg_node is not None
    assert bg_node.data == "bg room"
    
    # show e happy -> Asset(SHOW)
    show_node = next((n for n in nodes if isinstance(n, AssetNode) and n.asset_type == "SHOW"), None)
    assert show_node is not None
    assert show_node.data == "e happy"
    
    # e "Hello" -> Dialogue
    dial_node = next((n for n in nodes if isinstance(n, DialogueNode)), None)
    assert dial_node is not None
    assert dial_node.character == "e"
    assert dial_node.text == "Hello"
    
    # menu -> Decision
    dec_node = next((n for n in nodes if isinstance(n, DecisionNode)), None)
    assert dec_node is not None
    
    # Choice
    choice_node = next((n for n in nodes if isinstance(n, ChoiceNode)), None)
    assert choice_node is not None
    assert choice_node.label == "Go West"
    assert choice_node.target == "west_room"

if __name__ == "__main__":
    try:
        test_twee_parser()
        print("test_twee_parser PASSED")
        test_renpy_parser()
        print("test_renpy_parser PASSED")
        print("ALL TESTS PASSED")
    except AssertionError as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
