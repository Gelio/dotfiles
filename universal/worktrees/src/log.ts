import { chalk } from 'zx';

export function die(msg: string): never {
  console.error(chalk.red(`Error: ${msg}`));
  process.exit(1);
}
export const warn = (msg: string): void => console.error(chalk.yellow(msg));
export const ok = (msg: string): void => console.log(chalk.green(msg));
