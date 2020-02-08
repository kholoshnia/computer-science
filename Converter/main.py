import os
import re
import json
import yaml
import time

#with libraries
def json_to_dict_lib(s):
    return json.loads(s)

def dict_to_yaml_lib(s):
    return yaml.dump(s, allow_unicode=True)

def json_to_yaml_lib(s):
    return yaml.dump(json.loads(s), allow_unicode=True)

#without libraries
def json_to_dict(s):
    def sequence(*funcs):
        if len(funcs) == 0:
            def result(src):
                yield (), src
        else:
            def result(src):
                for arg1, src in funcs[0](src):
                    for others, src in sequence(*funcs[1:])(src):
                        yield (arg1,) + others, src
        return result

    number_regex = re.compile(r"(-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*(.*)", re.DOTALL)

    def parse_number(src):
        match = number_regex.match(src)
        if match is not None:
            number, src = match.groups()
            yield eval(number), src

    string_regex = re.compile(r"(\"(?:[^\\\"]|\\[\"\\/bfnrt]|\\u[0-9a-fA-F]{4})*?\")\s*(.*)", re.DOTALL)

    def parse_string(src):
        match = string_regex.match(src)
        if match is not None:
            string, src = match.groups()
            yield eval(string), src

    def parse_word(word, value=None):
        l = len(word)
        def result(src):
            if src.startswith(word):
                yield value, src[l:].lstrip()
        result.__name__ = "parse_%s" % word
        return result

    parse_true = parse_word("true", True)
    parse_false = parse_word("false", False)
    parse_null = parse_word("null", None)

    def parse_value(src):
        for match in parse_string(src):
            yield match
            return
        for match in parse_number(src):
            yield match
            return
        for match in parse_array(src):
            yield match
            return
        for match in parse_object(src):
            yield match
            return
        for match in parse_true(src):
            yield match
            return
        for match in parse_false(src):
            yield match
            return
        for match in parse_null(src):
            yield match
            return

    parse_left_square_bracket = parse_word("[")
    parse_right_square_bracket = parse_word("]")
    parse_empty_array = sequence(parse_left_square_bracket, parse_right_square_bracket)

    def parse_array(src):
        for _, src in parse_empty_array(src):
            yield [], src
            return

        for (_, items, _), src in sequence(
            parse_left_square_bracket,
            parse_comma_separated_values,
            parse_right_square_bracket,
        )(src):
            yield items, src

    parse_comma = parse_word(",")

    def parse_comma_separated_values(src):
        for (value, _, values), src in sequence(
            parse_value,
            parse_comma,
            parse_comma_separated_values
        )(src):
            yield [value] + values, src
            return

        for value, src in parse_value(src):
            yield [value], src

    parse_left_curly_bracket = parse_word("{")
    parse_right_curly_bracket = parse_word("}")
    parse_empty_object = sequence(parse_left_curly_bracket, parse_right_curly_bracket)

    def parse_object(src):
        for _, src in parse_empty_object(src):
            yield {}, src
            return
        for (_, items, _), src in sequence(
            parse_left_curly_bracket,
            parse_comma_separated_keyvalues,
            parse_right_curly_bracket,
        )(src):
            yield items, src

    parse_colon = parse_word(":")

    def parse_keyvalue(src):
        for (key, _, value), src in sequence(
            parse_string,
            parse_colon,
            parse_value
        )(src):
            yield {key: value}, src

    def parse_comma_separated_keyvalues(src):
        for (keyvalue, _, keyvalues), src in sequence(
            parse_keyvalue,
            parse_comma,
            parse_comma_separated_keyvalues,
        )(src):
            keyvalue.update(keyvalues)
            yield keyvalue, src
            return

        for keyvalue, src in parse_keyvalue(src):
            yield keyvalue, src

    s = s.strip()
    match = list(parse_value(s))
    if len(match) != 1:
        raise ValueError('not a valid JSON string')
    result, src = match[0]
    if src.strip():
        raise ValueError('not a valid JSON string')
    return result

def dict_to_yaml_simple(s):
    s = format(s)

    s = s.replace('}, {', '\n- ')
    s = s.replace('[', '\n- ')

    s = s.replace(': {', ':\n    ')
    s = s.replace('}, ', '\n  ')

    s = s.replace('\'', '')
    s = s.replace(', ', '\n    ')

    s = s.replace('{', '')
    s = s.replace('}', '')

    for i in re.findall(r"[0-9]{2}:[0-9]{2}", s):
        new_str = '\'' + i + '\''
        s = s.replace(i, new_str)

    s = s.replace('None', '~')

    return s

def json_to_yaml(s):
    s = s.replace('\n', '')
    s = re.sub(' +', ' ', s)

    s = s.replace(' }, { ', '\n- ')
    s = s.replace('[ ', '\n- ')

    s = s.replace(': { ', ':\n    ')
    s = s.replace(' }, ', '\n  ')

    s = s.replace('"', '')
    s = s.replace(', ', '\n    ')

    s = s.replace('{ ', '')
    s = s.replace('} ', '')

    for i in re.findall(r"[0-9]{2}:[0-9]{2}", s):
        new_str = '\'' + i + '\''
        s = s.replace(i, new_str)

    s = s.replace('null', '~')

    return s

path_in = os.path.dirname(os.path.abspath(__file__)) + '/input.json'
path_out = os.path.dirname(os.path.abspath(__file__)) +  '/output.yaml'

try:
    f_in = open(path_in, 'r')
    f_out = open(path_out, 'w')

    f_out.write(json_to_yaml(f_in.read()))
    # f_out.write(json_to_yaml_lib(f_in.read()))

    f_in.close()
    f_out.close()
except IOError:
    print('Error: could not open file!')
