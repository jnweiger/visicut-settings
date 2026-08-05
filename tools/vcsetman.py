#! /usr/bin/python
#
# vcsetman.py - manage visicut settings, native XML data and Wiki tables
#
# (C) 2026, juergen@fabmail.org


import os, sys, json
import argparse
from urllib.request import urlopen
from urllib.parse import urlsplit

LIB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
sys.path.insert(0, LIB_DIR)

from visicut_xml import *
from wiki_markdown_table import *


def main():
    def_settings_dir = os.environ.get("HOME", '/') + "/.visicut"

    parser = argparse.ArgumentParser(description="vcsetman - Manage VisiCut Settings", epilog="Use 'vcsetman COMMAND --help' for more information.")
    parser._optionals.title = "Global options"
    parser.add_argument("-d", "--settings-dir", metavar="DIR", default=def_settings_dir, help="My Visicut settings directory. Default ~/.visicut")
    parser.add_argument("-n", "--noop", action="store_true", help="Prevent an changes. Default: write or update settings when needed.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Report more details.")
    parser.add_argument("-b", "--backup", action="store_true", help="Backup files with '.orig' suffix before overwriting. Default: No backup.") 

    subparsers = parser.add_subparsers(title="Available sub commands", metavar="COMMAND", dest="command", required=True)

    list_parser = subparsers.add_parser("list", aliases=["l"], help="print laserdevices, materials, and profiles found in the XML files of the settings directory.")
    list_parser.add_argument("filter", metavar="l|m|p|lp", nargs="?", choices=("all", "l", "lasers", "d", "devices", "n", "names", "m", "materials", "p", "profiles", "lp", "laserprofiles", "g", "gen", "generator"), default="all", help="optional filter to not print everything: lasers, materials, profiles")

    check_parser = subparsers.add_parser("check", aliases=["c"], help="Report inconsistencies of visicut profiles. E.g. unused materials, unused thickness, material profiles only defined for one laser, or only defined for cut or engrave.")
    check_parser.add_argument("-f", "--fix", action="store_true", help="Fill in missing entries.")
    check_parser.add_argument("-g", "--gen", "--generator-file", type=str, help="Specify the generator file used for fixing. This implies --fix. Default: SETTINGS_DIR/laserprofiles/generator.json")
    check_parser.add_argument("-o", "--output-dir", metavar="OUTDIR", help="Output directory, if writing settings. Default: write inplace in my settings directory.")

    import_parser = subparsers.add_parser("import", aliases=["i"], help="Process external data, such as wiki tables or json exports.")
    import_parser.add_argument("source", metavar="file.md|URL", help="wiki url or wiki markdown file to import. Use -o ... to create new xml settings for later 'compare' or 'merge'.")
    import_parser.add_argument("-l", "--laser-name", metavar="DEVICE", help="specfy the name of the laser to import. Default: guess from the filename or URL.")
    import_parser.add_argument("-o", "--output-dir", metavar="OUTDIR", help="Output directory, if writing settings. Default: write inplace in my settings directory.")

    export_parser = subparsers.add_parser("export", aliases=["e"], help="produce a wiki markdown file with tables.")
    export_parser.add_argument("name", metavar="LASER", nargs="?", help="Specify which laser to export. Default: All laser devices, one file per laser.")
    export_parser.add_argument("-f", "--output-file", metavar="FNAME", help="Specfy the name markdown file to export to. Requires a LASER device name. Default: derived from the laser device name.")
    export_parser.add_argument("-a", "--all", "--all-profiles", action="store_true", help="Generate wiki tables for really all profiles. Default: cut, mark, engrave")

    merge_parser = subparsers.add_parser("merge", aliases=["m"], help="Combine two settings into one.")
    merge_parser.add_argument("name", help="Specify the other directory to merge with.")
    merge_parser.add_argument("-O", "--overwrite", action="store_true",  help="My settings are overwritten by conflicting settings from other directory. Default: preserve my settings, skip conflicts.")
    merge_parser.add_argument("-C", "--conflict", action="store_true",  help="Report conflicts and abort, if any. Default: preserve my settings, skip conflicts.")
    merge_parser.add_argument("-o", "--output-dir", metavar="OUTDIR", help="Output directory, if writing settings. Default: write inplace in my settings directory.")

    rename_parser = subparsers.add_parser("rename", aliases=["r"], help="rename laser device, profile, or material.")
    rename_parser.add_argument("oldname", help="Name of an existing laser, material or profile. Which of the three is autodetected.")
    rename_parser.add_argument("newname", help="")

    args = parser.parse_args()
    if args.command is None:     # add_subparsers(..., required=True) in modern python.
      parser.print_help()
      parser.exit(2)

    if not args.output_dir:
      args.output_dir = args.settings_dir
 
    if args.verbose:
      print(f"... reading {args.settings_dir}", file=sys.stderr)
    mpd = collect_profiles(args.settings_dir)

    ############################
    if args.command in ("list"):
      filt = None
      if args.filter in ("l", "d", "n", "laser", "lasers", "dev", "device", "devices", "name", "names"):
        filt = "devices"
      elif args.filter in ("g", "gen", "generator"):
        filt = "generator"
      elif args.filter in ("lp", "laserprofiles", "m", "materials"):
        filt = "materials"
        if args.filter in ("m", "material", "materials"):   # shorten, to only show materials.
          for m in mpd[filt]:
            if 'profiles' in mpd[filt][m]:
              del(mpd[filt][m]['profiles'])
      elif args.filter in ("a", "all", "*"):
        filt = None
      elif args.filter:
        filt = "profiles"

      if args.verbose:
        print(f"list filter: {filt}", args.filter, file=sys.stderr)
      if filt:
        print(json.dumps(mpd[filt]))
      else:
        print(json.dumps(mpd))
      sys.exit(0)

    ############################
    if args.command in ("check"):
      if not args.noop:
        stats = write_xml(mpd, args.output_dir, noop=True)
        if stats['changed'] > 0:
          print("INTERNAL ERROR: write_xml would produce changes on unchanged data: ", stats, file=sys.stderr)
          sys.exit(0)

      result = check_profiles(mpd, autofix=False)
      if args.verbose:
        for change in result:
          print(change)
      else:
        print(f"check found {len(result)} issues.", file=sys.stderr)
        if len(result):
          print("Use --verbose check to list them all.", file=sys.stderr)

      if args.fix:
        res2 = check_profiles(mpd, autofix=True)
        if len(result) > len(res2):
          raise ValueError(f"check_profiles with autofix=True found only {len(res2)} issues. That was {len(result)} without autofix.")
        remainder = check_profiles(mpd, autofix=False)
        if remainder:
          print(json.dumps({"ERROR": "check --fix failed to fix: ", "remainder": remainder } ))

        if not args.noop:
          stats = write_xml(mpd, args.output_dir, noop=False, orig_suffix=(".orig" if args.backup else ""))
          print(stats)
      sys.exit(0)

    ############################
    if args.command in ("import"):
      if not args.laser_name:
        if "://" in args.source:    # oh, its an url.
          urlpath = urlsplit(args.source).path
          args.laser_name = os.path.splitext(os.path.basename(urlpath))[0] 
        else:
          args.laser_name = os.path.splitext(os.path.basename(args.source))[0] 
      if "://" in args.source:
        if not "?action=" in args.source and not ".md" in args.source:
          args.source += "?action=raw"
        if args.verbose: print(f" ... reading url {args.source} for {args.laser_name}", file=sys.stderr)
        with urlopen(args.source) as fd:
          table_list = list_tables(fd)
      else:
        if args.verbose: print(f" ... reading file {args.source} for {args.laser_name}", file=sys.stderr)
        with open(args.source, "r") as fd:
          table_list = list_tables(fd)
      # if args.verbose:
      #   print(json.dumps(table_list))
      imp = import_from_tables(table_list, args.laser_name, args.source)
      print(json.dumps(imp))
      # TODO: write_xml()
      sys.exit(0)

    ############################
    if args.command in ("export"):
      print(f"{args.command} not impl.", file=sys.stderr)
      sys.exit(0)

    ############################
    if args.command in ("merge"):
      print(f"{args.command} not impl.", file=sys.stderr)
      sys.exit(0)

    ############################
    if args.command in ("rename"):
      print(f"{args.command} not impl.", file=sys.stderr)
      sys.exit(0)

    print(f"ERROR: unknown command {args.command}.", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()

