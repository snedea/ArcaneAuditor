# In pmd_script_parser.py
from lark import Lark
from pathlib import Path

# Load the grammar from the external .lark file
def load_grammar():
    """Load the PMD script grammar from the .lark file."""
    grammar_path = Path(__file__).parent / "pmd_script_grammar.lark"
    
    try:
        with open(grammar_path, 'r', encoding='utf-8') as f:
            grammar_content = f.read()
        return grammar_content
    except FileNotFoundError:
        raise FileNotFoundError(f"Grammar file not found: {grammar_path}")
    except Exception as e:
        raise RuntimeError(f"Error loading grammar file: {e}")

# Load the grammar and create parser
try:
    pmd_script_grammar = load_grammar()
    pmd_script_parser = Lark(pmd_script_grammar, start='program', parser='lalr')
except Exception as e:
    print(f"Warning: Failed to load grammar: {e}")