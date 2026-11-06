"""Invented bytes only: none of these checks represents owner execution."""
import copy
from io import BytesIO
import json
import stat
import unittest
import zipfile
from parent_contract import authenticate, pin, prepare_reuse, read_source, write_source


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def fixture(identity_changes=None, extra=None, manifest_change=None, receipt_change=None):
    identity = dict(schema='demo.owner-return.v1', project='invented', run_id='carrier-A',
                    cycle='annual', fixture=True, package_sha256='a'*64, parent_package_sha256='b'*64)
    identity.update(identity_changes or {})
    files = {'IDENTITY.json': encoded(identity), 'study/result.json': b'{"fits":2}',
             'forward/selection.json': b'{"rule":"invented"}',
             'cover/orientation.json': b'{"condition":"invented-home"}'}
    files.update(extra or {})
    manifest = {n: pin(b) for n, b in files.items()}
    if manifest_change: manifest_change(manifest)
    files['MANIFEST.json'] = encoded(manifest)
    stream = BytesIO()
    with zipfile.ZipFile(stream, 'w') as zf:
        for name, body in files.items():
            info = zipfile.ZipInfo(name); info.external_attr = (stat.S_IFREG | 0o600) << 16
            zf.writestr(info, body)
    archive = stream.getvalue()
    receipt = dict(identity=identity, archive=pin(archive), manifest=pin(files['MANIFEST.json']),
                   packaged_at='2020-01-01T01:00:00+00:00', completed_at='2020-01-01T01:00:01+00:00')
    if receipt_change: receipt_change(receipt)
    completion = encoded(receipt)
    return [archive, identity, pin(archive), pin(files['MANIFEST.json']), completion, pin(completion)]


class ParentContractTests(unittest.TestCase):
    def setUp(self):
        self.args = fixture(); self.carrier = authenticate(*self.args)
        self.latest = dict(self.args[1], run_id='later-failed-B', schema='demo.owner-return.v2')
        self.selections = {role: {'carrier': dict(self.carrier.identity), 'members': {name: pin(self.carrier.members[name])}}
                           for role, name in [('completed_study','study/result.json'),
                                              ('fixed_forward','forward/selection.json'),
                                              ('cover_conditional','cover/orientation.json')]}

    def test_later_invocation_does_not_replace_scientific_carrier(self):
        p=prepare_reuse(self.carrier,self.latest,self.selections,b'original anchors')
        self.assertEqual(p['carrier']['run_id'],'carrier-A'); self.assertEqual(p['latest_invocation']['run_id'],'later-failed-B')
        self.assertEqual(len(p['roles']),3); self.assertEqual((p['new_native_fits'],p['new_forecasts']),(0,0))

    def test_original_anchors_preserved_byte_for_byte(self):
        raw=b'legacy label\noriginal issue clock\x00'
        self.assertEqual(prepare_reuse(self.carrier,self.latest,self.selections,raw)['original_anchors'],raw)

    def test_expected_full_identity_required(self):
        for field in self.args[1]:
            with self.subTest(field=field):
                args=copy.deepcopy(self.args);del args[1][field]
                with self.assertRaises(ValueError):authenticate(*args)

    def test_identity_schema_and_cycle_are_not_ignored(self):
        for field in ('schema','cycle','run_id','package_sha256','parent_package_sha256','project','fixture'):
            with self.subTest(field=field):
                args=copy.deepcopy(self.args);args[1][field]=False if field=='fixture' else ('c'*64 if 'sha256' in field else 'wrong')
                with self.assertRaises(ValueError):authenticate(*args)

    def test_wrong_physical_archive_or_manifest_rejected(self):
        for index in (2,3,5):
            args=copy.deepcopy(self.args);args[index]['sha256']='c'*64
            with self.subTest(index=index),self.assertRaises(ValueError):authenticate(*args)

    def test_missing_manifest_member_rejected(self):
        with self.assertRaises(ValueError):authenticate(*fixture(manifest_change=lambda m:m.pop('study/result.json')))

    def test_unlisted_manifest_member_rejected(self):
        with self.assertRaises(ValueError):authenticate(*fixture(manifest_change=lambda m:m.update({'absent':pin(b'')})))

    def test_payload_mismatch_rejected(self):
        with self.assertRaises(ValueError):authenticate(*fixture(manifest_change=lambda m:m.update({'study/result.json':pin(b'changed')})))

    def test_unsafe_member_rejected(self):
        for name in ('../outside','/absolute','x\\y','x//y','x/./y','C:drive'):
            with self.subTest(name=name),self.assertRaises(ValueError):authenticate(*fixture(extra={name:b'x'}))

    def test_receipt_cannot_bind_another_return(self):
        with self.assertRaises(ValueError):authenticate(*fixture(receipt_change=lambda r:r['archive'].update(sha256='d'*64)))

    def test_receipt_cannot_bind_another_identity(self):
        with self.assertRaises(ValueError):authenticate(*fixture(receipt_change=lambda r:r.update(identity=dict(r['identity'],cycle='wrong'))))

    def test_external_completion_must_be_later_and_timezone_aware(self):
        for clock in ('2020-01-01T01:00:00+00:00','2019-01-01T01:00:00+00:00','2020-01-01T01:00:01'):
            with self.subTest(clock=clock),self.assertRaises(ValueError):authenticate(*fixture(receipt_change=lambda r:r.update(completed_at=clock)))

    def test_all_three_domains_required(self):
        for role in self.selections:
            selected=copy.deepcopy(self.selections);del selected[role]
            with self.subTest(role=role),self.assertRaises(ValueError):prepare_reuse(self.carrier,self.latest,selected,b'a')

    def test_wrong_carrier_in_any_domain_rejected_before_return(self):
        for role in self.selections:
            selected=copy.deepcopy(self.selections);selected[role]['carrier']=self.latest
            with self.subTest(role=role),self.assertRaises(ValueError):prepare_reuse(self.carrier,self.latest,selected,b'a')

    def test_wrong_member_in_any_domain_rejected_before_return(self):
        for role in self.selections:
            selected=copy.deepcopy(self.selections);next(iter(selected[role]['members'].values()))['sha256']='f'*64
            with self.subTest(role=role),self.assertRaises(ValueError):prepare_reuse(self.carrier,self.latest,selected,b'a')

    def test_empty_or_missing_member_selection_rejected(self):
        for members in ({},{'not-present':pin(b'')},{'IDENTITY.json':pin(self.carrier.members['IDENTITY.json'])}):
            selected=copy.deepcopy(self.selections);selected['completed_study']['members']=members
            with self.subTest(members=list(members)),self.assertRaises(ValueError):prepare_reuse(self.carrier,self.latest,selected,b'a')

    def test_verified_result_cannot_be_mutated(self):
        with self.assertRaises(TypeError):self.carrier.identity['cycle']='changed'
        with self.assertRaises(TypeError):self.carrier.members['study/result.json']=b'changed'

    def test_versioned_source_round_trip_preserves_bytes(self):
        namespace={'version':'v-next','cycle':'future','role':'official-report'}
        self.assertEqual(read_source(write_source(namespace,b'invented source'),namespace),b'invented source')

    def test_stale_reader_or_wrong_role_is_rejected(self):
        namespace={'version':'v-next','cycle':'future','role':'official-report'}
        envelope=write_source(namespace,b'invented source')
        for field in namespace:
            with self.subTest(field=field),self.assertRaises(ValueError):read_source(envelope,dict(namespace,**{field:'old'}))

    def test_source_payload_tampering_is_rejected(self):
        namespace={'version':'v-next','cycle':'future','role':'official-report'}
        envelope=write_source(namespace,b'invented source');envelope['payload']=b'changed'
        with self.assertRaises(ValueError):read_source(envelope,namespace)

    def test_missing_namespace_field_is_rejected(self):
        with self.assertRaises(ValueError):write_source({'version':'v-next','role':'official-report'},b'x')


if __name__=='__main__':unittest.main()
