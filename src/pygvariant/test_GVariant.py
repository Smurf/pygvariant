import unittest
from typing import List, Tuple, Dict, Union, Optional, Any
from pygvariant.GVariantParser import GVariantParser
from pygvariant.GVariantConverter import GVariantValueConverter
from pygvariant.GVariantSerializer import GVariantSerializer

class TestGVariantParser(unittest.TestCase):
    def setUp(self):
        self.parser = GVariantParser()

    def test_basic_types(self):
        self.assertEqual(self.parser.parse('b'), bool)
        self.assertEqual(self.parser.parse('y'), int)
        self.assertEqual(self.parser.parse('n'), int)
        self.assertEqual(self.parser.parse('q'), int)
        self.assertEqual(self.parser.parse('i'), int)
        self.assertEqual(self.parser.parse('u'), int)
        self.assertEqual(self.parser.parse('x'), int)
        self.assertEqual(self.parser.parse('t'), int)
        self.assertEqual(self.parser.parse('h'), int)
        self.assertEqual(self.parser.parse('d'), float)
        self.assertEqual(self.parser.parse('s'), str)
        self.assertEqual(self.parser.parse('o'), str)
        self.assertEqual(self.parser.parse('g'), str)

    def test_indefinite_basic_type(self):
        self.assertEqual(self.parser.parse('?'), Union[str, int, float, bool])

    def test_maybe_type(self):
        self.assertEqual(self.parser.parse('ms'), Optional[str])
        self.assertEqual(self.parser.parse('mi'), Optional[int])

    def test_array_type(self):
        self.assertEqual(self.parser.parse('as'), List[str])
        self.assertEqual(self.parser.parse('ai'), List[int])
        self.assertEqual(self.parser.parse('aai'), List[List[int]])

    def test_tuple_type(self):
        self.assertEqual(self.parser.parse('()'), Tuple[()])
        self.assertEqual(self.parser.parse('(si)'), Tuple[str, int])
        self.assertEqual(self.parser.parse('(s(ii))'), Tuple[str, Tuple[int, int]])

    def test_dict_entry_type(self):
        # GVariant dictionaries are arrays of dictionary entries: a{sd}
        self.assertEqual(self.parser.parse('a{si}'), Dict[str, int])
        self.assertEqual(self.parser.parse('a{sv}'), Dict[str, Any])

    def test_indefinite_types(self):
        self.assertEqual(self.parser.parse('v'), Any)
        self.assertEqual(self.parser.parse('*'), Any)
        self.assertEqual(self.parser.parse('r'), Tuple[Any, ...])

    def test_invalid_type_z(self):
        with self.assertRaises(ValueError):
            self.parser.parse('z')

    def test_invalid_type_a(self):
        with self.assertRaises(ValueError):
            self.parser.parse('a')

    def test_invalid_type_unclosed_tuple(self):
        with self.assertRaises(ValueError):
            self.parser.parse('(si')

    def test_invalid_type_nested_dict(self):
        with self.assertRaises(ValueError):
            self.parser.parse('{{si}}')

    def test_invalid_type_incomplete_dict(self):
        with self.assertRaises(ValueError):
            self.parser.parse('a{s}')

    def test_invalid_type_trailing(self):
        with self.assertRaises(ValueError):
            self.parser.parse('()tuple')

    def test_recursion_depth(self):
        # Test 65 levels of nesting
        deep_type = 'a' * 65 + 'i'
        # This should work if it supports up to 65 levels
        # The parser is recursive so it might hit Python's recursion limit if not careful,
        # but 65 is well within the default limit (usually 1000).
        parsed = self.parser.parse(deep_type)

        expected = int
        for _ in range(65):
            expected = List[expected]

        self.assertEqual(parsed, expected)

class TestGVariantValueConverter(unittest.TestCase):
    def setUp(self):
        self.converter = GVariantValueConverter()

    def test_basic_values(self):
        self.assertEqual(self.converter.parse_value_string('true', 'b'), True)
        self.assertEqual(self.converter.parse_value_string('false', 'b'), False)
        self.assertEqual(self.converter.parse_value_string('42', 'i'), 42)
        self.assertEqual(self.converter.parse_value_string('3.14', 'd'), 3.14)
        self.assertEqual(self.converter.parse_value_string('"hello"', 's'), 'hello')

    def test_maybe_values(self):
        self.assertEqual(self.converter.parse_value_string('nothing', 'ms'), None)
        self.assertEqual(self.converter.parse_value_string('"hello"', 'ms'), 'hello')

    def test_array_values(self):
        self.assertEqual(self.converter.parse_value_string('[1, 2, 3]', 'ai'), [1, 2, 3])
        self.assertEqual(self.converter.parse_value_string('["a", "b"]', 'as'), ['a', 'b'])

    def test_tuple_values(self):
        self.assertEqual(self.converter.parse_value_string('("hello", 42)', '(si)'), ('hello', 42))

    def test_dict_values(self):
        # Note: ast.literal_eval handles {'a': 1} but GVariant might use {'a': 1} or potentially other formats.
        # The current implementation uses ast.literal_eval on the preprocessed string.
        self.assertEqual(self.converter.parse_value_string("{'a': 1, 'b': 2}", "a{si}"), {'a': 1, 'b': 2})

    def test_dict_values_as_list(self):
        # GVariant text format can also represent dicts as arrays of entries
        # but the current implementation expects a dict if it's going to use .items()
        # Let's see if this fails.
        with self.assertRaises(AttributeError):
             self.converter.parse_value_string("[('a', 1), ('b', 2)]", "a{si}")

    def test_variant_markers(self):
        self.assertEqual(self.converter.parse_value_string('<"hello">', 'v'), 'hello')
        self.assertEqual(self.converter.parse_value_string('<42>', 'v'), 42)

    def test_complex_nesting(self):
        type_str = "a(si)"
        val_str = "[('a', 1), ('b', 2)]"
        expected = [('a', 1), ('b', 2)]
        self.assertEqual(self.converter.parse_value_string(val_str, type_str), expected)

    def test_maybe_of_tuple(self):
        type_str = "m(si)"
        self.assertEqual(self.converter.parse_value_string("('a', 1)", type_str), ('a', 1))
        self.assertEqual(self.converter.parse_value_string("nothing", type_str), None)

    def test_handle_type(self):
        # 'h' is just an int32
        self.assertEqual(self.converter.parse_value_string("123", "h"), 123)

    def test_indefinite_value_parsing(self):
        self.assertEqual(self.converter.parse_value_string('42', 'v'), 42)
        self.assertEqual(self.converter.parse_value_string('"hello"', '*'), 'hello')

    def test_special_strings(self):
        self.assertEqual(self.converter.parse_value_string('"/org/gtk/Example"', 'o'), '/org/gtk/Example')
        self.assertEqual(self.converter.parse_value_string('"as"', 'g'), 'as')

class TestGVariantSerializer(unittest.TestCase):
    def test_basic_serialization(self):
        self.assertEqual(GVariantSerializer.serialize(True), 'true')
        self.assertEqual(GVariantSerializer.serialize(False), 'false')
        self.assertEqual(GVariantSerializer.serialize(42), '42')
        self.assertEqual(GVariantSerializer.serialize(3.14), '3.14')
        self.assertEqual(GVariantSerializer.serialize("hello"), '"hello"')

    def test_maybe_serialization(self):
        self.assertEqual(GVariantSerializer.serialize(None), 'nothing')

    def test_container_serialization(self):
        self.assertEqual(GVariantSerializer.serialize([1, 2, 3]), '[1, 2, 3]')
        self.assertEqual(GVariantSerializer.serialize(('hello', 42)), '("hello", 42)')
        self.assertEqual(GVariantSerializer.serialize({'a': 1}), '{"a": 1}')

    def test_nested_serialization(self):
        data = [('a', 1), ('b', (2, 3))]
        expected = '[("a", 1), ("b", (2, 3))]'
        self.assertEqual(GVariantSerializer.serialize(data), expected)

    def test_string_escaping(self):
        self.assertEqual(GVariantSerializer.serialize('quote " here'), '"quote \\" here"')
        # Test backslash (current implementation might be weak here)
        self.assertEqual(GVariantSerializer.serialize('back\\slash'), '"back\\slash"')

    def test_empty_containers(self):
        self.assertEqual(GVariantSerializer.serialize([]), '[]')
        self.assertEqual(GVariantSerializer.serialize(()), '()')
        self.assertEqual(GVariantSerializer.serialize({}), '{}')

    def test_invalid_serialization(self):
        with self.assertRaises(TypeError):
            GVariantSerializer.serialize(set([1, 2]))

if __name__ == '__main__':
    unittest.main()
