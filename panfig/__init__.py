import collections
import os
import sys
import shlex
import hashlib
import subprocess
import json
import pandocfilters
import inspect
from . import aliases, errors

class ParseError(Exception): pass

_PanfigBlockBase = collections.namedtuple('_PanfigBlockBase', ['identifier', 'classes', 'attributes', 'content'])
class PanfigBlock(_PanfigBlockBase):

  @classmethod
  def is_element_a_figure_block(cls, key, value):
    return key=='CodeBlock' and 'panfig' in value[0][1]
  @classmethod
  def from_pandoc_element(cls, alias_set, key, value):
    if not cls.is_element_a_figure_block(key, value):
      raise ParseError('given Pandoc element does not represent a Panfig block')
    (identifier, classes, attributes), content = value
    attributes = dict(attributes)
    if 'alias' in attributes:
      alias = attributes['alias']
      if attributes['alias'] not in alias_set:
        raise aliases.NoSuchAliasException(alias)
      attributes = collections.ChainMap(attributes, alias_set[alias])
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

def transform_pandoc_element(alias_set, key, value):
  if alias_set.can_be_updated_from_element(key, value):
    try:
      alias_set.update_from_element(key, value)
      return pandocfilters.Null()
    except Exception as exception:
      return errors.make_diagnostic_code_block(key, value, exception)

  if PanfigBlock.is_element_a_figure_block(key, value):
    block  = PanfigBlock.from_pandoc_element(alias_set, key, value)
    try:
      return block.build_replacement_pandoc_element()
    except Exception as exception:
      return errors.make_diagnostic_code_block(key, value, exception)

def main():
  alias_set = aliases.DEFAULT_ALIASES.copy()
  pandocfilters.toJSONFilter(lambda key, value, format, meta: transform_pandoc_element(alias_set, key, value))
