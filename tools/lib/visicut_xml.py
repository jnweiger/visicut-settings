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
    d[t]['md5sum'] = hashlib.file_digest(open(p, 'rb'), "md5").hexdigest()
    r[d[t]['name']] = { decode_xml_name(k): v for k, v in d[t].items() }
  return r


def collect_devices(dir):
  pdir = pathlib.Path(dir + "/devices")
  r = {}
  for  p in pdir.glob("*.xml"):
    try:
      d = xmltodict.parse(open(p, 'rb'), xml_attribs=True)    # we want the class attribute
    except Exception as e:
      raise ValueError(f"{p} faild to parse XML: {e}") from None
    # d = { "laserDevice": { "originBottomLeft": "false", "jobSentText": "...", "laserCutter": {
    #                       "@class": "de.thomas_oster.liblasercut.drivers.Ruida", "baudRate": "921600", "comport": "auto", ... }, "cameraTiming": "0", "projectorTiming": "0", "name": ... } }
    d = list(d.values())[0]
    if 'laserCutter' in d:
      d['laserCutter'] = { decode_xml_name(k): v for k, v in d['laserCutter'].items() }
    r[d['name']] = { decode_xml_name(k): v for k, v in d.items() }
    r[d['name']]['md5sum'] = hashlib.file_digest(open(p, 'rb'), "md5").hexdigest()
  return r


def collect_laserprofiles(dir, gen_file=None):
  # This is the main xml reader entry point. It also calls collect_materials, collect_devices, collect_profiles;
  # and augments the data with attributes found in annotations.json
  #
  # The visicut xml structure has no freetext field for comments in laserprofiles, but
  # description exisits for devices and profiles, but wiki comments correspond to laserprofile descriptions
  m = collect_materials(dir)
  pdir = pathlib.Path(dir + "/laserprofiles")
  anno_file = pdir.joinpath("annotations.json")
  if not gen_file:
    gen_file = pdir.joinpath("generator.json")  # CAUTION: keep in sync with vcsetman.py: command "rename"
  else:
    gen_file = pathlib.Path(gen_file)   # convert string to Path() object.
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
    a = [decode_xml_name(a) for a in str(rpath).split("/")]
    a = [decode_xml_name(a) for a in str(rpath).split("/")]
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

  return { 'materials': m, 'profiles': p, 'devices': l, 'generator': generator, 'encode_pathname': encode_xml_name }


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
    return xml, lp['annotation']
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
    elif      v  is None:     a[k] = ''
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
  piscut = None
  if not ptype: # try to guess from name
    if 'eng' in pname.lower():
      if '3d' in pname.lower() or '3 d' in pname.lower():
        ptype = 'raster3dProfile'
      else:
        ptype = 'rasterProfile'
      piscut = False
    elif 'cut' in pname.lower():
      ptype = 'vectorProfile'
      piscut = True
    elif 'mark' in pname.lower():
      ptype = 'vectorProfile'
      piscut = False
    else:
      raise ValueError(f"fmt_profile_xml({pname}, p) -> 'type' missing and guessing failed.")

  if ptype == 'rasterProfile':
    template = template_raster
  elif ptype == 'raster3dProfile':
    template = template_raster3d
  elif ptype != 'vectorProfile':
    raise ValueError(f"fmt_profile_xml({pname}, unknown type='{ptype}'")

  return template.format_map(xml_escape_values(p, { "name": pname, "DPI": 500.0, "description": "", "orderStrategy": "INNER_FIRST", "useOutline": False, "isCut": piscut, "width": 0.2, "invertColors": False, "colorShift": 0.0, "ditherAlgorithm": { "progress": "0", "class": "de.thomas_oster.liblasercut.dithering.FloydSteinberg" } }))


def _guess_device_class(line):
  # "Zing"
  # "Thunderlaser Nova 35"
  h = line.lower()
  if "epilog" in h or "zing" in h:
    return "de.thomas_oster.liblasercut.drivers.EpilogZing"
  if "thunder" in h or "nova" in h or "ruida" in h:
    return "de.thomas_oster.liblasercut.drivers.Ruida"


def fmt_device_xml(name, d):
  template = """<?xml version="1.0" encoding="UTF-8"?>

<laserDevice version="{version}">
  <originBottomLeft>{originBottomLeft}</originBottomLeft>
  <jobSentText>{jobSentText}</jobSentText>
  <jobPrefix>{jobPrefix}</jobPrefix>
  <laserCutter class="{laserCutter[class]}">
    <hostname>{laserCutter[hostname]}</hostname>
    <port>{laserCutter[port]}</port>
    <autofocus>{laserCutter[autofocus]}</autofocus>
    <hideSoftwareFocus>{laserCutter[hideSoftwareFocus]}</hideSoftwareFocus>
    <bedWidth>{laserCutter[bedWidth]}</bedWidth>
    <bedHeight>{laserCutter[bedHeight]}</bedHeight>
  </laserCutter>
  <cameraTiming>{cameraTiming}</cameraTiming>
  <projectorTiming>{projectorTiming}</projectorTiming>
  <projectorWidth>{projectorWidth}</projectorWidth>
  <projectorHeight>{projectorHeight}</projectorHeight>
  <thumbnailPath>{thumbnailPath}</thumbnailPath>
  <description>{description}</description>
  <name>{name}</name>
</laserDevice>
"""
  template_ruida = """<?xml version="1.0" encoding="UTF-8"?>

<laserDevice version="{version}">
  <originBottomLeft>{originBottomLeft}</originBottomLeft>
  <jobSentText>{jobSentText}</jobSentText>
  <jobPrefix>{jobPrefix}</jobPrefix>
  <laserCutter class="{laserCutter[class]}">
    <baudRate>{laserCutter[baudRate]}</baudRate>
    <host>{laserCutter[host]}</host>
    <comport>{laserCutter[comport]}</comport>
    <bedWidth>{laserCutter[bedWidth]}</bedWidth>
    <bedHeight>{laserCutter[bedHeight]}</bedHeight>
    <LaserPowerMin>{laserCutter[LaserPowerMin]}</LaserPowerMin>
    <LaserPowerMax>{laserCutter[LaserPowerMax]}</LaserPowerMax>
    <MaxVectorCutSpeed>{laserCutter[MaxVectorCutSpeed]}</MaxVectorCutSpeed>
    <MaxVectorMoveSpeed>{laserCutter[MaxVectorMoveSpeed]}</MaxVectorMoveSpeed>
    <serialTimeout>{laserCutter[serialTimeout]}</serialTimeout>
    <exportPath>{laserCutter[exportPath]}</exportPath>
    <uploadMethod>{laserCutter[uploadMethod]}</uploadMethod>
  </laserCutter>
  <cameraTiming>{cameraTiming}</cameraTiming>
  <projectorTiming>{projectorTiming}</projectorTiming>
  <projectorWidth>{projectorWidth}</projectorWidth>
  <projectorHeight>{projectorHeight}</projectorHeight>
  <thumbnailPath>{thumbnailPath}</thumbnailPath>
  <description>{description}</description>
  <name>{name}</name>
</laserDevice>
"""

  default_port = 515
  cl = d.get("laserCutter", {}).get("class", None)
  if not cl:
    cl = _guess_device_class(name)
  if "Ruida" in cl:
    template = template_ruida

  if not cl:
    raise ValueError(f"fmt_device_xml({name}) not implemented. We can do EpilogZing and Ruida")

  print(d, xml_escape_values(d, { "version": "0", "originBottomLeft": "false", "jobSentText": "$jobname -> $name", "jobPrefix": "visicut ", "laserCutter": {"class": cl, "baudRate": "921600", "host": "", "hostname": "", "port": "515", "comport": "auto", "autofocus": "false", "hideSoftwareFocus": "true", "bedWidth": "400", "bedHeight": "300", "LaserPowerMin": "0", "LaserPowerMax": "100", "MaxVectorMoveSpeed": "1000", "MaxVectorCutSpeed": "1000", "serialTimeout": "15000", "exportPath": "", "uploadMethod": "IP"}, "cameraTiming": "0", "projectorTiming": "0", "projectorWidth": "0", "projectorHeight": "0", "thumbnailPath": f"{name}.png", "description": "", "name": name }))
  return template.format_map(xml_escape_values(d, { "version": "0", "originBottomLeft": "false", "jobSentText": "$jobname -> $name", "jobPrefix": "visicut ", "laserCutter": {"class": cl, "baudRate": "921600", "host": "", "hostname": "", "port": "515", "comport": "auto", "autofocus": "false", "hideSoftwareFocus": "true", "bedWidth": "400", "bedHeight": "300", "LaserPowerMin": "0", "LaserPowerMax": "100", "MaxVectorMoveSpeed": "1000", "MaxVectorCutSpeed": "1000", "serialTimeout": "15000", "exportPath": "", "uploadMethod": "IP"}, "cameraTiming": "0", "projectorTiming": "0", "projectorWidth": "0", "projectorHeight": "0", "thumbnailPath": f"{name}.png", "description": "", "name": name }))


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
  """
  write_xml compares md5sums like this:
   - the md5sum stored in mpd with the data is compared to the md5sum of the freshly formatted xml.
   - if they match, the file is not written (unless it is physically missing). If they don't, the file is overwritten.
   - CAUTION: this does not compare md5sum of what is actually on disk in the output directory.

  CAUTION: when the import command calls write_xml() it is effectively a "merge -O"
  """
  stats = { "same": 0, "added": 0, "changed": 0 }

  ## write "materials/*.xml"
  print(f"... writing={not noop} to {dir}/materials/*.xml ...", file=sys.stderr)

  for name, mat in mpd['materials'].items():
    mat_xml = fmt_material_xml(name, mat)
    md5 = hashlib.md5(mat_xml.encode("utf-8")).hexdigest()
    filename = f"{dir}/materials/{mpd["encode_pathname"](name)}.xml"
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
  print(f"... writing={not noop} to {dir}/laserprofiles/**.xml ...", file=sys.stderr)
  anno = {}
  for n,m in mpd['materials'].items():
    for d in m['profiles']:
      for p in m['profiles'][d]:
        for t in m['profiles'][d][p]:
          print(n,d,p,t, m['profiles'][d][p][t], file=sys.stderr)
          name = f"{mpd["encode_pathname"](d)}/{mpd["encode_pathname"](n)}/{t}mm/{mpd["encode_pathname"](p)}.xml"
          lp = m['profiles'][d][p][t]
          lp_xml, lp_anno = fmt_laserprofile_xml(lp)
          if lp_anno:
            anno[name] = lp_anno
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
              print(f"written={not noop} new: {filename}",  file=sys.stderr)
              stats['added'] += 1
            elif md5 != lp['md5sum']:
              print(f"written={not noop} changed: {filename}", md5, lp['md5sum'], file=sys.stderr)
              stats['changed'] += 1
            else:
              print(f"writtem={not noop} unchanged: {filename}", file=sys.stderr)
              stats['same'] += 1

          else:
            print(f"unchanged: {filename}", file=sys.stderr)
            stats['same'] += 1

  ## write "profiles/*.xml
  for name, pro in mpd['profiles'].items():
    pro_xml = fmt_profile_xml(name, pro)
    md5 = hashlib.md5(pro_xml.encode("utf-8")).hexdigest()
    filename = f"{dir}/profiles/{mpd["encode_pathname"](name)}.xml"
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
        print(f"written={not noop} new: {filename}", file=sys.stderr)
        stats['added'] += 1
      elif md5 != pro['md5sum']:
        print(f"written={not noop} changed: {filename}", file=sys.stderr)
        stats['changed'] += 1
      else:
        print(f"written={not noop} unchanged: {filename}", file=sys.stderr)
        stats['same'] += 1

    else:
      print(f"unchanged: {filename}", file=sys.stderr)
      stats['same'] += 1


  ## write "laserprofiles/annotations.json"
  print(f"... writing={not noop} {dir}/laserprofiles/annotations.json ...", file=sys.stderr)
  filename = f"{dir}/laserprofiles/annotations.json"
  if os.path.exists(filename):
    old_anno = json.load(open(filename))
    if old_anno == anno:        # dict comparion is recursive, nice.
      print(f"unchanged: {filename}", file=sys.stderr)
      stats['same'] += 1
    else:
      anno = old_anno | anno        # that is a dict merge (second dict wins on collisions) in Python 3.9+

      if not noop:
        if os.path.exists(filename) and orig_suffix:
          os.rename(filename, filename+orig_suffix)
        with open(filename, "wb") as f:
          f.write(json.dumps(anno, indent=2).encode('utf-8'))
      print(f"changed: {filename}", file=sys.stderr)
      stats['changed'] += 1
  else:
    if not noop:
      if os.path.exists(filename) and orig_suffix:
        os.rename(filename, filename+orig_suffix)
      with open(filename, "wb") as f:
        f.write(json.dumps(anno, indent=2).encode('utf-8'))
    print(f"written={not noop} new: {filename}", file=sys.stderr)
    stats['added'] += 1


  ## write "devices/*.xml"
  for name, las in mpd['devices'].items():
    las_xml = fmt_device_xml(name, las)
    md5 = hashlib.md5(las_xml.encode("utf-8")).hexdigest()
    filename = f"{dir}/devices/{mpd["encode_pathname"](name)}.xml"
    missing = not os.path.exists(filename)
    if not 'md5sum' in las or md5 != las['md5sum'] or missing:
      if not noop:
        print(json.dumps({'filename': filename }))
        _mkdir_pf(filename)
        if os.path.exists(filename) and orig_suffix:
          os.rename(filename, filename+orig_suffix)
        with open(filename, "wb") as f:
          f.write(las_xml.encode("utf-8"))

      if not 'md5sum' in pro:
        print(f"written={not noop} new: {filename}", file=sys.stderr)
        stats['added'] += 1
      elif md5 != las['md5sum']:
        print(f"written={not noop} changed: {filename}", file=sys.stderr)
        stats['changed'] += 1
      else:
        print(f"written={not noop} unchanged: {filename}", file=sys.stderr)
        stats['same'] += 1

    else:
      print(f"unchanged: {filename}", file=sys.stderr)
      stats['same'] += 1

  return stats

