import collections
import os
import sys
import shlex
import hashlib
import subprocess
import json
import pandocfilters
import inspect
from . import errors

class ParseError(Exception): pass
class NoSuchAliasException(Exception): pass

_PanfigBlockBase = collections.namedtuple('_PanfigBlockBase', ['identifier', 'classes', 'attributes', 'content'])
class PanfigBlock(_PanfigBlockBase):

  aliases = {
    'dot': {'shell': 'dot -Tpng -o {path}'},
    'mathematica': {'shell': 'MathKernel {path}',
                    'epilogue': 'Export[$CommandLine[[2]], %, "png"]'},
    'matplotlib': {'shell': '/usr/bin/python - {path}',
                   'prologue': 'import sys; from matplotlib import pyplot as plt',
                   'epilogue': 'plt.savefig(sys.argv[1], format="png")',
                   'dedent': 'true'}}
  @classmethod
  def is_element_an_alias_block(cls, key, value):
    return key=='CodeBlock' and 'panfig-aliases' in value[0][1]
  @classmethod
  def add_aliases_from_pandoc_element(cls, key, value, format, meta):
    if not cls.is_element_an_alias_block(key, value):
      raise ParseError('given Pandoc element does not represent a Panfig alias block')
    (identifier, classes, attributes), content = value
    attributes = dict(attributes)
    if 'panfig-aliases' in classes:
      cls.aliases.update(json.loads(content))
      return

  @classmethod
  def is_element_a_figure_block(cls, key, value):
    return key=='CodeBlock' and 'panfig' in value[0][1]
  @classmethod
  def from_pandoc_element(cls, key, value, format, meta):
    if not cls.is_element_a_figure_block(key, value):
      raise ParseError('given Pandoc element does not represent a Panfig block')
    (identifier, classes, attributes), content = value
    attributes = dict(attributes)
    if 'alias' in attributes:
      if attributes['alias'] not in cls.aliases:
        raise NoSuchAliasException(attributes['alias'])
      attributes = collections.ChainMap(attributes, cls.aliases[attributes['alias']])
    if 'shell' in attributes:
      return cls(identifier=identifier, classes=classes, attributes=attributes, content=content)
    else:
      raise ParseError('block has no shell attribute, or alias giving it one')

  def generate_image(self, path):
    command_format = self.attributes['shell']
    command = command_format.format(path=shlex.quote(path))
    p = subprocess.Popen(
      command,
      shell=True,
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE)

    payload = self.content
    if self.attributes.get('dedent', 'false') == 'true':
      payload = inspect.cleandoc(payload)
    if 'prologue' in self.attributes:
      payload = '\n'.join([self.attributes['prologue'], payload])
    if 'epilogue' in self.attributes:
      payload = '\n'.join([payload, self.attributes['epilogue']])

    out, err = p.communicate(payload.encode())
    if p.returncode != 0:
      raise errors.SubprocessFailed(command, out, err, p.returncode)
    if not os.path.exists(path):
      raise errors.SubprocessFailed(command, out, err, p.returncode)

  def build_replacement_pandoc_element(self):
    path = os.path.join(os.path.expanduser('~'), '.cache', 'panfig', 'figures', sha1(str(self)))
    if not os.path.exists(path):
      os.makedirs(os.path.dirname(path), exist_ok=True)
      self.generate_image(path=path)
      if not os.path.exists(path):
        raise errors.NoFigureProduced()

    alt_text = pandocfilters.Code(['', [], []], errors.make_pandoc_for_block(self))
    image = pandocfilters.Image(
      [self.identifier, self.classes, list(self.attributes.items())],
      [alt_text],
      [path, ''])
    result = pandocfilters.Para([image])
    return result


def sha1(x):
  return hashlib.sha1(x.encode(sys.getfilesystemencoding())).hexdigest()

def pandoc_filter(key, value, format, meta):
  try:
    if PanfigBlock.is_element_an_alias_block(key, value):
      PanfigBlock.add_aliases_from_pandoc_element(key, value, format, meta)
      return pandocfilters.Null()
    elif PanfigBlock.is_element_a_figure_block(key, value):
      return PanfigBlock.from_pandoc_element(key, value, format, meta).build_replacement_pandoc_element()
  except Exception as exception:
    return errors.make_diagnostic_code_block(key, value, exception)

def main():
  pandocfilters.toJSONFilter(pandoc_filter)
