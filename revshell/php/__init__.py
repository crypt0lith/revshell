__all__ = ['cmd']

import json
from string import Formatter

from . import cmd

def php_escape(__obj: object) -> str:
    return json.dumps(__obj, ensure_ascii=False).replace('$', r'\$')

class PhpAdapter(Formatter):
    def convert_field(self, value, conversion):
        return (
            php_escape(value)
            if conversion == "p"
            else super().convert_field(value, conversion)
        )

php_adapter = PhpAdapter().format
