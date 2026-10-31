#!/usr/bin/env python3
"""Host-test the v4 writer, v0.3.2 transport guard and actual JSONL output. No game actions."""
import argparse,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--java-tools',type=Path,required=True);a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='toi-v032-export-tests-') as temp:
        output=Path(temp)/'fixtures'
        names=['ReadOnlyCatalogExport','CatalogExportGuard','CatalogFileCopy']
        sources=[ROOT/f'android/bridge/src/main/java/org/npc/toibridge/{name}.java' for name in names]
        sources.extend([ROOT/'tests/java/ReadOnlyCatalogExportTest.java',ROOT/'tests/java/CatalogExportRegressionTest.java'])
        subprocess.run(['java','-jar',str(a.java_tools/'ecj-3.38.0.jar'),'-source','1.8','-target','1.8','-proc:none','-d',temp,*map(str,sources)],check=True)
        for name in ['ReadOnlyCatalogExportTest','CatalogExportRegressionTest']:
            subprocess.run(['java','-cp',temp,name,str(output)],check=True)
        names=[json.loads(line) for line in (output/'host_names_fixture.jsonl').read_text().splitlines()]
        assert [r['id'] for r in names]==[1041161,1041162,1041163]
        assert names[0]['display_name_is_localization_fallback'] is True
        assert names[1]['name_key']=='item_name1041162'
        assert names[2]['name_key'] is None and names[2]['name_en'] is None
        for row in names:
            assert row['rarity'] is None and row['grade'] is None and row['description'] is None
            assert row['source_table']=='ConfItemProps' and row['snapshot_generation']==77
        large=[json.loads(line) for line in (output/'host_large_fixture.jsonl').read_text().splitlines()]
        assert len(large)==1643 and len({r['id'] for r in large})==1643
        assert '漢字' in large[0]['display_name']
        print('PASS: actual Java JSONL parsed by Python; 1,643 unique rows, Unicode, explicit unknowns, exact fallback keys.')
