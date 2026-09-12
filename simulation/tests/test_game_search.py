import tempfile
import unittest
from simulation.game_search import candidates,rank,search


class SearchTests(unittest.TestCase):
    def test_grid_and_censored_ranking(self):
        self.assertEqual(len(candidates()),18)
        rows=[dict(candidate='lucky',metrics=dict(players=10,mean_floor=2,floor_days=20,median_floor=1),seed=1),
              dict(candidate='repeatable',metrics=dict(players=10,mean_floor=3,floor_days=19,median_floor=3),seed=1)]
        self.assertEqual(rank(rows)[0]['candidate'],'repeatable')

    def test_disjoint_seeds(self):
        with self.assertRaisesRegex(ValueError,'disjoint'):search(training_seeds=(1,),validation_seeds=(1,))

    def test_parallel_search_matches_serial_and_locks_training_winner(self):
        with tempfile.TemporaryDirectory() as folder:
            args=dict(screen_players=1,screen_days=1,training_seeds=(41,),validation_players=1,validation_days=1,
                      validation_seeds=(42,),finalists=1,directory=folder,run_directory=folder+'/runs',grid=candidates()[:2],progress=None)
            a,_=search(workers=1,**args);b,path=search(workers=2,**args)
            self.assertEqual(a['ranking'],b['ranking']);self.assertEqual(a['validation'],b['validation'])
            self.assertEqual([t['deterministic_sha256'] for t in a['trials']],[t['deterministic_sha256'] for t in b['trials']])
            self.assertEqual(b['winner'],b['ranking'][0]['candidate']);self.assertEqual(b['status'],'complete')
            self.assertTrue(path.is_file());self.assertEqual(len(b['trials']),6)
