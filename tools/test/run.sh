#!/bin/sh
#

basedir=/tmp/vca
set -x
set -e

if [ ! -d "$basedir" ]; then
  mkdir -p "$basedir"
  cp -a ~/.visicut "$basedir"
fi

# simple check, if the expected two lasers from FBALABNBG are here:
l1="Thunderlaser Nova 35
Zing"
l2=$(./vcsetman.py -d $basedir/.visicut list l| jq 'keys[]' -r | sort)
test "$l1" = "$l2" || { echo "expected: '$l1' == '$l2'"; exit 1; }


# convert wiki to useable visicut xml settings.
w=$basedir/wiki
rm -rf $w; mkdir $w
./vcsetman.py -v -d $w  import https://wiki.fablab-nuernberg.de/w/Nova_35

for d in $w/laserprofiles $w/materials $w/profiles $w/devices; do
  test -d $d || { echo "ERROR: expected existing dir $d"; exit 1; }
done

for f in $w/laserprofiles/annotations.json; do
  test -f $f || { echo "ERROR: expected existing: file $f"; exit 1; }
done
