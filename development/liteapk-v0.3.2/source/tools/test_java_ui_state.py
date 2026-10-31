#!/usr/bin/env python3
"""Compile/run the actual Android-independent UI state guard with host Java."""
import argparse,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--java-tools',type=Path,required=True);a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='toi-v031-java-test-') as temp:
        subprocess.run(['java','-jar',str(a.java_tools/'ecj-3.38.0.jar'),'-source','1.8','-target','1.8','-proc:none','-d',temp,str(ROOT/'android/bridge/src/main/java/org/npc/toibridge/ControlUiState.java'),str(ROOT/'tests/java/ControlUiStateTest.java')],check=True)
        subprocess.run(['java','-cp',temp,'ControlUiStateTest'],check=True)
