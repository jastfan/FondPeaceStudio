import sys
import asyncio
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from build_gittrend_reel import build_instant_gittrend_reel

def main():
    parser = argparse.ArgumentParser(description="FondPeaceRepos — Daily GitHub Trending Video Generator")
    parser.add_argument("--repo", type=str, help="Specific GitHub repository (e.g. 'Panniantong/Agent-Reach')")
    parser.add_argument("--rank", type=int, default=1, help="Trending rank to generate video for (1-5, default: 1)")
    args = parser.parse_args()

    asyncio.run(build_instant_gittrend_reel(repo_target=args.repo, rank_target=args.rank))

if __name__ == "__main__":
    main()
