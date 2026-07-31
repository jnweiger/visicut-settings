#! /usr/bin/python
#
# vcsetman.py - manage visicut settings, native XML data and Wiki tables
#
# (C) 2026, juergen@fabmail.org


import os, sys, json

LIB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
sys.path.insert(0, LIB_DIR)

from visicut_xml import *
from wiki_markdown_table import *


if __name__ == "__main__":
  settings_dir = os.environ.get("HOME", '/') + "/.visicut"

  dowrite=True
  autofix=True
  if len(sys.argv) > 1:
    settings_dir = sys.argv[1]
  mpd = collect_profiles(settings_dir)
  if dowrite:
    stats = write_xml(mpd, settings_dir, noop=True)
    if stats['changed'] > 0:
      print("ERROR: write_xml disabled: would prodce changes on unchanged data: ", stats, file=sys.stderr)
      sys.exit(0)

  # print(json.dumps(mpd))
  print(stats)
  sys.exit(0)

  print(json.dumps(check_profiles(mpd, autofix=autofix)))
  remainder = check_profiles(mpd, autofix=False)
  if autofix and remainder:
    print("ERROR: check_profiles with autofix=True failed to fix: ", rest)
  stats = write_xml(mpd, "/tmp/visicut", noop=True, orig_suffix=".orig")

