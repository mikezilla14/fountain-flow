import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from core_parser import parse
from ast_nodes import (
    SceneHeadingNode, DialogueNode, ActionNode, AssetNode, 
    StateChangeNode, LogicNode, DecisionNode, ChoiceNode, 
    JumpNode, FrontmatterNode
)

def test_frontmatter():
    script = """$ THEME: Noir
$ HP: 100
===
Action line."""
    nodes = parse(script)
    assert isinstance(nodes[0], FrontmatterNode)
    assert nodes[0].variables == {"THEME": "Noir", "HP": "100"}
    assert isinstance(nodes[1], ActionNode)

def test_scene_heading():
    script = "INT. BAR - NIGHT"
    nodes = parse(script)
    assert isinstance(nodes[0], SceneHeadingNode)
    assert nodes[0].text == "INT. BAR - NIGHT"

def test_dialogue():
    script = """
EVE
(angry)
Why are you here?
    """
    nodes = parse(script.strip())
    # Note: Whitespace handling might need adjustment in parser if strictly testing "strip()"d input
    # But let's see what the parser does with the newlines
    
    # My simple parser loop might catch empty lines as ActionNodes or skip them
    # Let's clean up the input for the test
    clean_script = "EVE\n(angry)\nWhy are you here?"
    nodes = parse(clean_script)
    assert isinstance(nodes[0], DialogueNode)
    assert nodes[0].character == "EVE"
    assert nodes[0].parenthetical == "(angry)"
    assert nodes[0].text == "Why are you here?"

def test_assets():
    script = "! BG: ruins\n! MUSIC: tension"
    nodes = parse(script)
    assert isinstance(nodes[0], AssetNode)
    assert nodes[0].asset_type == "BG"
    assert nodes[0].data == "ruins"
    assert nodes[1].asset_type == "MUSIC"
    assert nodes[1].data == "tension"

def test_logic_flow():
    script = """
(IF: HP > 0)
You are alive.
(ELSE)
You are dead.
(END)
~ HP -= 10
-> #GAME_OVER
    """
    nodes = parse(script.strip())
    # Depending on how I implemented the parser loop, we expect:
    # LogicNode(IF), ActionNode, LogicNode(ELSE), ActionNode, LogicNode(END), StateChangeNode, JumpNode
    
    # Filter out empty ActionNodes if any (my parser currently skips empty lines)
    relevant_nodes = [n for n in nodes if not (isinstance(n, ActionNode) and not n.text.strip())]
    
    assert isinstance(relevant_nodes[0], LogicNode)
    assert relevant_nodes[0].start_condition == "HP > 0"
    
    assert isinstance(relevant_nodes[1], ActionNode)
    assert relevant_nodes[1].text == "You are alive."
    
    assert isinstance(relevant_nodes[2], LogicNode)
    assert relevant_nodes[2].is_else
    
    assert isinstance(relevant_nodes[3], ActionNode)
    
    assert isinstance(relevant_nodes[4], LogicNode)
    assert relevant_nodes[4].is_end
    
    assert isinstance(relevant_nodes[5], StateChangeNode)
    assert relevant_nodes[5].expression == "HP -= 10"
    
    assert isinstance(relevant_nodes[6], JumpNode)
    assert relevant_nodes[6].target == "GAME_OVER"

def test_choice():
    script = "? What do?\n+ [Attack] Hit him -> #FIGHT"
    nodes = parse(script)
    assert isinstance(nodes[0], DecisionNode)
    assert nodes[0].text == "What do?"
    assert isinstance(nodes[1], ChoiceNode)
if __name__ == "__main__":
    try:
        test_frontmatter()
        print("test_frontmatter PASSED")
        test_scene_heading()
        print("test_scene_heading PASSED")
        test_dialogue()
        print("test_dialogue PASSED")
        test_assets()
        print("test_assets PASSED")
        test_logic_flow()
        print("test_logic_flow PASSED")
        test_choice()
        print("test_choice PASSED")
        print("ALL TESTS PASSED")
    except AssertionError as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
