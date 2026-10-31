"""Read-only integration and preservation regression checks. No Android/device claims."""
import hashlib,json,re,unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from audit_hotfix_preservation import function
JAVA=ROOT/'android/bridge/src/main/java/org/npc/toibridge'
class ExportIntegrationTests(unittest.TestCase):
    def test_native_and_jni_sources_are_exact_v031(self):
        golden=json.loads((ROOT/'config/v031_reuse_hashes.json').read_text())
        for name,digest in golden['unchanged_source'].items():
            with self.subTest(name=name):self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest)
    def test_working_menu_methods_unchanged(self):
        golden=json.loads((ROOT/'config/v031_reuse_hashes.json').read_text());menu=(JAVA/'ModMenu.java').read_text()
        for name,digest in golden['unchanged_menu_method_bodies'].items():
            with self.subTest(name=name):self.assertEqual(hashlib.sha256(function(menu,name).encode()).hexdigest(),digest)
    def test_export_only_uses_catalog_and_one_receipt_consumer(self):
        menu=(JAVA/'ModMenu.java').read_text();start=menu.index('    // Read-only export:');end=menu.index('    private void submitCatalog(){',start);export=menu[start:end]
        calls=re.findall(r'NativeBridge\.(\w+)\((.*?)\);',export,re.S)
        self.assertEqual(len(calls),1);self.assertEqual(calls[0][0],'request')
        self.assertEqual(calls[0][1],'"catalog","@-1||"+offset,0,0,false')
        self.assertEqual(menu.count('NativeBridge.takeGameResults()'),1)
        self.assertIn('catalogExport.guard.owns(id)',menu)
    def test_generation_and_cancel_are_enforced(self):
        menu=(JAVA/'ModMenu.java').read_text()
        self.assertIn('receipt.optLong("generation",-1)',menu)
        self.assertIn('nativeSnapshot.optLong("generation",-1)',menu)
        self.assertIn('job.guard.check(',menu);self.assertIn('job.guard.receive(',menu)
        self.assertIn('onActivityPaused(Activity a)',menu);self.assertIn('job.guard.cancel()',menu)
        self.assertIn('exportWorker.shutdown()',menu)
        self.assertIn('unregisterActivityLifecycleCallbacks(exportLifecycle)',menu)
    def test_file_io_is_queued_and_late_receipts_guarded(self):
        menu=(JAVA/'ModMenu.java').read_text()
        self.assertIn('newSingleThreadExecutor(',menu)
        self.assertIn('job.cancelled=true',menu)
        self.assertIn('catalogExport!=job||job.cancelled',menu)
        self.assertIn('if(completed)job.writer.close();else job.writer.discard()',menu)
        self.assertIn('||catalogExport!=null)',menu)
    def test_no_storage_permission_or_manifest_change(self):
        source=(JAVA/'CatalogDocumentFragment.java').read_text()
        self.assertIn('Intent.ACTION_CREATE_DOCUMENT',source)
        self.assertIn('startActivityForResult(intent,CREATE_DOCUMENT)',source)
        self.assertIn('onActivityResult(int request,int result,Intent data)',source)
        self.assertIn('new Thread(',source)
        self.assertNotIn('file://',source);self.assertNotIn('requestPermissions',source)
        self.assertIn('Original completed export retained',source)
    def test_schema_does_not_claim_full_manuals_or_invent_fields(self):
        source=(JAVA/'ReadOnlyCatalogExport.java').read_text()
        for text in ['existing_native_catalog_nonhidden','ConfItemProps','snapshot_generation','display_only_localization_unverified','display_name_is_localization_fallback']:
            self.assertIn(text,source)
        for name in ['name_en','name_ch','rarity','description','subtype']:
            self.assertIn('\\"'+name+'\\":null',source)
        self.assertNotIn('NewMartial',source)
if __name__=='__main__':unittest.main()
