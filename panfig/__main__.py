#!/usr/bin/python3

import sys
import os
import pandocfilters
import panfig

pandocfilters.toJSONFilter(panfig.build_pandoc_filter(panfig.examples.graphviz.generate_image))
