import collections
import os
import sys
import hashlib
import pandocfilters

_PanfigBlockBase = collections.namedtuple('_PanfigBlockBase', ['identifier', 'classes', 'attributes', 'content'])
class PanfigBlock(_PanfigBlockBase):
  @classmethod
  def from_pandoc_element(cls, key, value, format, meta):
    if key=='CodeBlock':
      (identifier, classes, attributes), content = value
      if 'panfig' in classes:
        return cls(identifier=identifier, classes=classes, attributes=attributes, content=content)
    raise ValueError('given Pandoc element does not represent a Panfig block')

def sha1(x):
  return hashlib.sha1(x.encode(sys.getfilesystemencoding())).hexdigest()

def build_pandoc_filter(generate_image):
  def pandoc_filter(key, value, format, meta):
    try:
      panfig_block = PanfigBlock.from_pandoc_element(key, value, format, meta)
    except ValueError:
      return None

    figure_path = os.path.join('panfig-figures', sha1(str(panfig_block)))
    if not os.path.exists(figure_path):
      os.makedirs('panfig-figures', exist_ok=True)
      generate_image(panfig_block, figure_path)

    alt_text = pandocfilters.Code(['', [], []], panfig_block.content)
    image = pandocfilters.Image(
      [panfig_block.identifier,
       panfig_block.classes,
       panfig_block.attributes],
      [alt_text],
      [figure_path, ''])
    result = pandocfilters.Para([image])
    return result

  return pandoc_filter


from . import examples
