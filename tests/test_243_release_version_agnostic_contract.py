#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'tests' / 'test_localization_completeness_contract.py'

def main():
    text = TARGET.read_text(encoding='utf-8')
    assert 'version == "2.4.2"' not in text, 'release validation must not pin localization completeness to 2.4.2'
    assert 'expected 2.4.2 candidate' not in text, 'stale candidate assertion would block 2.4.3 release validation'
    updater=(ROOT/'tests'/'test_goal4_desktop_updater_contract.py').read_text(encoding='utf-8')
    assert "'tauri-plugin-updater = \"2\"' in cargo" not in updater, 'updater contract must accept a pinned compatible Tauri v2 plugin'
    print('2.4.3 release version-agnostic contracts: PASS')

if __name__ == '__main__': main()
