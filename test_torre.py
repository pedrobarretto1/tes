import unittest
from torre import new_run, choose, start_match, finish_match, domain, public_state

def play(run, match, outcome, route="guardian"):
    return finish_match(start_match(choose(run,route),match),match,outcome)

class TowerTests(unittest.TestCase):
    def test_ascension_checkpoint_and_record(self):
        r=new_run()
        for n in range(1,5):
            r=play(r,str(n),"win")
        self.assertEqual((r.floor,r.highest,r.lives),(5,4,3))
        for n in range(5,8):
            r=play(r,str(n),"loss")
        self.assertEqual((r.floor,r.highest,r.lives,r.status),(1,4,3,"choose"))
    def test_expedition_ends(self):
        r=new_run("expedicao")
        for n in range(3):
            r=play(r,str(n),"loss")
        self.assertEqual((r.lives,r.status),(0,"ended"))
    def test_draw_and_idempotence(self):
        r=play(new_run(),"a","draw")
        self.assertEqual((r.floor,r.lives),(1,3))
        self.assertIs(finish_match(r,"a","win"),r)
        with self.assertRaises(ValueError):
            finish_match(r,"b","win")
    def test_first_domain(self):
        r=new_run()
        for n in range(1,11):
            r=play(r,str(n),"win")
        self.assertEqual((r.floor,r.highest,r.status),(10,10,"completed"))
        self.assertEqual(public_state(r)["domain"]["boss"],"O Cavaleiro Sem Nome")
    def test_routes_and_domains(self):
        with self.assertRaises(ValueError):
            choose(new_run(),"invalid")
        self.assertEqual(domain(17)["id"],"crypt")
        self.assertIsNone(domain(55))
        self.assertEqual(domain(100)["boss"],"O Rei Primordial")

if __name__ == "__main__":
    unittest.main()
