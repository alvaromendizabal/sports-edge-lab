import unittest
from examples.fbs_contracts.phase_admission import admission, AdmissionRefused


class AdmissionEvidenceTests(unittest.TestCase):
    def test_refusal_is_durable_before_exception(self):
        saved=[]
        with self.assertRaises(AdmissionRefused) as context:
            admission(lambda:{'invented_capacity':2},lambda s:{'admitted':False,'reason':'CAPACITY'},
                      saved.append,max_observations=3,retry_reasons=('PRESSURE',))
        self.assertEqual(len(saved),1)
        self.assertEqual(context.exception.record,saved[0])

    def test_transient_reobservation_retains_chain(self):
        observations=iter([{'ready':False},{'ready':True}]); saved=[]
        result=admission(lambda:next(observations),
                         lambda s:{'admitted':s['ready'],'reason':'READY' if s['ready'] else 'PRESSURE'},
                         saved.append,max_observations=2,retry_reasons=('PRESSURE',))
        self.assertTrue(result['admitted'])
        self.assertEqual(saved[1]['previous_record_sha256'],saved[0]['sha256'])
        self.assertFalse(saved[0]['admitted'])

    def test_persistence_failure_never_returns_admission(self):
        def fail(record): raise OSError('invented read-only evidence destination')
        with self.assertRaises(OSError):
            admission(lambda:{},lambda s:{'admitted':True,'reason':'READY'},fail,max_observations=1)

    def test_persistent_pressure_is_bounded(self):
        saved=[]
        with self.assertRaises(AdmissionRefused):
            admission(lambda:{},lambda s:{'admitted':False,'reason':'PRESSURE'},saved.append,
                      max_observations=3,retry_reasons=('PRESSURE',))
        self.assertEqual(len(saved),3)

    def test_mutation_by_gate_does_not_erase_original(self):
        snapshot={'capacity':2}; saved=[]
        def decide(value):
            value['capacity']=200
            return {'admitted':True,'reason':'DEMONSTRATION_ONLY'}
        admission(lambda:snapshot,decide,saved.append,max_observations=1)
        self.assertEqual(snapshot,{'capacity':2})
        self.assertEqual(saved[0]['snapshot'],snapshot)

    def test_invalid_decision_is_not_truthy_admission(self):
        with self.assertRaises(ValueError):
            admission(lambda:{},lambda s:{'admitted':'yes','reason':'INVALID'},lambda x:None,max_observations=1)

if __name__=='__main__':unittest.main()
