"""Synthetic archive tests for replacement/preservation; never gameplay tests."""
import hashlib,tempfile,unittest,zipfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import apply_v03_to_v02_apk as patch
class PatchV03Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.old=(patch.OLD_MAIN,patch.OLD_HELPER,patch.OLD_NATIVE)
        self.primary=b'synthetic primary dex';self.helper=b'synthetic helper dex';self.native=b'synthetic old native'
        patch.OLD_MAIN=patch.sha(self.primary);patch.OLD_HELPER=patch.sha(self.helper);patch.OLD_NATIVE=patch.sha(self.native)
        self.apk=self.root/'fixture.apk';self.updated=self.root/'patch.zip';self.out=self.root/'unsigned.apk'
        with zipfile.ZipFile(self.apk,'w') as z:
            for n,b in {'classes.dex':self.primary,'classes2.dex':b'other game dex','classes3.dex':self.helper,'lib/arm64-v8a/libtoimodmenu.so':self.native,'assets/fixture.txt':b'keep exact bytes','META-INF/CERT.RSA':b'synthetic obsolete signature'}.items():z.writestr(n,b)
    def tearDown(self):
        patch.OLD_MAIN,patch.OLD_HELPER,patch.OLD_NATIVE=self.old;self.tmp.cleanup()
    def components(self,valid=True):
        payloads={'APK_ROOT/classes2.dex':b'synthetic new helper','APK_ROOT/lib/arm64-v8a/libtoimodmenu.so':b'synthetic new native'}
        with zipfile.ZipFile(self.updated,'w') as z:
            for n,b in payloads.items():z.writestr(n,b)
            z.writestr('SHA256SUMS.txt',''.join((hashlib.sha256(b).hexdigest() if valid else '0'*64)+'  '+n+'\n' for n,b in payloads.items()))
    def test_replace_actual_helper_slot_preserves_original_inputs(self):
        self.components();before=self.apk.read_bytes();patch.apply(self.apk,self.updated,self.out)
        with zipfile.ZipFile(self.out) as z:
            self.assertEqual(z.read('classes.dex'),self.primary);self.assertEqual(z.read('classes2.dex'),b'other game dex')
            self.assertEqual(z.read('classes3.dex'),b'synthetic new helper');self.assertEqual(z.read('assets/fixture.txt'),b'keep exact bytes')
            self.assertEqual(z.read('lib/arm64-v8a/libtoimodmenu.so'),b'synthetic new native');self.assertNotIn('META-INF/CERT.RSA',z.namelist())
        self.assertEqual(self.apk.read_bytes(),before)
    def test_bad_component_digest_does_not_create_apk(self):
        self.components(False)
        with self.assertRaisesRegex(ValueError,'checksum'):patch.apply(self.apk,self.updated,self.out)
        self.assertFalse(self.out.exists())
    def test_unrecognized_old_native_does_not_create_apk(self):
        self.components();patch.OLD_NATIVE='0'*64
        with self.assertRaisesRegex(ValueError,'mismatched'):patch.apply(self.apk,self.updated,self.out)
        self.assertFalse(self.out.exists())
if __name__=='__main__':unittest.main()
