import ast
from typing import get_origin, get_args, Union, Any, List, Tuple, Dict, Optional
from . import GVariantParser

class GVariantValueConverter:
    def __init__(self, parser=None):
        self.parser = parser or GVariantParser()

    def parse_value_string(self, value_str: str, type_str: str) -> Any:
        """
        Parses a string representation of data into Python objects 
        based on a GVariant type string.
        """
        # 1. Get the target Python type representation
        target_type = self.parser.parse(type_str)
        
        # 2. Safely evaluate the string into a basic Python structure
        # Note: GVariant 'true'/'false' matches Python 'True'/'False'
        # but we lowercase them for literal_eval compatibility if needed.
        cleaned_str = value_str.replace('true', 'True').replace('false', 'False')
        if cleaned_str.lower() == 'nothing': # GVariant "maybe" empty
            raw_value = None
        else:
            try:
                raw_value = ast.literal_eval(cleaned_str)
            except (ValueError, SyntaxError):
                # Fallback for plain strings that aren't quoted
                raw_value = value_str

        # 3. Coerce the raw value into the target type structure
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
            return {self._coerce(k, k_type): self._coerce(v, v_type) for k, v in value.items()}

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

# --- Usage Example ---
converter = GVariantValueConverter()

# 1. Parsing a complex tuple
val1 = converter.parse_value_string("(true, 42, 'hello')", "(bis)")
print(f"Tuple: {val1} | Types: {[type(x) for x in val1]}")

# 2. Parsing an array of integers
val2 = converter.parse_value_string("[1, 2, 3, 4]", "ai")
print(f"Array: {val2} | Inner Type: {type(val2[0])}")

# 3. Parsing a dictionary
val3 = converter.parse_value_string("{'key1': 1.5, 'key2': 3.0}", "a{sd}")
print(f"Dict:  {val3}")

# 4. Parsing a 'Maybe' type
val4 = converter.parse_value_string("nothing", "ms")
print(f"Maybe: {val4}")
