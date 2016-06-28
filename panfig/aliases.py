class NoSuchAliasException(Exception):
  pass

class AliasSet(dict):
  def can_be_updated_from_element(self, key, value):
    return key=='CodeBlock' and 'panfig-aliases' in value[0][1]

  def update_from_element(self, key, value):
    if not self.is_element_an_alias_block(key, value):
      raise ParseError('given Pandoc element does not represent a Panfig alias block')
    (identifier, classes, attributes), content = value
    self.update(json.loads(content))

  def copy(self):
    return AliasSet(super().copy())

DEFAULT_ALIASES = AliasSet(
  dot={'shell': 'dot -Tpng -o {path}'},
  mathematica={'shell': 'MathKernel {path}',
               'epilogue': 'Export[$CommandLine[[2]], %, "png"]'},
  matplotlib={'shell': '/usr/bin/python - {path}',
              'prologue': 'import sys; from matplotlib import pyplot as plt',
              'epilogue': 'plt.savefig(sys.argv[1], format="png")',
              'dedent': 'true'})
