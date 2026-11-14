import unittest
from torre import new_run, choose, start_match, finish_match, domain, public_state, encounter, RELEASE_MAX_FLOOR

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
        for n in range(1,31):
            r=play(r,str(n),"win")
        self.assertEqual((r.floor,r.highest,r.status),(30,30,"completed"))
        self.assertEqual(public_state(r)["domain"]["id"],"crypt")
        self.assertEqual(public_state(r)["domain"]["first"],26)
    def test_domain_checkpoint(self):
        r=new_run()
        for n in range(1,11):r=play(r,str(n),"win")
        self.assertEqual((r.floor,r.checkpoint,r.lives),(11,11,3))
        for n in range(11,14):r=play(r,str(n),"loss")
        self.assertEqual((r.floor,r.highest,r.lives),(11,10,3))
    def test_routes_and_domains(self):
        with self.assertRaises(ValueError):
            choose(new_run(),"invalid")
        self.assertEqual(domain(17)["id"],"castle")
        self.assertEqual(domain(26)["id"],"crypt")
        self.assertEqual(domain(55)["id"],"gold")
        self.assertEqual(domain(100)["boss"],"O Rei Primordial")

    def test_castle_catalog(self):
        self.assertEqual(len(public_state(new_run())["realm_map"]),25)
        self.assertEqual([n for n in range(1,26) if encounter(n)["kind"]=="elite"],[5,10,15,20])
        self.assertEqual(encounter(24)["kind"],"preboss")
        self.assertEqual(encounter(25)["name"],"O Cavaleiro Sem Nome")
        self.assertEqual(encounter(25)["kind"],"boss")
        self.assertEqual(encounter(26)["stage"],1)
        self.assertEqual(encounter(100)["kind"],"boss")
        self.assertFalse(encounter(31)["released"])
    def test_castle_boundary_and_fixed_routes(self):
        r=new_run()
        for n in range(1,25):r=play(r,str(n),"win")
        self.assertEqual((r.floor,r.checkpoint),(25,21))
        with self.assertRaises(ValueError):choose(r,"unknown")
        r=play(r,"25","win")
        self.assertEqual((r.floor,r.highest,r.checkpoint,r.lives),(26,25,26,3))
        p=public_state(r)
        self.assertEqual([m["floor"] for m in p["realm_map"]],list(range(26,51)))
    def test_legacy_state_preserved(self):
        from torre import Run
        r=Run(id="old",mode="ascensao",floor=24,highest=23,checkpoint=21,lives=1,status="playing",route="unknown",match="old-match",version=7)
        r=finish_match(r,"old-match","win")
        self.assertEqual((r.id,r.floor,r.highest,r.lives,r.checkpoint),("old",25,24,1,21))
        r=play(r,"next","win")
        self.assertEqual((r.floor,r.checkpoint,r.lives),(26,26,3))

if __name__ == "__main__":
    unittest.main()
