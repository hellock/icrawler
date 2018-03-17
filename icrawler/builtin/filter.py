# -*- coding: utf-8 -*-


class Filter():

    def __init__(self):
        self.rules = {}

    def add_rule(self, name, format_fn, choices=None):
        assert callable(format_fn)
        assert choices is None or isinstance(choices, list)
        self.rules[name] = (format_fn, choices)

    def apply(self, options, sep=''):
        if options is None:
            return ''
        assert isinstance(options, dict)
        formatted = []
        for name, val in options.items():
            if name not in self.rules:
                raise KeyError(
                    'unsupported filter "{}"， supported filter options are {}'.
                    format(name), ', '.join(self.rules.keys()))
            format_fn, choices = self.rules[name]
            # validate the option value
            if isinstance(choices, type) and not isinstance(val, choices):
                raise TypeError(
                    'filter option "{}" must be a {}, not {}'.format(
                        name, choices.__name__,
                        type(val).__name__))
            elif isinstance(choices, list) and val not in choices:
                raise ValueError(
                    'filter option "{}" must be one of the following: {}'.
                    format(name, ', '.join(choices)))
            formatted.append(format_fn(val))
        return sep.join(formatted)
