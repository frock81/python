#!/usr/bin/python3
# -*- coding: utf-8 -*-
import yaml, sys, getopt, os
from collections import OrderedDict

DEFAULT_SINGLE = True
DEFAULT_REQUIRED = False
DEFAULT_SUBKEYS = False
DEFAULT_TYPE = 'keyvalue'

def to_bacula_keyword(snake_str, glue = ' '):
    components = snake_str.split('_')
    return glue.join(x.title() for x in components)

def get_daemon_type(daemon_var):
    # director, storage, client, console.
    return daemon_var.split('___')[1].split('_')[0]

def print_usage(argv):
    print('Usage:')
    print(f'    {os.path.basename(argv[0])} -d|--daemon-var=<daemon-var> -i|--input-file=<input-file>')
    print(f'    {os.path.basename(argv[0])} -h|--help')

def parse_options(argv):
    daemon_var = ''
    input_file = ''
    try:
        opts, args = getopt.getopt(argv[1:], 'hd:i:', ['help', 'daemon-var=', 'input-file='])
    except getopt.GetoptError:
        print('Error parsing options.')
        print_usage(argv)
        sys.exit(1)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print_usage(argv)
            sys.exit()
        elif opt in ('-d', '--daemon-var'):
            daemon_var = arg
        elif opt in ('-i', '--input-file'):
            input_file = arg
    if not daemon_var or not input_file:
        print('daemon-var and input-file are required options')
        sys.exit(1)
    return daemon_var, input_file
def print_if_start(key, padding_jinja = ''):
    print(f'{padding_jinja}{{% if {key} is defined %}}')

def print_if_end(padding_jinja = ''):
    print(f'{padding_jinja}{{% endif %}}')

def print_for_start(key, parent_key, padding_jinja = ''):
    print(f'{padding_jinja}{{% for {key} in {parent_key}.{key}s %}}')

def print_for_end(padding_jinja = ''):
    print(f'{padding_jinja}{{% endfor %}}')

def print_key_start(key, parent_key, key_type, padding_conf = ''):
    if key_type == 'resource':
        print(f'{padding_conf}{to_bacula_keyword(key)} {{')
    if key_type == 'keyvalue':
        print(f'{padding_conf}{to_bacula_keyword(key)} = {{{{ {parent_key}.{key} }}}}')
    if key_type == 'message':
        print('TO_BE_DONE')

def print_key_end(key_type, padding_conf = '', multiple = False):
    if key_type == 'resource':
        print(f'{padding_conf}}}')
        if multiple:
            print(f'{padding_conf}')

    # if key_type == 'keyvalue':
    #     print(f'{padding_conf}{to_bacula_keyword(key)} = {{{{ {key} }}}}')
    if key_type == 'message':
        print('TO_BE_DONE')

def print_dict(parent_key, dictionary, padding_jinja = '', padding_conf = ''):
    for key0, value0 in dictionary.items():
        required = DEFAULT_REQUIRED
        single = DEFAULT_SINGLE
        has_subkeys = DEFAULT_SUBKEYS
        key_type = DEFAULT_TYPE
        for value0_key1, value0_value1 in value0.items():
            if value0_key1 == 'required':
                required = value0_value1
            if value0_key1 == 'single':
                single = value0_value1
            if value0_key1 == 'subkeys':
                has_subkeys = value0_value1
            if value0_key1 == 'type':
                if value0_value1 not in ('keyvalue', 'resource', 'message'):
                    print(f'Value not allowed for key type of {key0}: {value0_value1}')
                    sys.exit(1)
                key_type = value0_value1
        if not required:
            current_key = f'{parent_key}.{key0}' if single else f'{parent_key}.{key0}s'
            print_if_start(key = current_key, padding_jinja = padding_jinja)
            padding_jinja = f'  {padding_jinja}'
        if not single:
            print_for_start(key = key0, parent_key = parent_key, padding_jinja = padding_jinja)        
            padding_jinja = f'  {padding_jinja}'
            print_key_start(key = key0, parent_key = parent_key, key_type = key_type, padding_conf = padding_conf)
        else:
            current_key = f'{parent_key}.{key0}' if single else f'{parent_key}.{key0}s'
            print_key_start(key = key0, parent_key = parent_key, key_type = key_type, padding_conf = padding_conf)
        if has_subkeys:
            padding_jinja = f'  {padding_jinja}'
            padding_conf = f'    {padding_conf}'
            if single:
                passing_key = f'{parent_key}.{key0}'
            else:
                passing_key = key0
            print_dict(parent_key = passing_key, dictionary = value0['subkeys'], padding_jinja = padding_jinja, padding_conf = padding_conf)
            padding_jinja = padding_jinja[:-2]
            padding_conf = padding_conf[:-4]
        print_key_end(key_type = key_type, padding_conf = padding_conf, multiple = (not single))
        if not single:
            padding_jinja = padding_jinja[:-2]
            print_for_end(padding_jinja = padding_jinja)
        if not required:
            padding_jinja = padding_jinja[:-2]
            print_if_end(padding_jinja = padding_jinja)

def main(argv):
    daemon_var, input_file = parse_options(argv)
    # print(daemon_var)
    daemon_type = get_daemon_type(daemon_var)
    # print(daemon_type)
    with open(input_file, "r") as stream:
        config = yaml.safe_load(stream)
        print_dict(parent_key = daemon_var, dictionary = config)

if __name__ == '__main__':
    main(sys.argv)