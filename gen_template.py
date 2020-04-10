#!/usr/bin/python3
# -*- coding: utf-8 -*-
import yaml, sys, getopt, os
from collections import OrderedDict

def to_bacula_keyword(snake_str, glue = ' '):
    components = snake_str.split('_')
    return glue.join(x.title() for x in components)

def get_daemon_type(daemon_var):
	# director, storage, client, console.
	return daemon_var.split('___')[1].split('_')[0]

def print_header(daemon_type):
	print(f'''\
#jinja2: trim_blocks: True, lstrip_blocks: True
# Bacula {daemon_type.title()} Configuration File
#
# The order in which the resources and directives appears are equal to how they
# appear in the Bacula docs, with required keywords appearing first.
''')

def print_messages_section(daemon_var):
	print(f'''\
#===============================================================================
# Messages section
#===============================================================================
{{% for message in {daemon_var}.messages %}}
Messages {{
    Name = {{{{ message.name }}}}
  {{% if message.mail_command is defined %}}
    Mail Command = {{{{ message.mail_command }}}}
  {{% endif %}}
  {{% if message.operator_command is defined %}}
    Operator Command = {{{{ message.operator_command }}}}
  {{% endif %}}
  {{% if message.destinations is defined %}}
    {{% for destination in message.destinations %}}
    {{{{ destination.dest }}}}{{{{ ' = ' + destination.address if destination.address is defined else '' }}}} = {{{{ destination.msg_types | join(', ') }}}}
    {{% endfor %}}
  {{% endif %}}
}}

{{% endfor %}}''')

def print_director_specific_resources(daemon_var):
	print(f'''
#===============================================================================
# Schedules section
#===============================================================================
{{% if {daemon_var}.schedules is defined %}}
  {{% for schedule in {daemon_var}.schedules %}}
Schedule {{
    Name = {{{{ schedule.name }}}}
    {{% for run in schedule.runs %}}
    Run = {{{{ run }}}}
    {{% endfor %}}
}}

  {{% endfor %}}
{{% endif %}}

#===============================================================================
# FileSets section
#===============================================================================
{{% if {daemon_var}.file_sets is defined %}}
  {{% for file_set in {daemon_var}.file_sets %}}
FileSet {{
    Name = "{{{{ file_set.name }}}}"
    {{% if file_set.ignore_fileset_changes is defined %}}
    Ignore Fileset Changes = {{{{ file_set.ignore_fileset_changes }}}}
    {{% endif %}}
    {{% if file_set.enable_vss is defined %}}
    Enable Vss = {{{{ file_set.enable_vss }}}}
    {{% endif %}}
    {{% if file_set.include is defined %}}
    Include {{
      {{% if file_set.include.options is defined %}}
        Options {{
          {{% for key, value in file_set.include.options.items() %}}
            {{{{ key }}}} = {{{{ value }}}}
          {{% endfor %}}
        }}
      {{% endif %}}
      {{% if file_set.include.files is defined %}}
        {{% for file in file_set.include.files %}}
        File = {{{{ file }}}}
        {{% endfor %}}
      {{% endif %}}
    }}
    {{% endif %}}
    {{% if file_set.exclude is defined %}}
    Exclude {{
      {{% if file_set.exclude.files is defined %}}
        {{% for file in file_set.exclude.files %}}
        File = {{{{ file }}}}
        {{% endfor %}}
      {{% endif %}}
    }}
    {{% endif %}}
}}

  {{% endfor %}}
{{% endif %}}
''')

def print_run_script_section(resource, padding = ''):
	print(f'''\
  {padding}{{% if {resource}.run_scripts is defined %}}
    {padding}{{% for run_script in {resource}.run_scripts %}}
    RunScript {{
      {padding}{{% if run_script.runs_on_success is defined %}}
        {to_bacula_keyword('runs_on_success')} = {{{{ run_script.runs_on_success }}}}
      {padding}{{% endif %}}
      {padding}{{% if run_script.runs_on_failure is defined %}}
        {to_bacula_keyword('runs_on_failure')} = {{{{ run_script.runs_on_failure }}}}
      {padding}{{% endif %}}
      {padding}{{% if run_script.runs_on_client is defined %}}
        {to_bacula_keyword('runs_on_client')} = {{{{ run_script.runs_on_client }}}}
      {padding}{{% endif %}}
      {padding}{{% if run_script.runs_when is defined %}}
        {to_bacula_keyword('runs_when')} = {{{{ run_script.runs_when }}}}
      {padding}{{% endif %}}
      {padding}{{% if run_script.fail_job_on_error is defined %}}
        {to_bacula_keyword('fail_job_on_error')} = {{{{ run_script.fail_job_on_error }}}}
      {padding}{{% endif %}}
      {padding}{{% if run_script.command is defined %}}
        {to_bacula_keyword('command')} = {{{{ run_script.command }}}}
      {padding}{{% endif %}}
      {padding}{{% if run_script.console is defined %}}
        {to_bacula_keyword('console')} = {{{{ run_script.console }}}}
      {padding}{{% endif %}}
    }}
    {padding}{{% endfor %}}
  {padding}{{% endif %}}''')

def print_section_header(resource, single = True):
	if single:
		print(f'''\
#===============================================================================
# {to_bacula_keyword(resource)} Section
#===============================================================================''')
	else:
		print(f'''\
#===============================================================================
# {to_bacula_keyword(resource)}s Section
#===============================================================================''')

def print_not_mandatory_section(resource, daemon_var, single = True):
	pluralize = '' if single else 's'
	print(f"{{% if {daemon_var}.{resource}{pluralize} is defined %}}")

def print_optional_value(resource, value, daemon_var, single = True, padding = ''):
	if single:
		print(f"{padding}{{% if {daemon_var}.{resource}.{value} is defined %}}")
		print(f"    {to_bacula_keyword(value)} = {{{{ {daemon_var}.{resource}.{value} }}}}")
		print(f"{padding}{{% endif %}}")
	else:
		print(f"  {padding}{{% if {resource}.{value} is defined %}}")
		print(f"    {to_bacula_keyword(value)} = {{{{ {resource}.{value} }}}}")
		print(f"  {padding}{{% endif %}}")

def process_main_print(resource, values_dict, daemon_var, is_single = True,
	is_mandatory = False, padding = ''):
	print_section_header(resource = resource, single = is_single)
	if not is_mandatory:
		print_not_mandatory_section(resource = resource, single = is_single,
			daemon_var = daemon_var)
	if not is_single:
		print(f"{padding}{{% for {resource} in {daemon_var}.{resource}s %}}")
	print(f"{to_bacula_keyword(resource, glue = '')} {{")
	for value in values_dict['required']:
		if is_single:
			print(f"    {to_bacula_keyword(value)} = {{{{ {daemon_var}.{resource}.{value} }}}}")
		else:
			print(f"    {to_bacula_keyword(value)} = {{{{ {resource}.{value} }}}}")
	if 'optional' in values_dict:
		for value in values_dict['optional']:
			print_optional_value(resource = resource, value = value,
				single = is_single, padding = padding, daemon_var = daemon_var)
	if resource == 'job' or resource == 'job_defs':
		print_run_script_section(resource = resource, padding = padding)
	print("}\n")
	if not is_single:
		print(f"{padding}{{% endfor %}}")
	if not is_mandatory:
		print("{% endif %}")

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

def main(argv):
	daemon_var, input_file = parse_options(argv)
	daemon_type = get_daemon_type(daemon_var)
	print_header(daemon_type)
	with open(input_file, "r") as stream:
		config = OrderedDict(yaml.safe_load(stream))
		for resource, values_dict in config.items():
			# Not single resources have an extra for loop in the template.
			is_single = True if \
			  ('single' in values_dict and values_dict['single']) else False
			# Not mandatory resources have an extra conditional if in the
			# template.
			is_mandatory = True if ('mandatory' not in values_dict
				or values_dict['mandatory']) else False
			padding = '' if is_mandatory else '  '
			process_main_print(resource = resource, values_dict = values_dict,
				is_single = is_single, is_mandatory = is_mandatory,
				padding = padding, daemon_var = daemon_var)
		if daemon_type != 'console':
			print_messages_section(daemon_var = daemon_var)
		if daemon_type == 'director':
			# Print Schedule and FileSet custom template blocks.
			print_director_specific_resources(daemon_var)

if __name__ == '__main__':
	main(sys.argv)