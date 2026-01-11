import typing
from typing import Any, List, Tuple, Union, Optional, Dict

class GVariantParser:
    # Map basic types to Python equivalents
    BASIC_TYPES = {
        'b': bool,
        'y': int,   # Byte
        'n': int,   # Int16
        'q': int,   # UInt16
        'i': int,   # Int32
        'u': int,   # UInt32
        'x': int,   # Int64
        't': int,   # UInt64
        'h': int,   # Handle
        'd': float, # Double
        's': str,   # String
        'o': str,   # Object Path
        'g': str,   # Signature
        '?': Union[str, int, float, bool], # Any basic type
        'v': Any,   # Variant
        '*': Any,   # Any type
        'r': Tuple[Any, ...], # Any tuple
    }

    def __init__(self):
        self._it = None

    def parse(self, type_str: str) -> Any:
        """Entry point for parsing a GVariant type string."""
        self._it = iter(type_str)
        try:
            result = self._parse_one()
            # Check if there is trailing data
            try:
                next(self._it)
                raise ValueError("Trailing characters in type string")
            except StopIteration:
                return result
        except StopIteration:
            raise ValueError("Unexpected end of type string")

    def _parse_one(self) -> Any:
        char = next(self._it)

        if char in self.BASIC_TYPES:
            return self.BASIC_TYPES[char]

        if char == 'a': # Array
            inner_type = self._parse_one()
            # Special case: Array of Dict Entries 'a{kv}' is a Python Dict
            if getattr(inner_type, "__origin__", None) is dict_entry:
                return Dict[inner_type.__args__[0], inner_type.__args__[1]]
            return List[inner_type]

        if char == 'm': # Maybe
            return Optional[self._parse_one()]

        if char == '(': # Tuple
            types = []
            while True:
                peek = self._peek()
                if peek == ')':
                    next(self._it) # Consume ')'
                    break
                types.append(self._parse_one())
            return Tuple[tuple(types)] if types else Tuple[()]

        if char == '{': # Dictionary Entry
            key_type = self._parse_one()
            # Validation: GVariant requires the key to be a basic type
            if key_type not in self.BASIC_TYPES.values() and key_type is not Any:
                raise ValueError(f"Dictionary key must be a basic type, not {key_type}")
            
            value_type = self._parse_one()
            
            if next(self._it) != '}':
                raise ValueError("Expected '}' at end of dict entry")
            
            # We use a custom Generic to represent the entry itself
            return dict_entry[key_type, value_type]

        raise ValueError(f"Unknown type character: {char}")

    def _peek(self):
        """Look at the next character without consuming it."""
        try:
            self._peeked = next(self._it)
            self._it = self._combine_peek()
            return self._peeked
        except StopIteration:
            return None

    def _combine_peek(self):
        yield self._peeked
        yield from self._it

# Helper for internal dictionary entry representation
T = typing.TypeVar("T")
U = typing.TypeVar("U")
class dict_entry(typing.Generic[T, U]):
    pass

def parse_gvariant_type(type_string: str):
    return GVariantParser().parse(type_string)

# --- Examples ---
if __name__ == "__main__":
    examples = [
        "i",            # Integer
        "ai",           # Array of integers
        "(is)",         # Tuple of (int, string)
        "a{sd}",        # Dictionary (Array of dict entries: string -> double)
        "m(ni)",        # Maybe tuple
        "aaaaai",       # Deeply nested array
        "(ui(nq((y)))s)", # Complex nested tuple
    ]

    for ex in examples:
        print(f"String: {ex:15} -> Python Type: {parse_gvariant_type(ex)}")
