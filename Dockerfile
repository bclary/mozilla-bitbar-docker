FROM ubuntu:18.04@sha256:017eef0b616011647b269b5c65826e2e2ebddbe5d1f8c1e56b3599fb14fabec8

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y \
    curl \
    dnsutils \
    ffmpeg \
    gettext-base \
    git \
    lib32stdc++6 \
    lib32z1 \
    libavcodec-dev \
    libavformat-dev \
    libbz2-dev \
    libcurl4 \
    libcurl4-openssl-dev \
    libffi-dev \
    libgconf-2-4 \
    libgtk-3-0 \
    libopencv-dev \
    libpython-dev \
    libreadline-dev \
    libsqlite3-dev \
    libssl-dev \
    libswscale-dev \
    locales \
    net-tools \
    netcat \
    openjdk-8-jdk-headless \
    python \
    python-pip \
    python3 \
    python3-pip \
    sudo \
    tzdata \
    unzip \
    wget \
    xvfb \
    zip \
    zlib1g-dev \
    zstd && \
    apt-get clean all -y

RUN mkdir /builds && \
    useradd -d /builds/worker -s /bin/bash -m worker

# https://docs.docker.com/samples/library/ubuntu/#locales

WORKDIR /builds/worker
RUN localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8 && \
    mkdir -p \
        android-sdk-linux \
        Documents \
        Downloads \
        Pictures \
        Music \
        Videos \
        bin \
        .cache

# Set variables normally configured at login, by the shells parent process, these
# are taken from GNU su manual
# - PYTHONIOENCODING is set so that unicode characters can be output
#   - see https://bugzilla.mozilla.org/show_bug.cgi?id=1600833

ENV    HOME=/builds/worker \
       SHELL=/bin/bash \
       LANGUAGE=en_US.UTF-8 \
       LANG=en_US.UTF-8 \
       LC_ALL=en_US.UTF-8 \
       PYTHONIOENCODING=utf-8 \
       PATH=$PATH:/builds/worker/bin

# download things
ADD https://nodejs.org/dist/v8.11.3/node-v8.11.3-linux-x64.tar.gz /builds/worker/Downloads
ADD https://dl.google.com/android/android-sdk_r24.3.4-linux.tgz /builds/worker/Downloads
ADD https://dl.google.com/android/repository/sdk-tools-linux-4333796.zip /builds/worker/Downloads
ADD https://github.com/taskcluster/generic-worker/releases/download/v16.0.0/generic-worker-simple-linux-amd64 /usr/local/bin/generic-worker
ADD https://github.com/taskcluster/livelog/releases/download/v1.1.0/livelog-linux-amd64 /usr/local/bin/livelog
ADD https://github.com/taskcluster/taskcluster-proxy/releases/download/v5.1.0/taskcluster-proxy-linux-amd64 /usr/local/bin/taskcluster-proxy

# for testing builds (these lines mirror above), copy above artifacts from the downloads dir
# COPY downloads/node-v8.11.3-linux-x64.tar.gz /builds/worker/Downloads
# COPY downloads/android-sdk_r24.3.4-linux.tgz /builds/worker/Downloads
# COPY downloads/sdk-tools-linux-4333796.zip /builds/worker/Downloads
# COPY downloads/generic-worker-nativeEngine-linux-amd64 /usr/local/bin/generic-worker
# COPY downloads/livelog-linux-amd64 /usr/local/bin/livelog
# COPY downloads/taskcluster-proxy-linux-amd64 /usr/local/bin/taskcluster-proxy

# copy stackdriver credentials over
COPY stackdriver_credentials.json /etc/google/stackdriver_credentials.json

COPY .bashrc /root/.bashrc
COPY .bashrc /builds/worker/.bashrc
COPY version /builds/worker/version
COPY taskcluster /builds/taskcluster
COPY licenses /builds/worker/android-sdk-linux/licenses

# Add entrypoint script
COPY scripts/entrypoint.py /usr/local/bin/entrypoint.py
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY scripts/run_gw.py /usr/local/bin/run_gw.py
COPY scripts/tooltool.py /usr/local/bin/tooltool.py

# touch /root/.android/repositories.cfg to suppress warnings that is
# it missing during sdkmanager updates.

# chmod -R root:root /builds since we have to run this as root at
# bitbar. Changing ownership prevents user mismatches when caching pip
# installs.

RUN cd /tmp && \
    chmod +x /usr/local/bin/generic-worker && \
    chmod +x /usr/local/bin/livelog && \
    chmod +x /usr/local/bin/taskcluster-proxy && \
    chmod +x /usr/local/bin/tooltool.py && \
    chmod +x /usr/local/bin/entrypoint.* && \
    chmod +x /builds/taskcluster/script.py && \
    mkdir /root/.android && \
    touch /root/.android/repositories.cfg && \
    tar xzf /builds/worker/Downloads/node-v8.11.3-linux-x64.tar.gz -C /usr/local --strip-components 1 && \
    node -v && \
    npm -v && \
    tar xzf /builds/worker/Downloads/android-sdk_r24.3.4-linux.tgz --directory=/builds/worker || true && \
    unzip -qq -n /builds/worker/Downloads/sdk-tools-linux-4333796.zip -d /builds/worker/android-sdk-linux/ || true && \
    /builds/worker/android-sdk-linux/tools/bin/sdkmanager platform-tools "build-tools;28.0.3" && \
    # upgrade the builtin setuptools
    pip install setuptools -U && \
    pip3 install setuptools -U && \
    # pips used by scripts in this docker image
    pip install google-cloud-logging && \
    pip3 install google-cloud-logging && \
    pip install mozdevice==3.0.7 && \
    pip3 install mozdevice==3.0.7 && \
    # pips used by jobs
    pip install zstandard==0.11.1 && \
    pip3 install zstandard==0.11.1 && \
    # cleanup
    rm -rf /tmp/* && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /builds/worker/Downloads/* && \
    chown -R root:worker /builds && \
    chmod 775 /builds

ENTRYPOINT ["entrypoint.sh"]
USER worker
