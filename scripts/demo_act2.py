from __future__ import annotations

import subprocess
import sys


def run(cmd: list[str]) -> None:
    print(f"\n>>> Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main() -> None:
    base = [sys.executable, '-m', 'agent.orchestrator']
    run(base + ['--company', 'Ramp', '--recipient', 'test@example.com'])
    run(base + ['--company', 'Ramp', '--reply', "Yes, let's talk next week", '--recipient', 'test@example.com', '--book'])
    run(base + ['--company', 'Clay', '--reply', 'Can you send a bit more detail first?', '--recipient', 'test@example.com'])
    run(base + ['--company', 'Retool', '--reply', 'Follow up next quarter please', '--recipient', 'test@example.com'])
    run(base + ['--company', 'Ramp', '--latency-batch', '20', '--recipient', 'test@example.com'])


if __name__ == '__main__':
    main()
