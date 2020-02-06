import json


def warningDecode_string(string):
    return string.encode('windows-1252').decode('utf-8')


def save_warnings(path, data, resid):
    if not isinstance(data, str):
        raise TypeError('data must be str, not %s' %
                        data.__class__.__name__)
    with open(file=path + F"/all_warnings{resid}.json", mode='w') as f:
        return f.write(data)


def warning_to_json(warnings):
    result = {}
    if (isinstance(warnings, str)):
        warnings = warnings.replace('\\n', '\n').split('\n')
        warnings = list(
            filter(lambda line: 'WARNING' in line or 'USE FLAG' in line, warnings))
        for line in warnings:
            start = line.find('-')+1
            end = line.find('-', start)
            key = line[start: end]
            if (key not in result):
                result[key] = []
            result[key].append(line)
    return json.dumps(result)

# print(warning_to_json(read_file("testwar")))
