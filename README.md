# Fountain-Flow (.fflow)
![alt text](https://img.shields.io/badge/License-MIT-yellow.svg)

![alt text](https://img.shields.io/badge/Standard-Fountain%201.1-blue.svg)

![alt text](https://img.shields.io/badge/Status-Experimental-orange.svg)

**Fountain-Flow** is a syntax superset and parsing engine that bridges the gap between **Screenwriting** and **Game Development**.

It allows writers to craft interactive narratives using the industry-standard **Fountain** screenplay format, while embedding:
- Game Logic
- Branching Choices
- Asset Management

All in a way that is **human-readable** and **machine-parsable**.

## 🚀 The Problem

Visual Novel and RPG writers often face a dilemma:
- **Write in Word/Fountain**: Great for creative flow and dialogue, but requires a developer to manually "port" the script into code later.
- **Write in Code (Ren'Py/Twine/JSON)**: Great for logic, but kills the creative momentum and is unreadable for editors/producers.

## 💡 The Solution

**Fountain-Flow** allows you to write a screenplay that compiles into a game.

It preserves the "invisible syntax" philosophy of Fountain—formatting dictates function—while adding strict anchors for the Game Engine.

## Key Features

- **Narrative First**: 100% compatible with standard Fountain. It looks like a script, not code.
- **Engine Agnostic**: Compiles to Ren'Py (.rpy), Twine (.twee), or raw JSON AST for Unity/Godot/Unreal.
- **Explicit State**: Manage variables (Health, Inventory, Relationship) directly in the script.
- **Asset Pipelines**: Define Backgrounds, Sprites, and Audio using the `!` "Bang" operator.
- **LLM Optimized**: Designed to be the perfect "Intermediate Representation" for AI coding agents. It separates narrative context from logic, allowing LLMs to generate game code without hallucinating story details.

## 📝 Syntax Example

A `.fflow` file looks like a screenplay, but with super-powers:

```fountain
$ PLAYER_HP: 100
$ HAS_KEY: false
===

INT. ANCIENT RUINS - NIGHT
! BG: ruins_dark_stormy
! MUSIC: tension_loop_v2

The wind howls through the cracked masonry.

! SHOW: Elara, nervous, left
ELARA
We shouldn't be here.

? What do you do?

+ [Force Door] Kick the door open.
    (IF: PLAYER_HP > 10)
    ~ PLAYER_HP -= 5
    The wood splinters. You are in.
    -> #SCENE_INTERIOR
    (ELSE)
    You are too weak.
    -> #SCENE_FAIL

+ [Use Key] Unlock it carefully.
    (IF: HAS_KEY == true)
    The mechanism clicks. Smooth.
    -> #SCENE_INTERIOR
```

## 🛠 Architecture

Fountain-Flow is built as a modular compilation pipeline:
- **Lexer**: Tokenizes the script, separating "Narrative Blocks" (Dialogue, Action) from "Logic Blocks" (Choice, State, Assets).
- **Parser**: Constructs an Abstract Syntax Tree (AST).
- **Transpiler**: Visits the AST and generates engine-specific code.

### The "Dual-Pass" Philosophy
- **Pass 1 (Narrative)**: Can be stripped to generate a clean PDF for voice actors or editors (hiding all logic).
- **Pass 2 (Logic)**: Extracts the decision tree and state requirements for developers.

## 🤖 AI & LLM Integration

Fountain-Flow is designed as the ideal format for AI-Assisted Storytelling:
- **Context Window Optimization**: The parser extracts only the relevant variables for a scene, allowing an LLM to validate logic without reading the whole novel.
- **Asset Generation**: The `! BG:` and `! SHOW:` tags can be fed directly into Image Generation pipelines (Stable Diffusion/Midjourney) to auto-generate storyboards.

## 📦 Installation & Usage

*(Coming Soon: PyPi package release)*

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/fountain-flow.git

# Install dependencies
pip install -r requirements.txt

# Run the parser example
python src/parser.py examples/detective.fflow
```

## ⚖️ Attribution & License

Fountain-Flow is released under the **MIT License**.

This project uses the Fountain markup syntax developed by John August and Nima Yousefi.
- Original Specification: [fountain.io](https://fountain.io)

Fountain-Flow is an independent open-source project and is not endorsed by the creators of Fountain.