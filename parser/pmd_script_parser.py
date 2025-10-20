# In pmd_script_parser.py
from lark import Lark
from pathlib import Path
from .pmd_preprocessor import PMDPreprocessor

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

# Global parser and preprocessor instances
pmd_script_parser = None
preprocessor = None

def get_pmd_script_parser():
    """Get the PMD script parser, creating it if necessary."""
    global pmd_script_parser, preprocessor
    if pmd_script_parser is None:
        try:
            pmd_script_grammar = load_grammar()
            pmd_script_parser = Lark(pmd_script_grammar, start='program', parser='lalr', propagate_positions=True)
            preprocessor = PMDPreprocessor()
        except Exception as e:
            print(f"Warning: Failed to load grammar with LALR: {e}")
            # Fallback to Earley if LALR fails
            try:
                pmd_script_grammar = load_grammar()
                pmd_script_parser = Lark(pmd_script_grammar, start='program', parser='earley', propagate_positions=True)
                preprocessor = None
                print("Fallback: Using Earley parser")
            except Exception as e2:
                print(f"Warning: Failed to load grammar with Earley: {e2}")
                # Final fallback to minimal grammar
                pmd_script_parser = Lark("?program: source_elements?\n?source_elements: statement+\n?statement: IDENTIFIER", start='program', parser='earley')
                preprocessor = None
    
    return pmd_script_parser

def parse_with_preprocessor(code: str):
    """Parse code using the preprocessor and LALR parser, with fallback to Earley."""
    global preprocessor
    
    # Ensure we have a preprocessor
    if preprocessor is None:
        try:
            preprocessor = PMDPreprocessor()
        except Exception as e:
            print(f"Warning: Failed to create preprocessor: {e}")
            # Fallback to direct parsing if preprocessor creation fails
            return get_pmd_script_parser().parse(code)
    
    # Preprocess the code to disambiguate braces
    preprocessed_code = preprocessor.preprocess(code)
    
    # Log any warnings from preprocessing
    if preprocessor.warnings:
        for warning in preprocessor.warnings:
            print(f"Preprocessor warning: {warning}")
    
    # Try parsing with LALR first
    try:
        return get_pmd_script_parser().parse(preprocessed_code)
    except Exception as e:
        # If LALR fails (e.g., due to newline issues), fall back to Earley
        try:
            from lark import Lark
            grammar = load_grammar()
            earley_parser = Lark(grammar, start='program', parser='earley', propagate_positions=True)
            return earley_parser.parse(preprocessed_code)  # Use preprocessed code
        except Exception as e2:
            print(f"Warning: Both LALR and Earley parsing failed: {e2}")
            # Final fallback - try minimal parsing
            try:
                minimal_parser = Lark("?program: source_elements?\n?source_elements: statement+\n?statement: IDENTIFIER", start='program', parser='earley')
                return minimal_parser.parse(code)
            except Exception as e3:
                print(f"Warning: All parsing attempts failed: {e3}")
                return None