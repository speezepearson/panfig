import traceback
import json

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

{pandoc_for_block}
'''

addendum='''
Stdout:

{stdout}

Stderr:

{stderr}'''


def make_pandoc_for_block(block):
  footer = '~' * max((len(line) for line in block.content.split('\n') if all(c=='~' for c in line)), default=8)
  header = '{footer} {{ {rest} }}'.format(
    footer=footer,
    rest=' '.join(
      (['#'+block.identifier] if block.identifier else []) +
      ['.'+cls for cls in block.classes] +
      ['{}={}'.format(k,json.dumps(v)) for k,v in block.attributes.items()]))
  return '\n'.join([header, block.content, footer])


def format_figure_failure(panfig_block, exception):
  result = main_format.format(
      pandoc_for_block=indent(make_pandoc_for_block(panfig_block)),
      content=indent(panfig_block.content, level=2),
      traceback=indent(''.join(traceback.format_exception(exception.__class__, exception, exception.__traceback__))))

  if isinstance(exception, SubprocessFailed):
    try: stdout = exception.out.decode()
    except UnicodeDecodeError: stdout = exception.out
    try: stderr = exception.err.decode()
    except UnicodeDecodeError: stderr = exception.err
    result += addendum.format(
        stdout=indent(stdout),
        stderr=indent(stderr))

  return result
