import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { sandbox } from './helpers.ts';
import { mergeSymlink } from '../src/symlinks.ts';

test('mergeSymlink: links new, recurses real dirs, preserves real files', async () => {
  const { root } = sandbox();
  const src = path.join(root, 'src');
  const dst = path.join(root, 'dst');
  fs.mkdirSync(path.join(src, 'sub'), { recursive: true });
  fs.writeFileSync(path.join(src, 'a.txt'), 'a');
  fs.writeFileSync(path.join(src, 'sub', 'b.txt'), 'b');
  fs.mkdirSync(path.join(dst, 'sub'), { recursive: true });
  fs.writeFileSync(path.join(dst, 'sub', 'b.txt'), 'local'); // real file preserved
  const skipped: string[] = [];
  await mergeSymlink(src, dst, skipped);
  assert.equal(fs.lstatSync(path.join(dst, 'a.txt')).isSymbolicLink(), true);
  assert.equal(fs.lstatSync(path.join(dst, 'sub', 'b.txt')).isSymbolicLink(), false);
  assert.equal(fs.readFileSync(path.join(dst, 'sub', 'b.txt'), 'utf8'), 'local');
  assert.deepEqual(skipped, [path.join(dst, 'sub', 'b.txt')]);
});
