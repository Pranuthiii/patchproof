def parse_setting(text):
    # VULNERABLE: eval() runs whatever expression it is given
    return eval(text)
