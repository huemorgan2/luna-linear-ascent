import tempfile
import unittest
from simulation.experiments import plan,run_study,VARIANTS


class ExperimentTests(unittest.TestCase):
    def test_single_factors_and_paired_settings(self):
        jobs=plan(dict(players=6,days=1),[31,32],list(VARIANTS))
        configs={x['variant']:x['config'] for x in jobs if x['seed']==31}
        expected={'decisions':['decision_model'],'starter':['recovery_mode'],'partial':['recovery_mode'],
            'repair':['repair_fraction'],'durability':['durability_scale'],'group':['group_hp_scale'],'healing':['heal_cost_scale']}
        for key,fields in expected.items():
            parent=VARIANTS[key]['parent']
            self.assertEqual([f for f in configs[key] if configs[key][f]!=configs[parent][f]],fields)
        with self.assertRaises(ValueError):plan({},[1,1],['original'])
        with self.assertRaises(ValueError):plan({},[1],['unknown'])

    def test_batch_persists_and_resume_does_not_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            config=dict(players=2,days=1,max_floor=3,workers=1,readiness_trials=4,warden_trials=1)
            a,path=run_study(config,[33],['audited','decisions'],directory=directory,run_directory=directory)
            b,_=run_study(resume=path,run_directory=directory)
            self.assertEqual(a,b)
            self.assertEqual(len(a['completed']),2)
            self.assertEqual(a['analysis']['variants']['decisions']['paired']['players'],2)
            self.assertEqual(a['status'],'complete')


if __name__=='__main__':unittest.main()
