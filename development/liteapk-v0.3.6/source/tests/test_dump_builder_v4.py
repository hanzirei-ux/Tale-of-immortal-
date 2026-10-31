import importlib.util, json, pathlib, tempfile, unittest
p=pathlib.Path(__file__).parents[1]/'tools'/'build_catalog_from_dump.py'
spec=importlib.util.spec_from_file_location('catalog_builder', p)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class TestDumpCompatibility(unittest.TestCase):
    def test_real_ui_shape_preserves_display_without_mislabeling_language(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=pathlib.Path(tmp)/'catalog.jsonl'
            source.write_text(json.dumps({'kind':'item','id':7000004,'props_type':2,'level':5,
                                          'display_name':'Superior Sect Manual','source':'LiteAPK-v0.3.1 catalog read-only'})+'\n',encoding='utf-8')
            output=pathlib.Path(tmp)/'csv';summary=mod.process(source,output)
            text=(output/'items.csv').read_text(encoding='utf-8-sig')
            self.assertIn('Superior Sect Manual',text)
            self.assertEqual(summary['item_rows'],1)
            self.assertIn('Book-related items (NOT all manuals)',text)
            self.assertEqual(summary['manual_instances'],0)
if __name__=='__main__':unittest.main()
