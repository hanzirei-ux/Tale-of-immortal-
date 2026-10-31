import copy,csv,importlib.util,json,pathlib,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from normalize_full_catalog import CatalogError,normalize,normalize_item
def item(i=1,**extra):
    r={'kind':'item','id':i,'display_name':'Untranslated Name','props_type':7,'level':6,'source_table':'ConfItemProps','collector_version':'0.3.2','snapshot_generation':2,'grade':None,'rarity':None,'realm_id':None}
    r.update(extra);return r
def proven(**extra):
    r=item();r['field_status']={k:'VERIFIED_RUNTIME' for k in ['id','display_name','props_type','level']}
    for k,v in extra.items():r[k]=v;r['field_status'][k]='VERIFIED_JOIN' if v is not None else 'UNKNOWN'
    return r
class FullNormalizerTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def write(self,name,rows):
        p=self.root/name;p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows));return p
    def run_rows(self,rows,expected=None,metadata=None):return normalize([self.write('in.jsonl',rows)],self.root/'output',expected,metadata)
    def test_runtime_columns_preserved_without_realm_grade_rarity_guess(self):
        summary=self.run_rows([item()],{1});r=json.loads((self.root/'output/items.jsonl').read_text())
        self.assertEqual(r['level'],6);self.assertEqual(r['props_type'],7)
        self.assertIsNone(r['realm_id']);self.assertIsNone(r['grade']);self.assertIsNone(r['rarity'])
        self.assertIsNone(r['name_en']);self.assertIsNone(r['name_ch']);self.assertEqual(r['field_status']['level'],'VERIFIED_RUNTIME')
        self.assertEqual(summary['sections']['realms'],'BLOCKED_NATIVE')
    def test_verified_values_are_independent_dimensions(self):
        r=proven(realm_id=10,grade=3,rarity=5,subtype=99,cultivation_quality=2)
        self.run_rows([r]);out=json.loads((self.root/'output/items.jsonl').read_text())
        self.assertEqual([out[k] for k in ['realm_id','grade','rarity','level','cultivation_quality']],[10,3,5,6,2])
    def test_metadata_type_enum_is_not_implicitly_joined(self):
        md={'item_types':[{'kind':'item_type','id':7,'name':'Enum candidate','source_table':'SomeEnum','status':'VERIFIED_METADATA'}],'contracts':[]}
        summary=self.run_rows([item()],metadata=md);out=json.loads((self.root/'output/items.jsonl').read_text())
        self.assertIsNone(out['type_name']);self.assertEqual(summary['counts_by_section']['item_types'],2)
    def test_schema_is_not_a_realm_record(self):
        md={'item_types':[],'contracts':[{'kind':'metadata_contract','owner':'ConfRoleGradeItem','section':'realms','fields':[{'name':'grade','value':None}],'data_values_available':False}]}
        summary=self.run_rows([item()],metadata=md)
        self.assertEqual(summary['counts_by_section']['realms'],0);self.assertEqual(summary['counts_by_section']['metadata_contracts'],1)
        self.assertEqual((self.root/'output/realms.jsonl').read_bytes(),b'')
    def test_book_skill_template_manual_template_instance_ids_are_separate(self):
        records=[item(),{'kind':'book','id':1,'source_table':'ConfItemBook'},{'kind':'skill_template','id':1,'source_table':'ConfBattleSkillBase'},{'kind':'manual_template','id':1,'source_table':'ConfItemSkill'},{'kind':'manual_instance','base_id':1,'source_table':'MartialInfoData'}]
        summary=self.run_rows(records)
        for section in ['items','books','skill_templates','manual_templates','manual_instances']:self.assertEqual(summary['counts_by_section'][section],1)
    def test_unknown_cannot_erase_confirmed_enrichment(self):
        old=self.write('old.jsonl',[proven(grade=3)]);new=self.write('new.jsonl',[item()])
        normalize([old,new],self.root/'output',{1});out=json.loads((self.root/'output/items.jsonl').read_text());self.assertEqual(out['grade'],3);self.assertEqual(len(out['observations']),2)
    def test_new_confirmed_field_merges_all_original_ids(self):
        old=self.write('old.jsonl',[item(1),item(2)]);new=self.write('new.jsonl',[proven(grade=3)])
        summary=normalize([old,new],self.root/'output',{1,2});self.assertEqual(summary['reference_ids_preserved'],2)
        rows=[json.loads(l) for l in (self.root/'output/items.jsonl').read_text().splitlines()];self.assertEqual([r['id'] for r in rows],[1,2]);self.assertEqual(rows[0]['grade'],3)
    def test_reference_gap_rejected_without_output(self):
        with self.assertRaisesRegex(CatalogError,'REFERENCE_ID_GAP'):self.run_rows([item()],{1,2})
        self.assertFalse((self.root/'output').exists())
    def test_conflicting_verified_values_rejected(self):
        a=self.write('a.jsonl',[proven(grade=2)]);b=self.write('b.jsonl',[proven(grade=3)])
        with self.assertRaisesRegex(CatalogError,'Conflicting verified'):normalize([a,b],self.root/'output')
        self.assertFalse((self.root/'output').exists())
    def test_duplicate_in_single_file_rejected(self):
        with self.assertRaisesRegex(CatalogError,'Duplicate identity'):self.run_rows([item(),item()])
    def test_unknown_field_cannot_carry_fabricated_grade(self):
        r=proven(grade=99);r['field_status']['grade']='UNKNOWN'
        with self.assertRaisesRegex(CatalogError,'invented value'):self.run_rows([r])
    def test_invalid_evidence_status_rejected(self):
        r=proven();r['field_status']['level']='DEVICE_VERIFIED'
        with self.assertRaisesRegex(CatalogError,'evidence status'):self.run_rows([r])
    def test_invalid_numeric_identity_rejected(self):
        for value in [True,0,-1,2**40]:
            with self.subTest(value=value),self.assertRaises(CatalogError):normalize_item(item(value))
    def test_csv_formula_guard_does_not_alter_json(self):
        self.run_rows([item(display_name='=literal item name')])
        self.assertEqual(json.loads((self.root/'output/items.jsonl').read_text())['display_name'],'=literal item name')
        with (self.root/'output/items.csv').open(encoding='utf-8-sig') as f:r=next(csv.DictReader(f))
        self.assertEqual(r['display_name'],"'=literal item name");self.assertEqual(r['realm_id_status'],'UNKNOWN')
    def test_original_visible_key_remains_inferred(self):
        self.run_rows([item(display_name='item_name1041161',name_key='item_name1041161')]);r=json.loads((self.root/'output/items.jsonl').read_text());self.assertEqual(r['field_status']['name_key'],'INFERRED')
    def test_malformed_json_rejected(self):
        p=self.root/'broken.jsonl';p.write_text('{bad json\n')
        with self.assertRaisesRegex(CatalogError,'Malformed JSONL'):normalize([p],self.root/'output')
    def test_unknown_record_kind_rejected(self):
        with self.assertRaisesRegex(CatalogError,'Unknown catalog record'):self.run_rows([{'kind':'npc','id':1}])
    def test_manifest_record_count_mismatch_rejected(self):
        begin={'kind':'catalog_manifest','stage':'begin','snapshot_generation':2};end={'kind':'catalog_manifest','stage':'complete','snapshot_generation':2,'completion_status':'COMPLETE_SUPPORTED_SCOPE','item_count':1,'record_count':999}
        with self.assertRaisesRegex(CatalogError,'manifest count'):self.run_rows([begin,item(),end])
    def test_cross_generation_manifest_rejected(self):
        begin={'kind':'catalog_manifest','stage':'begin','snapshot_generation':3};end={'kind':'catalog_manifest','stage':'complete','snapshot_generation':3,'completion_status':'COMPLETE_SUPPORTED_SCOPE','item_count':1,'record_count':3}
        with self.assertRaisesRegex(CatalogError,'Mixed-generation'):self.run_rows([begin,item(),end])
    def test_incomplete_export_rejected(self):
        with self.assertRaisesRegex(CatalogError,'Incomplete full-schema'):self.run_rows([{'kind':'catalog_manifest','stage':'begin'},item()])
    def test_existing_output_is_never_overwritten(self):
        out=self.root/'output';out.mkdir();(out/'important').write_text('retain')
        with self.assertRaisesRegex(CatalogError,'already exists'):self.run_rows([item()])
        self.assertEqual((out/'important').read_text(),'retain')
    def test_future_records_without_claims_remain_explicitly_inferred(self):
        self.run_rows([item(),{'kind':'realm','id':10,'source_table':'TestFixture','name':'Synthetic realm'}])
        row=json.loads((self.root/'output/realms.jsonl').read_text());self.assertEqual(row['field_status']['name'],'INFERRED');self.assertEqual(row['field_status']['id'],'INFERRED')
if __name__=='__main__':unittest.main()
