"""Admit a complete feature dependency graph at a timezone-aware cutoff.

This is a lineage contract, not a source-truth oracle or a forecasting model.
The executable example uses invented, deterministic metadata only.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Iterable


@dataclass(frozen=True)
class FeatureNode:
    key: str
    sha256: str
    kind: str
    available_at: str | None
    parents: tuple[str, ...] = ()
    latest_training_label_available_at: str | None = None


@dataclass(frozen=True)
class Admission:
    key: str
    admitted: bool
    reasons: tuple[str, ...]
    dependency_ids: tuple[str, ...]
    dependency_hashes: tuple[tuple[str, str], ...]


def _clock(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.utcoffset() is None:
        raise ValueError('timezone-aware timestamp required')
    return result.astimezone(timezone.utc)


def admit_features(nodes: Iterable[FeatureNode], selected: Iterable[str], *,
                   cutoff: str) -> tuple[Admission, ...]:
    """Fail closed per selected root; never silently substitute another feature.

    ``available_at`` is an asserted source-publication/availability clock, not
    retrieval time. Unknown provenance remains ineligible. Fitted nodes must
    declare their latest training-label availability, strictly before cutoff.
    The caller must verify hashes and clocks against authenticated originals.
    """
    boundary = _clock(cutoff)
    graph: dict[str, FeatureNode] = {}
    for node in nodes:
        if not isinstance(node, FeatureNode):
            raise ValueError('FeatureNode required')
        if not node.key or node.key in graph:
            raise ValueError('empty or duplicate node identity')
        if not re.fullmatch(r'[0-9a-f]{64}', node.sha256):
            raise ValueError('exact lowercase SHA-256 required')
        if node.kind not in {'observed', 'transform', 'fitted'}:
            raise ValueError('unknown node kind')
        if len(node.parents) != len(set(node.parents)):
            raise ValueError('duplicate parent identity')
        if node.kind == 'observed' and node.parents:
            raise ValueError('observed node cannot hide a dependency')
        if node.kind != 'fitted' and node.latest_training_label_available_at is not None:
            raise ValueError('training clocks belong to fitted nodes')
        for value in (node.available_at, node.latest_training_label_available_at):
            if value is not None:
                _clock(value)
        graph[node.key] = node
    requested = tuple(selected)
    if len(requested) != len(set(requested)):
        raise ValueError('duplicate selected feature')
    output = []
    for root in requested:
        reasons: set[str] = set()
        visited: set[str] = set()
        active: set[str] = set()

        def visit(key: str) -> None:
            if key in active:
                reasons.add(f'{key}:dependency_cycle')
                return
            if key in visited:
                return
            visited.add(key)
            node = graph.get(key)
            if node is None:
                reasons.add(f'{key}:missing_dependency')
                return
            active.add(key)
            if node.available_at is None:
                reasons.add(f'{key}:unknown_availability')
            elif _clock(node.available_at) > boundary:
                reasons.add(f'{key}:available_after_cutoff')
            if node.kind == 'fitted':
                if node.latest_training_label_available_at is None:
                    reasons.add(f'{key}:unknown_training_lineage')
                else:
                    latest = _clock(node.latest_training_label_available_at)
                    if latest >= boundary:
                        reasons.add(f'{key}:training_label_not_strictly_prior')
                    if node.available_at is not None and latest > _clock(node.available_at):
                        reasons.add(f'{key}:training_label_after_artifact_availability')
            for parent in node.parents:
                visit(parent)
                source = graph.get(parent)
                if (source is not None and source.available_at is not None
                        and node.available_at is not None
                        and _clock(source.available_at) > _clock(node.available_at)):
                    reasons.add(f'{key}:{parent}:parent_available_after_child')
            active.remove(key)

        visit(root)
        deps = tuple(sorted(visited))
        output.append(Admission(root, not reasons, tuple(sorted(reasons)), deps,
                                tuple((key, graph[key].sha256) for key in deps if key in graph)))
    return tuple(output)


def main() -> None:
    before = '2020-01-01T00:00:00Z'
    nodes = [FeatureNode('count', 'a' * 64, 'observed', before),
             FeatureNode('teacher', 'b' * 64, 'fitted', before),
             FeatureNode('derived', 'c' * 64, 'transform', before, ('teacher',)),
             FeatureNode('counts_only', 'd' * 64, 'transform', before, ('count',))]
    for result in admit_features(nodes, ('counts_only', 'derived'), cutoff='2020-01-02T00:00:00Z'):
        print(result.key, 'ADMITTED' if result.admitted else 'BLOCKED', result.reasons)


if __name__ == '__main__':
    main()
