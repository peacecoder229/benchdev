#!/bin/bash

python_int="python3"
if command -v python3 &>/dev/null; then
   python_int="python3"
elif command -v python2 &>/dev/null; then
   python_int="python2"
elif command -v python &>/dev/null; then
   python_int="python"
else
   echo "Unable to find valid python on the system, please install python and retry the dcsomc tool installation"
   exit
fi

CHECK_PIPVERSION="${python_int} -m pip --version 2>&1"
PIP_VERSION=$(eval $CHECK_PIPVERSION)
NOT_FOUND="No module"
if [[ "$PIP_VERSION" == *"$NOT_FOUND"* ]]; then
  wget https://bootstrap.pypa.io/get-pip.py
  python_int=python
  $python_int get-pip.py
  rm -rf get-pip.py
fi

# check python version
CHECK_PYTHONVERSION="${python_int} --version"
PYTHONVERSION=$(eval $CHECK_PYTHONVERSION)
PYTHON38="Python 3.8"
PYTHON39="Python 3.9"
PYTHONDEVEL="python3-devel"
PYTHONDEV="python3-dev"
if [[ $PYTHONVERSION =~ $PYTHON38 ]]; then
  PYTHONDEVEL="python38-devel"
  PYTHONDEV="python38-dev"
elif [[ $PYTHONVERSION =~ $PYTHON39 ]]; then
  PYTHONDEVEL="python39-devel"
  PYTHONDEV="python39-dev"
fi

YUM_CMD=$(which yum)
DNF_CMD=$(which dnf)
APT_GET_CMD=$(which apt-get)
APT_CMD=$(which apt)

if [[ ! -z $YUM_CMD ]]; then
  yum install sshpass -y
  yum install rsync -y
  yum install $PYTHONDEVEL -y
  yum install sysstat -y
elif [[ ! -z $DNF_CMD ]]; then
  dnf install sshpass -y
  dnf install rysnc -y
  dnf install $PYTHONDEVEL -y
  dnf install sysstat -y
elif [[ ! -z $APT_GET_CMD ]] || [[ ! -z $APT_CMD ]]; then
  apt-get install sshpass -y
  apt-get install rsync -y
  apt-get install $PYTHONDEV -y
  apt-get install sysstat -y
else
  echo "Failed to install required sshpass, python dev packages. Please install them manually"
  exit 1;
fi

$python_int -m pip install -U psutil termcolor requests pgrep
$python_int -m pip install 'easysettings==3.3.3'

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

addtopath () {
  if ! echo "$PATH" | /bin/grep -Eq "(^|:)$1($|:)" ; then
      if [ "$2" = "after" ] ; then
        echo 'export PATH=$PATH:'$1 >> ~/.bashrc
      else
        echo 'export PATH='$1':$PATH' >> ~/.bashrc
      fi
  fi
}
pushd $DIR

TMC_BIN=tmc
cat << 'EOF' > $TMC_BIN
#!/bin/bash
set -e
ssh-keygen -R dcsometrics.intel.com
totally_loaded_sep_kernel_drivers="$(lsmod | awk '{print $1}' | grep sepint | wc -l)"
set -o pipefail
EMONDIR="/opt/intel/sep/sepdk/src"
if (( $totally_loaded_sep_kernel_drivers < 1 )); then
    if [ -d "$EMONDIR" ]; then
      echo "Looks like sepint & socperf driver not loaded...."
      pushd $EMONDIR && ./insmod-sep
      popd
    else
      echo "Looks like emon not installed on the platform.. If you have emon installed in custom path please update the EMONDIR var in tmc script file in dcsomc installation dir"
    fi
fi

totally_loaded_sep_kernel_drivers=$(lsmod | grep sepint | wc -l)
if (( $totally_loaded_sep_kernel_drivers < 1 )); then
    echo "Looks like sepint & socperf driver not loaded....Try loading them manually..."
    exit
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
EOF
echo "$python_int \$DIR/tmc.py \"\$@\"" >> $TMC_BIN
chmod +x $TMC_BIN

DCSOMC_BIN=dcsomc
cat << 'EOF' > $DCSOMC_BIN
#!/bin/bash
ssh-keygen -R dcsometrics.intel.com
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
EOF
echo "$python_int \$DIR/dcsomc.py \"\$@\"" >> $DCSOMC_BIN
chmod +x $DCSOMC_BIN

popd

addtopath $DIR

echo "PATH updated with emon collectors, just restart session or run . ~/.bashrc to start using dcsomc or tmc tool"
