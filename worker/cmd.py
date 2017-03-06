import re

def hint(hint_str):
    def decorator(f):
        f.hint_str = f
        return f
    return decorator

def register(command):
    def decorator(f):
        regex = get_regex(command)
        command_name = get_command_name(command)

        f.is_command = True
        f.regex = re.compile(regex)
        f.command_name = command_name
        return f
    return decorator

def get_command_name(command):
    pattern = r'^!([a-zA-Z0-9_\-]*)'
    match = re.match(pattern, command)

    return match and match.group(1)

def get_command_regex(command):
    pattern = '<(\w*):(\w*)>'
    args = re.findall(pattern, command)

    command_name = get_command_name(command)

    regex = '^!{}'.format(command_name)

    arg_regex = {'member': '<@!?(?P<ARG_NAME>[0-9]*)>',
                 'channel': '<#(?P<ARG_NAME>[0-9]*)>',
                 'role': '<@&(?P<ARG_NAME>[0-9]*)>',
                 'str': '(?P<ARG_NAME>.*)',
                 'int': '(?P<ARG_NAME>[0-9]*)'}
    for arg_name, arg_type in args:
        arg_type_regex = arg_regex.get(arg_type).replace('ARG_NAME',
                                                         arg_name)
        regex += '[ ]*' + arg_type_regex

    return regex

def command_handler(command_func, message):
    regex = command_func.regex
    match = regex.match(message.content)
    if not match:
        return

    args = match.groupdict()

    ctx = object()
    ctx.message = message
    ctx.guild = message.guild

    return command_func(ctx, **args)

"""
@command.register('!mention <member:member> <text:str>')
@command.hint('!mention [the member to mention] [the text to send]')
def mention(self, ctx, member, text):
"""
