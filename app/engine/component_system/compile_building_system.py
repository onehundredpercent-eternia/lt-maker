from __future__ import annotations
from typing import Dict
from app.engine.codegen.codegen_utils import GeneratedSource, get_codegen_header
from app.engine.component_system.utils import ARG_TYPE_MAP, HookInfo, ResolvePolicy

# City-aggregate hooks: mirror skill_system. `city` is the primary object (like `unit`);
# each hook fans out over every component of every building in the city. The parent
# `building` is NOT passed to the component method (a component reaches it via self.building),
# exactly as skill dispatch passes `unit` but not `skill`.
# Single-candidate-building hooks (condition, available, target_restrict) are hand-written
# in building_system_base.py instead, since they evaluate one candidate building.
BUILDING_HOOKS: Dict[str, HookInfo] = {
    'on_upkeep':                    HookInfo(['city'], ResolvePolicy.NO_RETURN),
    'produces_units':               HookInfo(['city'], ResolvePolicy.LIST),
    'influence_range_modification': HookInfo(['city'], ResolvePolicy.NUMERIC_ACCUM),
    # Asked about a unit the city has just drafted
    'starting_level_modification':  HookInfo(['city', 'unit'], ResolvePolicy.NUMERIC_ACCUM),
    'stat_change':                  HookInfo(['city', 'unit'], ResolvePolicy.LIST),
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
    for building in city.buildings[:]:
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
    compiled_building_system = GeneratedSource(os.path.join(
        dir_path, '..', 'building_system.py'))
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
