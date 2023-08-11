import os

def get_codegen_header() -> str:
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dir_path, 'warning_msg.txt'), 'r') as warning_msg:
        return warning_msg.readlines()