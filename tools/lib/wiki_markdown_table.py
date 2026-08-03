#! /usr/bin/python
#
# parse_md_table.py - read a raw wiki page, and find tables.
#
# Use with
# https://wiki.fablab-nuernberg.de/w/Nova_35?action=raw

import sys, json


def collect_tables(fd):
  r = []
  lastheading = None
  lineno = 0
  intable = False

  # FIXME: do we need .decode("utf-8") here?
  for line in fd.readlines():
    if type(line) != type(""):
      line = line.decode("utf-8")   # urlopen() brings us str
    line = line.strip()
    lineno = lineno + 1
    if line.startswith('=') and line.endswith('='):
      lastheading = line

    if line.startswith('{| class="wikitable"'):
      r.append({ "heading": lastheading, "lineno": lineno, "md_lines": [ ]})
      intable = True

    if intable:
      r[-1]["md_lines"].append(line)

    if line.startswith('|}'):
      intable = False

  return r


def mdlines2lists(mdlines):
  th = []
  tr = []
  # "{| class=\"wikitable\"",
  # "|-",
  # "! Material !! min power !! power !! speed !! frequency !! Bemerkung",
  # "|-",
  # "| Acryl 2mm || 45 || 70 || 4 || 500 || jw 20211204 fln",
  # "|-",
  # "|}",
  newline = False
  for line in mdlines:
    if line.startswith("{|") or line.startswith("|}"):
      continue

    if line == '|-':
      # print("newline seen")
      newline = True
      continue

    if line[0] == '|':
      # print("tr: " + line)
      cols = [col.strip() for col in line[1:].split("||")]
      if newline == True:
        tr.append(cols)
      else:
        # no newline seen. Merge with previos table row
        for i in range(len(cols)):
          if i >= len(tr[-1]):
            tr[-1].append("")
          # print(tr, i)
          tr[-1][i] = tr[-1][i] + "\n" + cols[i]
      newline = False

    if line[0] == '!':
      # print("th: " + line)
      cols = [col.strip() for col in line[1:].split("!!")]
      if newline == True:
        th.append(cols)
      else:
        # no newline seen. Merge with previos table row
        for i in range(len(cols)):
          if i > len(th[-1]):
            th[-1].append("")
          th[-1][i] = th[-1][i] + "\n" + cols[i]
      newline = False

  return(tr,th)


def list_tables(fd):
  table_list = collect_tables(fd)

  for table in table_list:
    tr, th = mdlines2lists(table['md_lines'])
    table['tr'] = tr
    table['th'] = th
    del(table['md_lines'])

  return table_list


if __name__ == "__main__":
  with open(sys.argv[1], "r") as fd:
    table_list = list_tables(fd)
  print(json.dumps(table_list))
