# <p align="center">markov bot
  
<p align="center">
  a bot that writes like you do<br><br>
  <a href="https://heroku.com/deploy?template=https://github.com/joaorafaelm/markov-bot"><img src="https://www.herokucdn.com/deploy/button.svg"></a><br><br>
  <a href="https://travis-ci.org/joaorafaelm/markov-bot"><img src="https://travis-ci.org/joaorafaelm/markov-bot.svg?branch=master"></a>
  <a href="https://pyup.io/repos/github/joaorafaelm/markov-bot/"><img src="https://pyup.io/repos/github/joaorafaelm/markov-bot/shield.svg"></a>
  <a href="https://pyup.io/repos/github/joaorafaelm/markov-bot/"><img src="https://pyup.io/repos/github/joaorafaelm/markov-bot/python-3-shield.svg"></a>
  <hr/>
</p>

<p align="center">
  Add <a href="https://t.me/botijao_bot"><b>t.me/botijao_bot</b></a> to a telegram group chat and it will generate pseudo random sentences.
</p>
<hr>

### Running locally
#### 1. Download
```bash
$ git clone https://github.com/joaorafaelm/markov-bot
$ cd markov-bot
```
#### 2. Requirements
```bash
$ pipenv install --dev
```
#### 3. Env vars
In order to run the bot, you need to define the env var `TELEGRAM_TOKEN` (to generate a bot token follow [these instructions](https://core.telegram.org/bots#creating-a-new-bot)):
```bash
$ cp local.env .env
$ vim .env
```

#### 4. Run
After defining the variables, run:
```bash
$ pipenv run python markov.py
```
#### 5. Permissions
Disable the bot privacy settings (it means that the bot will receive all messages, not just the ones starting with "/") and run the command `/enable` to start collecting text.
Run `/sentence` (*or the command you defined using the env var `SENTENCE_COMMAND`*) to generate random sentences.
If you wish to delete the model, run `/remove`.

Have fun :)
