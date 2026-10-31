import unittest, importlib.util, pathlib
p=pathlib.Path(__file__).parents[1]/'tools'/'integrate_v031.py'
spec=importlib.util.spec_from_file_location('integrator', p)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
FIXTURE='''
public final class ModMenu {
    private long catalogRequestId;
    private void release(){disposed=true;ui.removeCallbacksAndMessages(null);}
    private void buildItemBrowser(){
        itemTypeFilter.setOnItemSelectedListener(listener);
    }
    private void submitCatalog(){
        String reply=NativeBridge.request("catalog",key,0,0,false);
    }
    private void updatePoll(){
        JSONArray replies=new JSONArray(NativeBridge.takeGameResults());
        for(int i=0;i<replies.length();i++){
            JSONObject r=replies.getJSONObject(i);long id=r.getLong("id");
            String kind="catalog",state="CATALOG",message="";
                    if("catalog".equals(kind)){
            }
        }
        if(panel.getVisibility()==View.VISIBLE&&!activity.isFinishing())ui.postDelayed(pollTask,pendingCatalog||!pendingActions.isEmpty()?100:1000);
    }
}
'''
class TestIntegration(unittest.TestCase):
    def test_patch(self):
        new=mod.transform(FIXTURE)
        self.assertIn('new ReadOnlyCatalogExport(destination,100000)',new)
        self.assertIn('id==catalogExportRequestId',new)
        self.assertIn('"@-1||"+offset',new)
        self.assertIn('catalogExportRequestId!=0?100:1000',new)
        self.assertIn('catalogExport.close()',new)
        self.assertIn('startReadOnlyCatalogExport();',new)
    def test_double_apply_is_blocked(self):
        with self.assertRaises(ValueError):mod.transform(mod.transform(FIXTURE))
    def test_missing_anchor_is_blocked(self):
        with self.assertRaises(ValueError):mod.transform(FIXTURE.replace('    private void submitCatalog(){',''))
if __name__=='__main__':unittest.main()
