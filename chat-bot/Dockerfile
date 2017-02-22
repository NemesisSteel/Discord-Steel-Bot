FROM python:3.5

ENV DEBIAN_FRONTEND noninteractive
# Update and install minimal.
RUN \
  apt-get update \
            --quiet \
  && apt-get install \ 
            --yes \
            --no-install-recommends \
            --no-install-suggests \
        autoconf \
        automake \
        build-essential \
        ca-certificates \
        git-core \
        libass-dev \
        libgpac-dev \
        libtheora-dev \
        libtool \
        libvorbis-dev \
        pkg-config \
        python-minimal \
        texi2html \
        zlib1g-dev \
	openssl \
	libssl-dev \
	libmp3lame-dev \
# Clean up packages.
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Prepare for cloning/building.
## Yasm
RUN git clone git://github.com/yasm/yasm.git \
    && cd yasm \
    && ./autogen.sh \
    && ./configure \
    && make -j`getconf _NPROCESSORS_ONLN` \
    && make install \
    && make distclean \
    && cd /tmp \
    && rm -rf /tmp/yasm
## libopus
RUN git clone git://git.opus-codec.org/opus.git \
    && cd opus \
    && ./autogen.sh \

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y libffi-dev
RUN apt-get install -y git
ADD requirements.txt /requirements.txt
RUN pip install --upgrade -r requirements.txt
RUN python3 -m pip install -U https://github.com/Rapptz/discord.py/archive/master.zip#egg=discord.py[voice]
ADD . /
CMD ["python", "bot.py"]
