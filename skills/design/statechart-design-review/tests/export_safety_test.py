"""Synthetic safety kernel, not a full statechart interpreter or production test."""
from dataclasses import dataclass, replace
from itertools import product

@dataclass(frozen=True)
class M:
    phase: str = 'Idle'
    online: bool = False
    rev: int = 1
    epoch: int = 0
    captured: int | None = None
    published: tuple | None = None
    revoked: frozenset = frozenset()

ACTIVE = frozenset({'AwaitingConnection', 'Reconciling', 'Running'})

def step(m, event):
    kind, *args = event
    if kind == 'EDIT':
        revoked = m.revoked | ({m.epoch} if m.phase in ACTIVE else set())
        return replace(m, rev=m.rev+1, published=None, revoked=frozenset(revoked),
                       phase='Superseded' if m.phase in ACTIVE or m.phase == 'Ready' else m.phase)
    if kind == 'CONNECT':
        return replace(m, online=True, phase='Reconciling' if m.phase == 'AwaitingConnection' else m.phase)
    if kind == 'DISCONNECT':
        return replace(m, online=False, phase='AwaitingConnection' if m.phase in ACTIVE else m.phase)
    if kind == 'REQUEST' and m.phase not in ACTIVE:
        return replace(m, epoch=m.epoch+1, captured=m.rev, published=None,
                       phase='Reconciling' if m.online else 'AwaitingConnection')
    if kind == 'CANCEL' and m.phase in ACTIVE:
        return replace(m, phase='Canceled', published=None, revoked=m.revoked | {m.epoch})
    if kind == 'FAILED' and m.phase in ACTIVE:
        return replace(m, phase='Failed', revoked=m.revoked | {m.epoch})
    if kind == 'PENDING' and m.phase == 'Reconciling':
        return replace(m, phase='Running')
    if kind == 'DONE':
        epoch, rev = args
        if m.phase in ACTIVE and m.online and epoch == m.epoch and epoch not in m.revoked and rev == m.captured == m.rev:
            return replace(m, phase='Ready', published=(epoch, rev))
    return m

def run(events):
    m = M()
    for event in events:
        m = step(m, event)
        assert m.published is None or (m.phase == 'Ready' and m.published[1] == m.rev and m.published[0] not in m.revoked)
    return m

C=('CONNECT',); D=('DISCONNECT',); R=('REQUEST',); E=('EDIT',); X=('CANCEL',)
A=('DONE',1,1); B=('DONE',2,1); N=('DONE',2,2)
cases = [
 ('default', [], 'Idle', None),
 ('success', [C,R,A], 'Ready', (1,1)),
 ('cancel_then_done', [C,R,X,A], 'Canceled', None),
 ('done_then_cancel', [C,R,A,X], 'Ready', (1,1)),
 ('edit_then_done', [C,R,E,A], 'Superseded', None),
 ('done_then_edit', [C,R,A,E], 'Superseded', None),
 ('offline_completion', [C,R,D,A], 'AwaitingConnection', None),
 ('reconnect_completion', [C,R,D,A,C,A], 'Ready', (1,1)),
 ('offline_edit_reconnect', [C,R,D,E,C,A], 'Superseded', None),
 ('retry_ignores_old', [C,R,X,R,A], 'Reconciling', None),
 ('retry_current', [C,R,X,R,A,B], 'Ready', (2,1)),
 ('retry_latest_revision', [C,R,E,R,A,N], 'Ready', (2,2)),
 ('duplicate_done', [C,R,A,A], 'Ready', (1,1)),
 ('failure_then_late', [C,R,('FAILED',),A], 'Failed', None),
]
for name, events, phase, published in cases:
    result = run(events)
    assert (result.phase, result.published) == (phase, published), (name, result)
print(f'{len(cases)} named safety traces passed')
alphabet = [C,D,R,E,X,A,B,N]
count=0
for events in product(alphabet, repeat=6):
    run(events)
    count += 1
print(f'{count} length-six event sequences passed the displayed-revision/revocation invariant')
print('Limits: reduced safety kernel only; no outbox, restart, network, timeouts, runtime semantics, or liveness checks')
