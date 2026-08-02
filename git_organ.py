import argparse
import logging
from pathlib import Path
from git import Repo
import os
import shutil
from datetime import datetime, timezone
from mido import MidiFile, MidiTrack, Message

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
oldest = datetime.max.replace(tzinfo=timezone.utc)
newest = datetime.min.replace(tzinfo=timezone.utc)

authors = {}

repo = Repo(Path("temp_repo"))
for commit in repo.iter_commits():
    length = len(commit.message)
    max_message_length = max(max_message_length, length)
    min_message_length = min(min_message_length, length)
    commit_time = commit.committed_datetime
    oldest = min(oldest, commit_time)
    newest = max(newest, commit_time)
    author = commit.author.name
    try:
        authors[author] += 1
    except:
        authors[author] = 1

logging.info(f"Minimum message length was {min_message_length}")
logging.info(f"Maximum message length was {max_message_length}")
logging.info(f"The oldest commit is {oldest}")

top_authors = sorted(
    authors.items(),
    key=lambda x: x[1],
    reverse=True
)[:args.n-1]
top_authors = [entry[0] for entry in top_authors]

def map_to_track_id(author):
    index = args.n
    if author.name in top_authors:
        index = top_authors.index(author.name)
    return index   

# Create a new MIDI file
mid = MidiFile()

# Add the number of instruments wanted
# Plus one as a catch all
instruments = [0, 24, 32, 40, 48, 56, 73, 80]
for i in range(args.n+1):
    mid.tracks.append(MidiTrack())
    mid.tracks[i].append(Message('program_change', program=instruments[i%len(instruments)], channel=i, time=0))

track_counters = []
for _ in range(args.n+1):
    track_counters.append(0)

# MIDI note numbers for C major scale
notes = [60, 62, 64, 65, 67, 69, 71, 72, 71, 69, 67, 65, 64, 62, 60]
num_notes = len(notes)
length_unit = 10
timestep = 30

logging.info("Generating track")
hexsha = set()
tick = [repo.head.commit]
next_tick = []
ts = 0
while len(tick) > 0:
    # Go though steps.
    # For an example this needs to be recursive, for example:
    # A -> B -> C -> D -> G -> H -> I -> J
    #           \ -> E -> F         \ -> K
    # So the notes starting together are:
    # A, B, C, D+E, G+F, H, I, J+K
    for commit in tick:
        if commit.hexsha in hexsha:
            continue
        hexsha.add(commit.hexsha)

        author = commit.author
        track_i = map_to_track_id(author)

        commit_len = len(commit.message)
        normalized_len = (commit_len-min_message_length)/(1+max_message_length-min_message_length)
        scaled_len = round(length_unit * (normalized_len+1))

        note = track_counters[track_i]
        track_counters[track_i] = (track_counters[track_i] + 1) % num_notes

        mid.tracks[track_i].append(Message('note_on', note=notes[note], velocity=64, channel=track_i, time=ts))
        mid.tracks[track_i].append(Message('note_off', note=notes[note], velocity=64, channel=track_i, time=ts+scaled_len))
        print(ts, length_unit, scaled_len)
        next_tick += commit.parents

    ts += timestep
    tick = next_tick
    next_tick = []

logging.info("Saving track")
# Save the MIDI file
mid.save('song.mid')
logging.info("Done")
