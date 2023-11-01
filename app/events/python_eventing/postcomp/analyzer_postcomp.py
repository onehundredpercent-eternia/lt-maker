
from app.events.python_eventing.swscomp.comp_utils import COMMAND_SENTINEL, ScriptWithSentinel
from app.events.python_eventing.utils import EVENT_INSTANCE

class AnalyzerPostComp():
    """
    Differs from full postcomp in that it puts the functions in as normal functions.
    This is easier to analyze the AST for to do error-checking.
    """
    @staticmethod
    def postcomp(sentinel_script: ScriptWithSentinel):
        n_commands = sentinel_script.source.count(COMMAND_SENTINEL)
        script = sentinel_script.source
        if not n_commands == len(sentinel_script.commands):
            raise ValueError("Number of commands does not match number of sentinels.")
        for i in range(n_commands):
            command_data = sentinel_script.commands[i]
            command = "%s.%s" % (EVENT_INSTANCE, command_data.to_event_command_str())
            script = script.replace(COMMAND_SENTINEL, command, 1)
        return script
