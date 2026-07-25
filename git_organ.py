import argparse
import logging
from pathlib import Path
from git import Repo
import os
import shutil
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

parser = argparse.ArgumentParser(description="Play a Git repository as music.")

parser.add_argument("--repo", help="Path to the Git repository, such as https://github.com/git/git.git.", default="https://github.com/git/git.git")
parser.add_argument("-n", help="Number of channels.", type=int, default=10)
parser.add_argument("-o",  type=Path, help="Path for output midi file.", default=Path("output.mid"),)

args = parser.parse_args()

logging.info(f"The repo being parsed is {args.repo}.")
logging.info(f"{args.n} instruments will be used.")
logging.info(f"The output midi file {args.o} will be generated.")

def get_repo_history(repo):
    Repo.clone_from(
        repo,
        Path("temp_repo"),
        multi_options=[
            "--filter=blob:none",
            "--no-checkout",
        ]
    )

#logging.info("Removing previous repos")
#try:
#    shutil.rmtree(Path("temp_repo"))
#except:
#    logging.info("No existing repo was present")

#logging.info("Grabbing git history")
#get_repo_history(args.repo)

logging.info("Processing git history")
max_message_length = -1
min_message_length = 100000
oldest = None
newest = None

authors = {}

repo = Repo(Path("temp_repo"))
for commit in repo.iter_commits():
    length = len(commit.message)
    max_message_length = max(max_message_length, length)
    min_message_length = min(min_message_length, length)
    commit_time = commit.committed_datetime
    oldest = min(oldest, commit_time)
    newest = min(newest, commit_time)
    author = commit.author.name
    try:
        authors[author] += 1
    except:
        authors[author] = 1


logging.info(f"Minimum message length was {min_message_length}")
logging.info(f"Maximum message length was {max_message_length}")

top_authors = sorted(
    authors.items(),
    key=lambda x: x[1],
    reverse=True
)[:args.n-1]
