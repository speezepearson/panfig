import traceback
import json
import pandocfilters

class SubprocessFailed(RuntimeError):
  def __init__(self, command, out, err, returncode):
    super().__init__('exit status {} from {!r}'.format(returncode, command))
    self.command = command
    self.out = out
    self.err = err
    self.returncode = returncode

class NoFigureProduced(RuntimeError):
  pass

def indent(s, level=1):
  return '\n'.join(level*'  '+line for line in s.split('\n'))

def make_pandoc_for_block(block):
  return make_pandoc_for_code_block([[block.identifier, block.classes, list(block.attributes.items())], block.content])

def make_pandoc_for_code_block(value):
  (identifier, classes, attributes), content = value
  attributes = dict(attributes)

  fence = '~' * max((len(line) for line in content.split('\n') if all(c=='~' for c in line)), default=8)
  header = '{fence} {{ {rest} }}'.format(
    fence=fence,
    rest=' '.join(
      (['#'+identifier] if identifier else []) +
      ['.'+cls for cls in classes] +
      ['{}={}'.format(k,json.dumps(v)) for k,v in attributes.items()]))
  return '\n'.join([header, content, fence])


def make_diagnostic_code_block(key, value, exception):
  paragraphs = [
    'Error! Offending element:',
    indent(make_pandoc_for_code_block(value) if key=='CodeBlock' else str((key,value))),
    'Traceback:',
    indent('\n'.join(traceback.format_exception(exception.__class__, exception, exception.__traceback__)))]
  if isinstance(exception, SubprocessFailed):
    try: stdout = exception.out.decode()
    except UnicodeDecodeError: stdout = exception.out
    try: stderr = exception.err.decode()
    except UnicodeDecodeError: stderr = exception.err
    paragraphs += ['Stdout:', indent(stdout), 'Stderr:', indent(stderr)]

  return pandocfilters.CodeBlock(['', [], []], '\n\n'.join(paragraphs))
