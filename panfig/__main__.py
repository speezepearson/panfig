#!/home/spencer/.virtualenvusr/bin/python3

import pandocfilters as pf
import tempfile


import os, sys
os.makedirs('panfig-figures', exist_ok=True)

import hashlib
def sha1(x):
  return hashlib.sha1(x.encode(sys.getfilesystemencoding())).hexdigest()



import subprocess
def graphviz(content, path):
  with open(path, 'wb') as f:
    p = subprocess.Popen(['dot', '-Tpng'], stdin=subprocess.PIPE, stdout=f)
    p.communicate(('digraph G {'+content+'}').encode())

def replace_panfig_blocks(key, value, format, meta):
  import sys; print(key, value, format, meta, file=sys.stderr)
  if key == 'CodeBlock':
    (identifier, classes, attributes), content = value
    if 'panfig' in classes:
      path = os.path.join('panfig-figures', sha1(str(value)))
      if not os.path.exists(path):
        graphviz(content, path)
        return pf.Para([pf.Image(['', [], []], [], [path, ''])])

if __name__ == '__main__':
  pf.toJSONFilter(replace_panfig_blocks)
