#!/usr/bin/env python3
"""Normalize a read-only Tale of Immortal runtime JSONL dump into CSV files.

NOT an IL2CPP runtime reader. Input comes from a separately developed, read-only
in-game collector. Never fabricate missing localized names, rarity colors or skills.
"""
import csv
import json
import pathlib
import re
import sys
from collections import Counter, defaultdict

LANGUAGES = ('en', 'ch', 'tc', 'kr')
ITEM_HEADERS = ['item_id', 'name_en', 'name_ch', 'name_tc', 'name_kr', 'display_name',
                'name_key', 'props_type', 'category', 'subcategory', 'level', 'grade',
                'rarity_color', 'rarity_verified', 'description', 'description_key',
                'source', 'status']
MANUAL_HEADERS = ['base_id', 'name', 'grade', 'level', 'prefixes', 'source', 'status']
SKILL_HEADERS = ['template_id', 'main_skill', 'weapon_type', 'magic_type', 'source', 'status']
CLASS = {0: 'Currency', 1: 'Pills', 2: 'Book-related items (NOT all manuals)',
         3: 'Equipment', 5: 'Materials', 6: 'Other'}
ALLOWED = {'localization', 'item', 'item_book', 'item_horse', 'item_ring',
           'cloth', 'skill_template', 'manual_instance', 'rarity_rule'}
LIMIT = 300000

def safe_text(v, limit=2048):
    if v is None:
        return ''
    if isinstance(v, (dict, list)):
        v = json.dumps(v, ensure_ascii=False, separators=(',', ':'))
    return str(v).replace('\x00', '')[:limit]

def safe_int(value):
    if isinstance(value, bool):
        return None
    try:
        num = int(str(value))
        return num if str(value) == str(num) and 0 <= num <= 2_000_000_000 else None
    except (ValueError, TypeError):
        return None

def csv_write(path, fields, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

def process(input_jsonl, output_dir):
    path = pathlib.Path(input_jsonl)
    target = pathlib.Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    records = defaultdict(list)
    invalid = []
    with path.open('r', encoding='utf-8-sig') as stream:
        for line_no, line in enumerate(stream, 1):
            if line_no > LIMIT:
                raise ValueError('Runtime dump exceeds maximum 300,000 lines')
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if not isinstance(record, dict) or record.get('kind') not in ALLOWED:
                    raise ValueError('Unexpected kind / invalid object')
                records[record['kind']].append(record)
            except (ValueError, TypeError) as e:
                invalid.append({'line': line_no, 'error': str(e)[:120]})

    localization = {}
    for rec in records['localization']:
        k = safe_text(rec.get('key'), 250)
        if k:
            if k in localization:
                for lang in LANGUAGES:
                    if not localization[k].get(lang) and rec.get(lang):
                        localization[k][lang] = rec[lang]
            else:
                localization[k] = rec.copy()
    extra = {}
    for kind, sub in [('item_book', 'Book / special book'), ('item_horse', 'Mount'),
                      ('item_ring', 'Ring'), ('cloth', 'Outfit / clothing')]:
        for rec in records[kind]:
            item_id = safe_int(rec.get('item_id', rec.get('id')))
            # Cloth IDs may represent appearances only; not automatically inventory item IDs.
            if kind == 'cloth' and not rec.get('inventory_item_id_verified', False):
                continue
            if item_id is not None:
                extra.setdefault(item_id, []).append((kind, sub, rec))
    rarity_colors = {}
    for rec in records['rarity_rule']:
        key = rec.get('grade')
        if isinstance(key, int) and rec.get('verified') is True and isinstance(rec.get('color'), str):
            col = rec['color'].strip()
            if re.fullmatch(r'#[a-fA-F0-9]{6,8}', col):
                rarity_colors[key] = col
    items = {}
    missing = Counter()
    failures = Counter()
    for rec in records['item']:
        iid = safe_int(rec.get('id'))
        if iid is None:
            failures['invalid_item_id'] += 1
            continue
        if iid in items:
            failures['duplicate_item_id'] += 1
            continue
        key = safe_text(rec.get('name_key'), 250)
        lex = localization.get(key, {})
        names = {lang: safe_text(rec.get('name_' + lang) or lex.get(lang), 250) for lang in LANGUAGES}
        if not any(names.values()) and key:
            missing[key] += 1
        # v0.3.1 UI catalog provides a localized display name but not language identity.
        # Preserve it without claiming it is English or inventing a source key.
        display = next((names[lang] for lang in ('en','ch','tc','kr') if names[lang]),
                       safe_text(rec.get('display_name'),250) or key or f'item #{iid}')
        kind = rec.get('props_type')
        ptype = safe_int(kind)
        category = CLASS.get(ptype, 'Unknown (unmapped props_type)')
        matches = extra.get(iid, [])
        subcategory = 'Unclassified'
        # Never infer mount/outfit/manual by item name, ID range or level.
        if matches:
            precedence = ('cloth','item_horse','item_ring','item_book')
            matches.sort(key=lambda x: precedence.index(x[0]))
            subcategory = matches[0][1]
        grade = rec.get('grade')
        color = safe_text(rec.get('rarity_color')) if rec.get('rarity_verified') is True else ''
        if not color and isinstance(grade, int):
            color = rarity_colors.get(grade, '')
        desc_key = safe_text(rec.get('desc_key'), 250)
        dlex = localization.get(desc_key, {})
        description = safe_text(rec.get('description') or dlex.get('en') or dlex.get('ch'), 1000)
        items[iid] = dict(item_id=iid, name_en=names['en'], name_ch=names['ch'], name_tc=names['tc'],
                          name_kr=names['kr'], display_name=display, name_key=key,
                          props_type=safe_text(kind), category=category, subcategory=subcategory,
                          level=safe_text(rec.get('level')), grade=safe_text(grade),
                          rarity_color=color, rarity_verified='YES' if color else 'NO',
                          description=description, description_key=desc_key,
                          source=safe_text(rec.get('source') or 'runtime'), status='RUNTIME_DUMP_UNVERIFIED_ON_PHONE')
    item_rows = sorted(items.values(), key=lambda row: (row['category'], row['subcategory'], row['item_id']))
    manual_rows = []
    for rec in records['manual_instance']:
        bid = safe_int(rec.get('base_id'))
        if bid is None:
            failures['invalid_manual_base_id'] += 1
            continue
        manual_rows.append(dict(base_id=bid, name=safe_text(rec.get('name'),250), grade=safe_text(rec.get('grade')),
                                level=safe_text(rec.get('level')), prefixes=safe_text(rec.get('prefixes')),
                                source=safe_text(rec.get('source')), status='INSTANCE_ONLY_NOT_SKILL_ITEM_CATALOG'))
    skill_rows = []
    for rec in records['skill_template']:
        tid = safe_int(rec.get('id'))
        if tid is None:
            failures['invalid_template_id'] += 1
            continue
        skill_rows.append(dict(template_id=tid, main_skill=safe_text(rec.get('main_skill')),
                               weapon_type=safe_text(rec.get('weapon_type')), magic_type=safe_text(rec.get('magic_type')),
                               source=safe_text(rec.get('source')), status='TEMPLATE_ONLY_NOT_USABLE_MANUAL'))
    csv_write(target / 'items.csv', ITEM_HEADERS, item_rows)
    csv_write(target / 'manual_instances.csv', MANUAL_HEADERS, manual_rows)
    csv_write(target / 'skill_templates.csv', SKILL_HEADERS, skill_rows)
    csv_write(target / 'missing_localizations.csv', ['key','count'],
              [{'key': key, 'count': count} for key,count in sorted(missing.items())])
    csv_write(target / 'input_errors.csv', ['line','error'], invalid)
    summary = {'source_file':path.name,'item_rows':len(item_rows),'manual_instances':len(manual_rows),
               'skill_templates':len(skill_rows),'localized_keys':len(localization),
               'missing_localization_keys':len(missing),'invalid_jsonl_records':len(invalid),
               'validation_failures':dict(failures),'counts_by_category':dict(Counter(x['category'] for x in item_rows)),
               'statement':'Output reflects supplied JSONL input only, not direct verification of Android game behavior.'}
    (target / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    return summary

if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('Usage: python3 build_catalog_from_dump.py <runtime_dump.jsonl> <output_dir>')
    print(json.dumps(process(sys.argv[1], sys.argv[2]), ensure_ascii=False, indent=2))
