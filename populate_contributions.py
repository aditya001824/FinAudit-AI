"""
GitHub Contribution Graph Generator
Generates backdated commits across past days to illuminate the GitHub contribution graph with active commits.
"""
import os
import subprocess
import random
from datetime import datetime, timedelta, timezone

COMMIT_MESSAGES = [
    "docs: update AML forensic typology guidelines",
    "refactor: optimize NetworkX graph traversal speed",
    "fix: refine fuzzy sanctions matching threshold for aliases",
    "feat: add FATF recommendation 16 wire transit validation",
    "chore: sync OFAC SDN watchlist dataset definitions",
    "test: add unit tests for structuring anomaly detection engine",
    "docs: update SAR Form 111 XML schema references",
    "perf: improve ReAct agent multi-step reasoning response latency",
    "feat: add betweenness centrality hub detection",
    "style: enhance war room cyber-finance dark theme UI",
    "chore: update FinCEN red flag indicators catalog",
    "refactor: modularize regulatory RAG corpus search",
    "test: verify circular round-trip wash trading heuristics",
    "docs: clarify BSA anti-structuring statutory authorities",
    "feat: expand high-risk offshore jurisdiction definitions",
    "fix: handle zero-amount edge cases in flow reconstructor",
    "chore: optimize docker-compose build caching",
    "perf: stream SSE agent thought tokens asynchronously"
]

def generate_contributions(days_back: int = 180):
    print(f"[*] Starting GitHub Contribution Generation across past {days_back} days...")
    
    log_file = "HISTORY.md"
    today = datetime.now(timezone.utc)
    total_commits = 0

    with open(log_file, "w", encoding="utf-8") as f:
        f.write("# FinAudit AI - Research & Engineering Activity History\n\n")

    for day_offset in range(days_back, -1, -1):
        target_date = today - timedelta(days=day_offset)
        
        # 88% chance of activity on any given day for high density
        if random.random() > 0.12:
            # 1 to 4 commits per active day
            num_commits = random.choices([1, 2, 3, 4], weights=[25, 40, 25, 10])[0]
            
            for c_idx in range(num_commits):
                hour = random.randint(9, 21)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                commit_time = target_date.replace(hour=hour, minute=minute, second=second)
                date_str = commit_time.strftime("%Y-%m-%d %H:%M:%S +0530")
                iso_date = commit_time.isoformat()

                msg = random.choice(COMMIT_MESSAGES)
                
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"- [{commit_time.strftime('%Y-%m-%d %H:%M')}] {msg}\n")

                # Environment with git author & committer dates
                env = os.environ.copy()
                env["GIT_AUTHOR_DATE"] = date_str
                env["GIT_COMMITTER_DATE"] = date_str
                env["GIT_AUTHOR_NAME"] = "aditya001824"
                env["GIT_AUTHOR_EMAIL"] = "adityavardhansharma2@gmail.com"
                env["GIT_COMMITTER_NAME"] = "aditya001824"
                env["GIT_COMMITTER_EMAIL"] = "adityavardhansharma2@gmail.com"

                # Stage and commit
                subprocess.run(["git", "add", log_file], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(
                    ["git", "commit", "-m", msg, "--date", date_str],
                    env=env,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                total_commits += 1

    print(f"[+] Successfully generated {total_commits} commits across {days_back} days!")

if __name__ == "__main__":
    generate_contributions(days_back=180)
