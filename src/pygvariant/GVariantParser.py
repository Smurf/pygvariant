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
    }

    OTHER_TYPES = {
        'v': Any,   # Variant
        '*': Any,   # Any type
        'r': Tuple[Any, ...], # Any tuple
    }

    def __init__(self):
        self._it = None
        self._peeked = None # Buffer for peeking

    def parse(self, type_str: str) -> Any:
        self._it = iter(type_str)
        self._peeked = None 
        try:
            result = self._parse_one()
            if self._peek() is not None:
                raise ValueError("Trailing characters in type string")
            return result
        except StopIteration:
            raise ValueError("Unexpected end of type string")

    def _next(self):
        """Consumes and returns the next character."""
        if self._peeked is not None:
            char = self._peeked
            self._peeked = None
            return char
        return next(self._it)

    def _peek(self):
        """Look at the next character without consuming it."""
        if self._peeked is None:
            try:
                self._peeked = next(self._it)
            except StopIteration:
                return None
        return self._peeked

    def _parse_one(self, basic_only=False) -> Any:
        char = self._next() # Use the new helper

        if char in self.BASIC_TYPES:
            return self.BASIC_TYPES[char]
        
        if basic_only:
            raise ValueError(f"Expected basic type, got {char}")

        if char in self.OTHER_TYPES:
            return self.OTHER_TYPES[char]

        if char == 'm':
            maybe_type = self._parse_one()
            return Optional[maybe_type]

        if char == 'a': 
            inner_type = self._parse_one()
            if getattr(inner_type, "__origin__", None) is dict_entry:
                return Dict[inner_type.__args__[0], inner_type.__args__[1]]
            return List[inner_type]

        if char == '{':
            key = self._parse_one(basic_only=True)
            val = self._parse_one()
            if self._next() != '}':
                raise ValueError("Expected '}' to close dictionary type")
            return dict_entry[key, val]
            
        if char == '(':
            types = []
            while self._peek() != ')': # Peek check
                types.append(self._parse_one())
            self._next() # Consume ')'
            return Tuple[tuple(types)] if types else Tuple[()]

        raise ValueError(f"Unknown GVariant type character: {char}")


# Helper for internal dictionary entry representation
T = typing.TypeVar("T")
U = typing.TypeVar("U")
class dict_entry(typing.Generic[T, U]):
    pass

def parse_gvariant_type(type_string: str):
    return GVariantParser().parse(type_string)
