import hashlib,importlib.util,pathlib,tempfile,unittest,zipfile
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('full_export_patch',ROOT/'tools/apply_full_catalog_patch.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def sha(data):return hashlib.sha256(data).hexdigest()
class FullExportPatchTests(unittest.TestCase):
    def fixture(self,tmp,slot='classes3.dex',native=b'v031 native',helper=b'v032 helper',tamper=False):
        apk=tmp/'original.apk';update=tmp/'patch.zip';out=tmp/'unsigned.apk';dex=b'dex\nnew export helper'
        with zipfile.ZipFile(apk,'w') as z:
            for n,b in {'classes.dex':b'primary','classes2.dex':b'another dex',slot:helper,'lib/arm64-v8a/libtoimodmenu.so':native,'assets/original':b'private game asset','META-INF/CERT.RSA':b'old signature'}.items():z.writestr(n,b)
        with zipfile.ZipFile(update,'w') as z:
            z.writestr('APK_ROOT/classes2.dex',dex)
            z.writestr('SHA256SUMS.txt',('0'*64 if tamper else sha(dex))+'  APK_ROOT/classes2.dex\n')
        return apk,update,out,dex
    def test_only_helper_changes_and_actual_multidex_slot_retained(self):
        with tempfile.TemporaryDirectory() as d,patch.object(mod,'MAIN',sha(b'primary')),patch.object(mod,'HELPER',sha(b'v032 helper')),patch.object(mod,'NATIVE',sha(b'v031 native')):
            apk,z,out,dex=self.fixture(pathlib.Path(d));before=apk.read_bytes();mod.apply(apk,z,out)
            self.assertEqual(apk.read_bytes(),before)
            with zipfile.ZipFile(out) as updated:
                self.assertEqual(updated.read('classes3.dex'),dex);self.assertEqual(updated.read('classes2.dex'),b'another dex')
                self.assertEqual(updated.read('classes.dex'),b'primary');self.assertEqual(updated.read('lib/arm64-v8a/libtoimodmenu.so'),b'v031 native')
                self.assertEqual(updated.read('assets/original'),b'private game asset');self.assertNotIn('META-INF/CERT.RSA',updated.namelist())
    def test_wrong_native_is_rejected(self):
        with tempfile.TemporaryDirectory() as d,patch.object(mod,'MAIN',sha(b'primary')):
            apk,z,out,_=self.fixture(pathlib.Path(d),native=b'v030 native')
            with self.assertRaisesRegex(ValueError,'native component'):mod.apply(apk,z,out)
            self.assertFalse(out.exists())
    def test_tampered_patch_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            apk,z,out,_=self.fixture(pathlib.Path(d),tamper=True)
            with self.assertRaisesRegex(ValueError,'checksum'):mod.apply(apk,z,out)
            self.assertFalse(out.exists())
    def test_wrong_helper_is_rejected(self):
        with tempfile.TemporaryDirectory() as d,patch.object(mod,'MAIN',sha(b'primary')),patch.object(mod,'NATIVE',sha(b'v031 native')):
            apk,z,out,_=self.fixture(pathlib.Path(d),helper=b'unknown helper')
            with self.assertRaisesRegex(ValueError,'helper DEX'):mod.apply(apk,z,out)
if __name__=='__main__':unittest.main()
