import collections
import os
import sys
import hashlib
import importlib
import subprocess
import pandocfilters
from . import errors

_PanfigBlockBase = collections.namedtuple('_PanfigBlockBase', ['identifier', 'classes', 'attributes', 'content'])
class PanfigBlock(_PanfigBlockBase):
  @classmethod
  def from_pandoc_element(cls, key, value, format, meta):
    if key=='CodeBlock':
      (identifier, classes, attributes), content = value
      attributes = dict(attributes)
      if 'panfig-function' in attributes or 'panfig-script' in attributes:
        return cls(identifier=identifier, classes=classes, attributes=attributes, content=content)
    raise ValueError('given Pandoc element does not represent a Panfig block')

  def generate_image(self, path):
    if 'panfig-function' in self.attributes:
      module_name, function_name = self.attributes['panfig-function'].rsplit('.', 1)
      module = importlib.import_module(module_name)
      function = getattr(module, function_name)
      function(self, path)
    elif 'panfig-script' in self.attributes:
      command_format = self.attributes['panfig-script']
      command = command_format.format(block=self, path=path)
      p = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      out, err = p.communicate(self.content.encode())
      if p.returncode != 0:
        raise errors.SubprocessFailed(command, out, err, p.returncode)
      if not os.path.exists(path):
        raise errors.SubprocessFailed(command, out, err, p.returncode)

def sha1(x):
  return hashlib.sha1(x.encode(sys.getfilesystemencoding())).hexdigest()

def pandoc_filter(key, value, format, meta):
  try:
    panfig_block = PanfigBlock.from_pandoc_element(key, value, format, meta)
  except ValueError:
    return None

  figure_path = os.path.join('panfig-figures', sha1(str(panfig_block)))
  if not os.path.exists(figure_path):
    os.makedirs('panfig-figures', exist_ok=True)
    try:
      panfig_block.generate_image(path=figure_path)
      if not os.path.exists(figure_path):
        raise errors.NoFigureProduced()
    except Exception as e:
      return pandocfilters.CodeBlock(['', [], []], errors.format_figure_failure(panfig_block, e))

  alt_text = pandocfilters.Code(['', [], []], panfig_block.content)
  image = pandocfilters.Image(
    [panfig_block.identifier, panfig_block.classes, list(panfig_block.attributes.items())],
    [alt_text],
    [figure_path, ''])
  result = pandocfilters.Para([image])
  return result


from . import examples
