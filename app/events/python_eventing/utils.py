from typing import Any

DO_NOT_EXECUTE_SENTINEL = -1

class ResumeCheck():
    def __init__(self, line_no_to_catch: int) -> None:
        self.catching_up = True
        self.line_no = line_no_to_catch

    def check_set_caught_up(self, line_no):
        is_catching_up = self.catching_up
        if line_no == self.line_no:
            self.catching_up = False
        return is_catching_up