FROM python:3.5
RUN apt-get install -y libffi-dev
RUN apt-get install -y python3.5-dev
RUN apt-get install -y git
ADD requirements.txt /requirements.txt
RUN pip install --upgrade -r requirements.txt
RUN python3 -m pip install -U https://github.com/Rapptz/discord.py/archive/master.zip#egg=discord.py[voice]
ADD . /
CMD ["python", "bot.py"]
