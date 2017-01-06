import json
from . import errors
from ._types import PandocCodeBlockType

class NoSuchAliasException(Exception):
  pass

class AliasSet(dict):
  def can_be_updated_from_element(self, key:str, value:PandocCodeBlockType) -> bool:
    return key=='CodeBlock' and 'panfig-aliases' in value[0][1]

  def update_from_element(self, key:str, value:PandocCodeBlockType) -> bool:
    if not self.can_be_updated_from_element(key, value):
      raise errors.ParseError('given Pandoc element does not represent a Panfig alias block')
    (identifier, classes, attributes), content = value
    self.update(json.loads(content))

  def copy(self) -> 'AliasSet':
    return AliasSet(super().copy())

DEFAULT_ALIASES = AliasSet(
  dot={'shell': 'dot -Tpng -o %s'},
  mathematica={'shell': 'MathKernel %s',
               'epilogue': 'Export[$CommandLine[[2]], %, "png"]'},
  matplotlib={'shell': '/usr/bin/python - %s',
              'prologue': 'import sys; from matplotlib import pyplot as plt',
              'epilogue': 'plt.savefig(sys.argv[1], format="png")',
              'dedent': 'true'})
