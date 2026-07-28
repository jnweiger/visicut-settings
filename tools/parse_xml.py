#! /usr/bin/python
#
# parse_xml.py - read the visicut settings tree of XML files
#


import os, sys, json

LIB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
sys.path.insert(0, LIB_DIR)

import visicut_xml


if __name__ == "__main__":
  settings_dir = os.environ.get("HOME", '/') + "/.visicut"

  if len(sys.argv) > 1:
    settings_dir = sys.argv[1]
  print(json.dumps(visicut_xml.collect_profiles(settings_dir)))
