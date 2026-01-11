class GVariantSerializer:
    @classmethod
    def serialize(cls, value) -> str:
        """
        Converts a Python object into a GVariant/gschema compatible string.
        """
        # Handle Booleans
        if isinstance(value, bool):
            return "true" if value else "false"

        # Handle Null / Maybe types
        if value is None:
            return "nothing"

        # Handle Strings (escaped)
        if isinstance(value, str):
            # We use repr to handle escaping, but ensure double quotes
            # GVariant typically expects "double quotes" for strings
            escaped = value.replace('"', '\\"')
            return f'"{escaped}"'

        # Handle Numbers (Integers and Floats)
        if isinstance(value, (int, float)):
            return str(value)

        # Handle Arrays/Lists
        if isinstance(value, list):
            contents = ", ".join(cls.serialize(item) for item in value)
            return f"[{contents}]"

        # Handle Tuples
        if isinstance(value, tuple):
            contents = ", ".join(cls.serialize(item) for item in value)
            # Special case for empty tuples
            if not contents:
                return "()"
            return f"({contents})"

        # Handle Dictionaries (GVariant dictionaries are {key: value})
        if isinstance(value, dict):
            items = []
            for k, v in value.items():
                items.append(f"{cls.serialize(k)}: {cls.serialize(v)}")
            contents = ", ".join(items)
            return f"{{{contents}}}"

        raise TypeError(f"Object of type {type(value).__name__} is not GVariant compatible")

# --- Practical Usage ---
def to_gschema(value):
    return GVariantSerializer.serialize(value)
