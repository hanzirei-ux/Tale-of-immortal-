#!/usr/bin/env python3
"""Compile/run actual writer, validate JSONL, optionally replay the private phone dump."""
import argparse,hashlib,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(java_tools,baseline_source=None,device_dump=None,report=None):
    compiler=java_tools/'ecj-3.38.0.jar';base=ROOT/'android/bridge/src/main/java/org/npc/toibridge'
    result={'device_tested':False}
    with tempfile.TemporaryDirectory(prefix='toi-v036-tests-') as tmp:
        tmp=Path(tmp);classes=tmp/'classes';classes.mkdir();fixtures=tmp/'fixtures'
        sources=[base/(n+'.java') for n in ['ReadOnlyCatalogExport','FullCatalogExport','CatalogDefinitions']]
        sources += [ROOT/'tests/java'/n for n in ['FullCatalogExportTest.java','CatalogLegacyParity.java','CatalogPhoneReplay.java']]
        subprocess.run(['java','-jar',str(compiler),'-source','1.8','-target','1.8','-proc:none','-d',str(classes),*map(str,sources)],check=True)
        subprocess.run(['java','-cp',str(classes),'FullCatalogExportTest',str(fixtures)],check=True)
        rows=[json.loads(l) for l in (fixtures/'full_fixture.jsonl').read_text().splitlines()];items=[r for r in rows if r['kind']=='item']
        from jsonschema import Draft202012Validator
        schema=json.loads((ROOT/'schema/full_catalog_v036.schema.json').read_text());Draft202012Validator.check_schema(schema);validator=Draft202012Validator(schema)
        for r in rows:validator.validate(r)
        result['json_schema_draft_2020_12']='PASS'
        assert len(items)==3 and rows[-1]['record_count']==len(rows)
        assert all(r['realm_id'] is None and r['grade'] is None and r['rarity'] is None and r['internal_name'] is None for r in items)
        assert all(r['field_status']['hidden']=='VERIFIED_JOIN' and r['field_status']['level']=='VERIFIED_RUNTIME' for r in items)
        assert {r['source_table'] for r in rows if r['kind']=='item_type'}=={'PropsType','ConfItemProps.type'}
        assert not any(r['kind'] in {'realm','manual_instance','skill_template'} for r in rows)
        result['actual_java_jsonl_schema_checks']='PASS'
        if baseline_source:
            old=tmp/'old';old.mkdir();harness=ROOT/'tests/java/CatalogLegacyParity.java'
            subprocess.run(['java','-jar',str(compiler),'-source','1.8','-target','1.8','-proc:none','-d',str(old),str(baseline_source/'android/bridge/src/main/java/org/npc/toibridge/ReadOnlyCatalogExport.java'),str(harness)],check=True)
            for where,name in [(old,'old'),(classes,'new')]:subprocess.run(['java','-cp',str(where),'CatalogLegacyParity',str(tmp/(name+'.jsonl'))],check=True)
            assert (tmp/'old.jsonl').read_bytes()==(tmp/'new.jsonl').read_bytes();result['legacy_v032_export_byte_identical']=True
        if device_dump:
            original=[json.loads(l) for l in device_dump.read_text().splitlines() if l.strip()]
            assert len(original)==3284 and len({r['id'] for r in original})==3284
            pages=tmp/'pages';pages.mkdir()
            for offset in range(0,len(original),40):
                page='CATALOG\t3284\t'+str(offset)+'\t40\n'
                for r in original[offset:offset+40]:
                    assert not any(c in r['display_name'] for c in '\t\r\n')
                    page+=f"{r['id']}\t{r['display_name']}\t{r['props_type']}\t{r['level']}\n"
                (pages/(f'{offset:06}.page')).write_text(page)
            out=tmp/'replay.jsonl';subprocess.run(['java','-cp',str(classes),'CatalogPhoneReplay',str(pages),str(out)],check=True)
            replay=[json.loads(l) for l in out.read_text().splitlines()];new=[r for r in replay if r['kind']=='item']
            for r in replay:validator.validate(r)
            assert {r['id'] for r in new}=={r['id'] for r in original}
            assert [(r['id'],r['display_name'],r['props_type'],r['level']) for r in new]==[(r['id'],r['display_name'],r['props_type'],r['level']) for r in original]
            assert replay[-1]['baseline_ids_preserved']==3284 and replay[-1]['record_count']==len(replay)
            from normalize_full_catalog import normalize
            md=json.loads((ROOT/'config/catalog_metadata_v036.json').read_text());ref=json.loads((ROOT/'config/runtime_reference_v036.json').read_text())
            summary=normalize([device_dump,out],tmp/'normalized',ref['item_ids'],md)
            assert summary['item_count']==3284 and summary['reference_ids_preserved']==3284
            assert summary['counts_by_section']['realms']==0 and summary['counts_by_section']['manual_instances']==0
            result['phone_input_sha256']=hashlib.sha256(device_dump.read_bytes()).hexdigest();result['host_replay_summary']=summary
            result['host_replay_records']=len(replay);result['host_replay_jsonl_bytes']=out.stat().st_size;result['phone_dump_was_only_legacy_four_columns']=True
    if report:report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: full-schema JSONL, namespace separation, reference IDs and requested host comparisons. No v0.3.6 device test.',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--java-tools',type=Path,required=True);p.add_argument('--baseline-source',type=Path);p.add_argument('--device-dump',type=Path);p.add_argument('--report',type=Path);a=p.parse_args();run(a.java_tools,a.baseline_source,a.device_dump,a.report)
