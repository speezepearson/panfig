import collections
import os
import sys
import hashlib
import importlib
import subprocess
import pandocfilters
from . import errors

def environment_with_scripts_on_path():
  env = os.environ
  d = os.path.join(os.path.expanduser('~'),'.config','panfig','scripts')
  return collections.ChainMap(
    {'PATH': os.pathsep.join([d, os.environ['PATH']])},
    os.environ)

_PanfigBlockBase = collections.namedtuple('_PanfigBlockBase', ['identifier', 'classes', 'attributes', 'content'])
class PanfigBlock(_PanfigBlockBase):
  @classmethod
  def from_pandoc_element(cls, key, value, format, meta):
    if key=='CodeBlock':
      (identifier, classes, attributes), content = value
      attributes = dict(attributes)
      if 'panfig-cmd' in attributes:
        return cls(identifier=identifier, classes=classes, attributes=attributes, content=content)
    raise ValueError('given Pandoc element does not represent a Panfig block')

  def generate_image(self, path):
    command_format = self.attributes['panfig-cmd']
    command = command_format.format(block=self, path=path)
    p = subprocess.Popen(
      command,
      shell=True,
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      env=environment_with_scripts_on_path())
    out, err = p.communicate(self.content.encode())
    if p.returncode != 0:
      raise errors.SubprocessFailed(command, out, err, p.returncode)
    if not os.path.exists(path):
      raise errors.SubprocessFailed(command, out, err, p.returncode)


  def build_replacement_pandoc_element(self):
    path = os.path.join('panfig-figures', sha1(str(self)))
    if not os.path.exists(path):
      os.makedirs('panfig-figures', exist_ok=True)
      try:
        self.generate_image(path=path)
        if not os.path.exists(path):
          raise errors.NoFigureProduced()
      except Exception as e:
        return pandocfilters.CodeBlock(['', [], []], errors.format_figure_failure(self, e))

    alt_text = pandocfilters.Code(['', [], []], self.content)
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
    panfig_block = PanfigBlock.from_pandoc_element(key, value, format, meta)
  except ValueError:
    return None

  return panfig_block.build_replacement_pandoc_element()
