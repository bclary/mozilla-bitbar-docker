# .bashrc

# Source global definitions
if [ -f /etc/bash.bashrc ]; then
        . /etc/bash.bashrc
fi

if [ -f /etc/profile ]; then
        . /etc/profile
fi

export ANDROID_HOME=/builds/worker/android-sdk-linux
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=${PATH}:/usr/local/bin:/builds/worker/android-sdk-linux/platform-tools:/builds/worker/android-sdk-linux/platform-tools/bin:/builds/worker/android-sdk-linux/tools:/builds/worker/android-sdk-linux/tools/bin:/builds/worker/android-sdk-linux/build-tools/27.0.3
# Work around broken libcurl3 minidump_stackwalk requirement.
export LD_LIBRARY_PATH=/builds/worker/LD_LIBRARY

# setup pyenv
export PYENV_ROOT=$HOME/.pyenv
export PATH=$PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH
if command -v pyenv 1>/dev/null 2>&1; then
  eval "$(pyenv init -)"
fi

# Set umask 0 so that a setuid adb will create world readable/writeable
# files while the process is running as the worker user.
umask 0
