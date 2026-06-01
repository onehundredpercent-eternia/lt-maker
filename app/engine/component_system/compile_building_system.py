from __future__ import annotations
from typing import Dict
from app.engine.codegen.codegen_utils import get_codegen_header
from app.engine.component_system.utils import ARG_TYPE_MAP, HookInfo

BUILDING_HOOKS: Dict[str, HookInfo] = {    
}

def generate_building_hook_str(hook_name: str, hook_info: HookInfo):
    args = hook_info.args
    if 'city' not in args:
        raise ValueError("Expected 'city' in args for hook %s" % hook_name)
    func_signature = ['{arg}: {type}'.format(arg=arg, type=ARG_TYPE_MAP.get(arg, "Any")) for arg in args]

    conditional_check = "condition(building, city)"
    default_handling = "return result"
    unconditional_handling = ""
    cache_handling = ""
    if hook_info.has_default_value:
        default_handling = "return result if values else Defaults.{hook_name}({args})".format(hook_name=hook_name, args=', '.join(args))
    if hook_info.has_unconditional:
        unconditional_handling = """
            if component.defines('{hook_name}_unconditional'):
                values.append(component.{hook_name}_unconditional({args}))
""".format(hook_name=hook_name, args=', '.join(args))
    if hook_info.is_cached:
        cache_handling = """
@ltcached"""

    func_text = """{cache_handling}
def {hook_name}({func_signature}):
    values = []
    for component in building.components:
        if component.defines('{hook_name}'):
            if component.ignore_conditional or {conditional_check}:
                values.append(component.{hook_name}({args}))
{unconditional_handling}
    result = utils.{policy_resolution}(values)
    {default_handling}
""".format(hook_name=hook_name,
           func_signature=', '.join(func_signature),
           conditional_check=conditional_check,
           args=', '.join(args),
           policy_resolution=hook_info.policy.value,
           default_handling=default_handling,
           unconditional_handling=unconditional_handling,
           cache_handling=cache_handling)

    return func_text

def compile_building_system():
    import os
    dir_path = os.path.dirname(os.path.realpath(__file__))
    compiled_building_system = open(os.path.join(
        dir_path, '..', 'building_system.py'), 'w')
    building_system_base = open(os.path.join(
        dir_path, 'building_system_base.py'), 'r')

    # write warning msg
    compiled_building_system.writelines(get_codegen_header())

    # copy building system base
    for line in building_system_base.readlines():
        compiled_building_system.write(line)

    for hook_name, hook_info in BUILDING_HOOKS.items():
        func = generate_building_hook_str(hook_name, hook_info)
        compiled_building_system.write(func)

    building_system_base.close()
    compiled_building_system.close()
