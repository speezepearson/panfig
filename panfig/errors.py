import traceback

class SubprocessFailed(RuntimeError):
  def __init__(self, command, out, err, returncode):
    super().__init__(command, returncode)
    self.command = command
    self.out = out
    self.err = err
    self.returncode = returncode

class NoFigureProduced(RuntimeError):
  pass

def indent(s, level=1):
  return '\n'.join(level*'  '+line for line in s.split('\n'))

main_format='''
Exception:

{traceback}

Offending block:

  Identifier: {block.identifier},
  Classes: {block.classes},
  Attributes: {block.attributes},

  Content:

{content}
'''

addendum='''
Stdout:

{stdout}

Stderr:

{stderr}'''


def format_figure_failure(panfig_block, exception):
  result = main_format.format(
      block=panfig_block,
      content=indent(panfig_block.content, level=2),
      traceback=indent(''.join(traceback.format_exception(exception.__class__, exception, exception.__traceback__))))

  if isinstance(exception, SubprocessFailed):
    result += addendum.format(
        stdout=indent(exception.out.decode()),
        stderr=indent(exception.err.decode()))

  return result
