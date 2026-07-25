# git_organ
A repository which "audiolises" as opposed to "visualises" a git repo of choice. Instead of seeing the shape of a git repo, you hear it.

## How the shape of a repo impacts the sounds you hear

The play head travels from the beginning of the git history.

- The time between commits impacts the spacing between notes.
- The size of the commit impacts its pitch. Maybe use the commit message as a proxy to avoid computing diffs.
- Parallel branches which merged as a result of a merge are separate instruments.
- Mayor contributors have their own instruments, all other contributors are one instrument.

## Architecture

1. The user passes a git url.
2. The program clones the git repo in a special way to get only the history and none of the files: `git clone --filter=blob:none --no-checkout <repo>`
3. Parse the repo history into a custom representation, a node-and-parent based data representation, which holds all the data from the git history needed to make the music.
4. make midi with mido module
5. play with pygame