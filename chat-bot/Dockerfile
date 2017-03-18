FROM cookkkie/ffmpeg
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y libffi-dev
RUN apt-get install -y git
WORKDIR /
ADD requirements.txt /requirements.txt
RUN pip install --upgrade -r requirements.txt
RUN python3 -m pip install -U https://github.com/rapptz/discord.py/archive/async.zip#egg=discord.py[voice]
ADD . /
CMD ["python", "bot.py"]
