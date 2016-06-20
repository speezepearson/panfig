import collections
import os
import sys
import hashlib
import importlib
import subprocess
import pandocfilters

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
      p = subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stdin=subprocess.PIPE)
      p.communicate(self.content.encode())

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
    panfig_block.generate_image(path=figure_path)

  alt_text = pandocfilters.Code(['', [], []], panfig_block.content)
  image = pandocfilters.Image(
    [panfig_block.identifier, panfig_block.classes, list(panfig_block.attributes.items())],
    [alt_text],
    [figure_path, ''])
  result = pandocfilters.Para([image])
  return result


from . import examples
