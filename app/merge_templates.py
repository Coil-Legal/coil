"""Restricted Jinja environments for templates edited by firm users."""
from jinja2 import TemplateSyntaxError, nodes
from jinja2.sandbox import ImmutableSandboxedEnvironment


class MergeEnvironment(ImmutableSandboxedEnvironment):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.globals.clear()

    def is_safe_attribute(self, obj, attr, value):
        return False

    def is_safe_callable(self, obj):
        return False

    def _parse(self, source, name, filename):
        tree = super()._parse(source, name, filename)
        for node in tree.find_all((nodes.Getattr, nodes.Call)):
            raise TemplateSyntaxError(
                "Use merge fields and filters; attribute access and function calls are not allowed.",
                node.lineno, name, filename)
        return tree
