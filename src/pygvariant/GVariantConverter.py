import ast
import re
from typing import get_origin, get_args, Union, Any, List, Tuple, Dict, Optional
from . import GVariantParser

class GVariantValueConverter:
    def __init__(self, parser=None):
        self.parser = parser or GVariantParser()

    def _preprocess_gvariant_string(self, value_str: str) -> str:
        """
        Transforms a GVariant text format string into a Python-compatible
        literal string by carefully handling variant markers.
        """
        s = value_str.replace('true', 'True').replace('false', 'False')
        if s.lower() == 'nothing':
            return 'None'

        # A more robust way to handle variants without corrupting string literals.
        # This parser iterates through the string, keeping track of whether it's
        # inside a string literal.

        res = []
        in_string = False
        quote_char = ''
        i = 0
        while i < len(s):
            char = s[i]
            if in_string:
                res.append(char)
                if char == '\\': # Handle escaped quotes
                    if i + 1 < len(s):
                        res.append(s[i+1])
                        i += 1
                elif char == quote_char:
                    in_string = False
            elif char in "\"'":
                res.append(char)
                in_string = True
                quote_char = char
            elif char not in "<>":
                res.append(char)
            # Variants are just ignored, not added to res
            i += 1

        return "".join(res)

    def parse_value_string(self, value_str: str, type_str: str) -> Any:
        """
        Parses a string representation of data into Python objects 
        based on a GVariant type string.
        """
        # 1. Get the target Python type representation
        target_type = self.parser.parse(type_str)

        # 2. Preprocess the GVariant string to be Python-compatible
        processed_str = self._preprocess_gvariant_string(value_str.strip())

        # 3. Safely evaluate the string into a basic Python structure
        try:
            raw_value = ast.literal_eval(processed_str)
        except (ValueError, SyntaxError):
            # Fallback for plain strings that aren't quoted
            raw_value = processed_str

        # 4. Coerce the raw value into the target type structure
        return self._coerce(raw_value, target_type)

    def _coerce(self, value, target_type):
        origin = get_origin(target_type)
        args = get_args(target_type)

        # Handle 'Any' or indefinite types
        if target_type is Any:
            return value

        # Handle Optional/Maybe (m)
        if origin is Union and type(None) in args:
            if value is None or value == 'nothing':
                return None
            # Extract the actual type from Optional[T]
            actual_type = next(t for t in args if t is not type(None))
            return self._coerce(value, actual_type)

        # Handle Arrays (a) -> List
        if origin is list:
            inner_type = args[0]
            return [self._coerce(item, inner_type) for item in value]

        # Handle Dictionaries (a{kv}) -> Dict
        if origin is dict:
            k_type, v_type = args
            # When GVariant dictionary values are variants (v), they might be
            # returned as string representations of dicts.
            # We need to handle this case by parsing them again.
            coerced_dict = {}
            for k, v in value.items():
                coerced_key = self._coerce(k, k_type)
                if v_type is Any and isinstance(v, str):
                    try:
                        # If the variant value is a string-encoded dict, parse it
                        v = ast.literal_eval(v)
                    except (ValueError, SyntaxError):
                        pass # Not a dict, treat as a plain string
                coerced_dict[coerced_key] = self._coerce(v, v_type)
            return coerced_dict

        # Handle Tuples (()) -> Tuple
        if origin is tuple:
            # Fixed-size tuple: Tuple[int, str]
            if len(args) > 0 and args[-1] is not Ellipsis:
                return tuple(self._coerce(v, t) for v, t in zip(value, args))
            # Variadic tuple: Tuple[Any, ...]
            return tuple(value)

        # Handle Basic Types (b, i, s, d, etc.)
        if target_type in (int, float, bool, str):
            try:
                return target_type(value)
            except (TypeError, ValueError):
                return value

        return value
