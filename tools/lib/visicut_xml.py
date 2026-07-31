#! /usr/bin/python3
#
# visicut_xml.py - read the visicut settings tree of XML files
#
# (C) 2026, juergen@fabmail.org


import sys, pathlib, json, re, xmltodict
import datetime, hashlib
import xml.sax.saxutils as sax


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


def collect_profile_details(dir):
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


def collect_profiles(dir):
  # This augments the data with attributes found in annotations.json
  # the visicut xml structure has no freetext field for comments here.
  # (description exisits for devices and profiles, but wiki comments correspond to laserprofile descriptions
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

  p = collect_profile_details(dir)
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


def create_laserprofile(mpd, material_name, device_name, profile_name, thickness, print_prefix=""):
  print(f"{print_prefix}clp({material_name}, {device_name}, {profile_name}, {thickness})")
  # plist = used_laser_profiles(mpd, material_name, device_name)
  # if plist:
  #   print(f"clp have plist:", plist)
  #   # raise "create_laserprofile with plist not impl."
  if not "generator" in mpd or not mpd['generator']:
    raise f"{print_prefix}create_laserprofile cannot create profile without generator."
  dlist = mpd['generator'][device_name]
  for i in range(len(dlist)):
    d = dlist[i]
    # Material    Profile     Thickness   { ...data... }
    # [ "holz",   "cut",          "3.0",  { "speed": 33, "power": 34 } ]
    # [ 'holz',   'mark|eng',     '',     {'speed': 99, 'power': 34}]
    if re.search(d[0], material_name, re.IGNORECASE) and \
       re.search(d[1], profile_name,  re.IGNORECASE) and \
       re.search(d[2], str(thickness),     re.IGNORECASE):
      print(f"{print_prefix}generator.{device_name}.{i}: match", d)
      r = d[3].copy()
      date = datetime.datetime.now().strftime("%Y%m%d")

      r['annotations'] = { "source": f"generator.{device_name}.{i}", "description": "gen "+date }
      return r;
  print(f"{print_prefix}{device_name}: no matching default: ", [[d[0], d[1], d[2]] for d in dlist])
  raise "{print_prefix}create_laserprofile not impl."


def check_profiles(mpd, autofix=True):
  # mpd = { 'materials': m, 'profiles': p, 'devices': l } as generated with collect_profiles

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
            r.append(f"create_laserprofile(mpd, '{n}', '{d}', '{p}', '{t}')")
            if autofix:
              m['profiles'][d][p][t] = create_laserprofile(mpd, n, d, p, t, f"{fixcounter}: ")

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


def write_xml(mpd, dir, noop=False, orig_suffix=""):
  stats = { "same": 0, "added": 0, "changed": 0 }

  ## write "materials/*.xml"
  for name, mat in mpd['materials'].items():
    mat_xml = fmt_material_xml(name, mat)
    md5 = hashlib.md5(mat_xml.encode("utf-8")).hexdigest()
    if not 'md5sum' in mat or md5 != mat['md5sum']:

      if not noop:
        filename = f"{dir}/materials/{encode_xml_name(name)}.xml"
        if os.path.exists(filename) and orig_suffix:
          os.rename(filename, filename+orig_suffix)
        with open(filename, "wb") as f:
          f.write(mat_xml.encode("utf-8"))

      if not 'md5sum' in mat:
        print(f"new: material {name} ==============================\n", mat_xml)
        stats['added'] += 1
      else:
        print(f"\nchanged: material {name} ==============================\n", mat_xml)
        stats['changed'] += 1

    else:
      # print("\nmd5sum unchanged:", name)
      stats['same'] += 1

  ## write "laserprofiles/**.xml" (and collect annotations)
  anno = {}
  for n,m in mpd['materials'].items():
    for d in m['profiles']:
      for p in m['profiles'][d]:
        for t in m['profiles'][d][p]:
          print(n,d,p,t, m['profiles'][d][p][t])
          name = f"laserprofiles/{encode_xml_name(d)}/{encode_xml_name(n)}/{t}mm/{encode_xml_name(p)}.xml"
          lp = m['profiles'][d][p][t]
          lp_xml, anno[name] = fmt_laserprofile_xml(lp)
          # print(name, lp_xml, anno[name])
          md5 = hashlib.md5(lp_xml.encode("utf-8")).hexdigest()
          if not 'md5sum' in lp or md5 != lp['md5sum']:

            if not noop:
              filename = f"{dir}/{name}"
              if os.path.exists(filename) and orig_suffix:
                os.rename(filename, filename+orig_suffix)
              with open(filename, "wb") as f:
                f.write(lp_xml.encode("utf-8"))

            if not 'md5sum' in lp:
              print(f"new: {name} ==============================\n", lp_xml)
              stats['added'] += 1
            else:
              print(f"\nchanged: {name} ==============================\n", lp_xml, md5, lp['md5sum'])
              stats['changed'] += 1

          else:
            # print("\nmd5sum unchanged:", name)
            stats['same'] += 1

  ## write "annotations.json"

  print("write_xml: unfinsihed code.", file=sys.stderr)
  return stats

