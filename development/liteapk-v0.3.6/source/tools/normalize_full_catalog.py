#!/usr/bin/env python3
"""Normalize/merge legacy or full-schema JSONL without inventing Realm/grade/rarity.

Evidence statuses are source claims, not certification of device testing. No game
process, inventory, save file, DLL or native method is invoked by this tool.
"""
import argparse,copy,csv,hashlib,json,tempfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STATUSES={'VERIFIED_RUNTIME','VERIFIED_METADATA','VERIFIED_JOIN','INFERRED','UNKNOWN'}
FIELDS=['id','display_name','internal_name','name_key','name_en','name_ch','description','props_type','type_name','subtype','level','grade','rarity','rarity_color','realm_id','realm_requirement','cultivation_quality','hidden','book_template_id','skill_template_id','manual_instance_id','spawnable']
TABLES={'item':'items','item_type':'item_types','realm':'realms','grade':'grades','rarity':'rarity','localization':'localization','book':'books','skill_template':'skill_templates','manual_template':'manual_templates','manual_instance':'manual_instances','metadata_contract':'metadata_contracts'}
BLOCKED=['realms','grades','rarity','localization','books','skill_templates','manual_templates','manual_instances']
class CatalogError(ValueError):pass
def integer(v,positive=False):
    return type(v) is int and (-2147483648<=v<=2147483647) and (not positive or v>0)
def normalize_item(record):
    r=copy.deepcopy(record)
    if not integer(r.get('id'),True) or not integer(r.get('props_type')) or not integer(r.get('level')) or not isinstance(r.get('display_name'),str):raise CatalogError('Invalid native item identity/type/level/name')
    if r.get('source_table')!='ConfItemProps':raise CatalogError('Item namespace is not the verified inventory catalog')
    supplied=r.get('field_status')
    if supplied is not None and (not isinstance(supplied,dict) or any(v not in STATUSES for v in supplied.values())):raise CatalogError('Invalid field evidence status')
    states=dict(supplied or {})
    if supplied is None:
        for field in ['id','display_name','props_type','level']:states[field]='VERIFIED_RUNTIME'
        if r.get('name_key') is not None:states['name_key']='INFERRED'
    for field in FIELDS:
        r.setdefault(field,None);states.setdefault(field,'UNKNOWN')
        if states[field]=='UNKNOWN' and r[field] is not None:raise CatalogError('UNKNOWN field contains an invented value: '+field)
        if r[field] is None:states[field]='UNKNOWN'
    r['field_status']=states;r['schema_version']='0.3.6';r['identity_namespace']='ConfItemProps';r.setdefault('type_namespace','ConfItemProps.type')
    # Neither display names nor numeric Level/quality produce any Realm or rarity join.
    return r
def normalize_other(record):
    r=copy.deepcopy(record)
    if r['kind']=='metadata_contract':return r
    states=dict(r.get('field_status',{}))
    if any(v not in STATUSES for v in states.values()):raise CatalogError('Invalid non-item evidence status')
    default=r.get('status') if r.get('status') in STATUSES else 'INFERRED'
    for field,value in r.items():
        if field in {'kind','field_status','status','note','official_scope','schema_version'}:continue
        states.setdefault(field,'UNKNOWN' if value is None else default)
        if states[field]=='UNKNOWN' and value is not None:raise CatalogError('UNKNOWN non-item field contains a value: '+field)
    r['field_status']=states;return r
def identity(r):
    kind=r.get('kind')
    if kind not in TABLES:raise CatalogError('Unknown catalog record kind: '+str(kind))
    if kind=='metadata_contract':
        if not isinstance(r.get('owner'),str) or r.get('data_values_available') is not False:raise CatalogError('Invalid schema-only metadata contract')
        return kind,r.get('image','Assembly-CSharp.dll'),r['owner']
    source=r.get('source_table')
    if not isinstance(source,str) or not source:raise CatalogError('Missing record source namespace')
    key=r.get('key') if kind=='localization' else r.get('id',r.get('base_id'))
    if kind=='localization':
        if not isinstance(key,str) or not key:raise CatalogError('Invalid localization key')
    elif not integer(key):raise CatalogError('Invalid numeric identity')
    return kind,source,key
def load(path):
    path=Path(path)
    if path.stat().st_size>64*1024*1024:raise CatalogError('Input exceeds 64 MiB')
    digest=hashlib.sha256(path.read_bytes()).hexdigest();rows=[];unique=set();manifests={};item_count=0
    with path.open(encoding='utf-8-sig') as stream:
        for line_no,line in enumerate(stream,1):
            if line_no>300000 or len(line)>262144:raise CatalogError('Input record/line bound exceeded')
            if not line.strip():continue
            try:r=json.loads(line)
            except ValueError as ex:raise CatalogError('Malformed JSONL at line '+str(line_no)) from ex
            if not isinstance(r,dict):raise CatalogError('JSONL record must be an object')
            if r.get('kind')=='catalog_manifest':
                stage=r.get('stage')
                if stage not in {'begin','complete'} or stage in manifests:raise CatalogError('Duplicate/invalid export manifest')
                manifests[stage]=r;rows.append(r);continue
            key=identity(r)
            if key in unique:raise CatalogError('Duplicate identity within input: '+str(key))
            unique.add(key)
            if r['kind']=='item':
                r=normalize_item(r);item_count+=1
                r['observations']=[{'input_sha256':digest,'collector_version':r.get('collector_version'),'snapshot_generation':r.get('snapshot_generation')}]
            else:r=normalize_other(r)
            rows.append(r)
    if manifests:
        if set(manifests)!={'begin','complete'}:raise CatalogError('Incomplete full-schema export')
        begin,end=manifests['begin'],manifests['complete']
        if end.get('completion_status')!='COMPLETE_SUPPORTED_SCOPE' or end.get('item_count')!=item_count or end.get('record_count')!=len(rows):raise CatalogError('Export manifest count/state mismatch')
        if begin.get('snapshot_generation')!=end.get('snapshot_generation'):raise CatalogError('Export generation changed')
        for row in rows:
            if row.get('kind')=='item' and row.get('snapshot_generation')!=begin.get('snapshot_generation'):raise CatalogError('Mixed-generation item snapshot')
    return rows,digest
def merge_item(old,new):
    out=copy.deepcopy(old)
    for field in FIELDS:
        before,after=old.get(field),new.get(field);a=old['field_status'][field];b=new['field_status'][field]
        if after is None:continue
        if before is None or a=='UNKNOWN' or a=='INFERRED' and b.startswith('VERIFIED_'):
            out[field]=after;out['field_status'][field]=b
        elif before!=after and b!='INFERRED':raise CatalogError('Conflicting verified item field '+field+' for ID '+str(old['id']))
    history=old.get('observations',[])+new.get('observations',[]);out['observations']=[]
    for record in history:
        if record not in out['observations']:out['observations'].append(record)
    if len(out['observations'])>16:raise CatalogError('Too many observation sources')
    for field in ['snapshot_generation','collector_version','schema_version','field_sources']:
        if field in new:out[field]=new[field]
    return out
def normalize(inputs,output,expected_ids=None,metadata=None):
    output=Path(output)
    if output.exists():raise CatalogError('Output already exists; choose a new folder')
    merged={};hashes=[];manifests=[]
    for path in inputs:
        rows,digest=load(path);hashes.append(digest)
        for r in rows:
            if r['kind']=='catalog_manifest':manifests.append(r);continue
            key=identity(r)
            if key in merged:
                if r['kind']=='item':merged[key]=merge_item(merged[key],r)
                elif merged[key]!=r:raise CatalogError('Conflicting non-item identity '+str(key))
            else:merged[key]=r
    if metadata is not None:
        for r in metadata['item_types']+metadata['contracts']:
            r=normalize_other(r)
            key=identity(r)
            if key in merged and merged[key]!=r:raise CatalogError('Metadata definition conflict')
            merged.setdefault(key,r)
    items=sorted((r for r in merged.values() if r['kind']=='item'),key=lambda r:r['id'])
    ids={r['id'] for r in items};missing=set(expected_ids or [])-ids
    if missing:raise CatalogError('REFERENCE_ID_GAP: '+str(len(missing))+' of '+str(len(expected_ids))+' expected item IDs missing')
    # Derive observed type IDs only. Never join them to PropsType by numeric coincidence.
    counts=Counter(r['props_type'] for r in items)
    for t,n in counts.items():
        key=('item_type','ConfItemProps.type',t)
        if key not in merged:merged[key]={'kind':'item_type','id':t,'name':None,'source_table':'ConfItemProps.type','item_count':n,'status':'VERIFIED_RUNTIME','field_status':{'id':'VERIFIED_RUNTIME','name':'UNKNOWN','item_count':'VERIFIED_JOIN','source_table':'VERIFIED_JOIN'}}
    partitions={name:[] for name in TABLES.values()}
    for r in merged.values():partitions[TABLES[r['kind']]].append(r)
    sections={name:('COLLECTED' if rows else 'BLOCKED_NATIVE') for name,rows in partitions.items() if name!='metadata_contracts'}
    sections['items']='CURRENT_NONHIDDEN_JNI4_SCOPE';sections['item_types']='RAW_OBSERVATIONS_AND_SEPARATE_METADATA_ENUM'
    summary={'schema_version':'0.3.6','input_sha256':hashes,'item_count':len(items),'expected_reference_ids':len(expected_ids or []),'reference_ids_preserved':len(set(expected_ids or [])&ids),'counts_by_section':{k:len(v) for k,v in partitions.items()},'sections':sections,'observed_type_counts':dict(sorted(counts.items())),'unresolved_names':sum(r.get('display_name_is_localization_fallback') is True for r in items),'unknown_item_fields':{f:sum(r.get(f) is None for r in items) for f in FIELDS},'filters':['realm_id','props_type','subtype','grade','rarity','level'],'status_values':sorted(STATUSES),'device_verification':'Source evidence preserved; parser/host tests do not certify new Android functionality','warning':'Metadata schema rows are not runtime data. Realm, item Level, Grade, Rarity and cultivation quality remain independent.'}
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='toi-normalize-',dir=output.parent) as temp:
        staging=Path(temp)/'result';staging.mkdir()
        for name,rows in partitions.items():
            with (staging/(name+'.jsonl')).open('w',encoding='utf-8') as stream:
                for r in rows:stream.write(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')
        headers=['id','display_name','name_en','name_ch','realm_id','props_type','subtype','grade','rarity','level','source_table']
        status_fields=['realm_id','props_type','subtype','grade','rarity','level'];headers += [f+'_status' for f in status_fields]
        with (staging/'items.csv').open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=headers);writer.writeheader()
            for r in items:
                row={f:r.get(f) for f in headers};row.update({f+'_status':r['field_status'][f] for f in status_fields})
                for f,v in row.items():
                    if isinstance(v,str) and v[:1] in {'=','+','-','@'}:row[f]="'"+v
                writer.writerow(row)
        (staging/'manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
        staging.rename(output)
    return summary
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dump',type=Path);p.add_argument('output',type=Path);p.add_argument('--baseline',type=Path,action='append',default=[]);p.add_argument('--reference',type=Path,default=ROOT/'config/runtime_reference_v036.json');p.add_argument('--metadata',type=Path,default=ROOT/'config/catalog_metadata_v036.json');a=p.parse_args()
    ref=json.loads(a.reference.read_text())['item_ids'];md=json.loads(a.metadata.read_text());r=normalize([*a.baseline,a.dump],a.output,ref,md);print(json.dumps(r,ensure_ascii=False,indent=2))
