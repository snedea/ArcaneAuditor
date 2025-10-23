# In pmd_script_parser.py
from lark import Lark
from pathlib import Path
import sys
from importlib import resources
from .pmd_preprocessor import PMDPreprocessor

# Cache for grammar content and warning flags
_cached_grammar = None
_grammar_warned = False

def _read_grammar_from_disk() -> str:
    """Read grammar from disk using fallback methods."""
    try:
        # Primary method: use importlib.resources for robustness
        return resources.files(__package__).joinpath("pmd_script_grammar.lark").read_text(encoding="utf-8")
    except Exception:
        # Fallback to existing sys._MEIPASS logic with safer path matching
        if hasattr(sys, "_MEIPASS"):
            grammar_path = Path(sys._MEIPASS) / Path(__file__).name.replace(".py", ".lark")
        else:
            grammar_path = Path(__file__).with_name("pmd_script_grammar.lark")
        
        try:
            with open(grammar_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Grammar file not found: {grammar_path}")
        except Exception as e:
            raise RuntimeError(f"Error loading grammar file: {e}")

def load_grammar() -> str:
    """Load the PMD script grammar from the .lark file (cached)."""
    global _cached_grammar
    if _cached_grammar is None:
        _cached_grammar = _read_grammar_from_disk()
    return _cached_grammar

# Global parser and preprocessor instances
pmd_script_parser = None
preprocessor = None

def get_pmd_script_parser():
    """Get the PMD script parser, creating it if necessary."""
    global pmd_script_parser, preprocessor, _grammar_warned
    if pmd_script_parser is None:
        try:
            pmd_script_grammar = load_grammar()
            pmd_script_parser = Lark(pmd_script_grammar, start='program', parser='lalr', propagate_positions=True)
            preprocessor = PMDPreprocessor()
        except Exception as e:
            if not _grammar_warned:
                print(f"Warning: Failed to load grammar with LALR: {e}")
                _grammar_warned = True
            # Fallback to Earley if LALR fails
            try:
                pmd_script_grammar = load_grammar()
                pmd_script_parser = Lark(pmd_script_grammar, start='program', parser='earley', propagate_positions=True)
                preprocessor = None
                if not _grammar_warned:
                    print("Fallback: Using Earley parser")
                    _grammar_warned = True
            except Exception as e2:
                if not _grammar_warned:
                    print(f"Warning: Failed to load grammar with Earley: {e2}")
                    _grammar_warned = True
                # Final fallback to minimal grammar
                pmd_script_parser = Lark("?program: source_elements?\n?source_elements: statement+\n?statement: IDENTIFIER", start='program', parser='earley')
                preprocessor = None
    
    return pmd_script_parser

def parse_with_preprocessor(code: str):
    """Parse code using the preprocessor and LALR parser, with fallback to Earley."""
    global preprocessor, _grammar_warned
    
    # Ensure we have a preprocessor
    if preprocessor is None:
        try:
            preprocessor = PMDPreprocessor()
        except Exception as e:
            if not _grammar_warned:
                print(f"Warning: Failed to create preprocessor: {e}")
                _grammar_warned = True
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
            grammar = load_grammar()  # Uses cached grammar
            earley_parser = Lark(grammar, start='program', parser='earley', propagate_positions=True)
            return earley_parser.parse(preprocessed_code)  # Use preprocessed code
        except Exception as e2:
            if not _grammar_warned:
                print(f"Warning: Both LALR and Earley parsing failed: {e2}")
                _grammar_warned = True
            # Final fallback - try minimal parsing
            try:
                minimal_parser = Lark("?program: source_elements?\n?source_elements: statement+\n?statement: IDENTIFIER", start='program', parser='earley')
                return minimal_parser.parse(code)
            except Exception as e3:
                if not _grammar_warned:
                    print(f"Warning: All parsing attempts failed: {e3}")
                    _grammar_warned = True
                return None