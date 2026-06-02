import * as readline from 'node:readline/promises';

/**
 * Prompt on stdin/stdout, returning the answer as typed. Uses
 * node:readline/promises rather than zx's `question` because the latter does
 * not read piped (non-TTY) stdin — it reads one line then hangs. readline
 * works under both interactive TTY and piped stdin (tests pipe answers).
 */
export async function ask(prompt: string): Promise<string> {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  try {
    return await rl.question(prompt);
  } finally {
    rl.close();
  }
}
