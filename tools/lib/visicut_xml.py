#! /usr/bin/python3
#
# visicut_xml.py - read the visicut settings tree of XML files
#
# (C) 2026, juergen@fabmail.org


import os, sys, pathlib, json, re, xmltodict
import datetime, hashlib
import xml.sax.saxutils as sax
from copy import deepcopy


def collect_materials(dir):
  # returns a dict of materials, entries look like this:
  # {
  #   "Sperrholz Linde": { "engraveColor": "#000000", "cutColor": "#ff0000", "color": "#fff0b4", "name": "Sperrholz Linde",
  #                        "thicknesses": [ 3.0, 4.0, 5.0, 6.0, 8.0 ] }
  #   ...
  # }
  mdir = pathlib.Path(dir + "/materials")
  r = {}
  for m in mdir.glob("*.xml"):
    d = xmltodict.parse(open(m, 'rb'), xml_attribs=False, force_list=('float',))
    d = d['material']
    d['thicknesses'] = [float(t) for t in d['materialThicknesses']['float']]
    del(d['materialThicknesses'])
    d['md5sum'] = hashlib.file_digest(open(m, 'rb'), "md5").hexdigest()
    r[d['name']] = d
  return r


# CAUTION. Do not use. This looks nice, but spoils md5sums on fmt_laserprofile_xml, fmt_material_xml.
def _maybe_float_or_bool(v):
  try:
    return float(v)
  except (ValueError, TypeError):
    try:
      if v.lower() == 'true':
        return True
      if v.lower() == 'false':
        return False
      return v  # other string
    except (AttributeError, ValueError, TypeError):
      # ... a dict ...
      if type(v) == type({}):   # hackety
        if '@class' in v:
          v['class'] = v['@class']
          del(v['@class'])
      return v


def decode_xml_name(str):
  # "B_252_ttenpapier Arches 300g", "min__power", "Thunderlaser_32_Nova_32_35"

  def replace_umlaut(m):
    code = int(m.group(1))
    return chr(code)

  if str[0] == '@':
    str = str[1:]   # undo the attribute marking (@version, @class, ...)
  str = re.sub(r'_(\d+)_', replace_umlaut, str)
  str = str.replace("__", "_")
  return str


def encode_xml_name(str):
  return re.sub(r'[^A-Za-z0-9-]', lambda m: f"_{ord(m.group(0))}_", str)


def collect_profiles(dir):
  pdir = pathlib.Path(dir + "/profiles")
  r = {}
  for p in pdir.glob("*.xml"):
    d = xmltodict.parse(open(p, 'rb'), xml_attribs=True)    # we want the class attribute
    # d = { 'vectorProfile': {'DPI': '500.0', 'description': 'rote linie nearest neigbour', 'name': 'cut-nn', 'orderStrategy': 'NEAREST', 'useOutline': 'false', 'isCut': 'true', 'width': '0.2'}}}
    t = list(d.keys())[0]
    d[t]['type'] = t
    r[d[t]['name']] = { decode_xml_name(k): v for k, v in d[t].items() }
  return r


def collect_devices(dir):
  pdir = pathlib.Path(dir + "/devices")
  r = {}
  for p in pdir.glob("*.xml"):
    d = xmltodict.parse(open(p, 'rb'), xml_attribs=True)    # we want the class attribute
    # d = { "laserDevice": { "originBottomLeft": "false", "jobSentText": "...", "laserCutter": {
    #                       "@class": "de.thomas_oster.liblasercut.drivers.Ruida", "baudRate": "921600", "comport": "auto", ... }, "cameraTiming": "0", "projectorTiming": "0", "name": ... } }
    d = list(d.values())[0]
    if 'laserCutter' in d:
      d['laserCutter'] = { decode_xml_name(k): v for k, v in d['laserCutter'].items() }
    r[d['name']] = { decode_xml_name(k): v for k, v in d.items() }
  return r


def collect_laserprofiles(dir):
  # This is the main xml reader entry point. It also calls collect_materials, collect_devices, collect_profiles;
  # and augments the data with attributes found in annotations.json
  #
  # The visicut xml structure has no freetext field for comments in laserprofiles, but
  # description exisits for devices and profiles, but wiki comments correspond to laserprofile descriptions
  m = collect_materials(dir)
  pdir = pathlib.Path(dir + "/laserprofiles")
  anno_file = pdir.joinpath("annotations.json")
  gen_file = pdir.joinpath("generator.json")
  anno = {}
  if anno_file.is_file():
    anno = json.load(open(anno_file))
  # {'Zing/Kiefernbrettchen/5.0mm/cut.xml': {'description': 'gen 20260729', 'source': '../4.0mm/cut.xml via /tool/vcprofman.py'}}

  generator = {}
  if gen_file.is_file():
    generator = json.load(open(gen_file))
  # {'Zing/Kiefernbrettchen/5.0mm/cut.xml': {'description': 'gen 20260729', 'source': '../4.0mm/cut.xml via /tool/vcprofman.py'}}

  for p in pdir.rglob("*.xml"):
    d = xmltodict.parse(open(p, 'rb'), xml_attribs=False)
    # {'linked-list': {'com.t__oster.liblasercut.properties.FloatMinMaxPowerSpeedFrequencyProperty':
    #  {'power': '70.0', 'speed': '0.5', 'frequency': '500', 'min__power': '70.0'}}}
    d = list(list(d.values())[0].values())[0]
    # {'power': '70.0', 'speed': '0.5', 'frequency': '500', 'min__power': '70.0'}
    rpath = p.relative_to(pdir)
    # rpath = "Thunderlaser_32_Nova_32_35/Sperrholz_32_Kiefer/4.0mm/cut.xml"
    a = decode_xml_name(str(rpath)).split("/")
    # a = ['Thunderlaser Nova 35', 'Sperrholz Kiefer', '4.0mm', 'cut.xml']
    lp = { 'device': a[0], 'material': a[1], 'thickness': float(a[2].replace("mm", "")), 'profile': a[3].replace(".xml", "") }
    # reduce double __ to _ in names, and convert values to float
    lp["data"] = { decode_xml_name(k): v for k, v in d.items() }
    # {'device': 'Zing', 'material': 'Kraftplex', 'thickness': 1.0, 'profile': 'mark', 'data': {'power': 30.0, 'speed': 100.0, 'focus': 0.0, 'hideFocus': True, 'frequency': 2000.0}}
    # {'device': 'Thunderlaser Nova 35', 'material': 'Eiche Hirnholz', 'thickness': 5.0, 'profile': 'engrave-fs-200-neg', 'data': {'power': 100.0, 'speed': 66.0, 'frequency': 500.0, 'min_power': 10.0}}
    lp["data"]["md5sum"] = hashlib.file_digest(open(p, 'rb'), "md5").hexdigest()
    if str(rpath) in anno:
        lp["data"]["annotation"] = anno[str(rpath)]

    if not lp['material'] in m:
      m[lp['material']] = {}
    mlp = m[lp['material']]
    if not 'profiles' in mlp:
      mlp['profiles'] = {}
    if not lp['device'] in mlp['profiles']:
      mlp['profiles'][lp['device']] = {}
    if not lp['profile'] in mlp['profiles'][lp['device']]:
      mlp['profiles'][lp['device']][lp['profile']] = {}
    mlp['profiles'][lp['device']][lp['profile']][lp['thickness']] = lp['data']

  p = collect_profiles(dir)
  l = collect_devices(dir)

  return { 'materials': m, 'profiles': p, 'devices': l, 'generator': generator }


# Express the new path n as relative path coming from base b
# If paths are identical, return "./cut.xml"
# If one level up reaches inside b, return "../4.0mm/cut.xml"
# Similar to os.path.replpath(), but we
#  - treat the last component nicely as file, unless the path ends with "/"
#  - don't create long ../ chains, when there is no match. We simply return the full new path.
def frelpath(n, b):
  count = 0
  s = len(n)
  while True:
    try:
      s = n.rindex("/", 0, s)
    except (ValueError):
      return b

    if b.startswith(n[:s] + "/"):
      pre = "../" * count
      if pre == "":
        pre = "./"
      return pre + b[len(n[:s])+1:]
    count = count + 1


def path_of_laserprofile(m, d, p, t, b=None):
  path = f"{d}/{m}/{t}mm/{p}.xml"
  path = encode_xml_name(path)
  if b:
    return frelpath(path, b)
  return path


def used_laser_profiles(mpd, m, d):
  plist = []
  try:
    tree = mpd['materials'][m]['profiles'][d]
    for p in tree:
      for t in tree[p]:
        plist.append({ 'profile': p, 'thickness': t, 'data': tree[p][t] })
  except:
     pass
  return plist


def generate_laserprofile(mpd, material_name, device_name, profile_name, thickness, print_prefix=""):
  print(f"{print_prefix}clp({material_name}, {device_name}, {profile_name}, {thickness})", file=sys.stderr)
  # plist = used_laser_profiles(mpd, material_name, device_name)
  # if plist:
  #   print(f"clp have plist:", plist)
  #   # raise "generate_laserprofile with plist not impl."
  if not "generator" in mpd or not mpd['generator']:
    raise f"{print_prefix}generate_laserprofile cannot create profile without generator."
  dlist = mpd['generator'][device_name]
  for i in range(len(dlist)):
    d = dlist[i]
    # Material    Profile     Thickness   { ...data... }
    # [ "holz",   "cut",          "3.0",  { "speed": 33, "power": 34 } ]
    # [ 'holz',   'mark|eng',     '',     {'speed': 99, 'power': 34}]
    if re.search(d[0], material_name, re.IGNORECASE) and \
       re.search(d[1], profile_name,  re.IGNORECASE) and \
       re.search(d[2], str(thickness),     re.IGNORECASE):
      print(f"{print_prefix}generator.{device_name}.{i}: match", d, file=sys.stderr)
      r = d[3].copy()
      date = datetime.datetime.now().strftime("%Y%m%d")

      r['annotations'] = { "source": f"generator.{device_name}.{i}", "description": "gen "+date }
      return r;
  print(f"{print_prefix}{device_name}: no matching default: ", [[d[0], d[1], d[2]] for d in dlist], file=sys.stderr)
  raise ValueError(f"{print_prefix}generate_laserprofile failed.")


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
    p = _guess_profile(t.get("heading", ""))
    if not p:
      continue
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

####

def check_laserprofiles(mpd, autofix=True):
  # mpd = { 'materials': m, 'profiles': p, 'devices': l } as generated with collect_laserprofiles

  r = []
  fixcounter = 0
  ### find materials that have no name. (autocreated by profiles, but xml file missing in /materials folder.)
  for n,m in mpd['materials'].items():
    if not 'name' in m:
      r.append(f"material '{n}' used in laserprofiles, but materials/{encode_xml_name(n)}.xml is missing.")
      if autofix:
        m['name'] = n
        fixcounter = fixcounter + 1
    if not 'thicknesses' in m:
      m['thicknesses'] = []

  ### check that the thicknesses listed with each material agrees with the materials profiles.devices.profile.thickness tree
  for n,m in mpd['materials'].items():
    tseen = { t: 0 for t in m['thicknesses'] }
    tmiss = {}
    # print(n, m['thicknesses'])
    for d in m['profiles']:
      for p in m['profiles'][d]:
        for t in m['profiles'][d][p]:
          if t in tseen:
            tseen[t] = tseen[t] + 1
          else:
            tmiss[t] = tmiss.get(t, 0) + 1
    # print(tseen, tmiss)
    for t, c in tseen.items():
      if c == 0:
        r.append(f"material '{n}': thickness {t} is not used in any laserprofile.")
    for t in tmiss:
      r.append(f"material '{n}': thickness {t} used in laserprofiles, but not listed in thicknesses.")
      fixcounter = fixcounter + 1
      if autofix:
        m['thicknesses'] = sorted(m['thicknesses'] + [t])

  ### devices, profiles, and thicknesses are a three-dimensional space.
  ## the thicknesses dimension is material dependant.
  ## check that all points in this space are set in each material.
  devs = list(mpd['devices'].keys())
  profs = list(mpd['profiles'].keys())
  # print(devs, profs)
  for n,m in mpd['materials'].items():
    ths = m['thicknesses']
    # print(n, ths)
    for d in devs:
      if not d in m['profiles']:
        m['profiles'][d] = {}
      for p in profs:
        if not p in m['profiles'][d]:
          m['profiles'][d][p] = {}
        for t in ths:
          if not t in m['profiles'][d][p]:
            fixcounter = fixcounter + 1
            r.append(f"generate_laserprofile(mpd, '{n}', '{d}', '{p}', '{t}')")
            if autofix:
              m['profiles'][d][p][t] = generate_laserprofile(mpd, n, d, p, t, f"{fixcounter}: ")

  return r

####

def fmt_material_xml(name, m):
  # m = {"engraveColor": "#000000", "cutColor": "#ff0000", "color": "#fff0b4", "name": "Sperrholz Kiefer", "thicknesses": [4.0], "md5sum": "75428bee39c6fef42a2f3c7b3f3c381c", ... }
  th = m.get('thicknesses', [])
  description_opt=""
  if 'description' in m:
    description_opt=f"\n  <description>{sax.escape(m['description'])}</description>"

  # Maybe we need multiple templates to support multiple visicut versions?
  template = """<?xml version="1.0" encoding="UTF-8"?>

<material version="0">{description_opt}
  <engraveColor>{engraveColor}</engraveColor>
  <cutColor>{cutColor}</cutColor>
  <color>{color}</color>
  <name>{name}</name>
  <materialThicknesses>
{thicknesses}
  </materialThicknesses>
</material>
"""
  xml = template.format(
    description_opt=description_opt,
    engraveColor=m.get('engraveColor', '#000000'),
    cutColor=m.get('cutColor', '#000000'),
    color=m.get('color', '#000000'),
    name=sax.escape(name),
    thicknesses="\n".join([f"    <float>{t}</float>" for t in th])
  )
  return xml


def fmt_laserprofile_xml(lp):
  # Kiefernbrettchen Zing cut 5.0 {'power': 100.0, 'speed': 40.0, 'focus': 0.0, 'hideFocus': True, 'frequency': 500.0, 'md5sum': 'ec873e5a7ceaba1bab0eb5ba64cf1a9c', 'annotation': {'description': 'gen 20260729', 'source': '../4.0mm/cut.xml via /tool/vcprofman.py'}}
  # Sperrholz Kiefer Thunderlaser Nova 35 cut 4.0 {'power': '80.0', 'speed': '1.2', 'frequency': '500', 'min_power': '60.0', 'md5sum': 'af480744149fe7e1f49108e6c60c7df0'}
  # Sperrholz Birke Zing engrave 3.0 {'power': '100', 'speed': '100', 'focus': '0.0', 'hideFocus': 'true', 'engraveBottomUp': 'false', 'md5sum': 'b0e8b6c85c0629060ecbda3718c1084c'}


  template_minmax = """<?xml version="1.0" encoding="UTF-8"?>

<linked-list version="0.0.0.0">
  <com.t__oster.liblasercut.properties.FloatMinMaxPowerSpeedFrequencyProperty>
    <power>{power}</power>
    <speed>{speed}</speed>
    <frequency>500</frequency>
    <min__power>{min_power}</min__power>
  </com.t__oster.liblasercut.properties.FloatMinMaxPowerSpeedFrequencyProperty>
</linked-list>
"""
  template_epilog = """<?xml version="1.0" encoding="UTF-8"?>

<linked-list version="0.0.0.0">
  <com.t__oster.liblasercut.drivers.EpilogEngraveProperty>
    <power>{power}</power>
    <speed>{speed}</speed>
    <focus>{focus}</focus>
    <hideFocus>{hideFocus}</hideFocus>
    <engraveBottomUp>{engraveBottomUp}</engraveBottomUp>
  </com.t__oster.liblasercut.drivers.EpilogEngraveProperty>
</linked-list>
"""

  template = """<?xml version="1.0" encoding="UTF-8"?>

<linked-list version="0.0.0.0">
  <PowerSpeedFocusFrequencyProperty>
    <power>{power}</power>
    <speed>{speed}</speed>
    <focus>{focus}</focus>
    <hideFocus>{hideFocus}</hideFocus>
    <frequency>{frequency}</frequency>
  </PowerSpeedFocusFrequencyProperty>
</linked-list>
"""

  if 'engraveBottomUp' in lp:
    template = template_epilog

  if 'min_power' in lp:
    template = template_minmax

  # TODO: both, engraveBottomUp and min_power??

  xml = template.format(
    power=lp['power'],
    speed=lp['speed'],
    min_power=lp.get('min_power', 0),
    frequency=lp.get('frequency', 500),
    focus=lp.get('focus', 0.0),
    hideFocus=lp.get('hideFocus', 'true'),
    engraveBottomUp=lp.get('engraveBottomUp', 'false')
  )
  if 'annotation' in lp:
    return xml, json.dumps(lp['annotation'])
  return xml, None


def _merge_defaults(obj, defaults):
  a = deepcopy(obj)
  for k,v in defaults.items():
    if not k in a:
      a[k] = deepcopy(defaults[k])
  return a


def xml_escape_values(obj, defaults={}):
  a = _merge_defaults(obj, defaults)
  for k,v in a.items():
    if   type(v) == type(""): a[k] = sax.escape(v)
    elif type(v) == type({}): a[k] = xml_escape_values(v, defaults.get(k, {}))
    elif      v  is True:     a[k] = 'true'
    elif      v  is False:    a[k] = 'false'
  return a


def fmt_profile_xml(pname, p):
  # cut, p = { "version": 0.0, "DPI": 500.0, "description": "rote Linie", "name": "cut", "orderStrategy": "INNER_FIRST", "useOutline": false, "isCut": true, "width": 0.2, "type": "vectorProfile" }
  # mark, p = { "version": 0.0, "DPI": 500.0, "description": "A new Laserprofile", "name": "mark", "orderStrategy": "NEAREST", "useOutline": false, "isCut": false, "width": 0.1, "type": "vectorProfile" },
  # eng, p = { "version": 0.0, "DPI": 500.0, "description": "A new Laserprofile", "name": "eng-fs-500", "invertColors": false, "colorShift": 0.0, "ditherAlgorithm": { "progress": "0", "class": "de.thomas_oster.liblasercut.dithering.FloydSteinberg" }, "type": "rasterProfile" }
  # eng3d, p = { "version": 0.0, "DPI": 500.0, "description": "deep engrave", "name": "engrave 3d", "invertColors": false, "colorShift": 0.0, "type": "raster3dProfile" },

  template = """<?xml version="1.0" encoding="UTF-8"?>

<vectorProfile version="0.0">
  <DPI>{DPI}</DPI>
  <description>{description}</description>
  <name>{name}</name>
  <orderStrategy>{orderStrategy}</orderStrategy>
  <useOutline>{useOutline}</useOutline>
  <isCut>{isCut}</isCut>
  <width>{width}</width>
</vectorProfile>
"""
  template_raster = """<?xml version="1.0" encoding="UTF-8"?>

<rasterProfile version="0.0">
  <DPI>{DPI}</DPI>
  <description>{description}</description>
  <name>{name}</name>
  <invertColors>{invertColors}</invertColors>
  <colorShift>{colorShift}</colorShift>
  <ditherAlgorithm class="{ditherAlgorithm[class]}">
    <progress>{ditherAlgorithm[progress]}</progress>
  </ditherAlgorithm>
</rasterProfile>
"""
  template_raster3d = """<?xml version="1.0" encoding="UTF-8"?>

<raster3dProfile version="0.0">
  <DPI>{DPI}</DPI>
  <description>{description}</description>
  <name>{name}</name>
  <invertColors>{invertColors}</invertColors>
  <colorShift>{colorShift}</colorShift>
</raster3dProfile>
"""

  ptype = p.get('type', None)
  if not ptype: # try to guess from name
    if 'eng' in name.lower():
      if '3d' in name.lower() or '3 d' in name.lower():
        ptype = 'raster3dProfile'
      else:
        ptype = 'rasterProfile'
    elif 'cut' in name.lower() or 'mark' in name.lower():
      ptype = 'vectorProfile'
    else:
      raise ValueError(f"fmt_profile_xml({name}, p) -> 'type' missing and guessing failed.")

  if ptype == 'rasterProfile':
    template = template_raster
  elif ptype == 'raster3dProfile':
    template = template_raster3d
  elif ptype != 'vectorProfile':
    raise ValueError(f"fmt_profile_xml({name}, unknown type='{ptype}'")

  return template.format_map(xml_escape_values(p, { "DPI": 500.0, "description": "", "orderStrategy": "INNER_FIRST", "useOutline": False, "isCut": True, "width": 0.2, "invertColors": False, "colorShift": 0.0, "ditherAlgorithm": { "progress": "0", "class": "de.thomas_oster.liblasercut.dithering.FloydSteinberg" } }))


def _mkdir_pf(file):
  # create all the needed directory components that lead up to but not including the file itself.
  # To create a directory use _mkdir_pf(dir+"/.")
  l = file.split("/")
  for i in range(1, len(l)):
    p = "/".join(l[:i])
    if p != "":
      if not os.path.exists(p):
        os.mkdir(p)


def write_xml(mpd, dir, noop=False, orig_suffix=""):
  stats = { "same": 0, "added": 0, "changed": 0 }

  ## write "materials/*.xml"
  print(f"... writing to {dir}/materials/*.xml ...", file=sys.stderr)

  for name, mat in mpd['materials'].items():
    mat_xml = fmt_material_xml(name, mat)
    md5 = hashlib.md5(mat_xml.encode("utf-8")).hexdigest()
    filename = f"{dir}/materials/{encode_xml_name(name)}.xml"
    missing = not os.path.exists(filename)
    if not 'md5sum' in mat or md5 != mat['md5sum'] or missing:
      if not noop:
        # print(json.dumps({'filename': filename }))
        _mkdir_pf(filename)
        if os.path.exists(filename) and orig_suffix:
          os.rename(filename, filename+orig_suffix)
        with open(filename, "wb") as f:
          f.write(mat_xml.encode("utf-8"))

      if not 'md5sum' in mat:
        print(f"written new: {filename}", file=sys.stderr)
        stats['added'] += 1
      elif md5 != mat['md5sum']:
        print(f"written changed: {filename}", file=sys.stderr)
        stats['changed'] += 1
      else:
        print(f"writtem unchanged: {filename}", file=sys.stderr)
        stats['same'] += 1

    else:
      print(f"unchanged: {filename}", file=sys.stderr)
      stats['same'] += 1

  ## write "laserprofiles/**.xml" (and collect annotations)
  print(f"... writing to {dir}/laserprofiles/**.xml ...", file=sys.stderr)
  anno = {}
  for n,m in mpd['materials'].items():
    for d in m['profiles']:
      for p in m['profiles'][d]:
        for t in m['profiles'][d][p]:
          print(n,d,p,t, m['profiles'][d][p][t], file=sys.stderr)
          name = f"{encode_xml_name(d)}/{encode_xml_name(n)}/{t}mm/{encode_xml_name(p)}.xml"
          lp = m['profiles'][d][p][t]
          lp_xml, anno[name] = fmt_laserprofile_xml(lp)
          # print(name, lp_xml, anno[name])
          filename = f"{dir}/laserprofiles/{name}"
          missing = not os.path.exists(filename)
          md5 = hashlib.md5(lp_xml.encode("utf-8")).hexdigest()
          if not 'md5sum' in lp or md5 != lp['md5sum'] or missing:

            if not noop:
              _mkdir_pf(filename)
              if os.path.exists(filename) and orig_suffix:
                os.rename(filename, filename+orig_suffix)
              with open(filename, "wb") as f:
                f.write(lp_xml.encode("utf-8"))

            if not 'md5sum' in lp:
              print(f"written new: {filename}",  file=sys.stderr)
              stats['added'] += 1
            elif md5 != lp['md5sum']:
              print(f"written changed: {filename}", md5, lp['md5sum'], file=sys.stderr)
              stats['changed'] += 1
            else:
              print(f"writtem unchanged: {filename}", file=sys.stderr)
              stats['same'] += 1

          else:
            print(f"unchanged: {filename}", file=sys.stderr)
            stats['same'] += 1

  ## write "profiles/*.xml
  for name, pro in mpd['profiles'].items():
    pro_xml = fmt_profile_xml(name, pro)
    md5 = hashlib.md5(pro_xml.encode("utf-8")).hexdigest()
    filename = f"{dir}/profiles/{encode_xml_name(name)}.xml"
    missing = not os.path.exists(filename)
    if not 'md5sum' in pro or md5 != pro['md5sum'] or missing:
      if not noop:
        print(json.dumps({'filename': filename }))
        _mkdir_pf(filename)
        if os.path.exists(filename) and orig_suffix:
          os.rename(filename, filename+orig_suffix)
        with open(filename, "wb") as f:
          f.write(pro_xml.encode("utf-8"))

      if not 'md5sum' in pro:
        print(f"written new: {filename}", file=sys.stderr)
        stats['added'] += 1
      elif md5 != pro['md5sum']:
        print(f"written changed: {filename}", file=sys.stderr)
        stats['changed'] += 1
      else:
        print(f"writtem unchanged: {filename}", file=sys.stderr)
        stats['same'] += 1

    else:
      print(f"unchanged: {filename}", file=sys.stderr)
      stats['same'] += 1


  ## write "laserprofiles/annotations.json"
  print(f"TODO: ... writing {dir}/laserprofiles/annotations.json ...", file=sys.stderr)

  print("FIXME: write_xml: unfinsihed code.", file=sys.stderr)
  return stats

