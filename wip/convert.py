from app.events.event_commands import parse_text_to_command, EventCommand, Comment
from app.utilities.str_utils import camel_to_snake


def to_python_command(e: EventCommand):
    all_keywords = e.keywords + e.optional_keywords
    args_list = []
    for arg_name in all_keywords:
        arg_val = e.parameters.get(arg_name, None)
        if arg_val is not None:
            arg_val = arg_val.strip()
            arg_val = arg_val.replace('"', "\"")
            arg_val = arg_val.replace("'", "\'")
            if arg_name in e.keywords:
                args_list.append('\"' + str(arg_val) + '\"')
            elif arg_name in e.optional_keywords:
                args_list.append(camel_to_snake(arg_name) + '=\"' + str(arg_val) + '\"')
    all_args = ', '.join(args_list)
    flags = ', '.join(['\"' + flag + '\"' for flag in e.chosen_flags])
    flagstr = ""
    if flags:
        flagstr = ", flags=[{flags}]".format(flags=flags)
    return "{event_nid}({args}{flagstr})".format(event_nid=e.nid, args=all_args, flagstr=flagstr)

with open('event_0.txt') as f:
    for line in f.readlines():
        command, _ = parse_text_to_command(line)
        if not isinstance(command, Comment):
            print(to_python_command(command))