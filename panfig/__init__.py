import pandocfilters

from .panfigblock import PanfigBlock
from . import aliases, errors

def transform_pandoc_element(alias_set, key, value):
  if alias_set.can_be_updated_from_element(key, value):
    try:
      alias_set.update_from_element(key, value)
      return pandocfilters.Null()
    except Exception as exception:
      return errors.make_diagnostic_code_block(key, value, exception)

  if PanfigBlock.is_element_a_figure_block(key, value):
    try:
      block = PanfigBlock.from_pandoc_element(alias_set, key, value)
      return block.build_replacement_pandoc_element()
    except Exception as exception:
      return errors.make_diagnostic_code_block(key, value, exception)

def main():
  alias_set = aliases.DEFAULT_ALIASES.copy()
  pandocfilters.toJSONFilter(lambda key, value, format, meta: transform_pandoc_element(alias_set, key, value))
