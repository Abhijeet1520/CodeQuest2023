# CodeQuest 23 Python Submission Template

Use this repo as a starting point for your Python submissions to CodeQuest 23.


## Install dependencies
By default, any packages in `src/requirements.txt` will be installed. You may add any pip packages in that file.


## Changing the Dockerfile

You may make any changes you would like to the Dockerfile. However, there are a few requirements:
- Your final image should have a file at `/codequest/run.sh`. This will be your main executable. Whatever this file
prints will be taken as your bot's output and will be sent to the game server. Do not print logs or run other commands
in this file. It should only run your bot e.g. `python src/main.py`. If you need to install dependencies
make sure you do that somewhere else in your Dockerfile.
- Your final image needs to be Linux based. It also needs to have Python (>=3.9) and `socat` installed. These are
already provided in the Dockerfile in this repo so if you don't change them you'll be fine.