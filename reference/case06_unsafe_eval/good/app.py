import ast


def parse_setting(text):
    return ast.literal_eval(text)
