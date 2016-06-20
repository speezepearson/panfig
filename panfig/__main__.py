#!/usr/bin/python3

import sys
import os
import pandocfilters
import panfig

pandocfilters.toJSONFilter(panfig.pandoc_filter)
