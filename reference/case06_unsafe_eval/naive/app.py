def parse_setting(text):
    return eval(text, {"__builtins__": {}}, {})
