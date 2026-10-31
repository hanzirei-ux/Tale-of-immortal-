import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import unittest
from gm_command_builder import build_command,InvalidCommand
class BuilderTests(unittest.TestCase):
    def test_exp(self):self.assertEqual(build_command('add_exp',['100'])[0],'jingyan_100')
    def test_hp(self):self.assertEqual(build_command('add_player_stat',['hp','10'])[0],'shuxing_hp_10')
    def test_npc(self):self.assertEqual(build_command('add_npc_stat',['123','hp','10'],backup_ack=True)[0],'npcshuxing_123_hp_10')
    def test_realm(self):self.assertEqual(build_command('set_npc_realm',['123','5'],backup_ack=True)[0],'jingjienpc_123_5')
    def test_bag(self):self.assertEqual(build_command('resize_bag',['10'],backup_ack=True)[0],'beibao_10')
    def test_requires_backup(self):
        with self.assertRaises(InvalidCommand):build_command('set_npc_realm',['123','5'])
    def test_no_injection(self):
        with self.assertRaises(InvalidCommand):build_command('add_npc_stat',['123_foo','hp','10'],backup_ack=True)
    def test_no_negative_guess(self):
        with self.assertRaises(InvalidCommand):build_command('add_player_stat',['hp','-10'])
    def test_no_fabricated_recipe(self):
        with self.assertRaises(InvalidCommand):build_command('unlock_all_recipe',[])
    def test_item_parameter_semantics_opaque(self):
        cmd,note=build_command('add_item',['1001','5','2'],backup_ack=True)
        self.assertEqual(cmd,'daoju_1001_5_2')
        self.assertIn('NOT guaranteed',note)
if __name__=='__main__':unittest.main()
