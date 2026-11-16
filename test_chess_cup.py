"""Regression tests for the independently scored Chess Copa de Honra."""
import json
import tempfile
import time
import unittest
from pathlib import Path

import servidor as s
import chess_duels as games
import chess_cup as cups


class ChessCupTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original = (s.BASE, s.DATABASE_URL)
        s.BASE = Path(self.temp.name)
        s.DATABASE_URL = ''
        s.setup()
        self.tokens = [chr(65+i)*64 for i in range(9)]
        self.players = [s.profile(dict(name='Copa Jogador '+str(i),profileToken=t))
                        for i,t in enumerate(self.tokens)]
        for t in self.tokens:
            self.ok(t,'state')

    def tearDown(self):
        for p in self.players:
            s.PRESENCE.pop(p,None)
            s.PRESENCE_GAME.pop(p,None)
            s.MATCH_QUEUE.pop(p,None)
        s.BASE,s.DATABASE_URL = self.original
        self.temp.cleanup()

    def call(self,token,op,**payload):
        return s.social_action('/api/social/chess/'+op,
            dict(profileToken=token,**payload),time.monotonic())

    def ok(self,token,op,**payload):
        code,response=self.call(token,op,**payload)
        self.assertEqual(code,200,response)
        return response

    def create(self):
        result=self.ok(self.tokens[0],'cup-create')
        event=result['cup']['events'][0]
        self.assertEqual(event['count'],1)
        return event['id']

    def fill(self,event):
        for t in self.tokens[1:8]:
            self.ok(t,'cup-join',event=event)
        result=self.ok(self.tokens[0],'state')
        cup=next(x for x in result['cup']['events'] if x['id']==event)
        self.assertEqual(cup['round'],1)
        self.assertEqual(cup['status'],'playing')
        self.assertEqual(len(cup['pairs']),4)
        return cup

    def _raw(self,event):
        with s.database() as db:
            row=s.sql(db,"SELECT payload FROM chess_cups WHERE id=?",(event,)).fetchone()
        return json.loads(row[0])

    def _decide(self,event):
        e=self._raw(event)
        with s.database() as db:
            for p in e['pairs']:
                if p['winner']:
                    continue
                game=json.loads(s.sql(db,"SELECT payload FROM chess_matches WHERE id=?",
                                      (p['match'],)).fetchone()[0])
                winner=p['a']
                color=games.color(game,winner)
                games.finish(s,db,game,color,'checkmate')
        self.ok(self.tokens[0],'state')

    def test_eight_players_brackets_prize_and_idempotence(self):
        e=self.create()
        self.assertEqual(self.call(self.tokens[0],'cup-create')[0],409)
        self.assertEqual(self.call(self.tokens[0],'start',level='easy',minutes=0,nonce='a'*16)[0],409)
        self.assertEqual(self.call(self.tokens[0],'cup-join',event='invalid')[0],404)
        self.fill(e)
        games_seen=set()
        for round_num,expected in ((1,4),(2,2),(3,1)):
            cup=self._raw(e)
            self.assertEqual((cup['round'],len(cup['pairs'])),(round_num,expected))
            for p in cup['pairs']:
                self.assertNotIn(p['match'],games_seen)
                games_seen.add(p['match'])
                with s.database() as db:
                    g=json.loads(s.sql(db,"SELECT payload FROM chess_matches WHERE id=?",
                                       (p['match'],)).fetchone()[0])
                self.assertEqual(g['cup'],e)
                self.assertEqual(g['cup_round'],round_num)
                self.assertFalse(g['ranked'])
                self.assertEqual(g['minutes'],10)
                self.assertEqual(set(g['players'].values()),{p['a'],p['b']})
            self._decide(e)
        final=self._raw(e)
        self.assertEqual(final['status'],'finished')
        champion=final['champion']
        winning_index=self.players.index(champion)
        stats=self.ok(self.tokens[winning_index],'state')
        self.assertEqual(stats['profile']['coins'],100)
        self.assertEqual(stats['profile']['points'],1000)
        self.assertEqual(stats['profile']['cup_wins'],1)
        self.assertIn('pieces-champion',stats['shop']['owned'])
        self.assertIn('board-champion',stats['shop']['owned'])
        self.ok(self.tokens[winning_index],'shop-equip',item='pieces-champion')
        self.assertEqual(self.ok(self.tokens[winning_index],'state')['shop']['equipped']['pieces'],'pieces-champion')
        for _ in range(3):
            self.ok(self.tokens[winning_index],'state')
        self.assertEqual(self.ok(self.tokens[winning_index],'state')['profile']['coins'],100)
        with s.database() as db:
            self.assertEqual(s.sql(db,'SELECT COUNT(*) FROM chess_cup_champions').fetchone()[0],1)
        self.assertEqual(self.call(self.tokens[8],'cup-join',event=e)[0],409)

    def test_draw_creates_rematch_and_no_fake_results(self):
        e=self.create()
        self.fill(e)
        raw=self._raw(e)
        p=raw['pairs'][0]
        old=p['match']
        with s.database() as db:
            game=json.loads(s.sql(db,'SELECT payload FROM chess_matches WHERE id=?',
                                   (old,)).fetchone()[0])
            games.finish(s,db,game,None,'stalemate')
        self.ok(self.tokens[0],'state')
        new=self._raw(e)['pairs'][0]
        self.assertNotEqual(new['match'],old)
        self.assertEqual(new['draws'],1)
        self.assertEqual(new['winner'],None)
        self.assertEqual(self.call(self.tokens[8],'cup-cancel',event=e)[0],403)
        self.assertEqual(self.call(self.tokens[8],'cup-claim',event=e,winner=self.players[8])[0],404)
        self.assertEqual(self.call(self.tokens[8],'shop-buy',item='pieces-champion')[0],403)

    def test_leave_cancel_and_occupancy(self):
        e=self.create()
        self.ok(self.tokens[1],'cup-join',event=e)
        self.assertEqual(self.call(self.tokens[1],'queue',minutes=5)[0],409)
        self.assertEqual(self.call(self.tokens[1],'cup-cancel',event=e)[0],403)
        self.ok(self.tokens[1],'cup-leave',event=e)
        g=self.ok(self.tokens[1],'start',level='easy',minutes=0,nonce='b'*16)['match']
        self.assertEqual(g['mode'],'ai')
        self.ok(self.tokens[0],'cup-cancel',event=e)
        self.assertEqual(self._raw(e)['status'],'cancelled')

    def test_server_clock_forfeits_without_client_result(self):
        e=self.create()
        self.fill(e)
        p=self._raw(e)['pairs'][0]
        with s.database() as db:
            g=json.loads(s.sql(db,"SELECT payload FROM chess_matches WHERE id=?",
                              (p['match'],)).fetchone()[0])
            g['clock_at']=time.time()-700
            games.save(db,s.sql,g)
        self.ok(self.tokens[8],'state')
        self.assertIsNotNone(self._raw(e)['pairs'][0]['winner'])


if __name__=='__main__':
    unittest.main()
