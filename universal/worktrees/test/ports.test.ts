import { test } from 'node:test';
import assert from 'node:assert/strict';
import { computePorts, nextIndex } from '../src/ports.ts';
import { resolveConfig } from '../src/config.ts';

test('computePorts: base + index*step', () => {
  const cfg = { ports: { UI: 3003, SRV: 3004 }, portStep: 10 };
  assert.deepEqual(computePorts(cfg, 1), { UI: 3013, SRV: 3014 });
  assert.deepEqual(computePorts(cfg, 0), { UI: 3003, SRV: 3004 });
  assert.deepEqual(computePorts({ portStep: 10 }, 5), {});
});

test('resolveConfig: applies default portStep and preserves explicit', () => {
  assert.equal(resolveConfig({}).portStep, 10);
  assert.equal(resolveConfig({ portStep: 25 }).portStep, 25);
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
