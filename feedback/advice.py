# feedback/advice.py
# Compatibility shim to preserve public API after modularization.
# Re-exports the stable surface: generate_advice, get_title_phrase
from .advice_pkg import generate_advice, get_title_phrase

__all__ = ["generate_advice", "get_title_phrase"]
