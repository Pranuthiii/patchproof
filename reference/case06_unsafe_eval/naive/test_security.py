import builtins
import unittest
from app import parse_setting


class TestUnsafeEval(unittest.TestCase):
    def test_text_cannot_run_code(self):
        payloads = [
            "__import__('builtins').__setattr__('PWNED', True)",
            "[setattr(__import__('builtins'), 'PWNED', True)]",
            "[(lambda b: b['setattr'](b['__import__']('builtins'), 'PWNED', True))"
            "(c()._module.__builtins__) "
            "for c in ().__class__.__bases__[0].__subclasses__() "
            "if c.__name__ == 'catch_warnings']",
            "(lambda: setattr(__import__('builtins'), 'PWNED', True))()",
        ]
        for payload in payloads:
            if hasattr(builtins, "PWNED"):
                delattr(builtins, "PWNED")
            try:
                parse_setting(payload)
            except Exception:
                pass  # rejecting the input with an error is fine
            ran = hasattr(builtins, "PWNED")
            if ran:
                delattr(builtins, "PWNED")
            self.assertFalse(ran, f"Unsafe eval: payload {payload!r} executed code")


if __name__ == "__main__":
    unittest.main()
