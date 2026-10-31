#!/usr/bin/env python3
"""Generate Java schema/enum/reference-ID constants from audited project JSON only."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def generate(root=ROOT):
    md=json.loads((root/'config/catalog_metadata_v036.json').read_text())
    ref=json.loads((root/'config/runtime_reference_v036.json').read_text())
    ids=ref['item_ids']
    if len(ids)!=3284 or ids!=sorted(set(ids)) or any(type(x)!=int or x<=0 for x in ids):raise ValueError('Invalid 3,284-ID reference')
    def quote(s):return json.dumps(s,ensure_ascii=False)
    def records(items):return ',\n'.join('        '+quote(json.dumps(r,ensure_ascii=False,separators=(',',':'))) for r in items)
    text='''package org.npc.toibridge;

/** Generated from matching metadata schemas and IDs in the supplied device dump.
 * No names/assets/saves or unobserved configuration values are embedded.
 */
public final class CatalogDefinitions {
    private CatalogDefinitions(){}
'''
    text+='    public static final String METADATA_SHA256='+quote(md['metadata_sha256'])+';\n'
    text+='    public static final String REFERENCE_SHA256='+quote(ref['dump_sha256'])+';\n'
    text+='    public static final int[] REFERENCE_IDS={'+','.join(map(str,ids))+'};\n'
    text+='    public static final String[] TYPE_RECORDS={\n'+records(md['item_types'])+'\n    };\n'
    text+='    public static final String[] CONTRACT_RECORDS={\n'+records(md['contracts'])+'\n    };\n'
    text+='    public static final int[] TYPE_IDS={'+','.join(str(x['id']) for x in md['item_types'])+'};\n'
    text+='    public static final String[] TYPE_NAMES={'+','.join(quote(x['name']) for x in md['item_types'])+'};\n'
    text+='}\n'
    out=root/'android/bridge/src/main/java/org/npc/toibridge/CatalogDefinitions.java';out.write_text(text)
    return text
if __name__=='__main__':
    text=generate();print('Generated verified metadata definitions / reference IDs; SHA256',hashlib.sha256(text.encode()).hexdigest())
