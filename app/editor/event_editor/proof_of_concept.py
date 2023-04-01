
import ast
import re

from pprint import pprint

functions = ["print"]

EVENT_FUNC_REGEX = r'event\.([a-zA-Z0-9]*)(\(.*?\))'

scr = """
def pwrapper(x):
  event.eprint(x)

def pwrapper2(x): # SHOULD THROW
  event.eprint(x)
  event.eprint(x)

event.eprint(1)
event.eprint(2)
event.eprint(3)
# event.eprint(event.eprint(1), 2) # SHOULD FUCKING THROW
# event.eprint(1) or event.eprint(2) # SHOULD FUCKING THROW
event.eprint(1) or a.c(b)
for i in range(5):
  event.eprint(i)
with open('input.txt') as f:
  for line in f.readlines():
    event.eprint(line)
x = True
k = 0
while k < 5:
  k += 1
  event.eprint("k", k)
"""

efr = re.compile(EVENT_FUNC_REGEX)
strlines = scr.split("\n")
strlines = [line for line in strlines if line]
parsed = []
for line in strlines:
  try_find_command = efr.findall(line)
  if try_find_command:
    try:
      print("=============")
      print(try_find_command)
      print(line)
      p = ast.parse(line.strip())
      expr = p.body[0]
      print(p.body[0])
      if not isinstance(expr, ast.Expr):
        raise TypeError()
      v = expr.value
      if not isinstance(v, ast.Call):
        raise TypeError()
      print(ast.dump(expr))
      numCalls = 0
      for node in ast.walk(ast.parse(line.strip())):
        if isinstance(node, ast.Call):
          if node.func.attr in functions:
            numCalls += 1
      if numCalls > 1:
        raise TypeError()
      print(line)
      yield_def = "yield lambda: %s" % line.strip()
      line = line.replace(line.strip(), yield_def)
      parsed.append(line)
    except:
      print("ERROR RAN INTO!")
  else:
    parsed.append(line)

print("=====================")
print('\n'.join(parsed))

parsedstr = '\n\t'.join(parsed)

gen = \
"""
def gg():
\t%s
""" % parsedstr

print(gen)

exec(gen)

class Event():
  def eprint(self, *args):
    print(*args)

event = Event()

g = gg()
while True:
  try:
    next(g)()
  except StopIteration:
    print("done")
    break