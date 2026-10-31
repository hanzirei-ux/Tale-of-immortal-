"""Source-level compatibility checks; these do not claim device behavior."""
import re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JAVA=ROOT/'android/bridge/src/main/java/org/npc/toibridge'
def array(source,name):
    match=re.search(r'\b'+name+r'(?:\[\])?\s*(?:=\s*)?\{(.*?)\};',source,re.S)
    if not match:raise AssertionError('Missing array '+name)
    return match.group(1)
class HotfixSourceTests(unittest.TestCase):
    def test_java_native_ids_and_ranges(self):
        java=(JAVA/'ModMenu.java').read_text();cpp=(ROOT/'native/modifiers.cpp').read_text()
        keys=re.findall(r'"([^"]+)"',array(java,'KEYS'))
        minimum=[float(v.strip()) for v in array(java,'MIN').split(',')]
        maximum=[float(v.strip()) for v in array(java,'MAX').split(',')]
        native=re.findall(r'\{"([^"]+)",([^,]+),([^,]+),([^}]+)\}',array(cpp,'specs'))
        self.assertEqual(len(keys),22);self.assertEqual(keys,[v[0] for v in native[:22]])
        self.assertEqual(minimum,[float(v[1]) for v in native[:22]]);self.assertEqual(maximum,[float(v[2]) for v in native[:22]])
        self.assertEqual(keys[8],'all_defense');self.assertEqual(keys[5],'spiritual_damage')
    def test_ui_uses_detailed_native_apply_and_guard(self):
        source=(JAVA/'ModMenu.java').read_text()
        self.assertNotIn('Rejected or hook unavailable',source)
        self.assertNotIn('NativeBridge.setControl(',source)
        self.assertIn('NativeBridge.applyControl(r.id,KEYS[r.id],on,value)',source)
        self.assertIn('if(controlUi.callbacksAllowed())applyRow',source)
        self.assertIn('controlUi.programmatic(new Runnable()',source)
        self.assertIn('showResult(detail)',source)
    def test_async_receipt_does_not_replace_newer_control(self):
        source=(JAVA/'ModMenu.java').read_text()
        self.assertIn('controlUi.isLatest(ticket.epoch)',source)
        self.assertIn('if(latest){showResult(',source)
        self.assertIn('logDiagnostic(kind+',source)
    def test_only_load_replays_runtime_controls(self):
        source=(JAVA/'ModMenu.java').read_text();a=source.index('    private void loadSaved(){');b=source.index('    private void gmButton(',a)
        section=source[a:b]
        self.assertNotIn('NativeBridge.request(',section)
        self.assertIn('NativeBridge.applyControl(i,KEYS[i]',section)
    def test_currency_and_capacity_not_duplicated(self):
        source=(JAVA/'ModMenu.java').read_text();keys=re.findall(r'"([^"]+)"',array(source,'CURRENCY_KEYS'))
        self.assertEqual(keys,['money','contribution','city_token','immortal_token','sect_funds','sect_reputation','sect_faith'])
        self.assertNotIn('Chi You',source)
        cpp=(ROOT/'native/game_editors.cpp').read_text();self.assertIn('toimodmenu.v03.capacityBonus',cpp)
        self.assertIn('expected=10041',cpp);self.assertIn('expected=10051',cpp)
    def test_compact_layout_does_not_reintroduce_dark_text(self):
        source=(JAVA/'ModMenu.java').read_text()
        self.assertIn('FG=Color.rgb(244,248,255)',source)
        self.assertIn('result.setVisibility(View.GONE)',source)
        self.assertIn('new LinearLayout.LayoutParams(dp(55),dp(40))',source)
        self.assertIn('resizeItemList()',source)
        self.assertNotIn('slider.setMax(1000)',source)
    def test_localization_recovers_only_exact_exception(self):
        source=(ROOT/'native/managed_access.cpp').read_text()
        self.assertIn('exceptionNamespace!="System.Collections.Generic"',source)
        self.assertIn('exceptionOwner!="ConfLocalText"',source)
        self.assertIn('exceptionMethod!="GetText"',source)
        catalog=(ROOT/'native/game_editors.cpp').read_text()
        self.assertIn('m.consumeMissingLocalization()',catalog)
        self.assertIn('if(localizedName.failed)return',catalog)
        self.assertIn('Commit this row only after',catalog)
if __name__=='__main__':unittest.main()
