import collections
import os
import sys
import shlex
import hashlib
import subprocess
import inspect

import pandocfilters

from . import errors, aliases

def sha1(x):
  return hashlib.sha1(x.encode(sys.getfilesystemencoding())).hexdigest()

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

  @property
  def prologue(self):
    return self.attributes.get('prologue')
  @property
  def epilogue(self):
    return self.attributes.get('epilogue')
  @property
  def image_path(self):
    return os.path.join(os.path.expanduser('~'), '.cache', 'panfig', 'figures', sha1(str(self)))

  @property
  def shell_command(self):
    return self.attributes['shell'] % shlex.quote(self.image_path)

  @property
  def shell_command_payload(self):
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
      raise errors.SubprocessFailed(command, out, err, p.returncode)
    if not os.path.exists(self.image_path):
      raise errors.SubprocessFailed(command, out, err, p.returncode)

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
      [self.image_path, ''])
    result = pandocfilters.Para([image])
    return result
