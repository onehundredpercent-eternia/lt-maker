from app.engine.game_state import GameState
from app.engine import evaluate
import re
from typing import List, Tuple

from app.utilities import str_utils
import logging

class TextEvaluator():
    def __init__(self, logger: logging.Logger, game: GameState, unit=None, unit2=None, item=None, position=None, region=None) -> None:
        self.logger = logger
        self.game: GameState = game
        self.unit = unit
        self.unit2 = unit2
        self.created_unit = None
        self.item = item
        self.position = position
        self.region = region

    def _object_to_str(self, obj) -> str:
        if hasattr(obj, 'uid'):
            return str(obj.uid)
        elif hasattr(obj, 'nid'):
            return str(obj.nid)
        else:
            return str(obj)

    def _evaluate_phrase(self, text: str) -> str:
        """Accepts a string such as {eval:expr}, and returns its evaluation
        """
        if re.match(r'\{e:[^{}]*\}', text) or re.match(r'\{eval:[^{}]*\}', text): # eval statement
            return self._evaluate_evals(text)
        elif re.match(r'\{[1-5]\}', text):
            return self._evaluate_args(text)
        elif re.match(r'\{d:[^{}]*\}', text) or re.findall(r'\{data:[^{}]*\}', text):
            return self._evaluate_data(text)
        elif re.match(r'\{f:[^{}]*\}', text) or re.match(r'\{field:[^{}]*\}', text):
            return self._evaluate_unit_fields(text)
        elif re.match(r'\{v:[^{}]*\}', text) or re.match(r'\{var:[^{}]*\}', text):
            return self._evaluate_vars(text)
        else:
            return text

    def _evaluate_all(self, text: str) -> str:
        def recursive_parse(parse_list) -> str:
            copy = [""] * len(parse_list)
            for idx, nested in enumerate(parse_list):
                if isinstance(nested, list):
                    recursively_parsed = recursive_parse(nested)
                    copy[idx] = recursively_parsed
                else:
                    copy[idx] = nested
            return str(self._evaluate_phrase('{' + ''.join(copy) + '}'))
        to_evaluate = str_utils.matched_expr(text, '{', '}')
        evaluated = []
        for to_eval in to_evaluate:
            parsed = str_utils.nested_expr(to_eval, '{', '}')
            evaled = recursive_parse(parsed)
            evaluated.append(evaled)
        for idx in range(len(to_evaluate)):
            text = text.replace(to_evaluate[idx], evaluated[idx])
        return text

    def _evaluate_args(self, text) -> str:
        to_evaluate = re.findall(r'\{[1-5]\}', text)
        evaluated = []
        for to_eval in to_evaluate:
            try:
                if to_eval == '{1}':
                    if not isinstance(self.unit, str):
                        self.logger.error("{1} is not a string. If you wish to access {unit}, use that tag instead. Evaluating to %s" % self._object_to_str(self.unit))
                    value = self._object_to_str(self.unit)
                elif to_eval == '{2}':
                    if not isinstance(self.unit2, str):
                        self.logger.error("{2} is not a string. If you wish to access {unit2}, use that tag instead. Evaluating to %s" % self._object_to_str(self.unit2))
                    value = self._object_to_str(self.unit2)
                elif to_eval == '{3}':
                    if not isinstance(self.item, str):
                        self.logger.error("{3} is not a string. Evaluating to %s" % self._object_to_str(self.item))
                    value = self._object_to_str(self.item)
                elif to_eval == '{4}':
                    if not isinstance(self.position, str):
                        self.logger.error("{4} is not a string. Evaluating to %s" % self._object_to_str(self.position))
                    value = self._object_to_str(self.position)
                elif to_eval == '{5}':
                    if not isinstance(self.region, str):
                        self.logger.error("{5} is not a string. Evaluating to %s" % self._object_to_str(self.region))
                    value = self._object_to_str(self.region)
                evaluated.append(value)
            except Exception as e:
                self.logger.error("Could not evaluate %s (%s)" % (to_eval, e))
                evaluated.append('??')
        for idx in range(len(to_evaluate)):
            text = text.replace(to_evaluate[idx], evaluated[idx])
        return text

    def _evaluate_data(self, text) -> str:
        if not self.game:
            return "??"
        # find data fields {d:}
        to_evaluate: List[str] = re.findall(r'\{d:[^{}]*\}', text) + re.findall(r'\{data:[^{}]*\}', text)
        evaluated = []
        for to_eval in to_evaluate:
            to_eval = self.trim_eval_tags(to_eval)
            args = to_eval.split('.')
            try:
                data_nid = args[0]
                # expected syntax:
                # {d:data_nid} if str
                # {d:data_nid.key_nid} if kv dict
                # {d:data_nid.obj_nid.property_nid} if list/table
                # {d:data_nid.[p1=x,p2=y,p3=z].property_nid} if list/table with searching
                if len(args) == 1:
                    resolved_data = self.game.get_data(data_nid)
                elif len(args) == 2:
                    key_nid = args[1]
                    resolved_data = self.game.get_data(data_nid)[key_nid]
                elif len(args) == 3:
                    attr_nid = args[2]
                    if args[1].startswith('[') and args[1].endswith(']'): # searching
                        searches = args[1][1:-1].split(',')
                        search_keys: List[Tuple[str, str]] = []
                        general_search_keys: List[str] = []
                        for term in searches:
                            searchl = term.split('-')
                            if len(searchl) == 1: # single search term, if any match we're good
                                general_search_keys.append(searchl[0].strip())
                            elif len(searchl) == 2: # search key set to value
                                col, val = searchl
                                search_keys.append((col.strip(), val.strip()))
                        for item in self.game.get_data(data_nid)._list:
                            if all([hasattr(item, col) and getattr(item, col) == val for col, val in search_keys]) and \
                                all([any([getattr(item, col) == val for col in dir(item)]) for val in general_search_keys]):
                                return getattr(item, attr_nid)
                        raise ValueError("No data matching" + str(search_keys) + " and " + str(general_search_keys))
                    else:
                        obj_nid = args[1]
                        resolved_data = getattr(self.game.get_data(data_nid).get(obj_nid), attr_nid)
                else:
                    raise ValueError("Bad data format")
                evaluated.append(self._object_to_str(resolved_data))
            except Exception as e:
                self.logger.error("eval failed, failed to parse %s (%s)", to_eval, repr(e))
                evaluated.append('??')
        for idx in range(len(to_evaluate)):
            text = text.replace(to_evaluate[idx], evaluated[idx])
        return text

    def _evaluate_unit_fields(self, text) -> str:
        # find unit fields {f:}
        to_evaluate: List[str] = re.findall(r'\{f:[^{}]*\}', text) + re.findall(r'\{field:[^{}]*\}', text)
        evaluated = []
        for to_eval in to_evaluate:
            to_eval = self.trim_eval_tags(to_eval)
            # expected syntax: {f:[unit.]key, fallback}
            if ',' in to_eval:
                field_text, fallback = to_eval.split(',', 1)
            else:
                field_text, fallback = to_eval, " "

            if '.' in to_eval: # possible unit tag?
                unit_nid, field = field_text.split('.', 1)
            else:
                unit_nid, field = '_unit', field_text

            if unit_nid == '_unit':
                unit = self.unit
            elif unit_nid == '_unit2':
                unit = self.unit2
            elif self.game:
                unit = self.game.get_unit(unit_nid)

            if not unit:
                self.logger.error("eval of {f:%s} failed, unknown unit: %s", to_eval, unit_nid)
                evaluated.append('??')
                continue
            field_value = unit.get_field(field, fallback)
            evaluated.append(self._object_to_str(field_value))
        for idx in range(len(to_evaluate)):
            text = text.replace(to_evaluate[idx], evaluated[idx])
        return text

    def _evaluate_evals(self, text) -> str:
        # Set up variables so evals work well
        to_evaluate = re.findall(r'\{e:[^{}]*\}', text) + re.findall(r'\{eval:[^{}]*\}', text)
        evaluated = []
        for to_eval in to_evaluate:
            to_eval = self.trim_eval_tags(to_eval)
            try:
                val = evaluate.evaluate(to_eval, self.unit, self.unit2, self.item, self.position, self.region)
                evaluated.append(self._object_to_str(val))
            except Exception as e:
                self.logger.error("Could not evaluate %s (%s)" % (to_eval[6:-1], e))
                evaluated.append('??')
        for idx in range(len(to_evaluate)):
            text = text.replace(to_evaluate[idx], evaluated[idx])
        return text

    def _evaluate_vars(self, text) -> str:
        if not self.game:
            return "??"
        text = self._evaluate_args(text)
        to_evaluate = re.findall(r'\{v:[^{}]*\}', text) + re.findall(r'\{var:[^{}]*\}', text)
        evaluated = []
        for to_eval in to_evaluate:
            key = self.trim_eval_tags(to_eval)
            if key in self.game.level_vars:
                val = self._object_to_str(self.game.level_vars[key])
            elif key in self.game.game_vars:
                val = self._object_to_str(self.game.game_vars[key])
            else:
                self.logger.error("Could not find var {%s} in self.game.level_vars or self.game.game_vars" % key)
                val = '??'
            evaluated.append(val)
        for idx in range(len(to_evaluate)):
            text = text.replace(to_evaluate[idx], evaluated[idx])
        return text

    def trim_eval_tags(self, text: str) -> str:
        colon_idx = text.index(':')
        return text[colon_idx+1:-1]
