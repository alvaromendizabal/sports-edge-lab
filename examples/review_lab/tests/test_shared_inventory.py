import hashlib
import json
from dataclasses import replace
import unittest
from examples.review_lab.shared_inventory import Federation, Request, Scope, digest, encoded, fixture, walkthrough


class SharedInventoryTests(unittest.TestCase):
    def catalog(self, mutate=None):
        request, scopes, objects = fixture()
        if mutate:
            old = scopes[0].object_hashes[0]
            data = json.loads(objects[old])
            mutate(data)
            raw = encoded(data)
            sha = hashlib.sha256(raw).hexdigest()
            objects = {sha: raw}
            scopes = tuple(replace(s, object_hashes=(sha,)) for s in scopes)
        return request, Federation(('football', 'basketball', 'march'), scopes, objects)

    def eligible(self, catalog, **changes):
        args = dict(provider='invented-provider', sport='invented-football', event='game-1', ordered_teams=('home-1', 'away-1'),
                    kickoff='2025-09-07T18:00:00Z', cutoff='2025-09-07T12:00:00Z', freshness_seconds=900)
        args.update(changes)
        return catalog.eligible(**args)

    def test_cross_project_and_semantic_duplicates_do_not_inflate_coverage(self):
        x = walkthrough()
        self.assertEqual((x['object_references'], x['unique_content_objects'], x['unique_requests'], x['unique_observations']), (3,2,1,1))
        self.assertEqual(x['duplicate_object_references'], 1)
        self.assertEqual(x['duplicate_observation_occurrences'], 1)
        self.assertEqual(x['eligible_observations'], 1)
        self.assertTrue(x['same_source_preserves_all_aliases'])
        self.assertEqual((x['actual_requests'], x['actual_credits'], x['model_fits']), (0,0,0))

    def test_missing_scope_never_becomes_absence(self):
        _, scopes, objects = fixture()
        with self.assertRaisesRegex(ValueError, 'every required'):
            Federation(('football','basketball','march'), scopes[:-1], objects)

    def test_unresolved_inventory_blocks(self):
        _, scopes, objects = fixture()
        with self.assertRaisesRegex(ValueError, 'unclassified'):
            Federation(('football','basketball','march'), (replace(scopes[0],unresolved_objects=1),*scopes[1:]), objects)

    def test_missing_object_blocks(self):
        _, scopes, objects = fixture()
        objects.pop(next(iter(objects)))
        with self.assertRaisesRegex(ValueError, 'exactly close'):
            Federation(('football','basketball','march'), scopes, objects)

    def test_content_tamper_blocks(self):
        _, scopes, objects = fixture()
        objects[next(iter(objects))] += b' '
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            Federation(('football','basketball','march'), scopes, objects)

    def test_capture_after_cutoff_does_not_forge_archived_forecast(self):
        _, catalog = self.catalog()
        self.assertEqual(len(self.eligible(catalog)),1)
        self.assertFalse(catalog.request_status(fixture()[0])['may_dispatch'])

    def test_after_cutoff_snapshot_excluded(self):
        _, catalog = self.catalog()
        self.assertEqual(self.eligible(catalog, cutoff='2025-09-07T11:59:30Z'),[])

    def test_stale_quote_excluded(self):
        _, catalog = self.catalog()
        self.assertEqual(self.eligible(catalog, freshness_seconds=30),[])

    def test_changed_team_kickoff_and_league_excluded(self):
        _, catalog = self.catalog()
        for changes in ({'ordered_teams':('away-1','home-1')},{'kickoff':'2025-09-07T18:05:00Z'},{'sport':'invented-basketball'}):
            self.assertEqual(self.eligible(catalog,**changes),[])

    def test_reuse_not_authorized_is_retained_but_not_admitted(self):
        request, catalog = self.catalog(lambda x:x['observations'][0].update(reuse_allowed=False))
        self.assertEqual(self.eligible(catalog),[])
        self.assertEqual(catalog.request_status(request)['status'],'CAPTURED')

    def test_captured_empty_response_still_blocks_duplicate(self):
        request, catalog = self.catalog(lambda x:x.update(observations=[]))
        self.assertEqual(self.eligible(catalog),[])
        self.assertEqual(catalog.request_status(request)['status'],'CAPTURED')

    def test_missing_request_is_scoped_and_not_authorized(self):
        request, catalog = self.catalog()
        result=catalog.request_status(replace(request,snapshot_at='2025-09-07T13:00:00Z'))
        self.assertEqual(result['status'],'NOT_FOUND_IN_DECLARED_SCOPES')
        self.assertFalse(result['may_dispatch'])

    def test_future_quote_rejected(self):
        with self.assertRaisesRegex(ValueError,'clocks'):
            self.catalog(lambda x:x['observations'][0].update(quote_at='2025-09-07T12:01:00Z'))

    def test_unknown_or_secret_fields_rejected(self):
        with self.assertRaisesRegex(ValueError,'unsupported normalized envelope'):
            self.catalog(lambda x:x.update(api_key='not-a-real-key'))

    def test_request_normalization_preserves_endpoint_identity(self):
        req=Request('provider','sport','endpoint','2025-01-01T01:00:00+01:00',('totals','h2h'),('us','eu'))
        equivalent=Request('provider','sport','endpoint','2025-01-01T00:00:00Z',('h2h','totals'),('eu','us'))
        self.assertEqual(req.identity,equivalent.identity)
        self.assertNotEqual(req.identity,replace(req,endpoint='another-endpoint').identity)

    def test_invalid_clocks_and_types_fail_closed(self):
        with self.assertRaises(ValueError): Request('provider','sport','endpoint','2025-01-01',('h2h',),('us',))
        _, catalog=self.catalog()
        for changes in ({'freshness_seconds':True},{'cutoff':'2025-09-07T18:00:00Z'}):
            with self.assertRaises(ValueError):self.eligible(catalog,**changes)

    def test_broader_captured_request_prevents_narrower_duplicate(self):
        request, catalog = self.catalog(lambda x:x['request'].update(markets=['totals','h2h']))
        self.assertEqual(catalog.request_status(request)['status'],'CAPTURED')
        self.assertNotEqual(catalog.request_status(request)['original_request_sha256s'],[request.identity])

    def test_conflicting_content_at_same_observation_coordinate_is_rejected(self):
        _, scopes, objects=fixture()
        old=scopes[-1].object_hashes[0]
        data=json.loads(objects.pop(old))
        data['observations'][0]['quote_sha256']=digest('different-paired-quote')
        raw=encoded(data); sha=hashlib.sha256(raw).hexdigest();objects[sha]=raw
        scopes=(*scopes[:-1],replace(scopes[-1],object_hashes=(sha,)))
        with self.assertRaisesRegex(ValueError,'conflicting quote'):
            Federation(('football','basketball','march'),scopes,objects)

    def test_distinct_binding_receipts_preserve_one_observation(self):
        _, scopes, objects=fixture()
        old=scopes[-1].object_hashes[0]
        data=json.loads(objects.pop(old))
        data['observations'][0]['binding_sha256']=digest('another-valid-binding-receipt')
        raw=encoded(data);sha=hashlib.sha256(raw).hexdigest();objects[sha]=raw
        scopes=(*scopes[:-1],replace(scopes[-1],object_hashes=(sha,)))
        catalog=Federation(('football','basketball','march'),scopes,objects)
        self.assertEqual(catalog.summary()['unique_observations'],1)
        self.assertEqual(len(self.eligible(catalog)[0]['binding_sha256s']),2)
