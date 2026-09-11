#! /usr/bin/python3
#
# visicut_ops.py - manipulate visicut settings in internal dict format
#
# (C) 2026, juergen@fabmail.org

import sys, re, shutil
from pathlib import Path


def rename_profile(mpd, oldname, newname):
  delfiles = []     # record, which files we should delete, when writing out the data
  if newname in mpd['profiles']:
    raise ValueError(f"rename_profile('{oldname}', '{newname}') failed: profile '{newname}' already exists.")
  p = mpd['profiles'][oldname]
  p['name'] = newname
  print(p, file=sys.stderr)
  mpd['profiles'][newname] = p

  if not 'encode_pathname' in mpd:
    raise ValueError("rename_profile: no 'encode_pathname' method initialized. Cannot construct pathnames for deleting old files")
  enc_oldname = mpd['encode_pathname'](oldname)
  delfiles.append(f"profiles/{enc_oldname}.xml")

  for n,m in mpd['materials'].items():
    for d in m['profiles']:
      if oldname in m['profiles'][d]:
        for t in m['profiles'][d][oldname]:
          enc_name = f"{mpd["encode_pathname"](d)}/{mpd["encode_pathname"](n)}/{t}mm/{mpd["encode_pathname"](oldname)}.xml"
          delfiles.append(f"laserprofiles/{enc_name}")
        m['profiles'][d][newname] = m['profiles'][d][oldname]
        del(m['profiles'][d][oldname])

  return delfiles


def rename_material(mpd, oldname, newname):
  delfiles = []     # record, which files we should delete, when writing out the data
  if newname in mpd['materials']:
    raise ValueError(f"rename_material('{oldname}', '{newname}') failed: material '{newname}' already exists.")
  m = mpd['materials'][oldname]
  m['name'] = newname
  print(m, file=sys.stderr)
  mpd['materials'][newname] = m

  if not 'encode_pathname' in mpd:
    raise ValueError("rename_material: no 'encode_pathname' method initialized. Cannot construct pathnames for deleting old files")
  enc_oldname = mpd['encode_pathname'](oldname)
  delfiles.append(f"materials/{enc_oldname}.xml")
  for lasername in mpd["devices"]:
    enc_lasername = mpd['encode_pathname'](lasername)
    delfiles.append(f"laserprofiles/{enc_lasername}/{enc_oldname}")
  return delfiles


def rename_device(mpd, oldname, newname, gen_file=None):
  delfiles = []     # record, which files we should delete, when writing out the data
  if newname in mpd['devices']:
    raise ValueError(f"rename_device('{oldname}', '{newname}') failed: device {newname} already exists.")
  d = mpd['devices'][oldname]
  print(d, file=sys.stderr)
  # rename the device itself
  d['name'] = newname
  mpd['devices'][newname] = d
  del(mpd['devices'][oldname])

  # record things for delete_paths later.
  if not 'encode_pathname' in mpd:
    raise ValueError("rename_device: no 'encode_pathname' method initialized. Cannot construct pathnames for deleting old files")
  enc_oldname = mpd['encode_pathname'](oldname)
  delfiles.append(f"devices/{enc_oldname}.xml")    # a file
  delfiles.append(f"laserprofiles/{enc_oldname}")  # a subtree

  # walk throug all [materials]*[profiles] an rename keys there.
  for m in mpd['materials']:
    p = mpd['materials'][m]['profiles']
    if oldname in p:
      p[newname] = p[oldname]
      del(p[oldname])

  repl_count = None
  if gen_file:
    repl_count = replace_string_in_file(gen_file, f"\"{oldname}\"", f"\"{newname}\"")

  print(f"rename_device: delfiles={delfiles}, replace_string={repl_count}")
  return delfiles


def delete_paths(basedir, pathlist):
  """Delete a file or a directory (recursively). Missing paths are ignored."""
  count = 0
  for obj in pathlist:
    if basedir:
      path = Path(basedir + '/' + obj)
    else:
      path = Path(obj)

    try:
        if path.is_dir() and not path.is_symlink():
            count += 1
            shutil.rmtree(path)
        else:
            count += 1
            path.unlink()
    except FileNotFoundError:
        pass
    except OSError as e:
        raise OSError(f"failed to delete {path}: {e}") from e

  return count


def replace_string_in_file(filename, olds, news):
    """Replace all occurrences of `old` with `new` in `filename`.

    Returns the number of replacements made. If the file doesn't
    exist, does nothing and returns 0.
    """
    path = Path(filename)

    try:
        content = path.read_text()
    except FileNotFoundError:
        return 0

    count = content.count(olds)
    if count:
        path.write_text(content.replace(olds, news))

    return count


####

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


def linear_spline_t(v, t):
  # print(f"tgen({v}, {t})")
  if not v.startswith("t(") or not v.endswith(")"):
    return float(v)

  s = v[2:-1]                # "1:60, 5:40, 8:15, 18:6"
  s = re.split("[\\s,;]+", s)         # multiple comma, whitespace, semicolons split.
  a = [x.split(':') for x in s]       # [['1', '60'], ['5', '40'], ['8', '15'], ['18', '6']]

  def to_float(s: str) -> float:
    return float(s.replace(',', '.'))   # allow both, . and , in floats...

  f = sorted([[to_float(x), to_float(y)] for x, y in a], key=lambda pair: pair[0])
  if len(f) < 1:
    raise ValueError(f"no mapping pairs found in {v}")
  if len(f) < 2:
    return f[0][1]                    # nothing to interpolate, we are a constant.

  if t <= f[1][0]:
    # we are in the first interval or smaller. Compute derivative between first and second, then interpolate/extrapolate
    d = (f[1][1] - f[0][1]) / (f[1][0] - f[0][0])
    return f[0][1] + (t-f[0][0])*d

  if t >= f[-2][0]:
    # we are in the last inteval or larger, compute derivative between last and second last, then interpolate/extrapolate
    d = (f[-1][1] - f[-2][1]) / (f[-1][0] - f[-2][0])
    return f[-1][1] + (t-f[-1][0])*d

  # loop through the remaining intervals to find where we sit, then interpolate
  for i in range(1, len(f)-2):
    if t <= f[i+1][0]:
      d = (f[i+1][1] - f[i][1]) / (f[i+1][0] - f[i][0])
      return f[i][1] + (t-f[i][0])*d

  # unreachable
  print(f)


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


def check_laserprofiles(mpd, autofix=True):
  # mpd = { 'materials': m, 'profiles': p, 'devices': l } as generated with collect_laserprofiles

  r = []
  fixcounter = 0
  ### find materials that have no name. (autocreated by profiles, but xml file missing in /materials folder.)
  for n,m in mpd['materials'].items():
    if not 'name' in m:
      r.append(f"material '{n}' used in laserprofiles, but materials/{mpd["encode_pathname"](n)}.xml is missing.")
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

