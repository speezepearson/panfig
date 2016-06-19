import os
import sys
import subprocess

def generate_image(panfig_block, path):
  with open(path, 'wb') as f:
    p = subprocess.Popen(['dot', '-Tpng'], stdin=subprocess.PIPE, stdout=f)
    p.communicate(('digraph G {'+panfig_block.content+'}').encode())
