import { test } from 'node:test';
import assert from 'node:assert/strict';
import { computePorts, nextIndex } from '../src/ports.ts';

test('computePorts: base + index*step', () => {
  const cfg = { ports: { UI: 3003, SRV: 3004 }, portStep: 10 };
  assert.deepEqual(computePorts(cfg, 1), { UI: 3013, SRV: 3014 });
  assert.deepEqual(computePorts(cfg, 0), { UI: 3003, SRV: 3004 });
  assert.deepEqual(computePorts({}, 5), {});
});

test('nextIndex: max+1', () => {
  assert.equal(nextIndex(new Map()), 1);
  assert.equal(
    nextIndex(
      new Map([
        ['a', 1],
        ['b', 3],
      ]),
    ),
    4,
  );
});
