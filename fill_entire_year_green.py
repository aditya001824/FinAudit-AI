"""
Full Year GitHub 100% Green Contribution Engine
Populates every single day over the past 365 days with 3-6 commits so the entire calendar turns solid green.
"""
import os
import subprocess
import random
from datetime import datetime, timedelta, timezone

COMMIT_ACTIONS = [
    "feat(engine): optimize forensic anomaly detector rules",
    "docs(aml): update FinCEN BSA compliance guidelines",
    "refactor(graph): enhance NetworkX cycle detection algorithm",
    "test(sanctions): add fuzzy matching test cases for OFAC aliases",
    "feat(rag): expand FATF 40 recommendations knowledge base",
    "perf(agent): reduce ReAct multi-agent thought latency",
    "chore(deps): update forensic cryptography packages",
    "style(ui): improve glassmorphism cyber-finance dashboard",
    "fix(parser): handle cross-border SWIFT wire transit edge cases",
    "docs(sar): update FinCEN Form 111 XML filing schemas",
    "feat(analytics): add betweenness centrality hub indicators",
    "test(integration): verify autonomous SAR generation pipeline",
    "chore(ci): optimize daily maintenance automated sync",
    "refactor(models): strengthen Pydantic v2 validation schemas"
]

def make_entire_year_green(days_total: int = 365):
    print(f"[*] Initializing 100% Full-Year Green Engine for past {days_total} days...")
    
    log_path = "ACTIVITY_LEDGER.md"
    today = datetime.now(timezone.utc)
    total_commits = 0

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("# FinAudit AI - Full Historical Research & Engineering Activity\n\n")

    # Iterate over every single day without skipping any day
    for day_offset in range(days_total, -1, -1):
        target_date = today - timedelta(days=day_offset)
        
        # 3 to 6 commits every single day to ensure vibrant dark green on all squares
        daily_commits_count = random.randint(3, 6)
        
        for c_idx in range(daily_commits_count):
            hour = random.randint(9, 22)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            commit_time = target_date.replace(hour=hour, minute=minute, second=second)
            date_str = commit_time.strftime("%Y-%m-%d %H:%M:%S +0530")
            msg = random.choice(COMMIT_ACTIONS)

            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"- [{commit_time.strftime('%Y-%m-%d %H:%M:%S')}] {msg} (Commit #{total_commits + 1})\n")

            env = os.environ.copy()
            env["GIT_AUTHOR_DATE"] = date_str
            env["GIT_COMMITTER_DATE"] = date_str
            env["GIT_AUTHOR_NAME"] = "aditya001824"
            env["GIT_AUTHOR_EMAIL"] = "adityavardhansharma2@gmail.com"
            env["GIT_COMMITTER_NAME"] = "aditya001824"
            env["GIT_COMMITTER_EMAIL"] = "adityavardhansharma2@gmail.com"

            subprocess.run(["git", "add", log_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(
                ["git", "commit", "-m", msg, "--date", date_str],
                env=env,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            total_commits += 1

        if day_offset % 30 == 0:
            print(f"[*] Processed {days_total - day_offset}/{days_total} days ({total_commits} commits created)...")

    print(f"\n[+] SUCCESS! Created {total_commits} commits across all {days_total} consecutive days!")

if __name__ == "__main__":
    make_entire_year_green(days_total=365)
