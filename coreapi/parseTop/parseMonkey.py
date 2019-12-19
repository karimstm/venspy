from coreapi.parseTop.classContainer import Variables
import json
from json.decoder import JSONDecoder


def get_data(path):
    with open(path, 'r') as file:
        data = file.read()
    return data


def put_data(path, data):
    if not isinstance(data, str):
        raise TypeError('data must be str, not %s' %
                        data.__class__.__name__)
    with open(file=path + '/mdl_parsed_top.json', mode='w') as f:
        return f.write(data)


def print_mdl_top(tab):
    for t in tab:
        print(f'name={t.name}\nunit={t.unit}\nrange={t.range}\njunk={t.junk}')


def result_to_json(tab):
    return json.dumps(tab, default=lambda obj: obj.__dict__, indent=4)


def parser_mdl_top(data):
    if data == None:
        return None
    i = 0
    tab = list()
    tab_purified = list()
    string = str()
    for i in range(len(data)):
        if data[i] == '\\' and data[i + 1] == '\\':
            break
        string += data[i]
        if data[i] == '|' and data[i + 1] == '\n':
            string += ';'
    first_array = string.replace('\n', '').replace('\t', '').split(';')
    for array in first_array:
        tab.append(Variables(array))

    for t in tab:
        if t.name:
            # print('name = ',t.name)
            tab_purified.append(t)
    return tab_purified
