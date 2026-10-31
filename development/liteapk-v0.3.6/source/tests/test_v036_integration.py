import hashlib,importlib.util,json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from generate_catalog_definitions import generate
class CollectorIntegrationTests(unittest.TestCase):
    def test_full_mode_shares_existing_receipt_transport(self):
        s=(ROOT/'android/bridge/src/main/java/org/npc/toibridge/ModMenu.java').read_text()
        self.assertEqual(s.count('NativeBridge.takeGameResults()'),1)
        self.assertIn('new FullCatalogExport(destination,100000,job.guard.generation)',s)
        self.assertIn('NativeBridge.request("catalog","@-1||"+offset,0,0,false)',s)
        self.assertIn('startReadOnlyCatalogExport(){startCatalogExport(false);}',s)
        self.assertIn('startFullCatalogExport(){startCatalogExport(true);}',s)
        self.assertIn('COMPLETE_SUPPORTED_SCOPE',s);self.assertIn('other tables BLOCKED_NATIVE',s)
    def test_generated_metadata_definitions_reproducible(self):
        p=ROOT/'android/bridge/src/main/java/org/npc/toibridge/CatalogDefinitions.java'
        before=p.read_bytes();self.assertEqual(generate().encode(),before)
    def test_reference_ids_are_the_actual_3284_unique_ids(self):
        r=json.loads((ROOT/'config/runtime_reference_v036.json').read_text())
        self.assertEqual(len(r['item_ids']),3284);self.assertEqual(r['item_ids'],sorted(set(r['item_ids'])))
        self.assertEqual(r['dump_sha256'],'c0dfdc8a810cf7e58c0bc3da9f87e6b2fb5aad64ff877411eb56ed8855fb4f7a')
        self.assertEqual(r['unresolved_names'],60)
    def test_nested_martial_info_data_is_excluded_from_schema(self):
        r=json.loads((ROOT/'config/catalog_metadata_v036.json').read_text());contracts=r['contracts']
        self.assertEqual(len(contracts),14)
        martial=[x for x in contracts if x['owner']=='MartialInfoData'];self.assertEqual(len(martial),1);self.assertEqual(martial[0]['type_index'],7962)
        self.assertTrue(all(x['image']=='Assembly-CSharp.dll' and x['data_values_available'] is False for x in contracts))
    def test_enum_definitions_do_not_fabricate_category_7_or_8(self):
        r=json.loads((ROOT/'config/catalog_metadata_v036.json').read_text());enums=r['item_types']
        self.assertEqual({x['id'] for x in enums},{0,1,2,3,5,6})
        self.assertTrue(all('not verified' in x['official_scope'] for x in enums))
    def test_full_schema_does_not_use_gm_or_unsafe_manual_creation(self):
        s=(ROOT/'android/bridge/src/main/java/org/npc/toibridge/FullCatalogExport.java').read_text()
        self.assertNotIn('NativeBridge.',s);self.assertNotIn('NewMartial',s);self.assertNotIn('RewardProp',s)
        self.assertIn('REFERENCE_ID_GAP',s);self.assertIn('matched!=reference.length',s)
        self.assertIn('"realm_id"',s);self.assertIn('"cultivation_quality"',s)
    def test_native_blocker_is_explicit_and_has_no_guessed_addresses(self):
        r=json.loads((ROOT/'config/native_collector_requirements_v036.json').read_text())
        self.assertFalse(r['native_extension_compiled']);self.assertFalse(r['requires_apk'])
        self.assertEqual(len(r['methods']),30)
        self.assertTrue(all(x['runtime_location'] is None and not x['runtime_call_verified'] for x in r['methods']))
if __name__=='__main__':unittest.main()
