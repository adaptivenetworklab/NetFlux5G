#!/usr/bin/env bash

# Mininet install script for Ubuntu (and Debian Wheezy+)
# Brandon Heller (brandonh@stanford.edu)

# Fail on error
set -e

# Fail on unset var usage
set -o nounset

# Get directory containing mininet folder
MININET_DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd -P )"

# Set up build directory, which by default is the working directory
#  unless the working directory is a subdirectory of mininet,
#  in which case we use the directory containing mininet
BUILD_DIR="$(pwd -P)"
case $BUILD_DIR in
  $MININET_DIR/*) BUILD_DIR=$MININET_DIR;; # currect directory is a subdirectory
  *) BUILD_DIR=$BUILD_DIR;;
esac

# Location of CONFIG_NET_NS-enabled kernel(s)
KERNEL_LOC=http://www.openflow.org/downloads/mininet

# Attempt to identify Linux release

DIST=Unknown
RELEASE=Unknown
CODENAME=Unknown
ARCH=`uname -m`
if [ "$ARCH" = "x86_64" ]; then ARCH="amd64"; fi
if [ "$ARCH" = "i686" ]; then ARCH="i386"; fi

test -e /etc/debian_version && DIST="Debian"
grep Ubuntu /etc/lsb-release &> /dev/null && DIST="Ubuntu"
if [ "$DIST" = "Ubuntu" ] || [ "$DIST" = "Debian" ]; then
    # Truly non-interactive apt-get installation
    install='sudo DEBIAN_FRONTEND=noninteractive apt-get -y -q install'
    remove='sudo DEBIAN_FRONTEND=noninteractive apt-get -y -q remove'
    pkginst='sudo dpkg -i'
    update='sudo apt-get'
    # Prereqs for this script
    if ! which lsb_release &> /dev/null; then
        $install lsb-release
    fi
fi
test -e /etc/fedora-release && DIST="Fedora"
test -e /etc/redhat-release && DIST="RedHatEnterpriseServer"
test -e /etc/centos-release && DIST="CentOS"

if [ "$DIST" = "Fedora" -o "$DIST" = "RedHatEnterpriseServer" -o "$DIST" = "CentOS" ]; then
    install='sudo yum -y install'
    remove='sudo yum -y erase'
    pkginst='sudo rpm -ivh'
    update='sudo yum'
    # Prereqs for this script
    if ! which lsb_release &> /dev/null; then
        $install redhat-lsb-core
    fi
fi
test -e /etc/SuSE-release && DIST="SUSE Linux"
if [ "$DIST" = "SUSE Linux" ]; then
    install='sudo zypper --non-interactive install '
    remove='sudo zypper --non-interactive  remove '
    pkginst='sudo rpm -ivh'
    # Prereqs for this script
    if ! which lsb_release &> /dev/null; then
		$install openSUSE-release
    fi
fi
if which lsb_release &> /dev/null; then
    DIST=`lsb_release -is`
    RELEASE=`lsb_release -rs`
    CODENAME=`lsb_release -cs`
fi
echo "Detected Linux distribution: $DIST $RELEASE $CODENAME $ARCH"

# Kernel params

KERNEL_NAME=`uname -r`
KERNEL_HEADERS=kernel-headers-${KERNEL_NAME}

# Treat Raspbian as Debian
[ "$DIST" = 'Raspbian' ] && DIST='Debian'

DISTS='Ubuntu|Debian|Fedora|RedHatEnterpriseServer|SUSE LINUX|CentOS'
if ! echo $DIST | egrep "$DISTS" >/dev/null; then
    echo "Install.sh currently only supports $DISTS."
    exit 1
fi

# More distribution info
DIST_LC=`echo $DIST | tr [A-Z] [a-z]` # as lower case


# Determine whether version $1 >= version $2
# usage: if version_ge 1.20 1.2.3; then echo "true!"; fi
function version_ge {
    # sort -V sorts by *version number*
    latest=`printf "$1\n$2" | sort -V | tail -1`
    # If $1 is latest version, then $1 >= $2
    [ "$1" == "$latest" ]
}

# Attempt to detect Python version
PYTHON=${PYTHON:-python}
PRINTVERSION='import sys; print(sys.version_info)'
PYTHON_VERSION=unknown
for python in $PYTHON python2 python3; do
    if $python -c "$PRINTVERSION" |& grep 'major=2'; then
        PYTHON=$python; PYTHON_VERSION=2; PYPKG=python
        break
    elif $python -c "$PRINTVERSION" |& grep 'major=3'; then
        PYTHON=$python; PYTHON_VERSION=3; PYPKG=python3
        break
    fi
done
if [ "$PYTHON_VERSION" == unknown ]; then
    echo "Can't find a working python command ('$PYTHON' doesn't work.)"
    echo "You may wish to export PYTHON or install a working 'python'."
    exit 1
fi

echo "Detected Python (${PYTHON}) version ${PYTHON_VERSION}"

# Kernel Deb pkg to be removed:
KERNEL_IMAGE_OLD=linux-image-2.6.26-33-generic

DRIVERS_DIR=/lib/modules/${KERNEL_NAME}/kernel/drivers/net

OVS_RELEASE=1.4.0
OVS_PACKAGE_LOC=https://github.com/downloads/mininet/mininet
OVS_BUILDSUFFIX=-ignore # was -2
OVS_PACKAGE_NAME=ovs-$OVS_RELEASE-core-$DIST_LC-$RELEASE-$ARCH$OVS_BUILDSUFFIX.tar
OVS_TAG=v$OVS_RELEASE

OF13_SWITCH_REV=${OF13_SWITCH_REV:-""}

function pre_build {
    cd $BUILD_DIR
    rm -rf openflow oflops ofsoftswitch13 loxigen ivs ryu noxcore nox13oflib
}

function kernel {
    echo "Install Mininet-compatible kernel if necessary"
    # yum_update='sudo yum -y update'
    # apt_update='sudo apt-get update'
    # if [ "$DIST" = "Fedora" -o "$DIST" = "RedHatEnterpriseServer" -o "$DIST" = "CentOS" ]; then
    #     $yum_update
    # else
    #     $apt_update
    # fi
    $update update
    if ! $install linux-image-$KERNEL_NAME; then
        echo "Could not install linux-image-$KERNEL_NAME"
        echo "Skipping - assuming installed kernel is OK."
    fi
}

function kernel_clean {
    echo "Cleaning kernel..."

    # To save disk space, remove previous kernel
    if ! $remove $KERNEL_IMAGE_OLD; then
        echo $KERNEL_IMAGE_OLD not installed.
    fi

    # Also remove downloaded packages:
    rm -f $HOME/linux-headers-* $HOME/linux-image-*
}

# Install Mininet-WiFi deps
function mn_wifi_deps {
    echo "Installing Mininet/Mininet-WiFi dependencies"
    echo "Installing Mininet-WiFi core"
    pushd $MININET_DIR/containernet
    if [ -d mininet-wifi ]; then
      echo "Removing Mininet-WiFi dir..."
      rm -r mininet-wifi
    fi
    sudo git clone https://github.com/intrig-unicamp/mininet-wifi.git
    cd mininet-wifi
    sudo git checkout 69c6251
    cd ..
    pushd $MININET_DIR/containernet/mininet-wifi
    sudo util/install.sh -Wlnfv6
    sudo PYTHON=${PYTHON} make install
    popd

    $install aptitude apt-transport-https ca-certificates curl build-essential software-properties-common gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
         "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
         sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    $update update
    $install docker-ce
    if [ "$DIST" = "Ubuntu" ] &&  [ `expr $RELEASE '>=' 24.04` = "1" ]; then
 	 sudo PYTHON=${PYTHON} pip install docker python-iptables --break-system-packages
    else
 	 sudo PYTHON=${PYTHON} pip install docker python-iptables
    fi

    pushd $MININET_DIR/containernet
    sudo PYTHON=${PYTHON} make install
    popd
}

# Install Mininet developer dependencies
function mn_dev {
    echo "Installing Mininet developer dependencies"
    $install doxygen doxypy texlive-fonts-recommended
    if ! $install doxygen-latex; then
        echo "doxygen-latex not needed"
    fi
}

# The following will cause a full OF install, covering:
# -user switch
# The instructions below are an abbreviated version from
# http://www.openflowswitch.org/wk/index.php/Debian_Install
function of {
    echo "Installing OpenFlow reference implementation..."
    cd $BUILD_DIR
    $install autoconf automake libtool make gcc patch
    if [ "$DIST" = "Fedora" ]; then
        $install git pkgconfig glibc-devel
    else
        $install git-core autotools-dev pkg-config libc6-dev
    fi
    git clone --depth=1 https://github.com/mininet/openflow
    cd $BUILD_DIR/openflow

    # Patch controller to handle more than 16 switches
    patch -p1 < $MININET_DIR/mininet-wifi/util/openflow-patches/controller.patch

    # Resume the install:
    ./boot.sh
    ./configure
    make
    sudo make install
    cd $BUILD_DIR
}

function of13 {
    echo "Installing OpenFlow 1.3 soft switch implementation..."
    cd $BUILD_DIR/
    $install  git-core autoconf automake autotools-dev pkg-config \
        make gcc g++ libtool libc6-dev cmake libpcap-dev libxerces-c3-dev  \
        unzip libpcre3-dev flex bison libboost-dev

    if [ ! -d "ofsoftswitch13" ]; then
        if [[ -n "$OF13_SWITCH_REV" ]]; then
            git clone https://github.com/CPqD/ofsoftswitch13.git
            cd ofsoftswitch13
            git checkout ${OF13_SWITCH_REV}
            cd ..
        else
            git clone --depth=1 https://github.com/CPqD/ofsoftswitch13.git
        fi
    fi

    # Install netbee
    NBEEDIR="netbee"
    git clone https://github.com/netgroup-polito/netbee.git
    cd ${NBEEDIR}/src
    cmake .
    make

    cd $BUILD_DIR/
    sudo cp ${NBEEDIR}/bin/libn*.so /usr/local/lib
    sudo ldconfig
    sudo cp -R ${NBEEDIR}/include/ /usr/

    # Resume the install:
    cd $BUILD_DIR/ofsoftswitch13
    ./boot.sh
    ./configure
    make
    sudo make install
    cd $BUILD_DIR
}


# Install Open vSwitch specific version Ubuntu package
function ubuntuOvs {
    echo "Creating and Installing Open vSwitch packages..."

    OVS_SRC=$BUILD_DIR/openvswitch
    OVS_TARBALL_LOC=http://openvswitch.org/releases

    if ! echo "$DIST" | egrep "Ubuntu|Debian" > /dev/null; then
        echo "OS must be Ubuntu or Debian"
        $cd BUILD_DIR
        return
    fi
    if [ "$DIST" = "Ubuntu" ] && ! version_ge $RELEASE 12.04; then
        echo "Ubuntu version must be >= 12.04"
        cd $BUILD_DIR
        return
    fi
    if [ "$DIST" = "Debian" ] && ! version_ge $RELEASE 7.0; then
        echo "Debian version must be >= 7.0"
        cd $BUILD_DIR
        return
    fi

    rm -rf $OVS_SRC
    mkdir -p $OVS_SRC
    cd $OVS_SRC

    if wget $OVS_TARBALL_LOC/openvswitch-$OVS_RELEASE.tar.gz 2> /dev/null; then
        tar xzf openvswitch-$OVS_RELEASE.tar.gz
    else
        echo "Failed to find OVS at $OVS_TARBALL_LOC/openvswitch-$OVS_RELEASE.tar.gz"
        cd $BUILD_DIR
        return
    fi

    # Remove any old packages

    $remove openvswitch-common openvswitch-datapath-dkms openvswitch-pki openvswitch-switch \
            openvswitch-controller || true

    # Get build deps
    $install build-essential fakeroot debhelper autoconf automake libssl-dev \
             pkg-config bzip2 openssl python-all procps python-qt4 \
             python-zopeinterface python-twisted-conch dkms dh-python dh-autoreconf \
             uuid-runtime

    # Build OVS
    parallel=`grep processor /proc/cpuinfo | wc -l`
    cd $BUILD_DIR/openvswitch/openvswitch-$OVS_RELEASE
            DEB_BUILD_OPTIONS='parallel=$parallel nocheck' fakeroot debian/rules binary
    cd ..
    for pkg in common datapath-dkms pki switch; do
        pkg=openvswitch-${pkg}_$OVS_RELEASE*.deb
        echo "Installing $pkg"
        $pkginst $pkg
    done
    if $pkginst openvswitch-controller_$OVS_RELEASE*.deb 2>/dev/null; then
        echo "Ignoring error installing openvswitch-controller"
    fi

    /sbin/modinfo openvswitch
    sudo ovs-vsctl show
    # Switch can run on its own, but
    # Mininet should control the controller
    # This appears to only be an issue on Ubuntu/Debian
    if sudo service openvswitch-controller stop 2>/dev/null; then
        echo "Stopped running controller"
    fi
    if [ -e /etc/init.d/openvswitch-controller ]; then
        sudo update-rc.d openvswitch-controller disable
    fi
}


# Install Open vSwitch

function ovs {
    echo "Installing Open vSwitch..."

    if [ "$DIST" = "Fedora" -o "$DIST" = "RedHatEnterpriseServer" -o "$DIST" = "CentOS" ]; then
        $install openvswitch openvswitch-controller
        return
    fi

    if [ "$DIST" = "Ubuntu" ] && ! version_ge $RELEASE 14.04; then
        # Older Ubuntu versions need openvswitch-datapath/-dkms
        # Manually installing openvswitch-datapath may be necessary
        # for manually built kernel .debs using Debian's defective kernel
        # packaging, which doesn't yield usable headers.
        if ! dpkg --get-selections | grep openvswitch-datapath; then
            # If you've already installed a datapath, assume you
            # know what you're doing and don't need dkms datapath.
            # Otherwise, install it.
            $install openvswitch-datapath-dkms
        fi
    fi

    $install openvswitch-switch
    OVSC=""
    if $install openvswitch-controller; then
        OVSC="openvswitch-controller"
    else
        echo "Attempting to install openvswitch-testcontroller"
        if $install openvswitch-testcontroller; then
            OVSC="openvswitch-testcontroller"
        else
            echo "Failed - skipping openvswitch-testcontroller"
        fi
    fi
    if [ "$OVSC" ]; then
        # Switch can run on its own, but
        # Mininet should control the controller
        # This appears to only be an issue on Ubuntu/Debian
        if sudo service $OVSC stop 2>/dev/null; then
            echo "Stopped running controller"
        fi
        if [ -e /etc/init.d/$OVSC ]; then
            sudo update-rc.d $OVSC disable
        fi
    fi
}

function remove_ovs {
    pkgs=`dpkg --get-selections | grep openvswitch | awk '{ print $1;}'`
    echo "Removing existing Open vSwitch packages:"
    echo $pkgs
    if ! $remove $pkgs; then
        echo "Not all packages removed correctly"
    fi
    # For some reason this doesn't happen
    if scripts=`ls /etc/init.d/*openvswitch* 2>/dev/null`; then
        echo $scripts
        for s in $scripts; do
            s=$(basename $s)
            echo SCRIPT $s
            sudo service $s stop
            sudo rm -f /etc/init.d/$s
            sudo update-rc.d -f $s remove
        done
    fi
    echo "Done removing OVS"
}

# Script to copy built OVS kernel module to where modprobe will
# find them automatically.  Removes the need to keep an environment variable
# for insmod usage, and works nicely with multiple kernel versions.
#
# The downside is that after each recompilation of OVS you'll need to
# re-run this script.  If you're using only one kernel version, then it may be
# a good idea to use a symbolic link in place of the copy below.
function modprobe {
    echo "Setting up modprobe for OVS kmod..."
    set +o nounset
    if [ -z "$OVS_KMODS" ]; then
      echo "OVS_KMODS not set. Aborting."
    else
      sudo cp $OVS_KMODS $DRIVERS_DIR
      sudo depmod -a ${KERNEL_NAME}
    fi
    set -o nounset
}

function all {
    if [ "$DIST" = "Fedora" ]; then
        printf "\nFedora 18+ support (still work in progress):\n"
        printf " * Fedora 18+ has kernel 3.10 RPMS in the updates repositories\n"
        printf " * Fedora 18+ has openvswitch 1.10 RPMS in the updates repositories\n"
        printf " * the install.sh script options [-bfnpvw] should work.\n"
        printf " * for a basic setup just try:\n"
        printf "       install.sh -fnpv\n\n"
        exit 3
    fi
    echo "Installing all packages except for -eix (doxypy, ivs, nox-classic)..."
    pre_build
    kernel
    mn_wifi_deps
    # Skip mn_dev (doxypy/texlive/fonts/etc.) because it's huge
    # mn_dev
    of
    ovs
    echo "Enjoy Mininet!"
}

# Restore disk space and remove sensitive files before shipping a VM.
function vm_clean {
    echo "Cleaning VM..."
    sudo apt-get clean
    sudo apt-get autoremove
    sudo rm -rf /tmp/*
    sudo rm -rf openvswitch*.tar.gz

    # Remove sensistive files
    history -c  # note this won't work if you have multiple bash sessions
    rm -f ~/.bash_history  # need to clear in memory and remove on disk
    rm -f ~/.ssh/id_rsa* ~/.ssh/known_hosts
    sudo rm -f ~/.ssh/authorized_keys*

    # Remove SSH keys and regenerate on boot
    echo 'Removing SSH keys from /etc/ssh/'
    sudo rm -f /etc/ssh/*key*
    if ! grep mininet /etc/rc.local >& /dev/null; then
        sudo sed -i -e "s/exit 0//" /etc/rc.local
        echo '
# mininet: regenerate ssh keys if we deleted them
if ! stat -t /etc/ssh/*key* >/dev/null 2>&1; then
    /usr/sbin/dpkg-reconfigure openssh-server
fi
exit 0
' | sudo tee -a /etc/rc.local > /dev/null
    fi

    # Remove Mininet files
    #sudo rm -f /lib/modules/python2.5/site-packages/mininet*
    #sudo rm -f /usr/bin/mnexec

    # Clear optional dev script for SSH keychain load on boot
    rm -f ~/.bash_profile

    # Clear git changes
    git config --global user.name "None"
    git config --global user.email "None"

    # Note: you can shrink the .vmdk in vmware using
    # vmware-vdiskmanager -k *.vmdk
    echo "Zeroing out disk blocks for efficient compaction..."
    time sudo dd if=/dev/zero of=/tmp/zero bs=1M || true
    sync ; sleep 1 ; sync ; sudo rm -f /tmp/zero

}

function usage {
    printf '\nUsage: %s [-abcdfhikmnprtvVwW03]\n\n' $(basename $0) >&2

    printf 'This install script attempts to install useful packages\n' >&2
    printf 'for Mininet. It should (hopefully) work on Ubuntu 11.10+\n' >&2
    printf 'If you run into trouble, try\n' >&2
    printf 'installing one thing at a time, and looking at the \n' >&2
    printf 'specific installation function in this script.\n\n' >&2

    printf 'options:\n' >&2
    printf -- ' -a: (default) install (A)ll packages - good luck!\n' >&2
    printf -- ' -b: install controller (B)enchmark (oflops)\n' >&2
    printf -- ' -c: (C)lean up after kernel install\n' >&2
    printf -- ' -d: (D)elete some sensitive files from a VM image\n' >&2
    printf -- ' -e: install Mininet d(E)veloper dependencies\n' >&2
    printf -- ' -f: install Open(F)low\n' >&2
    printf -- ' -h: print this (H)elp message\n' >&2
    printf -- ' -k: install new (K)ernel\n' >&2
    printf -- ' -m: install Open vSwitch kernel (M)odule from source dir\n' >&2
    printf -- ' -n: install Mini(N)et dependencies + core files\n' >&2
    printf -- ' -r: remove existing Open vSwitch packages\n' >&2
    printf -- ' -s <dir>: place dependency (S)ource/build trees in <dir>\n' >&2
    printf -- ' -t: complete o(T)her Mininet VM setup tasks\n' >&2
    printf -- ' -v: install Open (V)switch\n' >&2
    printf -- ' -V <version>: install a particular version of Open (V)switch on Ubuntu\n' >&2
    printf -- ' -W: install Mininet-WiFi\n' >&2
    printf -- ' -3: -3[fx] installs OpenFlow 1.3 versions\n' >&2
    exit 2
}

OF_VERSION=1.0

if [ $# -eq 0 ]
then
    all
else
    while getopts 'abcdefhkmnprs:vV:W3' OPTION
    do
      case $OPTION in
      a)    all;;
      c)    kernel_clean;;
      d)    vm_clean;;
      e)    mn_dev;;
      f)    case $OF_VERSION in
            1.0) of;;
            1.3) of13;;
            *)  echo "Invalid OpenFlow version $OF_VERSION";;
            esac;;
      h)    usage;;
      k)    kernel;;
      m)    modprobe;;
      r)    remove_ovs;;
      s)    mkdir -p $OPTARG; # ensure the directory is created
            BUILD_DIR="$( cd -P "$OPTARG" && pwd )"; # get the full path
            echo "Dependency installation directory: $BUILD_DIR";;
      v)    ovs;;
      V)    OVS_RELEASE=$OPTARG;
            ubuntuOvs;;
      W)    mn_wifi_deps;;
      x)    case $OF_VERSION in
            1.0) nox;;
            1.3) nox13;;
            *)  echo "Invalid OpenFlow version $OF_VERSION";;
            esac;;
      0)    OF_VERSION=1.0;;
      3)    OF_VERSION=1.3;;
      ?)    usage;;
      esac
    done
    shift $(($OPTIND - 1))
fi
