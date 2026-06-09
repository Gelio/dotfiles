import * as fsp from 'node:fs/promises';
import * as path from 'node:path';
import type { WorktreesConfig, ResolvedWorktreesConfig } from './types.ts';

export function portRegistryPath(repo: string): string {
  return path.join(repo, 'worktrees', '.port-registry');
}

/** Read `<repo>/worktrees/.port-registry` (lines `name:index`) into a Map. */
export async function readPortRegistry(repo: string): Promise<Map<string, number>> {
  const m = new Map<string, number>();
  let text: string;
  try {
    text = await fsp.readFile(portRegistryPath(repo), 'utf8');
  } catch {
    return m;
  }
  for (const line of text.split('\n')) {
    if (!line.trim()) continue;
    const [name, idx] = line.split(':');
    m.set(name, Number(idx));
  }
  return m;
}

export function nextIndex(reg: Map<string, number>): number {
  let max = 0;
  for (const v of reg.values()) if (v > max) max = v;
  return max + 1;
}

export async function appendPortRegistry(repo: string, name: string, idx: number): Promise<void> {
  const p = portRegistryPath(repo);
  await fsp.mkdir(path.dirname(p), { recursive: true });
  await fsp.appendFile(p, `${name}:${idx}\n`);
}

export async function removePortRegistryEntry(repo: string, name: string): Promise<void> {
  const p = portRegistryPath(repo);
  let text: string;
  try {
    text = await fsp.readFile(p, 'utf8');
  } catch {
    return;
  }
  const kept = text
    .split('\n')
    .filter(Boolean)
    .filter((l) => l.split(':')[0] !== name);
  await fsp.writeFile(p, kept.length ? kept.join('\n') + '\n' : '');
}

export function computePorts(
  config: ResolvedWorktreesConfig,
  index: number,
): Record<string, number> {
  const step = config.portStep;
  const out: Record<string, number> = {};
  for (const [name, base] of Object.entries(config.ports ?? {})) out[name] = base + index * step;
  return out;
}

export function hasPorts(config: WorktreesConfig): boolean {
  return !!config.ports && Object.keys(config.ports).length > 0;
}
