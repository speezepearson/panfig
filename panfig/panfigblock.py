import collections
import os
import sys
import shlex
import hashlib
import subprocess
import inspect
from typing import NamedTuple, Sequence, Mapping, Any

import pandocfilters

from . import errors, aliases
from ._types import PandocCodeBlockType

def sha1(s:str) -> str:
  return hashlib.sha1(s.encode(sys.getfilesystemencoding())).hexdigest()

_PanfigBlockBase = NamedTuple('_PanfigBlockBase', [('identifier',str), ('classes',Sequence[str]), ('attributes',Mapping[str,str]), ('content',str)])
class PanfigBlock(_PanfigBlockBase):

  @classmethod
  def is_element_a_figure_block(cls, key:str, value:Any) -> bool:
    return key=='CodeBlock' and 'panfig' in value[0][1]
  @classmethod
  def from_pandoc_element(cls, alias_set:aliases.AliasSet, key:str, value:PandocCodeBlockType) -> 'PanfigBlock':
    if not cls.is_element_a_figure_block(key, value):
      raise errors.ParseError('given Pandoc element does not represent a Panfig block')
    (identifier, classes, attributes_list), content = value
    attributes = dict(attributes_list)
    if 'alias' in attributes:
      alias = attributes['alias']
      if attributes['alias'] not in alias_set:
        raise aliases.NoSuchAliasException(alias)
      attributes = collections.ChainMap(attributes, alias_set[alias])
    if 'shell' in attributes:
      return cls(identifier=identifier, classes=classes, attributes=attributes, content=content)
    else:
      raise errors.ParseError('block has no shell attribute, or alias giving it one')

  @property
  def prologue(self) -> str:
    return self.attributes.get('prologue')
  @property
  def epilogue(self) -> str:
    return self.attributes.get('epilogue')
  @property
  def image_path(self) -> str:
    return os.path.join(os.path.expanduser('~'), '.cache', 'panfig', 'figures', sha1(str(self)))

  @property
  def shell_command(self) -> str:
    return self.attributes['shell'] % shlex.quote(self.image_path)

  @property
  def shell_command_payload(self) -> str:
    sections = []
    if self.prologue is not None:
      sections.append(self.prologue)
    sections.append(inspect.cleandoc(self.content) if self.attributes.get('dedent')=='true' else self.content)
    if self.epilogue is not None:
      sections.append(self.epilogue)
    return '\n'.join(sections)

  def start_subprocess(self):
    return subprocess.Popen(
      self.shell_command,
      shell=True,
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE)

  def generate_image(self):
    p = self.start_subprocess()

    out, err = p.communicate(self.shell_command_payload.encode())
    if p.returncode != 0:
      raise errors.SubprocessFailed(self.shell_command, out, err, p.returncode)
    if not os.path.exists(self.image_path):
      raise errors.SubprocessFailed(self.shell_command, out, err, p.returncode)

  def build_replacement_pandoc_element(self):
    if not os.path.exists(self.image_path):
      os.makedirs(os.path.dirname(self.image_path), exist_ok=True)
      self.generate_image()
      if not os.path.exists(self.image_path):
        raise errors.NoFigureProduced()

    alt_text = pandocfilters.Code(['', [], []], errors.make_pandoc_for_block(self))
    image = pandocfilters.Image(
      [self.identifier, self.classes, list(self.attributes.items())],
      [alt_text],
      [self.image_path, errors.make_pandoc_for_block(self)])
    result = pandocfilters.Para([image])
    return result
