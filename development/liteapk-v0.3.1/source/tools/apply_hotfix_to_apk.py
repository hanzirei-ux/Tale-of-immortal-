#!/usr/bin/env python3
"""Replace a recognized v0.2/v0.3 helper pair, retaining the actual multidex slot.

Produces a new UNSIGNED APK locally from the user's private APK. No game files
are downloaded or redistributed by this tool.
"""
import argparse
from pathlib import Path
from apply_v03_to_v02_apk import apply
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input_apk',type=Path);p.add_argument('hotfix_zip',type=Path);p.add_argument('output_unsigned_apk',type=Path);a=p.parse_args()
    apply(a.input_apk,a.hotfix_zip,a.output_unsigned_apk)
