#! /usr/bin/python
#
# parse_md_table.py - read a raw wiki page, and find tables.
#
# Use with
# https://wiki.fablab-nuernberg.de/w/Nova_35?action=raw

import sys, json
import html, re


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
      cols = []
      for col in line[1:].split("||"):
        if "|" in col:
          col = col[col.index('|')+1:]  # skip cell attributes like e.g. style="..." | 
        cols.append(html.unescape(col.strip()))     # strip whitespace at both ends and interpolate html sequences like &#124;

      if newline == True or len(tr) == 0:
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
      cols = []
      for col in line[1:].split("!!"):
        if "|" in col:
          col = col[col.index('|')+1:]              # skip cell attributes like e.g. style="..." | 
        cols.append(html.unescape(col.strip()))     # strip whitespace at both ends and interpolate html sequences like &#124;
      if newline == True or len(th) == 0:
        th.append(cols)
      else:
        # no newline seen. Merge with previous table row
        # print(line, cols, len(th))
        # print(th[-1])
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


def _guess_profile(line):
  # "== Abmessungen =="
  # "==== Schneiden: CUT - (\"Rote Linie\") ===="
  # "==== Markieren: MARK - (\"Grüne Linie\") ===="
  # "==== Gravieren: ENGRAVE - (\"Schwarze Fläche\") ===="
  h = line.lower()
  p = None
  if "cut" in h or "schneid" in h:
    p = "cut"
  elif "mark" in h:
    p = "mark"
  elif "grav" in h:
    p = "engrave"
  return p


def _find_cols_by_name(ths, name=""):
  # ths = [ [ "Material", "min power", "power", "speed", "frequency", "Bemerkung" ], ... ]
  cmap = { "material": -1, "thickness": -1, "min_power": -1, "power": -1, "speed": -1, "frequency": -1, "comment": -1 }
  if type(ths[0]) == type(""):
    ths = [ ths ]
  for th in ths:
    for i in range(len(th)):
      name = th[i].lower()
      if "power" in name and "min" in name:
        cmap['min_power'] = i
      elif "power" in name:
        cmap['power'] = i
      elif "thick" in name or "dick" in name or "stärke" in name:
        cmap['power'] = i
      elif "mat" in name:   # not "Materialstärke"
        cmap['material'] = i
      elif "speed" in name or "geschwind" in name:
        cmap['speed'] = i
      elif "freq" in name:
        cmap['frequency'] = i
      elif "merkung" in name or "beschreib" in name or "omment" in name or "not" in name:
        cmap['comment'] = i

  # material, power, speed are mandatory.
  # thickness, min_power, frequency, comment are optional.
  if cmap['material'] < 0 or cmap['power'] < 0 or cmap['speed'] < 0:
    raise ValueError(f"_find_cols_by_name: mandatory columns material, power, speed not found in table {name} th={ths}")
  return cmap


def import_from_tables(table_list, laser, source=""):
  mat = {}
  pro = {}
  dev = { laser: { "version":0, "name": laser} }
  notes = []

  def sort_float_like(s):
    try:
      return (0, float(s))
    except ValueError:
      return (1, s)

  for t in table_list:
    pdesc = t.get("heading", "")
    p = _guess_profile(pdesc)
    if not p:
      continue
    if not p in pro:
      ## we don't know much about this profile. we just have a name and the title, which we use as description. ...
      if source: pdesc += f" ({source})"
      pro[p] = { 'description': pdesc }
    cmap = _find_cols_by_name(t['th'])
    notes.append([p, cmap])
    for r in t['tr']:
      thick = None
      m = r[cmap['material']]
      if cmap['thickness'] < 0 or r[cmap['thickness']] == "":
        # try parse thickness from material name name = "Baumwollstoff 0.5mm"
        match = re.search(r"\s*([\d\.,]+)\s*mm\s*$", m)
        if match:
          m = m[:match.start()]                   # 'Baumwollstoff'
          thick = match.groups()[0].replace(",", ".")   # '0.5'
      else:
        thick = r[cmap['thickness']]

      # now we have laser_name laser, material m, profile p, thickness thick. That is sufficient to construct a nested laser profile
      if thick is None:
        if p == 'cut':
          raise ValueError(f"ERROR: cut setting found without thickness: {r} in {source}")
        else:
          thick = '3.0'
          notes.append(f"{p}: {r} from {source} has no thickness. Using {thick}")

      if not m in mat:
        mat[m] = { 'name': m, 'thicknesses': [], 'profiles': {} }
      if not laser in mat[m]['profiles']:
        mat[m]['profiles'][laser] = {}

      lp = mat[m]['profiles'][laser]
      if not p in lp:
        lp[p] = {}
      if thick in lp[p]:
        notes.append(f"duplicate thickness {thick} in {r} material={m}, profile={p}, device={laser} from source {source}: previous entry overwritten.")
      anno = {}
      if len(source):
        anno['source'] = source
      if cmap['comment'] >= 0 and r[cmap['comment']] != "":
        anno['description'] =     r[cmap['comment']]
      lp[p][thick] = { 'power': r[cmap['power']], 'speed': r[cmap['speed']], 'annotation': anno }

      if cmap['min_power'] >= 0 and r[cmap['min_power']] != "":
        lp[p][thick]['min_power'] = r[cmap['min_power']]
      if cmap['frequency'] >= 0 and r[cmap['frequency']] != "":
        lp[p][thick]['frequency'] = r[cmap['frequency']]

      if not thick in mat[m]['thicknesses']:
        mat[m]['thicknesses'] = sorted(mat[m]['thicknesses'] + [ thick ], key=sort_float_like)     # keep thicknesses list up to date

  return { 'materials': mat, 'profiles': pro, 'devices': dev, "debug": notes }



if __name__ == "__main__":
  with open(sys.argv[1], "r") as fd:
    table_list = list_tables(fd)
  print(json.dumps(table_list))
