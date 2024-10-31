#!/bin/bash
#
# Copyright (C) 2018 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them
# is governed by the express license under which they were provided to you ("License"). Unless
# the License provides otherwise, you may not use, modify, copy, publish, distribute, disclose
# or transmit this software or the related documents without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied
# warranties, other than those that are expressly stated in the License.
#

# Description: script to install SEP binaries
#
# Version: 0.1

# ------------------------------ CONSTANTS -----------------------------------

OS=linux
PACKAGE_EXT=".tar.bz2"
BETA=beta
AMD=amd
TOOL_RELEASE_TYPE=sep
SOFT_LINK_NAME=sep
TOOL_NAME_CAPS=SEP

# get the tool name from the package: SEP or EMON
GEN_PKG_NAME_REGEX="[_a-z]*[0-9\.]+(_${BETA})*(_${AMD})*_${OS}_[a-z0-9]+${PACKAGE_EXT}"
temp_tar_name=$( ls | grep -E ${GEN_PKG_NAME_REGEX} )
if [ -n "${temp_tar_name}" ] ; then
    prefix=${temp_tar_name%%_*}
    if [ "${prefix}x" = "emonx" ] ; then
        TOOL_RELEASE_TYPE=emon
        SOFT_LINK_NAME=emon
        TOOL_NAME_CAPS=EMON
    fi
fi

BINARY_NAME_REGEX="${TOOL_RELEASE_TYPE}[_a-z]*[0-9\.]+(_${BETA})*(_${AMD})*_${OS}_[a-z0-9]+"
PACKAGE_NAME_REGEX="${TOOL_RELEASE_TYPE}[_a-z]*[0-9\.]+(_${BETA})*(_${AMD})*_${OS}_[a-z0-9]+${PACKAGE_EXT}"

DEFAULT_INSTALL_PATH_BASE=/opt/intel
INSTALL_PATH_BASE=${DEFAULT_INSTALL_PATH_BASE}
INSTALL_PATH=${INSTALL_PATH_BASE}/${SOFT_LINK_NAME}
SEPDK=sepdk/src
LIB=/lib

SMALL_DASH="--------"
DASH="----------------"
LONG_DASH=${DASH}${DASH}${DASH}${DASH}
HEADER_STRING="\t\t\t${TOOL_NAME_CAPS} INSTALLATION\t\t\t"
ALERT="ALERT"

TMP=/tmp
DATE_FORMAT=+%m%d%Y.%H%M%S
TIMESTAMP=$(date ${DATE_FORMAT})
DATE=$(date +%m%d%Y)

DEFAULT_DRIVER_GROUP="vtune"
DEFAULT_DRIVER_PERM="660"
non_interactive=0
install_tool=0
load_driver_only=no
uninstall=0
enable_maxlog=0
load_driver="yes"
reload_driver="no"
yocto=0
collection_mode="driver"
udev="yes"

screen_1=uninstall_dialog_page
screen_2=installation_dialog_page
screen_3=manage_driver_group_dialog_page
screen_4=summary_page
SCREEN_LINEAR_ORDER=(${screen_1} ${screen_2} ${screen_3} ${screen_4})
screen_1_1=unload_driver_dialog_page
screen_2_0=update_collection_mode_dialog_page
screen_2_1=update_compiler_dialog_page
screen_2_2=update_make_cmd_dialog_page
screen_2_3=update_kernel_src_dialog_page
screen_2_4=manage_driver_group_dialog_page
screen_2_5=change_driver_perm_dialog_page
screen_2_6=change_load_drivers_page
screen_2_7=change_driver_reload_setup_page
screen_2_8=change_load_drivers_only_page
screen_2_9=update_install_location
BACK_SCREEN_MAP_1=(${screen_1} ${screen_1_1})
BACK_SCREEN_MAP_2=(${screen_2} ${screen_2_0} ${screen_2_1} ${screen_2_2} ${screen_2_3} ${screen_2_4} ${screen_2_5} ${screen_2_6} ${screen_2_7} ${screen_2_8} ${screen_2_9})

# error codes
SEP_RC_ALREADY_INSTALLED=200
SEP_RC_UNPACK_FAILURE=201
SEP_RC_NOT_INSTALLED=202
SEP_RC_DRIVER_BUILD_FAILURE=203
SEP_RC_DRIVER_UNLOAD_FAILURE=204
SEP_RC_DRIVER_LOAD_FAILURE=205
SEP_RC_UNLOAD_DRIVER_DEPENDENCY_CONFLICT=206
SEP_RC_LOAD_GROUP_CONFLICT=207
SEP_RC_INSTALL_PACKAGE_NOT_FOUND=208
SEP_RC_BOOTSCRIPT_INSTALL_FAIL=209
SEP_RC_BOOTSCRIPT_UNINSTALL_FAIL=210
SEP_RC_LICENSE_NOT_ACCEPTED=211
SEP_RC_LICENSE_NOT_AVAILABLE=212
SEP_RC_INVALID_SCREEN_NAME=213
SEP_RC_OPTIONS_ERROR=214
SEP_RC_SYS_LIB_NOT_FOUND=215
SEP_RC_CONSENT_NOT_AVAILABLE=216

# ------------------------------- OUTPUT -------------------------------------

init_logging()
{
    local log_folder_name=log_${TOOL_RELEASE_TYPE}_installer_${DATE}

    if [ ! -d /tmp/${log_folder_name} ]; then
        mkdir /tmp/${log_folder_name} > /dev/null 2>&1
        log_dir_ret_code=$?
        if [ ${log_dir_ret_code} -ne 0 ] ; then
            log_folder_name=
        else
            chmod 777 /tmp/${log_folder_name}
        fi
    fi

    LOG_PATH_PREFIX=${TMP}/${log_folder_name}

    LOG_NAME=${LOG_PATH_PREFIX}/${TOOL_RELEASE_TYPE}_installer_${TIMESTAMP}.log
}

LOG()
{
    echo "$@" >> ${LOG_NAME}
}

LOG_NNL()
{
    echo -n "$@" >> ${LOG_NAME}
}

GET_LOG_NAME()
{
    local DRIVER_OPERATION="$1"
    local TIMESTAMP=$(date ${DATE_FORMAT})
    echo "${LOG_PATH_PREFIX}/${TOOL_RELEASE_TYPE}_installer_driver_${DRIVER_OPERATION}_${TIMESTAMP}.log"
}

print_msg()
{
    MSG="$*"
    echo "$MSG"
}

print_ul_msg()
{
    MSG="$*"
    echo -e "\e[4m$MSG\e[0m"
}

print_tab()
{
    echo -ne '\t'
}

print_tabbed_msg()
{
    print_tab
    print_msg "$*"
}

print_tabbed_msg_nnl()
{
    print_tab
    print_nnl "$*"
}

print_tabbed_ul_msg()
{
    print_tab
    print_ul_msg "$*"
}

print_nnl()
{
    MSG="$*"
    echo -n "$MSG"
}

print_err()
{
    MSG="$*"
    if [ -w /dev/stderr ]; then
      if [ ! -S /dev/stderr ] ; then
          echo "$MSG" >> /dev/stderr
      else
          echo "$MSG" >&2
      fi
    else
        echo "$MSG"
    fi
}

print_debug()
{
    print_msg "$*"
    read debug
}

LOG_N_PRINT_MSG()
{
    FUNC_NAME="$1"
    MSG="$2"
    LOG "${FUNC_NAME}: ${MSG}"
    print_msg ${MSG}
}

LOG_N_PRINT_ERR()
{
    FUNC_NAME="$1"
    MSG="$2"
    LOG "${FUNC_NAME}: ${MSG}"
    print_err ${MSG}
}

print_header()
{
    if [ ${non_interactive} -eq 1 ] ; then
        return
    fi

    clear
    if [ -n "${STEP_NUM}" ] ; then
        print_msg "Step ${STEP_NUM} of ${TOTAL_STEPS} | ${STEP_NAME}"
    else
        print_msg "${STEP_NAME}"
    fi
    print_msg ${LONG_DASH}
    echo -e ${HEADER_STRING}
    print_msg ${LONG_DASH}
    print_msg ""

}

# TODO: delete after replacing usages with second function
print_footer()
{
    if [ ${non_interactive} -eq 1 ] ; then
        return
    fi

    if [ "$1" != "LICENSE" ] ; then
        print_msg ""
        print_tabbed_msg "[q] Quit"
    fi
    print_msg ${LONG_DASH}
    if [ "$1" = "PREINSTALL_SUMMARY" ] ; then
        print_nnl "Please press \"Enter\" to continue"
    elif [ "$1" = "CONFIRMATION" ] ; then
        print_nnl "Do you accept the above information? (y/n)"
    elif [ "$1" = "LICENSE" ] ; then
        print_nnl "Type \"accept\" to continue or \"decline\" to exit"
    elif [ "$1" = "CONSENT" ] ; then
        print_nnl "Type \"yes\" to agree or \"no\" to decline"
    else
        print_nnl "Please enter a selection or press \"Enter\" to accept default value"
        if [ -n "$1" ] ; then
            print_nnl " [$1]"
        fi
    fi
    print_nnl ": "
}

print_footer_2()
{
    if [ ${non_interactive} -eq 1 ] ; then
        return 0
    fi

    if [[ "$*" != *"skip-options"* ]] ; then
        print_msg ""
        if [[ "$*" != *"no-back"* ]] ; then
            print_tab
            print_nnl "[b] Back"
        fi
        if [[ "$*" != *"no-next"* ]] ; then
            print_tab
            print_nnl "[n] Next"
        fi
        if [[ "$*" != *"no-quit"* ]] ; then
            print_tab
            print_nnl "[q] Quit"
        fi
        if [[ "$*" != *"no-next"* || "$*" != *"no-back"* || "$*" != *"no-quit"* ]] ; then
            print_msg ""
        fi
        print_msg ${LONG_DASH}
    fi
    if [[ "$*" == *"enter-to-contiue"* ]] ; then
        print_nnl "Please press \"Enter\" to continue"
    elif [[ "$*" == *"yes-or-no"* ]] ; then
        print_nnl "Please enter y/n or press \"Enter\" to accept default value"
    elif [[ "$*" == *"accept-or-decline"* ]] ; then
        print_nnl "Type \"accept\" to continue or \"decline\" to exit"
    elif [[ "$*" == *"summary"* ]] ; then
        print_nnl "Press \"Enter\" to start installation"
    elif [[ "$*" == *"standard-2"* ]] ; then
        print_nnl "Please enter a value/option or press \"Enter\" to accept default value"
    elif [[ "$*" == *"finish"* ]] ; then
        print_nnl "Press \"Enter\" to exit installation"
    else
        print_nnl "Please enter an option or press \"Enter\" to accept default value"
    fi
    if [[ "$*" == *"default-value"* ]] ; then
        for val in $@; do :; done
        print_nnl " [${val}]"
    fi
    print_nnl ": "

    return 0
}

# set the path to include "standard" locations so commands below can be found
PATH="/sbin:/usr/sbin:/bin:/usr/bin/:/usr/local/sbin:/usr/local/bin:/usr/local/gnu/bin:"${PATH}":."
export PATH

# ------------------------------ COMMANDS ------------------------------------

CUT="cut"
GREP="grep"
INSMOD="insmod"
LSMOD="lsmod"
PGREP="pgrep"
PKILL="pkill"
RM="rm"
RMMOD="rmmod"
SED="sed"
SU="su"
TR="tr"
UNAME="uname"
WHICH="which"
ID="id"
TAR="tar"
CHOWN="chown"
CHGRP="chgrp"
LS="ls"
LN="ln"
STAT="stat"


COMMANDS_TO_CHECK="${CUT} ${GREP} ${INSMOD} ${LSMOD} ${RM} ${RMMOD} ${SED} ${TR} ${UNAME} ${ID} ${TAR} ${CHOWN} ${CHGRP} ${LS} ${LN} ${STAT}"

#
# Note: Busybox has a restricted shell environment, and
#       conventional system utilities may not be present;
#       so need to account for this ...
# Note: Restricted environment mode can be forced by the option -re
#       in case user may not know about the Busybox
#

# busybox binary check
if [ -z "${BUSYBOX_SHELL}" ]; then
    # if not forced by command line option -re then check it
    BUSYBOX_SHELL=` ${GREP} --help 2>&1 | ${GREP} BusyBox`
fi

if [ -z "${BUSYBOX_SHELL}" ] ; then
    COMMANDS_TO_CHECK="${PGREP} ${PKILL} ${SU} ${COMMANDS_TO_CHECK}"
fi

# if any of the COMMANDS_TO_CHECK are not executable, then exit script
OK="true"
for c in ${COMMANDS_TO_CHECK} ; do
    CMD=`${WHICH} $c 2> /dev/null` ;
    if [ -z "${CMD}" ] ; then
        OK="false"
        print_err "ERROR: unable to find command \"$c\" !"
    fi
done
if [ ${OK} != "true" ] ; then
    print_err "If you are using BusyBox, please re-run this script with the '-re' flag added"
    print_err "Otherwise, please add the above commands to your PATH and re-run the script ... exiting."
    exit 255
fi

# ------------------------------ VARIABLES -----------------------------------

SCRIPT=$0
PLATFORM=`${UNAME} -m`
KERNEL_VERSION=`${UNAME} -r`
CWD=`pwd`

# set the directory of the install script
SCRIPT_DIR=`dirname $0`
SEP_SHELL=
SEP_RECURSE=-r
SEP_FORCE=-f

if [ -n "${BUSYBOX_SHELL}" ] ; then
   SEP_SHELL=sh
   SEP_FORCE=
   SEP_RECURSE=
fi

MY_NAME=`whoami`
MY_GROUP=`${ID} -gn ${MY_NAME} 2> /dev/null`

c_compiler=gcc
make_command=make
# getting the default gcc compiler
COMPILER=`${WHICH} ${c_compiler} 2> /dev/null`
COMPILER=`echo ${COMPILER} | ${SED} 's/\/\//\//g'`
if [ -z "${COMPILER}" -o -d "${COMPILER}" ] ; then
    COMPILER=$c_compiler
fi
DEFAULT_COMPILER=${COMPILER}

# getting the default make command
MAKE_CMD=`${WHICH} ${make_command} 2> /dev/null`
MAKE_CMD=`echo ${MAKE_CMD} | ${SED} 's/\/\//\//g'`
if [ -z "${MAKE_CMD}" -o -d "${MAKE_CMD}" ] ; then
    MAKE_CMD=$make_command
fi
DEFAULT_MAKE_CMD=${MAKE_CMD}

OS_BITNESS=""
if [[ "${PLATFORM}" == 'x86_64' ]]; then
    OS_BITNESS="64"
elif [[ "${PLATFORM}" == 'i686' ]]; then
    OS_BITNESS="32"
fi

# license
LICENSE_FILENAME=license.txt
LICENSE_FILE=${CWD}/${LICENSE_FILENAME}

collection_mode_available=
if [ "${TOOL_NAME_CAPS}" = "EMON" ] ; then
    collection_mode_available=1
fi

# Google Analytics Consent
GA_CONSENT_ACCEPTED=0
ISIP_CONSENT_FILENAME=sep_emon_isip_consent.txt
ISIP_CONSENT_FILE=${CWD}/${ISIP_CONSENT_FILENAME}

ISIP_LOCATION="/home/${SUDO_USER}/intel"
if [ -z "${SUDO_USER}" ] ; then
    ISIP_LOCATION="/root/intel"
fi
ISIP_FILENAME="sep_emon_isip"
ISIP_FILE="${ISIP_LOCATION}/${ISIP_FILENAME}"

# ------------------------------ FUNCTIONS -----------------------------------

# function to show usage and exit
print_usage_and_exit()
{
    err=${1:-0}
    print_msg ""
    print_msg "Usage: $0 [ options ]"
    print_msg ""
    print_msg " where \"options\" are the following:"
    print_msg ""
    print_msg "    -ni | --non-interactive"
    print_msg "      executes the installer non-interactively."
    print_msg ""
    print_msg "    -i | --install"
    print_msg "      installs ${TOOL_NAME_CAPS}."
    print_msg ""
    print_msg "    --accept-license"
    print_msg "      accepts EULA license (${LICENSE_FILE}). Mandatory with -i option."
    print_msg ""
    print_msg "    -u | --uninstall"
    print_msg "      uninstalls all existing ${TOOL_NAME_CAPS} installations."
    print_msg ""
    print_msg "    -C | --custom-install-location"
    print_msg "      installs ${TOOL_NAME_CAPS} in specified location."
    print_msg ""
    print_msg "    -g | --driver-group"
    print_msg "      use the specified group as driver access group."
    print_msg ""
    print_msg "    -p | --driver-perm"
    print_msg "      use the specified permission as driver permission."
    print_msg ""
    print_msg "    -lo | --load-driver-only"
    print_msg "      performs only driver loading if ${TOOL_NAME_CAPS} is already"
    print_msg "      installed."
    print_msg ""
    print_msg "    --no-load-driver"
    print_msg "      installs ${TOOL_NAME_CAPS} without loading the drivers."
    print_msg "      All functionalities of ${TOOL_NAME_CAPS} may not be available."
    print_msg ""
    print_msg "    --install-boot-script"
    print_msg "      installs boot script to reload drivers during reboot."
    print_msg ""
    print_msg "    --kernel-src-dir"
    print_msg "      \"path\" directory of the configured kernel source tree;"
    print_msg "      several paths are searched to find a suitable default,"
    print_msg "      including \"/lib/modules/${KERNEL_VERSION}/{source,build}\","
    print_msg "      \"/usr/src/linux-${KERNEL_VERSION}\", and \"/usr/src/linux\""
    print_msg ""
    print_msg "    --c-compiler"
    print_msg "      \"c_compiler\" is the C compiler used to compile the kernel."
    print_msg "      Defaults to \"gcc\""
    print_msg ""
    print_msg "    --make-command"
    print_msg "      \"make_command\" is the make command used to build the kernel."
    print_msg "      Defaults to \"make\""
    print_msg ""
    print_msg "    --yocto"
    print_msg "      specify this option for Yocto OS."
    print_msg "      This will create a symbloic link from /lib to /lib64."
    print_msg ""
    if [ -n "${collection_mode_available}" ] ; then
        print_msg "    --driverless-mode"
        print_msg "      specify this option for using EMON in driverless mode."
        print_msg ""
    fi
    print_msg "E.g.: \"$0 -i -u -C /install/path --accept-license\" will uninstall all \
existing ${TOOL_NAME_CAPS} installations and installs the current package in /install/path."
    print_msg ""
    exit $err
}

# check for certain options
OPTIONS=""
while [ $# -gt 0 ] ; do
    case "$1" in
        -h | --help)
            print_usage_and_exit 0
            ;;
        -ni | --non-interactive)
            non_interactive=1
            OPTIONS="${OPTIONS} -ni"
            ;;
        -i | --install)
            install_tool=1
            OPTIONS="${OPTIONS} -i"
            ;;
        -u | --uninstall)
            uninstall=1
            OPTIONS="${OPTIONS} -u"
            ;;
        -lo | --load-driver-only)
            load_driver_only=yes
            OPTIONS="${OPTIONS} -lo"
            ;;
        -C | --custom-install-location)
            shift
            custom_install_loc="$1"
            OPTIONS="${OPTIONS} -C ${custom_install_loc}"
            ;;
        -g | --driver-group) # driver group
            shift
            custom_driver_group="$1"
            OPTIONS="${OPTIONS} -g ${custom_driver_group}"
            ;;
        -p | --driver-perm) # driver permission
            shift
            custom_driver_perm="$1"
            OPTIONS="${OPTIONS} -p ${custom_driver_perm}"
            ;;
        -up) # user permission for install directory
            shift
            install_folder_up="$1"
            OPTIONS="${OPTIONS} -up ${install_folder_up}"
            ;;
        -gp) # group permission for install directory
            shift
            install_folder_gp="$1"
            OPTIONS="${OPTIONS} -gp ${install_folder_gp}"
            ;;
        --maxlog)
            enable_maxlog=1
            OPTIONS="${OPTIONS} --maxlog"
            ;;
        --no-load-driver)
            load_driver=no
            OPTIONS="${OPTIONS} --no-load-driver"
            ;;
        --install-boot-script)
            reload_driver=yes
            OPTIONS="${OPTIONS} --install-boot-script"
            ;;
        --kernel-src-dir)
            shift
            CURRENT_KERNEL_SRC_DIR="$1"
            use_custom_kernel_src_dir=1
            OPTIONS="${OPTIONS} --kernel-src-dir ${CURRENT_KERNEL_SRC_DIR}"
            ;;
        --make-command)
            shift
            MAKE_CMD="$1"
            OPTIONS="${OPTIONS} --make-command ${MAKE_CMD}"
            ;;
        --c-compiler)
            shift
            COMPILER="$1"
            OPTIONS="${OPTIONS} --c-compiler ${COMPILER}"
            ;;
        --accept-license)
            LICENSE_ACCEPTED=1
            OPTIONS="${OPTIONS} --accept-license"
            ;;
        --yocto)
            yocto=1
            OPTIONS="${OPTIONS} --yocto"
            ;;
        --no-udev)
            udev="no"
            OPTIONS="${OPTIONS} --no-udev"
            ;;
        --driverless-mode)
            if [ -n "${collection_mode_available}" ] ; then
                collection_mode="driverless"
                load_driver="no"
                OPTIONS="${OPTIONS} --driverless-mode"
            else
                print_err ""
                print_err "ERROR: unrecognized option \"$1\""
                print_usage_and_exit 254
            fi
            ;;
        *)
            print_err ""
            print_err "ERROR: unrecognized option \"$1\""
            print_usage_and_exit 254
            ;;
    esac
    shift
done

# --------------------------------- FUNCTIONS --------------------------------

# function to check if combinations of args provided are acceptable
check_args()
{
    if [ ${non_interactive} -eq 1 ] ; then
        if [ "${load_driver_only}" = "no" -a ${install_tool} -eq 0 -a ${uninstall} -eq 0 ] ; then
            print_err ""
            LOG_N_PRINT_ERR "CHECK_ARGS" "ERROR: --install/-i, --uninstall/-u or --load-driver-only/-lo options should be used with -ni"
            print_err ""
            exit ${SEP_RC_OPTIONS_ERROR}
        fi
    fi

    if [ ${install_tool} -eq 1 -a "${load_driver_only}" = "yes" ] ; then
        print_err ""
        LOG_N_PRINT_ERR "CHECK_ARGS" "ERROR: --install/-i and --load-driver-only/-lo options cannot be used together."
        LOG_N_PRINT_ERR "CHECK_ARGS" "       Use -lo if only driver load is required."
        print_err ""
        exit ${SEP_RC_OPTIONS_ERROR}
    fi

    if [[ ${uninstall} -eq 1 && ${install_tool} -eq 0 && ( "${load_driver_only}" == "yes" || "${reload_driver}" == "yes" || "${load_driver}" == "no" || ${enable_maxlog} -eq 1 ) ]] ; then
        print_err ""
        LOG_N_PRINT_ERR "CHECK_ARGS" "ERROR: --uninstall/-u and --load-driver-only/-lo or --no-load-driver or --install-boot-script or --maxlog options cannot be used together."
        print_err ""
        exit ${SEP_RC_OPTIONS_ERROR}
    fi

    if [ "${reload_driver}" = "yes" -a "${collection_mode}" = "driverless" ] ; then
        print_err ""
        LOG_N_PRINT_ERR "CHECK_ARGS" "ERROR: --install-boot-script and --driverless-mode options cannot be used together."
        print_err ""
        exit ${SEP_RC_OPTIONS_ERROR}
    fi

    if [ "${load_driver_only}" = "yes" -a "${collection_mode}" = "driverless" ] ; then
        print_err ""
        LOG_N_PRINT_ERR "CHECK_ARGS" "ERROR: --load-driver-only/-lo and --driverless-mode options cannot be used together."
        print_err ""
        exit ${SEP_RC_OPTIONS_ERROR}
    fi

    if [ "${load_driver}" = "no" -a "${load_driver_only}" = "yes" ] ; then
        print_err ""
        LOG_N_PRINT_ERR "CHECK_ARGS" "ERROR: --no-load-driver and --load-driver-only/-lo options cannot be used together."
        print_err ""
        exit ${SEP_RC_OPTIONS_ERROR}
    fi

    if [ "${load_driver}" = "no" -a "${reload_driver}" = "yes" ] ; then
        print_err ""
        LOG_N_PRINT_ERR "CHECK_ARGS" "ERROR: --no-load-driver and --install-boot-script options cannot be used together."
        print_err ""
        exit ${SEP_RC_OPTIONS_ERROR}
    fi

    if [ "${load_driver}" = "no" -a ${enable_maxlog} -eq 1 ] ; then
        print_err ""
        LOG_N_PRINT_ERR "CHECK_ARGS" "ERROR: --no-load-driver and --maxlog options cannot be used together."
        print_err ""
        exit ${SEP_RC_OPTIONS_ERROR}
    fi

    if [[ -n "${install_folder_up}" || -n "${install_folder_gp}" ]] ; then
        if [[ -z "${install_folder_up}" || -z "${install_folder_gp}" ]] ; then
            print_err ""
            LOG_N_PRINT_ERR "CHECK_ARGS" "ERROR: -up and -gp options should be used together."
            print_err ""
            exit ${SEP_RC_OPTIONS_ERROR}
        fi
    fi

    if [ ${install_tool} -eq 1 -a -z "${LICENSE_ACCEPTED}" ] ; then
        print_err ""
        LOG_N_PRINT_ERR "CHECK_ARGS" "ERROR: please use --accept-license with --install/-i option to accept the EULA license (${LICENSE_FILE}). Exiting..."
        print_err ""
        exit ${SEP_RC_LICENSE_NOT_ACCEPTED}
    fi
}

init_variables()
{
    LOG "INIT_VARIABLES: Initializing variables"
    # initializing with default group and permission
    DRIVER_GROUP=${DEFAULT_DRIVER_GROUP}
    DRIVER_PERM=${DEFAULT_DRIVER_PERM}

    LOG "INIT_VARIABLES: Getting kernel src directory"
    kernel_src_dir=/usr/src/linux-${KERNEL_VERSION}
    DEFAULT_KERNEL_SRC_DIR=${kernel_src_dir}

    major=$(echo ${KERNEL_VERSION} | cut -d. -f1)
    minor=$(echo ${KERNEL_VERSION} | cut -d. -f2)

    # search heuristic for determining default kernel source directory
    if [ ! -d ${DEFAULT_KERNEL_SRC_DIR} ] ; then
        DEFAULT_KERNEL_SRC_DIR=/lib/modules/${KERNEL_VERSION}/build
        if [ ! -d ${DEFAULT_KERNEL_SRC_DIR} ] ; then
            DEFAULT_KERNEL_SRC_DIR=/lib/modules/${KERNEL_VERSION}/source
            if [ ! -d ${DEFAULT_KERNEL_SRC_DIR} ] ; then
                DEFAULT_KERNEL_SRC_DIR=/usr/src/linux-${major}.${minor}
                if [ ! -d ${DEFAULT_KERNEL_SRC_DIR} ] ; then
                    DEFAULT_KERNEL_SRC_DIR=/usr/src/linux
                    if [ ! -d ${DEFAULT_KERNEL_SRC_DIR} ] ; then
                        DEFAULT_KERNEL_SRC_DIR=/usr/src/kernel
                        if [ ! -d ${DEFAULT_KERNEL_SRC_DIR} ] ; then
                        # punt ...
                            DEFAULT_KERNEL_SRC_DIR=${kernel_src_dir}
                        fi
                    fi
                fi
            fi
        fi
    fi

    if [ -z "${use_custom_kernel_src_dir}" ] ; then
        CURRENT_KERNEL_SRC_DIR=${DEFAULT_KERNEL_SRC_DIR}
    fi

    if [ -n "${custom_driver_group}" ] ; then
        DRIVER_GROUP=${custom_driver_group}
    fi

    if [ -n "${custom_driver_perm}" ] ; then
        DRIVER_PERM=${custom_driver_perm}
    fi

    if [ -n "${custom_install_loc}" ] ; then
        INSTALL_PATH_BASE=${custom_install_loc}
        INSTALL_PATH=${INSTALL_PATH_BASE}/${SOFT_LINK_NAME}
    fi

    if [ ${non_interactive} -eq 1 ] ; then
        LOG "INIT_VARIABLES: non_interactive mode"
        USER_TYPE_SUDO=1
        if [ "${load_driver_only}" = "no" -a ${install_tool} -eq 0 ] ; then
            load_driver="no"
        fi
    else
        install_tool=1
        main_group_page_call=0
        sub_group_page_update=0
    fi

    uninstall_binary_name=
    driver_uninstall_binary_name=

    drvless_mode_invalid_screens=
}

# TODO: delete after replacing usages with second function
process_user_input()
{
    if [ ${non_interactive} -eq 1 ] ; then
        return
    fi

    while [ -z "${VALID_INPUT}" ] ; do
        read ui_option

        if [ "${ui_option}" = "q" ] ; then
            LOG "PROCESS_USER_INPUT: User manually quit"
            # delete temporarily created .log.err files
            ${RM} -rf ${LOG_PATH_PREFIX}/*.log.err > /dev/null 2>&1
            LOG "PROCESS_USER_INPUT: Removed .log.err files"
            exit 0
        fi

        if [ -z "${ui_option}" -a "$1" != "LICENSE" -a "$1" != "CONSENT" ] ; then
            ui_option=${DEFAULT_OPTION}
            if [ "$1" = "YES_OR_NO" ] ; then
                return 1
            else
                return
            fi
        elif [[ "${1}" == "PREINSTALL_SUMMARY" || "${1}" == "DRIVER_GROUP" || "${1}" == "DRIVER_PERM" ]] ; then
            return
        elif [[ "${1}" == "KERNEL_SRC_DIR" || "${1}" == "MAKE_CMD" || "${1}" == "COMPILER" ]] ; then
            return
        elif [[ "${1}" == "UPDATE_INSTALL_LOC" ]]; then
            return
        elif [[ "${1}" == "YES_OR_NO" ]] ; then
            if [[ "${ui_option}" == "y" || "${ui_option}" == "Y" ]] ; then
                LOG "PROCESS_USER_INPUT: User entered ${ui_option}"
                return 0
            elif [[ "${ui_option}" == "n" || "${ui_option}" == "N" ]] ; then
                LOG "PROCESS_USER_INPUT: User entered ${ui_option}"
                return 1
            else
                print_msg "Incorrect option, please try again."
                print_nnl "Please enter a selection or press \"Enter\" to accept default choice"
                if [ -n "${DEFAULT_OPTION}" ] ; then
                    print_nnl " [${DEFAULT_OPTION}]"
                fi
                print_nnl ": "
            fi
        elif [[ "${1}" == "LICENSE" ]] ; then
            if [[ "${ui_option}" == "accept" ]] ; then
                return 0
            elif [[ "${ui_option}" == "decline" ]] ; then
                return 1
            else
                print_msg "Incorrect option, please try again."
                print_nnl "Type \"accept\" to continue or \"decline\" to exit: "
            fi
        elif [[ "${1}" == "CONSENT" ]] ; then
            if [[ "${ui_option}" == "yes" || "${ui_option}" == "y" ]] ; then
                return 0
            elif [[ "${ui_option}" == "no" || "${ui_option}" == "n" ]] ; then
                return 1
            else
                print_msg "Incorrect option, please try again."
                print_nnl "Type \"yes\" to agree or \"no\" to decline: "
            fi
        elif [[ "${ui_option}" < 0 || "${ui_option}" > "$1" ]] ; then
            print_msg "Incorrect option, please try again."
            print_nnl "Please enter a selection or press \"Enter\" to accept default choice"
            if [ -n "${DEFAULT_OPTION}" ] ; then
                print_nnl " [${DEFAULT_OPTION}]"
            fi
            print_nnl ": "
        else
            return
        fi
    done
}

goto_screen()
{
    current_screen=${FUNCNAME[1]}
    if [ "${collection_mode}" = "driverless" ] ; then
        SCREEN_LINEAR_ORDER=(${screen_1} ${screen_2} ${screen_4})
    else
        SCREEN_LINEAR_ORDER=(${screen_1} ${screen_2} ${screen_3} ${screen_4})
    fi
    total_screens=${#SCREEN_LINEAR_ORDER[@]}
    last_screen=$( expr ${total_screens} - 1 )
    ret_val=0

    called=
    itr=0
    # print_debug "total_screens: $total_screens | last_screen: $last_screen"
    # print_debug "current_screen: ${current_screen}"
    for screen_name in ${SCREEN_LINEAR_ORDER[@]} ; do
        itr_prev=$( expr ${itr} - 1 )
        itr_next=$( expr ${itr} + 1 )

        # print_debug "screen_name: ${screen_name} | itr: $itr"

        if [[ "${current_screen}" != "${screen_name}" ]] ; then
            ret_val=1
            itr=$( expr ${itr} + 1 )
            continue
        fi

        # print_debug "option: $1"

        called=1
        if [[ "${1}" == "next" ]] ; then
            if [[ "${itr}" == "${last_screen}" || "$*" == *"no-next"* ]] ; then
                LOG "GOTO_SCREEN: No next option in screen ${current_screen}"
                ret_val=1
            else
                if [ "${SCREEN_LINEAR_ORDER[$itr_next]}" = "manage_driver_group_dialog_page" ] ; then
                    main_group_page_call=$( expr ${main_group_page_call} + 1 )
                    # set skip only when sub-group-page was updated first
                    if [ ${sub_group_page_update} -eq 1 -a ${main_group_page_call} -eq 1 ] ; then
                        LOG "GOTO_SCREEN: set skip manage_driver_group_dialog_page"
                        skip_page=1
                    fi
                    if [ -n "${skip_page}" ] ; then
                        LOG "GOTO_SCREEN: skipping manage_driver_group_dialog_page"
                        itr_next=$( expr ${itr_next} + 1 )
                    fi
                fi
                LOG "GOTO_SCREEN: Calling ${SCREEN_LINEAR_ORDER[$itr_next]}"
                ${SCREEN_LINEAR_ORDER[$itr_next]}
                ret_val=0
            fi
            break
        elif [[ "${1}" == "back" ]] ; then
            if [[ "${itr}" == "0" || "$*" == *"no-back"* ]] ; then
                LOG "GOTO_SCREEN: No back option in screen ${current_screen}"
                ret_val=1
            else
                if [ "${SCREEN_LINEAR_ORDER[$itr_prev]}" = "manage_driver_group_dialog_page" ] ; then
                    main_group_page_call=$( expr ${main_group_page_call} + 1 )
                    # set skip only when sub-group-page was updated first
                    if [ ${sub_group_page_update} -eq 1 -a ${main_group_page_call} -eq 1 ] ; then
                        LOG "GOTO_SCREEN: set skip manage_driver_group_dialog_page"
                        skip_page=1
                    fi
                    if [ -n "${skip_page}" ] ; then
                        LOG "GOTO_SCREEN: skipping manage_driver_group_dialog_page"
                        itr_prev=$( expr ${itr_prev} - 1 )
                    fi
                fi
                LOG "GOTO_SCREEN: Calling ${SCREEN_LINEAR_ORDER[$itr_prev]}"
                ${SCREEN_LINEAR_ORDER[$itr_prev]}
                ret_val=0
            fi
            break
        fi

        itr=$( expr ${itr} + 1 )
    done

    if [ -n "${called}" ] ; then
        return ${ret_val}
    fi

    for screen_name in ${BACK_SCREEN_MAP_1[@]} ; do
        # print_debug "1screen_name: ${screen_name} | itr: $itr"

        if [[ "${current_screen}" != "${screen_name}" ]] ; then
            ret_val=1
            continue
        fi

        # print_debug "option: $1"

        called=1
        if [[ "${1}" == "back" && "$*" != *"no-back"* ]] ; then
            LOG "GOTO_SCREEN: Calling ${BACK_SCREEN_MAP_1[0]}"
            ${BACK_SCREEN_MAP_1[0]}
            ret_val=0
        else
            LOG "GOTO_SCREEN: No back option in this screen. Skipping..."
            ret_val=1
        fi
        break
    done

    if [ -n "${called}" ] ; then
        return ${ret_val}
    fi

    for screen_name in ${BACK_SCREEN_MAP_2[@]} ; do
        # print_debug "2screen_name: ${screen_name} | itr: $itr"

        if [[ "${current_screen}" != "${screen_name}" ]] ; then
            ret_val=1
            continue
        fi

        # print_debug "option: $1"

        called=1
        if [[ "${1}" == "back" && "$*" != *"no-back"* ]] ; then
            LOG "GOTO_SCREEN: Calling ${BACK_SCREEN_MAP_2[0]}"
            ${BACK_SCREEN_MAP_2[0]}
            ret_val=0
        else
            LOG "GOTO_SCREEN: No back option in this screen. Skipping..."
            ret_val=1
        fi
        break
    done

    # next is being called from second main screen update_install_location
    if [ "${current_screen}" = "update_install_location" -a "$1" = "next" ] ; then
        LOG "GOTO_SCREEN: next selected in ${current_screen}"
        ret_val=0
        called=1
    fi

    if [ -z "${called}" ] ; then
        LOG_N_PRINT_ERR "GOTO_SCREEN" "Invalid screen name ${current_screen}. Exiting..."
        exit ${SEP_RC_INVALID_SCREEN_NAME}
    fi

    return ${ret_val}
}

process_user_input_2()
{
    if [ ${non_interactive} -eq 1 ] ; then
        return
    fi

    read ui_option

    if [ -z "${ui_option}" ] ; then
        ui_option=${DEFAULT_OPTION}
    fi

    LOG "PROCESS_USER_INPUT_2: input is \"${ui_option}\" in ${FUNCNAME[1]}"

    if [ "${ui_option}" = "q" ] ; then
        LOG "PROCESS_USER_INPUT_2: User manually quit"
        # delete temporarily created .log.err files
        ${RM} -rf ${LOG_PATH_PREFIX}/*.log.err > /dev/null 2>&1
        LOG "PROCESS_USER_INPUT: Removed .log.err files"
        exit 0
    fi

    return 0
}

exit_the_program()
{
    STEP_NUM=
    STEP_NAME="Exit"
    OPTION_LIMIT=
    DEFAULT_OPTION="n"

    print_header
    print_msg "Do you want to exit the installation? (yY/nN)"
    print_footer ${DEFAULT_OPTION}

    process_user_input "YES_OR_NO"
    if [ $? -eq 0 ] ; then
        LOG "EXIT_THE_PROGRAM: User manually quit"
        exit 0
    fi
}

show_license()
{
    if [ ${non_interactive} -eq 1 ] ; then
        return
    fi

    clear

    # --no-init does not clear screen at EOF
    # --dumb does not print errors in old dumb terminals
    # --QUIT-AT-EOF exits at first hit on EOF
    # --quit-on-intr exit on Ctrl-C with error code 2
    # -P print prompt
    less --no-init --dumb --QUIT-AT-EOF --quit-on-intr -P"[Press space to continue]" ${LICENSE_FILE}
    ret_code=$?
    if [ ${ret_code} -ne 0 ] ; then
        if [ ${ret_code} -eq 2 ] ; then
            LOG "SHOW_LICENSE: User pressed Ctrl+C"
            exit_the_program
            show_license
        else
            LOG "SHOW_LICENSE: License ${LICENSE_FILE} not found"
            finish_dialog_page ${SEP_RC_LICENSE_NOT_AVAILABLE}
        fi
    fi
    print_footer "LICENSE"

    process_user_input "LICENSE"
    ret_code=$?
    if [ ${ret_code} -ne 0 ] ; then
        exit_the_program
        show_license
    fi

    LOG "SHOW_LICENSE: License accepted"
    LICENSE_ACCEPTED=1
}

show_collect_consent()
{
    if [ ${non_interactive} -eq 1 ] ; then
        return
    fi

    LOG "SHOW_ISIP_CONSENT: ISIP_CONSENT_FILE - ${ISIP_CONSENT_FILE}"
    LOG "SHOW_ISIP_CONSENT: ISIP_FILE - ${ISIP_FILE}"

    clear

    less --no-init --dumb --QUIT-AT-EOF --quit-on-intr -P"[Press space to continue]" ${ISIP_CONSENT_FILE}
    ret_code=$?
    if [ ${ret_code} -ne 0 ] ; then
        if [ ${ret_code} -eq 2 ] ; then
            LOG "SHOW_ISIP_CONSENT: User pressed Ctrl+C"
            exit_the_program
            show_collect_consent
        else
            LOG "SHOW_ISIP_CONSENT: ISIP consent file ${ISIP_CONSENT_FILE} not found"
            finish_dialog_page ${SEP_RC_CONSENT_NOT_AVAILABLE}
        fi
    fi

    print_footer "CONSENT"

    process_user_input "CONSENT"
    ret_code=$?

    if [ $ret_code -eq 0 ] ; then
        GA_CONSENT_ACCEPTED=1
        LOG "SHOW_ISIP_CONSENT: ISIP consent accepted"
    else
        LOG "SHOW_ISIP_CONSENT: ISIP consent not accepted"
        return
    fi

    if [ ! -d ${ISIP_LOCATION} ] ; then
        mkdir -p ${ISIP_LOCATION}
        LOG "SHOW_ISIP_CONSENT: ISIP folder ${ISIP_LOCATION} created"
    else
        LOG "SHOW_ISIP_CONSENT: ISIP folder ${ISIP_LOCATION} exists"
    fi

    if [ -f "${ISIP_FILE}" ] ; then
        ${RM} ${SEP_FORCE} ${ISIP_FILE}
        LOG "SHOW_ISIP_CONSENT: Removed existing ${ISIP_FILE} file"
    else
        LOG "SHOW_ISIP_CONSENT: ISIP file ${ISIP_FILE} does not exist, nothing to remove"
    fi

    echo ${GA_CONSENT_ACCEPTED} > ${ISIP_FILE}
}

user_type_dialog_page()
{
    if [[ ${non_interactive} -eq 1 || "${USER}x" == "rootx" ]] ; then
        LOG "USER_TYPE_DIALOG_PAGE: User: ${USER}"
        return
    fi

    STEP_NUM=
    STEP_NAME="User Type Selection"
    OPTION_LIMIT=2
    DEFAULT_OPTION=1

    print_header
    print_tabbed_msg "[1] Run as sudo user [default]"
    print_tabbed_msg "[2] Run as root"
    print_footer ${DEFAULT_OPTION}
    process_user_input ${OPTION_LIMIT}

    USER_TYPE_SUDO=1
    if [ -n "${ui_option}" ] ; then
        if [ ${ui_option} -eq 2 ] ; then
            USER_TYPE_ROOT=1
            USER_TYPE_SUDO=
        fi
    fi
}

check_user_type()
{
    LOG "CHECK_USER_TYPE: options \"${OPTIONS}\""

    if [ "${USER}x" = "x" ] ; then
        USER=`whoami`
    fi

    if [ "${USER}x" = "rootx" ] ; then
        return
    fi

    OPTIONS="${OPTIONS} -up ${MY_NAME} -gp ${MY_GROUP}"

    LOG "CHECK_USER_TYPE: options \"${OPTIONS}\""

    if [ -z "${BUSYBOX_SHELL}" ] ; then
        if [ -n "${USER_TYPE_ROOT}" ] ; then
            LOG_N_PRINT_MSG "CHECK_USER_TYPE" "Attempting to login as \"root\" user..."
            exec ${SU} -c "/bin/bash ${SCRIPT} ${OPTIONS}"
        elif [ -n "${USER_TYPE_SUDO}" ] ; then
            if [ ${non_interactive} -eq 0 ] ; then
                LOG_N_PRINT_MSG "CHECK_USER_TYPE" "Attempting to login as \"sudo\" user..."
            fi
            exec sudo sh -c "/bin/bash ${SCRIPT} ${OPTIONS}"
        else
            exit 1
        fi
        exit $?
    fi
}

uninstall_boot_script()
{
    local driver_src_path=$1
    local boot_script_log=$(GET_LOG_NAME "boot_script_uninstall")

    LOG "UNINSTALL_BOOT_SCRIPT: Un-installing ${TOOL_NAME_CAPS} drivers boot_script. Logging details to ${boot_script_log}"

    ./boot-script -q >> ${boot_script_log} 2>&1
    bs_query_ret_code=$?
    # return 0 if already installed
    # return 107 if not installed
    if [ ${bs_query_ret_code} -eq 107 ] ; then
        echo "UNINSTALL_BOOT_SCRIPT: boot_script not installed..." >> ${boot_script_log}
        return
    fi

    grep -rn /etc/init.d/sep* -e "DRIVER_DIR=${driver_src_path}." >> ${boot_script_log} 2>&1
    if [ $? -ne 0 ] ; then
        echo "UNINSTALL_BOOT_SCRIPT: boot_script does not belong to this installation. Not uninstalling..." >> ${boot_script_log}
        return
    fi

    ./boot-script -u >> ${boot_script_log} 2>&1
    bs_uninstall_ret_code=$?
    if [ ${bs_uninstall_ret_code} -ne 0 ] ; then
        cd - > /dev/null 2>&1
        finish_dialog_page ${SEP_RC_BOOTSCRIPT_UNINSTALL_FAIL}
    fi
}

uninstall_driver()
{
    local driver_src_path=${INSTALL_PATH_BASE}/${binary_name}/${SEPDK}
    local driver_log=$(GET_LOG_NAME uninstall_${binary_name})
    driver_log_err=${driver_log}.err
    LOG "UNINSTALL_DRIVER: Logging uninstall details to ${driver_log}"

    cd ${driver_src_path}
    ./rmmod-sep -s >> ${driver_log} 2> ${driver_log_err}
    rmmod_result=$?
    cat ${driver_log_err} >> ${driver_log} 2>&1
    LOG "UNINSTALL_DRIVER: rmmod result: ${rmmod_result}"

    # skip in case of success and socperf or pax not unloaded due other drivers using it
    if [ ${rmmod_result} -ne 0 -a ${rmmod_result} -ne 247 ] ; then
        ./build-driver --verbose -ni >> ${driver_log} 2> ${driver_log_err}
        cat ${driver_log_err} >> ${driver_log} 2>&1
        ./rmmod-sep -s >> ${driver_log} 2> ${driver_log_err}
        rmmod_result=$?
        cat ${driver_log_err} >> ${driver_log} 2>&1
        LOG "UNINSTALL_DRIVER: rmmod result: ${rmmod_result}"
        # skip in case of success and socperf or pax not unloaded due other drivers using it
        if [ ${rmmod_result} -ne 0 -a ${rmmod_result} -ne 247 ] ; then
            ret_code=${SEP_RC_DRIVER_UNLOAD_FAILURE}
            LOG "UNINSTALL_DRIVER: Check ${driver_log} for more details!"
            cd - > /dev/null 2>&1
            finish_dialog_page ${ret_code}
        fi
    fi

    LOG "UNINSTALL_DRIVER: Sampling drivers removed successfully"

    if [ "$1" = "rm_boot_script" ] ; then
        uninstall_boot_script "${driver_src_path}"
    fi

    cd - > /dev/null 2>&1
}

check_group_exists()
{
    check_local_group_exists
    if [ $? -ne 0 ] ; then
        check_nis_group_exists
        if [ $? -eq 0 ] ; then
            LOG "CHECK_DRIVER_GROUP: Network driver group ${DRIVER_GROUP} exists"
            return
        fi
    else
        LOG "CHECK_DRIVER_GROUP: Local driver group ${DRIVER_GROUP} exists"
        return
    fi
    LOG "CHECK_DRIVER_GROUP: Driver group ${DRIVER_GROUP} does not exist"

    # STEP_NUM=1
    # TOTAL_STEPS=1
    # STEP_NAME="Options > Driver access group"

    # print_header
    # print_msg "The group ${DRIVER_GROUP} does not exist and the installer will create a local group."
    # print_msg ""
    # print_msg "Providing 'no' will exit the installation"
    # print_footer "CONFIRMATION"
    # process_user_input "DRIVER_GROUP"

    # if [[ "${ui_option}" == 'n' || "${ui_option}" == 'N' || "${ui_option}" == "no" || "${ui_option}" == "No" ]] ; then
    #     LOG "CHECK_DRIVER_GROUP: User did not confirm and manually quit"
    #     exit 0
    # fi

    # LOG "CHANGE_DRIVER_GROUP: User provided the group ${DRIVER_GROUP}"
}

# change_driver_group_dialog_page()
# {
#     STEP_NUM=1
#     TOTAL_STEPS=1
#     STEP_NAME="Options > Driver access group"
#     DEFAULT_OPTION=${DEFAULT_DRIVER_GROUP}

#     print_header
#     print_msg "Please provide the group name you wish to use"
#     print_msg ""
#     print_footer ${DEFAULT_DRIVER_GROUP}
#     process_user_input "DRIVER_GROUP"

#     if [ "${ui_option}" != "${DEFAULT_OPTION}" ] ; then
#         DRIVER_GROUP="${ui_option}"
#     fi
# }

# Yocto machine does not support "multi_lib", means only only /lib exists instead of lib32|64.
# In this case we need to make a symbolic link from lib to lib32|64.
check_for_prerequisites()
{
    if [ -d "${LIB}${OS_BITNESS}" ] ; then
        return
    fi

    STEP_NUM=1
    TOTAL_STEPS=1
    STEP_NAME="Pre-requisites"
    OPTION_LIMIT=2
    DEFAULT_OPTION=1

    if [ ${non_interactive} -eq 0 ] ; then
        print_header
        print_tabbed_msg "${LIB}${OS_BITNESS} is unavailable in the system."
        print_tabbed_msg "${TOOL_NAME_CAPS} may not work if ${LIB}${OS_BITNESS} does not exist."
        print_msg ""
    fi

    if [ -d "${LIB}" ] ; then
        if [ ${non_interactive} -eq 0 ] ; then
            print_tabbed_msg "Do you want to make a symbolic link from ${LIB} to ${LIB}${OS_BITNESS}?"
            print_tabbed_msg "[1] Yes"
            print_tabbed_msg "[2] Skip"
            print_footer ${DEFAULT_OPTION}
            process_user_input ${OPTION_LIMIT}

            if [ -n "${ui_option}" ] ; then
                if [ ${ui_option} -eq 1 ] ; then
                    make_soft_link_for_system_lib
                    return
                elif [ ${ui_option} -eq 2 ] ; then
                    return
                fi
            fi
        else
            if [ ${yocto} -eq 1 ] ; then
                make_soft_link_for_system_lib
            fi
        fi
    else
        if [ ${non_interactive} -eq 0 ] ; then
            print_tabbed_msg "Cannot find ${LIB} as well."
            print_tabbed_msg "If you know the path to shared library directory, make a symbolic link to ${LIB}${OS_BITNESS}"
            print_footer "PREINSTALL_SUMMARY"
            process_user_input
        else
            print_err ""
            LOG_N_PRINT_ERR "CHECK_FOR_PREREQ" "ERROR: Cannot find ${LIB}."
            LOG_N_PRINT_ERR "CHECK_FOR_PREREQ" "       If you know the path to shared library directory, make a symbolic link to ${LIB}${OS_BITNESS}"
            exit ${SEP_RC_SYS_LIB_NOT_FOUND}
            print_err ""
        fi
        return
    fi

    check_for_prerequisites
}

make_soft_link_for_system_lib()
{
    ln -s "${LIB}" "${LIB}${OS_BITNESS}"
}

verify_install_package_existence()
{
    TAR_NAME=$( ${LS} | ${GREP} -E ${PACKAGE_NAME_REGEX} )

    LOG "VERIFY_INSTALL_PACKAGE_EXIST: Checking for install package"

    if [ -z "${TAR_NAME}" ] ; then
        finish_dialog_page ${SEP_RC_INSTALL_PACKAGE_NOT_FOUND}
    fi

    LOG "VERIFY_INSTALL_PACKAGE_EXIST: [${TAR_NAME}]"
}

set_permissions()
{
    LOG "SET_PERMISSIONS: Updating the permission of installed ${TOOL_NAME_CAPS} package"
    if [ -n "${install_folder_up}" ] ; then
        ${CHOWN} -R ${install_folder_up} ${ORG_INSTALL_PATH}
    else
        ${CHOWN} -R ${MY_NAME} ${ORG_INSTALL_PATH}
    fi
    if [ -n "${install_folder_gp}" ] ; then
        ${CHGRP} -R ${install_folder_gp} ${ORG_INSTALL_PATH}
    else
        ${CHGRP} -R ${MY_GROUP} ${ORG_INSTALL_PATH}
    fi

    if [ ${GA_CONSENT_ACCEPTED} -eq 1 -a -n "${SUDO_USER}" ] ; then
        LOG "SET_PERMISSIONS: Updating the permission of ${ISIP_FILE}"
        LOG "SET_PERMISSIONS:   Cmd: ${CHOWN} -R ${SUDO_USER} ${ISIP_LOCATION}"
        ${CHOWN} -R ${SUDO_USER} ${ISIP_LOCATION}
    fi
}

check_local_group_exists()
{
    groupmod ${DRIVER_GROUP} > /dev/null 2>&1
    return $?
}

check_nis_group_exists()
{
    ypcat group 2> /dev/null | ${CUT} -d : -f1 | ${GREP} -E "^${DRIVER_GROUP}$" > /dev/null 2>&1
    return $?
}

add_driver_group()
{
    check_local_group_exists && local_group_exists=1
    check_nis_group_exists && nis_group_exists=1

    if [ -z "${local_group_exists}" -a -z "${nis_group_exists}" ] ; then
        LOG "ADD_DRIVER_GROUP: Creating group ${DRIVER_GROUP}"
        groupadd ${DRIVER_GROUP} > /dev/null 2>&1
        # if [ $? -ne 0 ]; then
        #     finish_dialog_page 509
        # fi
    fi
}

untar_package()
{
    # delete temporarily created .log.err files if any during uninstall
    ${RM} -rf ${LOG_PATH_PREFIX}/*.log.err > /dev/null 2>&1
    LOG "UNTAR_PACKAGE: Removed .log.err files fi any created during uninstall"

    TAR_NAME=$( ${LS} | ${GREP} -E ${PACKAGE_NAME_REGEX} )

    PACKAGE_NAME=${TAR_NAME%${PACKAGE_EXT}}
    local temp=${PACKAGE_NAME##*_}
    BUILD_NUMBER=${temp%%.*}
    temp=${PACKAGE_NAME#*_}
    VERSION_NUMBER=${temp%%_*}

    ORG_INSTALL_PATH=${INSTALL_PATH_BASE}/${PACKAGE_NAME}
    LOG "UNTAR_PACKAGE: package name and path is ${ORG_INSTALL_PATH}"
    LOG "UNTAR_PACKAGE: build# is ${BUILD_NUMBER}"
    LOG "UNTAR_PACKAGE: version# is ${VERSION_NUMBER}"

    if [ ${install_tool} -eq 0 ] ; then
        return
    fi

    if [ ! -d ${ORG_INSTALL_PATH} ] ; then
        mkdir -p ${ORG_INSTALL_PATH}
    else
        finish_dialog_page ${SEP_RC_ALREADY_INSTALLED}
    fi

    LOG "UNTAR_PACKAGE: Extracting the package"
    if [ ${non_interactive} -eq 0 ] ; then
        print_msg ${LONG_DASH}
        print_msg "Extracting package"
    fi
    ${TAR} --warning=no-timestamp -xf ${TAR_NAME} -C ${ORG_INSTALL_PATH} >> ${LOG_NAME} 2>&1
    if [ $? -ne 0 ] ; then
        ${RM} -rf ${ORG_INSTALL_PATH}
        finish_dialog_page ${SEP_RC_UNPACK_FAILURE}
    fi

    if [ -L ${INSTALL_PATH} ] ; then
        unlink ${INSTALL_PATH}
    fi
    ${LN} -s ${ORG_INSTALL_PATH} ${INSTALL_PATH}

    set_permissions

    return 0
}

build_driver()
{
    if [ "${load_driver}" = "no" ] ; then
        return
    fi

    local driver_log=$(GET_LOG_NAME "build")
    driver_log_err=${driver_log}.err

    if [ ! -d ${ORG_INSTALL_PATH} ] ; then
        finish_dialog_page ${SEP_RC_NOT_INSTALLED}
    fi

    BUILD_ARGS="--c-compiler=${COMPILER} --make-command=${MAKE_CMD} --kernel-src-dir=${CURRENT_KERNEL_SRC_DIR} --verbose -ni"
    if [ "${udev}" = "no" ]; then
        BUILD_ARGS+=" --no-udev"
    fi

    if [ ${enable_maxlog} -eq 1 ] ; then
        BUILD_ARGS="${BUILD_ARGS} --maxlog"
    fi

    LOG "BUILD_DRIVER: Building driver. Logging details to ${driver_log}"
    echo "COMMAND USED: ./build-driver ${BUILD_ARGS}" >> ${driver_log} 2>&1

    if [ ${non_interactive} -eq 0 ] ; then
        print_msg ${LONG_DASH}
        print_msg "Building drivers"
    fi

    cd ${ORG_INSTALL_PATH}/${SEPDK}
    ./build-driver ${BUILD_ARGS} >> ${driver_log} 2> ${driver_log_err}
    build_ret_code=$?
    cat ${driver_log_err} >> ${driver_log} 2>&1
    LOG "BUILD_DRIVER: build_driver result: ${build_ret_code}"
    if [ ${build_ret_code} -ne 0 ] ; then
        cd - > /dev/null 2>&1
        finish_dialog_page ${SEP_RC_DRIVER_BUILD_FAILURE}
    fi

    cd - > /dev/null 2>&1

    return 0
}

load_sep_driver()
{
    if [ "${load_driver}" = "no" ] ; then
        return
    fi

    local driver_src_path=${ORG_INSTALL_PATH}/${SEPDK}
    local driver_log=$(GET_LOG_NAME "install")
    driver_log_err=${driver_log}.err

    add_driver_group

    LOG "LOAD_SEP_DRIVER: Installing ${TOOL_NAME_CAPS} drivers. Logging details to ${driver_log}"
    echo "COMMAND USED: ./rmmod-sep -s" >> ${driver_log} 2>&1
    cd ${driver_src_path}
    ./rmmod-sep -s >> ${driver_log} 2> ${driver_log_err}

    unload_ret_code=$?
    cat ${driver_log_err} >> ${driver_log} 2>&1
    LOG "LOAD_SEP_DRIVER: rmmod result: ${unload_ret_code}"
    # skip in case of success and socperf or pax not unloaded due other drivers using it
    if [ ${unload_ret_code} -ne 0 -a ${unload_ret_code} -ne 247 ] ; then
        ret_code=${SEP_RC_DRIVER_UNLOAD_FAILURE}
        LOG "LOAD_SEP_DRIVER: Check ${driver_log} for more details!"

        cd - > /dev/null 2>&1

        finish_dialog_page ${ret_code}
    fi

    INSMOD_ARGS="-g ${DRIVER_GROUP} -p ${DRIVER_PERM}"
    if [ "${udev}" = "no" ]; then
        INSMOD_ARGS+=" --no-udev"
    fi

    echo "COMMAND USED: ./insmod-sep ${INSMOD_ARGS}" >> ${driver_log} 2>&1

    if [ ${non_interactive} -eq 0 ] ; then
        print_msg ${LONG_DASH}
        print_msg "Loading drivers"
    fi

    ./insmod-sep ${INSMOD_ARGS} >> ${driver_log} 2> ${driver_log_err}
    load_ret_code=$?
    cat ${driver_log_err} >> ${driver_log} 2>&1
    LOG "LOAD_SEP_DRIVER: insmod result: ${ret_code}"
    if [ ${load_ret_code} -ne 0 ] ; then
        ret_code=${SEP_RC_DRIVER_LOAD_FAILURE}
        LOG "LOAD_SEP_DRIVER: Check ${driver_log} for more details!"

        cd - > /dev/null 2>&1

        finish_dialog_page ${ret_code}
    fi

    cd - > /dev/null 2>&1

    return 0
}

install_boot_script()
{
    if [ "${reload_driver}" = "no" ] ; then
        return
    fi

    local driver_src_path=${ORG_INSTALL_PATH}/${SEPDK}
    local boot_script_log=$(GET_LOG_NAME "boot_script_install")

    BS_ARGS="--c-compiler=${COMPILER} --make-command=${MAKE_CMD} -g ${DRIVER_GROUP} -p ${DRIVER_PERM}"

    LOG "INSTALL_BOOT_SCRIPT: Installing ${TOOL_NAME_CAPS} drivers boot_script. Logging details to ${boot_script_log}"
    echo "COMMAND USED: ./boot-script -q" >> ${boot_script_log} 2>&1
    cd ${driver_src_path}
    ./boot-script -q >> ${boot_script_log} 2>&1
    bs_query_ret_code=$?
    LOG "INSTALL_BOOT_SCRIPT: bs_query_ret_code: ${bs_query_ret_code}"
    # return 0 if already installed
    # return 107 if not installed
    if [ ${bs_query_ret_code} -eq 0 ] ; then
        echo "Overwriting the exisiting configuration..." >> ${boot_script_log}
    fi

    echo "COMMAND USED: ./boot-script -i ${BS_ARGS}" >> ${boot_script_log} 2>&1

    if [ ${non_interactive} -eq 0 ] ; then
        print_msg ${LONG_DASH}
        print_msg "Configuring ${TOOL_NAME_CAPS} driver reload during reboot..."
    fi

    ./boot-script -i ${BS_ARGS} >> ${boot_script_log} 2>&1
    bs_install_ret_code=$?
    LOG "INSTALL_BOOT_SCRIPT: boot_script result: ${bs_install_ret_code}"
    if [ ${bs_install_ret_code} -ne 0 ] ; then
        cd - > /dev/null 2>&1
        finish_dialog_page ${SEP_RC_BOOTSCRIPT_INSTALL_FAIL}
    fi

    cd - > /dev/null 2>&1
}

set_drvless_mode_invalid_screens()
{
    drvless_mode_invalid_screens=("1" "2" "3" "4" "5" "6" "7" "8")
}

unset_drvless_mode_invalid_screens()
{
    drvless_mode_invalid_screens=()
}

update_collection_mode_dialog_page()
{
    STEP_NUM=
    TOTAL_STEPS=
    STEP_NAME="Options > Collection mode"
    DEFAULT_OPTION=1

    common_params="no-next standard-2"
    print_footer_params="${common_params} default-value ${DEFAULT_OPTION}"

    print_header
    print_msg "Select the collection mode."
    print_msg ""
    print_tabbed_msg "[1] Driver (requires root access for sampling drivers installation)"
    print_tabbed_msg "[2] Driverless (leverages Linux Perf subsystem)"
    print_msg ""
    print_msg "Warning: The driverless mode may not enable all features that are"
    print_msg "         supported with driver collection mode"
    print_msg ""
    print_msg "Please refer to \"EMON Driverless Option\" topic in the user guide for"
    print_msg "pre-requisites and more details."
    print_footer_2 ${print_footer_params}

    while [ 1 ] ; do
        ret_val=1
        process_user_input_2 ${common_params}
        if [ "${ui_option}" = "n" ] ; then
            goto_screen next ${common_params}
        elif [ "${ui_option}" = "b" ] ; then
            goto_screen back ${common_params}
        else
            if [ "${ui_option}" = "1" ] ; then
                collection_mode="driver"
                load_driver="yes"
                reload_driver="no"
                load_driver_only="no"
                unset_drvless_mode_invalid_screens
            elif [ "${ui_option}" = "2" ] ; then
                collection_mode="driverless"
                load_driver="no"
                reload_driver="no"
                load_driver_only="no"
                install_tool=1
                set_drvless_mode_invalid_screens
            else
                print_footer_2 skip-options ${print_footer_params}
                continue
            fi
            goto_screen back ${common_params}
        fi
        ret_val=$?
        if [ ${ret_val} -eq 0 ] ; then
            break
        fi
        print_footer_2 skip-options ${print_footer_params}
    done

    return 0
}

change_load_drivers_page()
{
    STEP_NUM=
    TOTAL_STEPS=
    STEP_NAME="Options > Load drivers"
    DEFAULT_OPTION=1

    common_params="no-next"
    print_footer_params="${common_params} default-value ${DEFAULT_OPTION}"

    print_header
    print_msg "The drivers are required to be loaded for data collection."
    print_msg "Select yes to load the drivers."
    print_msg ""
    print_tabbed_msg "[1] Yes"
    print_tabbed_msg "[2] No"
    print_footer_2 ${print_footer_params}

    while [ 1 ] ; do
        ret_val=1
        process_user_input_2 ${common_params}
        if [ "${ui_option}" = "n" ] ; then
            goto_screen next ${common_params}
        elif [ "${ui_option}" = "b" ] ; then
            goto_screen back ${common_params}
        else
            if [ "${ui_option}" = "1" ] ; then
                load_driver="yes"
                collection_mode="driver"
            elif [ "${ui_option}" = "2" ] ; then
                load_driver="no"
                reload_driver="no"
                load_driver_only="no"
            else
                print_footer_2 skip-options ${print_footer_params}
                continue
            fi
            goto_screen back ${common_params}
        fi
        ret_val=$?
        if [ ${ret_val} -eq 0 ] ; then
            break
        fi
        print_footer_2 skip-options ${print_footer_params}
    done

    return 0
}

change_driver_reload_setup_page()
{
    STEP_NUM=
    TOTAL_STEPS=
    STEP_NAME="Options > Reload drivers during boot"
    DEFAULT_OPTION=2

    common_params="no-next"
    print_footer_params="${common_params} default-value ${DEFAULT_OPTION}"

    print_header
    print_msg "Select yes to load the drivers during boot time."
    print_msg ""
    print_tabbed_msg "[1] Yes"
    print_tabbed_msg "[2] No"
    print_footer_2 ${print_footer_params}

    while [ 1 ] ; do
        ret_val=1
        process_user_input_2 ${common_params}
        if [ "${ui_option}" = "n" ] ; then
            goto_screen next ${common_params}
        elif [ "${ui_option}" = "b" ] ; then
            goto_screen back ${common_params}
        else
            if [ "${ui_option}" = "1" ] ; then
                reload_driver="yes"
                load_driver="yes"
            elif [ "${ui_option}" = "2" ] ; then
                reload_driver="no"
            else
                print_footer_2 skip-options ${print_footer_params}
                continue
            fi
            goto_screen back ${common_params}
        fi
        ret_val=$?
        if [ ${ret_val} -eq 0 ] ; then
            break
        fi
        print_footer_2 skip-options ${print_footer_params}
    done

    return 0
}

change_load_drivers_only_page()
{
    STEP_NUM=
    TOTAL_STEPS=
    STEP_NAME="Options > Complete failed installation"
    DEFAULT_OPTION=2

    tar_name=$( ${LS} | ${GREP} -E ${PACKAGE_NAME_REGEX} )
    package_name=${tar_name%${PACKAGE_EXT}}

    ${LS} ${INSTALL_PATH_BASE} | ${GREP} -w ${package_name} > /dev/null 2>&1
    if [ $? -eq 0 ] ; then
        package_installed=1
    else
        package_installed=0
        DEFAULT_OPTION=b
    fi

    common_params="no-next"
    print_footer_params="${common_params} default-value ${DEFAULT_OPTION}"

    print_header
    if [ ${package_installed} -eq 1 ] ; then
        print_msg "Found ${package_name} installed at ${INSTALL_PATH_BASE}."
        print_msg "Select yes to complete the installation."
        print_msg ""
        print_tabbed_msg "[1] Yes"
        print_tabbed_msg "[2] No"
    else
        print_msg "${package_name} not found at ${INSTALL_PATH_BASE}."
        print_msg "This option is not applicable."
    fi
    
    print_footer_2 ${print_footer_params}

    while [ 1 ] ; do
        ret_val=1
        process_user_input_2 ${common_params}
        if [ "${ui_option}" = "n" ] ; then
            goto_screen next ${common_params}
        elif [ "${ui_option}" = "b" ] ; then
            goto_screen back ${common_params}
        else
            if [ "${ui_option}" = "1" ] ; then
                # do not make any changes if package is not installed
                if [ ${package_installed} -eq 1 ] ; then
                    load_driver_only="yes"
                    load_driver="yes"
                    install_tool=0
                fi
            elif [ "${ui_option}" = "2" ] ; then
                load_driver_only="no"
                install_tool=1
            else
                print_footer_2 skip-options ${print_footer_params}
                continue
            fi
            goto_screen back ${common_params}
        fi
        ret_val=$?
        if [ ${ret_val} -eq 0 ] ; then
            break
        fi
        print_footer_2 skip-options ${print_footer_params}
    done

    return 0
}

change_driver_perm_dialog_page()
{
    STEP_NUM=
    TOTAL_STEPS=
    STEP_NAME="Options > Driver access permission"
    DEFAULT_OPTION=b

    common_params="no-next standard-2"
    print_footer_params="${common_params} default-value ${DEFAULT_OPTION}"

    print_header
    print_tabbed_msg "Driver permission: ${DRIVER_PERM}"
    print_msg ""
    print_msg "To restrict access to the driver, you can set custom permissions on driver"
    print_msg "files."
    print_msg "Both representations such an octal number (like 660) and symbolic form (like"
    print_msg "ug=rw) are accepted. The default permission is ${DEFAULT_DRIVER_PERM}."
    print_footer_2 ${print_footer_params}

    while [ 1 ] ; do
        ret_val=1
        process_user_input_2 ${common_params}
        if [ "${ui_option}" = "n" ] ; then
            goto_screen next ${common_params}
        elif [ "${ui_option}" = "b" ] ; then
            goto_screen back ${common_params}
        else
            DRIVER_PERM="${ui_option}"
            # check_driver_perm_validity
            goto_screen back ${common_params}
        fi
        ret_val=$?
        if [ ${ret_val} -eq 0 ] ; then
            break
        fi
        print_footer_2 skip-options ${common_params}
    done

    return 0
}

update_compiler_dialog_page()
{
    STEP_NUM=
    TOTAL_STEPS=
    STEP_NAME="Options > C Compiler"
    DEFAULT_OPTION=b

    common_params="no-next standard-2"
    print_footer_params="${common_params} default-value ${DEFAULT_OPTION}"

    print_header
    print_tabbed_msg "Compiler: ${COMPILER}"
    print_msg ""
    print_msg "Specify the full path and name of the C compiler to use for building"
    print_msg "the driver. The default compiler is ${DEFAULT_COMPILER}."
    print_footer_2 ${print_footer_params}

    while [ 1 ] ; do
        ret_val=1
        process_user_input_2 ${common_params}
        if [ "${ui_option}" = "n" ] ; then
            goto_screen next ${common_params}
        elif [ "${ui_option}" = "b" ] ; then
            goto_screen back ${common_params}
        else
            COMPILER=${ui_option}
            goto_screen back ${common_params}
        fi
        ret_val=$?
        if [ ${ret_val} -eq 0 ] ; then
            break
        fi
        print_footer_2 skip-options ${print_footer_params}
    done

    return 0
}

update_make_cmd_dialog_page()
{
    STEP_NUM=
    TOTAL_STEPS=
    STEP_NAME="Options > Make Command"
    DEFAULT_OPTION=b

    common_params="no-next standard-2"
    print_footer_params="${common_params} default-value ${DEFAULT_OPTION}"

    print_header
    print_tabbed_msg "Make command: ${MAKE_CMD}"
    print_msg ""
    print_msg "Specify the full path and name of the make command to use for building"
    print_msg "the driver. The default make command is ${DEFAULT_MAKE_CMD}."
    print_footer_2 ${print_footer_params}

    while [ 1 ] ; do
        ret_val=1
        process_user_input_2 ${common_params}
        if [ "${ui_option}" = "n" ] ; then
            goto_screen next ${common_params}
        elif [ "${ui_option}" = "b" ] ; then
            goto_screen back ${common_params}
        else
            MAKE_CMD=${ui_option}
            goto_screen back ${common_params}
        fi
        ret_val=$?
        if [ ${ret_val} -eq 0 ] ; then
            break
        fi
        print_footer_2 skip-options ${print_footer_params}
    done

    return 0
}

update_kernel_src_dialog_page()
{
    STEP_NUM=
    TOTAL_STEPS=
    STEP_NAME="Options > Kernel Source Directory"
    DEFAULT_OPTION=b

    common_params="no-next standard-2"
    print_footer_params="${common_params} default-value ${DEFAULT_OPTION}"

    print_header
    print_tabbed_msg "Kernel src dir: ${CURRENT_KERNEL_SRC_DIR}"
    print_msg ""
    print_msg "Specify the full path to the directory where system kernel header files"
    print_msg "are located. The default kernel src dir is ${DEFAULT_KERNEL_SRC_DIR}."
    print_footer_2 ${print_footer_params}

    while [ 1 ] ; do
        ret_val=1
        process_user_input_2 ${common_params}
        if [ "${ui_option}" = "n" ] ; then
            goto_screen next ${common_params}
        elif [ "${ui_option}" = "b" ] ; then
            goto_screen back ${common_params}
        else
            CURRENT_KERNEL_SRC_DIR=${ui_option}
            goto_screen back ${common_params}
        fi
        ret_val=$?
        if [ ${ret_val} -eq 0 ] ; then
            break
        fi
        print_footer_2 skip-options ${print_footer_params}
    done

    return 0
}

strip_error_log()
{
    if [ -z "${driver_log_err}" ] ; then
        LOG "STRIP_ERROR_LOG: No file ${driver_log_err}. Returning..."
        return
    fi

    local file_out=$(cat ${driver_log_err} 2> /dev/null)
    if [ -z "${file_out}" ] ; then
        LOG "STRIP_ERROR_LOG: Empty ${driver_log_err}. Returning..."
        return
    fi

    # remove empty lines at the beginning
    while [ 1 ] ; do
        startline=$(head -n 1 ${driver_log_err} 2> /dev/null)
        if [ -z "${startline}" ] ; then
            sed -i '1d' ${driver_log_err} > /dev/null 2>&1
        else
            break
        fi
    done

    # remove empty lines at the end
    while [ 1 ] ; do
        endline=$(tail -n 1 ${driver_log_err} 2> /dev/null)
        if [ -z "${endline}" ] ; then
            sed -i '$d' ${driver_log_err} > /dev/null 2>&1
        else
            break
        fi
    done

    LOG "STRIP_ERROR_LOG: Stripped ${driver_log_err}"
}

print_error_log()
{
    if [ -z "${driver_log_err}" ] ; then
        LOG "PRINT_ERROR_LOG: No file ${driver_log_err}. Returning..."
        return
    fi

    local file_out=$(cat ${driver_log_err} 2> /dev/null)
    if [ -z "${file_out}" ] ; then
        LOG "PRINT_ERROR_LOG: Empty ${driver_log_err}. Returning..."
        return
    fi

    echo "~~~" >&2
    if [ -n "$1" ] ; then
        echo "Warning(s) during driver load:" >&2
    fi
    echo "$(cat ${driver_log_err})" >&2
    if [ -z "$1" ] ; then
        echo "" >&2
        if [ ${non_interactive} -eq 1 ] ; then
            LOG_N_PRINT_ERR "FINISH_DIALOG_PAGE" "Use option \"--load-driver-only\" to re-install after resolving the issue"
        else
            LOG_N_PRINT_ERR "FINISH_DIALOG_PAGE" "Select option \"Complete failed installation\" to re-install after resolving the issue"
        fi
    fi
    echo "~~~" >&2
    echo "" >&2

    LOG "PRINT_ERROR_LOG: Printed ${driver_log_err}"
}

finish_dialog_page()
{
    if [ -z "$1" ] ; then
        ret_code=0
    else
        ret_code=$1
    fi

    strip_error_log

    if [[ ${non_interactive} -eq 1 && ${install_tool} -eq 0 && ${ret_code} -eq 0 && (${uninstall} -eq 1 || "${load_driver_only}" = "yes") ]] ; then
        if [ ${uninstall} -eq 1 ] ; then
            LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" "${TOOL_NAME_CAPS} uninstalled successfully."
        else
            LOG "FINISH_DIALOG_PAGE: Printing driver related warning if any to console"
            print_error_log success
            LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" "${TOOL_NAME_CAPS} drivers have been loaded successfully. Installation is complete!"
            LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" "Use \"source ${INSTALL_PATH}/sep_vars.sh\" to set up the environment."
        fi

        LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" ""
        LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" "Install log can be found at ${LOG_PATH_PREFIX}"

        exit $ret_code
    fi

    STEP_NUM=5
    TOTAL_STEPS=5
    STEP_NAME="Finish"
    DEFAULT_OPTION=

    print_footer_params="no-back no-next no-quit finish"

    print_header "Finish"
    case ${ret_code} in
        ${SEP_RC_ALREADY_INSTALLED})
            LOG_N_PRINT_ERR "FINISH_DIALOG_PAGE" "${TOOL_NAME_CAPS} package is already installed. Installation failed."
            LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" ""
            ;;
        ${SEP_RC_UNPACK_FAILURE})
            LOG_N_PRINT_ERR "FINISH_DIALOG_PAGE" "Package extraction failed. Installation failed."
            LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" ""
            ;;
        ${SEP_RC_NOT_INSTALLED})
            LOG_N_PRINT_ERR "FINISH_DIALOG_PAGE" "${TOOL_NAME_CAPS} is not installed."
            LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" ""
            ;;
        ${SEP_RC_DRIVER_BUILD_FAILURE})
            LOG "FINISH_DIALOG_PAGE: Printing build error to console"
            print_error_log
            LOG_N_PRINT_ERR "FINISH_DIALOG_PAGE" "Driver build failed. Installation is incomplete."
            LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" ""
            LOG_N_PRINT_ERR "FINISH_DIALOG_PAGE" "Check ${driver_log} for more details."
            ;;
        ${SEP_RC_DRIVER_UNLOAD_FAILURE})
            LOG "FINISH_DIALOG_PAGE: Printing driver unload error to console"
            print_error_log
            LOG_N_PRINT_ERR "FINISH_DIALOG_PAGE" "Driver unload failed. Installation is incomplete."
            LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" ""
            LOG_N_PRINT_ERR "FINISH_DIALOG_PAGE" "Check ${driver_log} for more details."
            ;;
        ${SEP_RC_DRIVER_LOAD_FAILURE})
            LOG "FINISH_DIALOG_PAGE: Printing driver load error to console"
            print_error_log
            LOG_N_PRINT_ERR "FINISH_DIALOG_PAGE" "Driver load failed. Installation is incomplete."
            LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" ""
            LOG_N_PRINT_ERR "FINISH_DIALOG_PAGE" "Check ${LOG_NAME} for more details."
            ;;
        ${SEP_RC_INSTALL_PACKAGE_NOT_FOUND})
            LOG_N_PRINT_ERR "FINISH_DIALOG_PAGE" "${TOOL_NAME_CAPS} install package not found. Installation failed."
            LOG_N_PRINT_ERR "FINISH_DIALOG_PAGE" "Install package should be placed at installer folder level."
            LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" ""
            ;;
        ${SEP_RC_BOOTSCRIPT_INSTALL_FAIL})
            LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" "${TOOL_NAME_CAPS} has been successfully installed at ${INSTALL_PATH}."
            LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" "Use \"source ${INSTALL_PATH}/sep_vars.sh\" to set up the environment."
            LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" ""
            LOG_N_PRINT_ERR "FINISH_DIALOG_PAGE" "Setting up ${TOOL_NAME_CAPS} driver auto reload during boot time failed."
            LOG_N_PRINT_ERR "FINISH_DIALOG_PAGE" "Check ${boot_script_log} for more details."
            LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" ""
            ;;
        ${SEP_RC_BOOTSCRIPT_UNINSTALL_FAIL})
            LOG_N_PRINT_ERR "FINISH_DIALOG_PAGE" "Removal of ${TOOL_NAME_CAPS} driver auto reload during boot time failed. Uninstallation failed."
            LOG_N_PRINT_ERR "FINISH_DIALOG_PAGE" "Check ${boot_script_log} for more details."
            LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" ""
            ;;
        ${SEP_RC_LICENSE_NOT_AVAILABLE})
            LOG_N_PRINT_ERR "FINISH_DIALOG_PAGE" "The license file ${LICENSE_FILE} is either unavailable or inaccessible."
            LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" ""
            ;;
        ${SEP_RC_CONSENT_NOT_AVAILABLE})
            LOG_N_PRINT_ERR "FINISH_DIALOG_PAGE" "The ISIP consent file ${ISIP_CONSENT_FILE} is either unavailable or inaccessible."
            LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" ""
            ;;
        *)
            LOG "FINISH_DIALOG_PAGE: Printing driver related warning if any to console"
            print_error_log success
            if [ "${load_driver_only}" = "yes" ] ; then
                LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" "${TOOL_NAME_CAPS} drivers have been loaded successfully. Installation is complete!"
            else
                LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" "${TOOL_NAME_CAPS} has been successfully installed at ${INSTALL_PATH}."
            fi
            LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" "Use \"source ${INSTALL_PATH}/sep_vars.sh\" to set up the environment."
            LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" ""
            ;;
    esac

    LOG_N_PRINT_MSG "FINISH_DIALOG_PAGE" "Install log can be found at ${LOG_PATH_PREFIX}"
    # delete temporarily created .log.err files
    ${RM} -rf ${LOG_PATH_PREFIX}/*.log.err > /dev/null 2>&1
    LOG "FINISH_DIALOG_PAGE: Removed .log.err files"

    print_footer_2 ${print_footer_params}
    process_user_input

    exit ${ret_code}
}

log_install_options()
{
    LOG "LOG_INSTALL_OPTIONS: Install location: ${INSTALL_PATH}"
    if [ -n "${collection_mode_available}" ] ; then
        LOG "LOG_INSTALL_OPTIONS: Collection options:"
        LOG "LOG_INSTALL_OPTIONS:   Collection mode: ${collection_mode}"
    fi
    LOG "LOG_INSTALL_OPTIONS: Driver build options:"
    LOG "LOG_INSTALL_OPTIONS:   C compiler: ${COMPILER}"
    LOG "LOG_INSTALL_OPTIONS:   Make command: ${MAKE_CMD}"
    LOG "LOG_INSTALL_OPTIONS:   Kernel source directory: ${CURRENT_KERNEL_SRC_DIR}"
    LOG "LOG_INSTALL_OPTIONS: Driver access options:"
    LOG "LOG_INSTALL_OPTIONS:   Driver access group: ${DRIVER_GROUP}"
    LOG "LOG_INSTALL_OPTIONS:   Driver permission: ${DRIVER_PERM}"
    LOG "LOG_INSTALL_OPTIONS: Driver load options:"
    LOG "LOG_INSTALL_OPTIONS:   Load drivers: ${load_driver}"
    LOG "LOG_INSTALL_OPTIONS:   Reload automatically at reboot: ${reload_driver}"
    LOG "LOG_INSTALL_OPTIONS:   Complete failed installation: ${load_driver_only}"
    LOG "LOG_INSTALL_OPTIONS: non_interactive: ${non_interactive}"
    LOG "LOG_INSTALL_OPTIONS: install_tool: ${install_tool}"
    LOG "LOG_INSTALL_OPTIONS: load_driver_only: ${load_driver_only}"
    LOG "LOG_INSTALL_OPTIONS: uninstall: ${uninstall}"
    LOG "LOG_INSTALL_OPTIONS: enable_maxlog: ${enable_maxlog}"
    LOG "LOG_INSTALL_OPTIONS: yocto: ${yocto}"
}

summary_page()
{
    STEP_NUM=4
    TOTAL_STEPS=5
    STEP_NAME="Summary"
    DEFAULT_OPTION=1

    common_params="no-next"
    print_footer_params="${common_params} summary default-value ${DEFAULT_OPTION}"

    print_header

    print_tabbed_msg "Install location               [${INSTALL_PATH_BASE}]"
    print_msg ""

    if [ -n "${collection_mode_available}" ] ; then
        print_tabbed_ul_msg "Collection options"
        print_tabbed_msg_nnl "Collection mode                [${collection_mode}"
        if [ "${collection_mode}" = "driverless" ] ; then
            print_nnl "*"
        fi
        print_msg "]"
        print_msg ""
    fi
    if [ "${collection_mode}" = "driverless" ] ; then
        print_tabbed_ul_msg "Driver load options"
        print_tabbed_msg "Load drivers                   [${load_driver}]"
        print_msg ""

        print_tabbed_msg "*the driverless mode may not enable all features that are"
        print_tabbed_msg "supported with driver collection mode"
        print_msg ""
        print_tabbed_msg "Please refer to \"EMON Driverless Option\" topic in the user guide for"
        print_tabbed_msg "pre-requisites and more details."
        print_msg ""
    else
        print_tabbed_ul_msg "Driver build options"
        print_tabbed_msg "C compiler                     [${COMPILER}]"
        print_tabbed_msg "Make command                   [${MAKE_CMD}]"
        print_tabbed_msg "Kernel source dir              [${CURRENT_KERNEL_SRC_DIR}]"
        print_msg ""

        print_tabbed_ul_msg "Driver access options"
        print_tabbed_msg "Driver group                   [${DRIVER_GROUP}]"
        print_tabbed_msg "Driver permission              [${DRIVER_PERM}]"
        print_msg ""

        print_tabbed_ul_msg "Driver load options"
        print_tabbed_msg_nnl "Load drivers                   [${load_driver}"
        if [ "${load_driver}" = "no" ] ; then
            print_nnl "*"
        fi
        print_msg "]"
        print_tabbed_msg "Reload automatically at reboot [${reload_driver}]"
        print_tabbed_msg_nnl "Complete failed installation   [${load_driver_only}"
        if [ "${load_driver_only}" = "yes" ] ; then
            print_nnl "*"
        fi
        print_msg "]"
        print_msg ""

        if [ "${load_driver}" = "no" ] ; then
            print_tabbed_msg "*all functionalities of the tool may not be available"
            print_msg ""
        fi
        if [ "${load_driver_only}" = "yes" ] ; then
            print_tabbed_msg "*the drivers will be loaded from ${INSTALL_PATH_BASE}/${package_name}"
            print_msg ""
        fi
    fi

    print_tabbed_msg "Go back to update any of the above options"
    print_msg ""

    print_tabbed_msg "[1] Start installation"

    print_footer_2 ${print_footer_params}

    while [ 1 ] ; do
        ret_val=1
        process_user_input_2 ${common_params}
        if [ "${ui_option}" = "n" ] ; then
            goto_screen next ${common_params}
        elif [ "${ui_option}" = "b" ] ; then
            goto_screen back ${common_params}
        elif [ "${ui_option}" = "1" ] ; then
            break
        else
            print_footer_2 skip-options ${print_footer_params}
            continue
        fi
        ret_val=$?
        if [ ${ret_val} -eq 0 ] ; then
            break
        fi
        print_footer_2 skip-options ${print_footer_params}
    done
}

manage_driver_group_dialog_page()
{
    STEP_NUM=
    TOTAL_STEPS=
    STEP_NAME="Options > Driver access group"

    if [ "$1" = "sub-page" ] ; then
        DEFAULT_OPTION=b
        common_params="no-next standard-2"
    else
        DEFAULT_OPTION=n
        common_params="standard-2"
    fi
    print_footer_params="${common_params} default-value ${DEFAULT_OPTION}"

    print_header
    print_tabbed_msg "Driver group: ${DRIVER_GROUP}"
    print_msg ""
    print_msg "Sampling drivers are accessible only to members of a specific group."
    print_msg "${TOOL_NAME_CAPS} users must be added to this group. The default group is \"${DEFAULT_DRIVER_GROUP}\"."
    if [ "${MY_NAME}" = "root" ] ; then
        print_msg "Specify group \"root\" for root usage."
    fi
    print_footer_2 ${print_footer_params}

    while [ 1 ] ; do
        ret_val=1
        process_user_input_2 ${common_params}
        if [ "${ui_option}" = "n" ] ; then
            goto_screen next ${common_params}
        elif [ "${ui_option}" = "b" ] ; then
            goto_screen back ${common_params}
        else
            DRIVER_GROUP="${ui_option}"
            #check_group_exists
            if [ "$1" = "sub-page" ] ; then
                sub_group_page_update=1
                goto_screen back ${common_params}
            else
                goto_screen next ${common_params}
            fi
        fi
        ret_val=$?
        if [ ${ret_val} -eq 0 ] ; then
            break
        fi
        print_footer_2 skip-options ${common_params}
    done

    return 0
}

installation_dialog_page()
{
    if [ ${non_interactive} -eq 1 ] ; then
        return
    fi

    STEP_NUM=2
    TOTAL_STEPS=5
    STEP_NAME="Options"
    DEFAULT_OPTION=n

    common_params=
    print_footer_params="${common_params} default-value ${DEFAULT_OPTION}"

    print_header
    print_tabbed_msg "Select an option to know more details"
    # print_msg ""
    # print_msg "Install space required: 18MB"
    # print_msg ""
    print_msg ""
    if [ -n "${1}" ] ; then
        print_tabbed_msg "${DASH}${SMALL_DASH} ${ALERT} ${SMALL_DASH}${DASH}-"
        print_tabbed_msg "Option [${1}] cannot be changed when collection mode in"
        print_tabbed_msg "option [0] is set to \"Driverless\". Please select the"
        print_tabbed_msg "collection mode as \"Driver\" to make any changes."
        print_tabbed_msg "${DASH}${DASH}${DASH}${SMALL_DASH}"
        print_msg ""
    fi
    if [ -n "${collection_mode_available}" ] ; then
        print_tabbed_ul_msg "Collection options"
        print_tabbed_msg "[0] Collection mode                [${collection_mode}]"
        print_msg ""
    fi
    if [ "${collection_mode}" = "driverless" ] ; then
        print_tabbed_ul_msg "Driver build options"
        print_tabbed_msg "[1] C compiler                     [N/A]"
        print_tabbed_msg "[2] Make command                   [N/A]"
        print_tabbed_msg "[3] Kernel source dir              [N/A]"
        print_msg ""
        print_tabbed_ul_msg "Driver access options"
        print_tabbed_msg "[4] Driver access group            [N/A]"
        print_tabbed_msg "[5] Driver permission              [N/A]"
        print_msg ""
        print_tabbed_ul_msg "Driver load options"
        print_tabbed_msg "[6] Load drivers                   [${load_driver}]"
        print_tabbed_msg "[7] Reload automatically at reboot [N/A]"
        print_tabbed_msg "[8] Complete failed installation   [N/A]"
    else
        print_tabbed_ul_msg "Driver build options"
        print_tabbed_msg "[1] C compiler                     [${COMPILER}]"
        print_tabbed_msg "[2] Make command                   [${MAKE_CMD}]"
        print_tabbed_msg "[3] Kernel source dir              [${CURRENT_KERNEL_SRC_DIR}]"
        print_msg ""
        print_tabbed_ul_msg "Driver access options"
        print_tabbed_msg "[4] Driver access group            [${DRIVER_GROUP}]"
        print_tabbed_msg "[5] Driver permission              [${DRIVER_PERM}]"
        print_msg ""
        print_tabbed_ul_msg "Driver load options"
        print_tabbed_msg "[6] Load drivers                   [${load_driver}]"
        print_tabbed_msg "[7] Reload automatically at reboot [${reload_driver}]"
        print_tabbed_msg "[8] Complete failed installation   [${load_driver_only}]"
    fi
    print_msg ""
    print_tabbed_ul_msg "General options"
    print_tabbed_msg "[9] Change install location        [${INSTALL_PATH_BASE}]"

    print_footer_2 ${print_footer_params}
    while [ 1 ] ; do
        ret_val=1
        process_user_input_2 ${common_params}

        option_num=
        for option_num in ${drvless_mode_invalid_screens[@]} ; do
            if [ "${option_num}" = "${ui_option}" ] ; then
                installation_dialog_page ${ui_option}
                return
            fi
        done

        if [ "${ui_option}" = "n" ] ; then
            goto_screen next ${common_params}
        elif [ "${ui_option}" = "b" ] ; then
            goto_screen back ${common_params}
        elif [[ "${ui_option}" = "0" && -n "${collection_mode_available}" ]] ; then
            update_collection_mode_dialog_page
        elif [ "${ui_option}" = "1" ] ; then
            update_compiler_dialog_page
        elif [ "${ui_option}" = "2" ] ; then
            update_make_cmd_dialog_page
        elif [ "${ui_option}" = "3" ] ; then
            update_kernel_src_dialog_page
        elif [ "${ui_option}" = "4" ] ; then
            manage_driver_group_dialog_page sub-page
        elif [ "${ui_option}" = "5" ] ; then
            change_driver_perm_dialog_page
        elif [ "${ui_option}" = "6" ] ; then
            change_load_drivers_page
        elif [ "${ui_option}" = "7" ] ; then
            change_driver_reload_setup_page
        elif [ "${ui_option}" = "8" ] ; then
            change_load_drivers_only_page
        elif [ "${ui_option}" = "9" ] ; then
            update_install_location sub-page
        else
            print_footer_2 skip-options ${print_footer_params}
            continue
        fi
        ret_val=$?
        if [ ${ret_val} -eq 0 ] ; then
            break
        fi
        print_footer_2 skip-options ${print_footer_params}
    done
}

check_existing_sep_products()
{
    ARR_BINARY_NAME=$( ${LS} -C1 ${INSTALL_PATH_BASE} | ${GREP} -E ${BINARY_NAME_REGEX} | ${TR} '\n' ' ')

    LOG "CHECK_EXISTING_SEP_PRODUCTS: Checking installed ${TOOL_NAME_CAPS} products"
    LOG "CHECK_EXISTING_SEP_PRODUCTS: Installed ${TOOL_NAME_CAPS} binaries: ${ARR_BINARY_NAME}"

    if [[ -z "${ARR_BINARY_NAME}" ]] ; then
        return
    fi

    TAR_NAME=$( ${LS} | ${GREP} -E ${PACKAGE_NAME_REGEX} )

    if [ -n "${TAR_NAME}" ] ; then
        PACKAGE_NAME=${TAR_NAME%${PACKAGE_EXT}}
        local temp=${PACKAGE_NAME##*_}
        BUILD_NUMBER=${temp%%.*}
    fi

    itr=1
    PACKAGE_ALREADY_INSTALLED=
    current_package_name=
    current_package_itr=
    for binary_name in ${ARR_BINARY_NAME}; do
        temp_build_number=${binary_name##*_}
        if [ -n "${TAR_NAME}" ] ; then
            if [ "${temp_build_number}x" = "${BUILD_NUMBER}x" ] ; then
                LOG "CHECK_EXISTING_SEP_PRODUCTS: The package in the current installer is already installed"
                PACKAGE_ALREADY_INSTALLED=1
                current_package_name=${binary_name}
                current_package_itr=${itr}
            fi
        fi
        itr=$( expr ${itr} + 1 )
    done
}

find_n_uninstall_driver()
{
    itr=0
    for binary_name in ${ARR_BINARY_NAME}; do
        itr=$( expr ${itr} + 1 )
        if [ "${itr}" != "$1" ] ; then
            continue
        fi
        clear

        print_msg ${LONG_DASH}
        LOG_N_PRINT_MSG "FIND_N_UNINSTALL_DRIVER" "Uninstalling drivers associated with ${binary_name}"
        print_msg ${LONG_DASH}
        driver_uninstall_binary_name=${binary_name}
        uninstall_driver
    done

    unload_driver_dialog_page

    return 0
}

unload_driver_dialog_page()
{
    STEP_NUM=
    TOTAL_STEPS=
    STEP_NAME="Unload Drivers"
    DEFAULT_OPTION=b

    common_params="no-next"
    print_footer_params="${common_params} default-value ${DEFAULT_OPTION}"

    print_header

    if [ -n "${driver_uninstall_binary_name}" ] ; then
        print_msg "Drivers from ${driver_uninstall_binary_name} unloaded successfully!"
        driver_uninstall_binary_name=
        print_msg ""
    fi

    itr=0
    print_tabbed_msg "Unload corresponding drivers from the below list:"
    for binary_name in ${ARR_BINARY_NAME}; do
        itr=$( expr ${itr} + 1 )
        print_tabbed_msg "[${itr}] ${binary_name}"
    done

    print_footer_2 ${print_footer_params}

    while [ 1 ] ; do
        ret_val=1
        process_user_input_2 ${common_params}
        if [ "${ui_option}" = "n" ] ; then
            goto_screen next ${common_params}
        elif [ "${ui_option}" = "b" ] ; then
            goto_screen back ${common_params}
        else
            if [ ${ui_option} -ge 1 -o ${ui_option} -le ${itr} ] ; then
                find_n_uninstall_driver ${ui_option}
            else
                print_footer_2 skip-options ${print_footer_params}
                continue
            fi
        fi
        ret_val=$?
        if [ ${ret_val} -eq 0 ] ; then
            break
        fi
        print_footer_2 skip-options ${print_footer_params}
    done

    return 0
}

uninstall_sep()
{
    if [ ${non_interactive} -eq 0 ] ; then
        clear
    elif [ -z "${ARR_BINARY_NAME}" -a ${install_tool} -eq 0 ] ; then
        finish_dialog_page ${SEP_RC_NOT_INSTALLED}
    fi

    itr=0
    for binary_name in ${ARR_BINARY_NAME}; do
        itr=$( expr ${itr} + 1 )
        if [[ -n "${uninstall_sep_itr}" && "${itr}" != "${uninstall_sep_itr}" ]] ; then
            continue
        fi
        uninstall_binary_name=${binary_name}
        LOG "UNINSTALL_SEP: Uninstalling $binary_name"
        if [ ${non_interactive} -eq 0 ] ; then
            print_msg ${LONG_DASH}
            print_msg "Uninstalling $binary_name"
            print_msg ${LONG_DASH}
        fi
        UNINSTALLED=1
        uninstall_driver "rm_boot_script"
        ${RM} -rf ${INSTALL_PATH_BASE}/${binary_name}
        if [ "${itr}" = "${current_package_itr}" ] ; then
            PACKAGE_ALREADY_INSTALLED=
        fi
    done

    if [ -L ${INSTALL_PATH} -a ! -e ${INSTALL_PATH} ] ; then
        sh -c "unlink ${INSTALL_PATH}"
    fi

    if [ -d ${ISIP_LOCATION} ] ; then
        if [ -f ${ISIP_FILE} ] ; then
            ${RM} ${SEP_FORCE} ${ISIP_FILE}
            LOG "UNINSTALL_SEP: Removed ISIP file ${ISIP_FILE}"
        fi

        if [ ! "$(ls -A ${ISIP_LOCATION})" ] ; then
            ${RM} -rf ${ISIP_LOCATION}
            LOG "UNINSTALL_SEP: ISIP location ${ISIP_LOCATION} empty; removed"
        fi
    fi

    if [ ${non_interactive} -eq 0 ] ; then
        uninstall_dialog_page
    fi

    return 0
}

uninstall_dialog_page()
{
    check_existing_sep_products

    STEP_NUM=1
    TOTAL_STEPS=5
    STEP_NAME="Uninstall"
    DEFAULT_OPTION=n

    common_params="no-back"
    print_footer_params="${common_params} default-value ${DEFAULT_OPTION}"

    print_header

    if [ -n "${uninstall_binary_name}" ] ; then
        if [ -n "${uninstall_sep_itr}" ] ; then
            print_msg "${uninstall_binary_name} uninstalled successfully!"
        else
            print_msg "All ${TOOL_NAME_CAPS} installations uninstalled successfully!"
        fi
        uninstall_binary_name=
        print_msg ""
    fi

    if [ -n "${ARR_BINARY_NAME}" ] ; then
        itr=1
        for binary_name in ${ARR_BINARY_NAME}; do
            print_tabbed_msg_nnl "[${itr}] Uninstall ${binary_name}"
            if [ "${current_package_name}" = "${binary_name}" ] ; then
                print_msg "*"
            else
                print_msg ""
            fi
            itr=$( expr ${itr} + 1 )
        done
        num_installed_packages=$( expr ${itr} - 1 )
        print_tabbed_msg "[${itr}] Uninstall all previous installation(s)"
        itr=$( expr ${itr} + 1 )
        print_tabbed_msg "[${itr}] Unload drivers"
        uninstall_all_option_num=$( expr ${num_installed_packages} + 1 )
        uninstall_driver_option_num=$( expr ${num_installed_packages} + 2 )
        LOG "UNINSTALL_DIALOG_PAGE: num_installed_packages is ${num_installed_packages}"
        LOG "UNINSTALL_DIALOG_PAGE: uninstall_all_option_num is ${uninstall_all_option_num}"
        LOG "UNINSTALL_DIALOG_PAGE: uninstall_driver_option_num is ${uninstall_driver_option_num}"
    else
        LOG "UNINSTALL_DIALOG_PAGE: No ${TOOL_NAME_CAPS} package installed"
        print_tabbed_msg "${TOOL_NAME_CAPS} installation(s) not found on the system!"
        print_tabbed_msg "Proceed to next screen..."
    fi

    if [ -n "${PACKAGE_ALREADY_INSTALLED}" ] ; then
        print_msg ""
        print_msg "*${TOOL_NAME_CAPS} version associated with this package is already installed!"
        print_msg " Uninstall if you wish to re-install"
    fi

    print_footer_2 ${print_footer_params}

    while [ 1 ] ; do
        ret_val=1
        process_user_input_2 ${common_params}
        if [ "${ui_option}" = "n" ] ; then
            goto_screen next ${common_params}
        elif [ "${ui_option}" = "b" ] ; then
            goto_screen back ${common_params}
        else
            if [ -n "${ARR_BINARY_NAME}" ] ; then
                if [ ${ui_option} -ge 1 -a ${ui_option} -le ${num_installed_packages} ] ; then
                    uninstall_sep_itr=${ui_option}
                    uninstall_sep
                elif [ ${ui_option} -eq ${uninstall_all_option_num} ] ; then
                    uninstall_sep_itr=
                    uninstall_sep
                elif [ ${ui_option} -eq ${uninstall_driver_option_num} ] ; then
                    uninstall_sep_itr=
                    unload_driver_dialog_page
                else
                    print_footer_2 skip-options ${print_footer_params}
                    continue
                fi
            else
                print_footer_2 skip-options ${print_footer_params}
                continue
            fi
        fi
        ret_val=$?
        if [ ${ret_val} -eq 0 ] ; then
            break
        fi
        print_footer_2 skip-options ${print_footer_params}
    done

    return 0
}

update_install_location()
{
    if [ ${non_interactive} -eq 1 ] ; then
        return
    fi

    STEP_NUM=
    TOTAL_STEPS=
    STEP_NAME="Install Location"

    if [ "$1" = "sub-page" ] ; then
        DEFAULT_OPTION=b
        common_params="no-next standard-2"
    else
        DEFAULT_OPTION=n
        common_params="no-back standard-2"
    fi
    print_footer_params="${common_params} default-value ${DEFAULT_OPTION}"

    print_header

    if [ -n "${invalid_path}" ] ; then
        print_msg "${ui_option} is an invalid path! Enter a valid path."
        print_msg ""
    fi
    if [ -n "${no_perm_in_install_loc}" ] ; then
        print_msg "The user does not have write permission in ${INSTALL_PATH_BASE}!"
        print_msg "Update the install location or location permission."
        print_msg ""
    fi
    print_tabbed_msg "Install location: ${INSTALL_PATH_BASE}"
    print_msg ""
    if [ "$1" != "sub-page" ] ; then
        print_msg "Installer searches for existing ${TOOL_NAME_CAPS} installations in this path."
    fi
    print_msg "Default install location: ${DEFAULT_INSTALL_PATH_BASE}"
    print_footer_2 ${print_footer_params}

    invalid_path=
    no_perm_in_install_loc=

    while [ 1 ] ; do
        ret_val=1
        process_user_input_2 ${common_params}
        if [ "${ui_option}" = "n" ] ; then
            goto_screen next ${common_params}
        elif [ "${ui_option}" = "b" ] ; then
            goto_screen back ${common_params}
        else
            if [ -n "${ui_option}" ] ; then
                INSTALL_PATH_BASE=${ui_option}
                if [ ! -d ${INSTALL_PATH_BASE} ] ; then
                    mkdir ${INSTALL_PATH_BASE} > /dev/null 2>&1
                fi

                mkdir ${INSTALL_PATH_BASE}/sep_installer_temp > /dev/null 2>&1
                if [ $? -ne 0 ] ; then
                    LOG "UPDATE_INSTALL_LOC: The user does not have write permission in ${INSTALL_PATH_BASE}!"
                    LOG "UPDATE_INSTALL_LOC: Update the install location or location permission."
                    no_perm_in_install_loc=1
                    update_install_location $1
                else
                    ${RM} -rf ${INSTALL_PATH_BASE}/sep_installer_temp > /dev/null 2>&1
                fi

                INSTALL_PATH=${INSTALL_PATH_BASE}/${SOFT_LINK_NAME}
            fi
            if [ "$1" = "sub-page" ] ; then
                goto_screen back ${common_params}
            else
                break;
            fi
        fi
        ret_val=$?
        if [ ${ret_val} -eq 0 ] ; then
            break
        fi
        print_footer_2 skip-options ${print_footer_params}
    done

    return 0
}

# ----------------------------------- MAIN ----------------------------------

# initialize logging
init_logging

# check user arguments
check_args

# initialize variables
init_variables

# check for install package
verify_install_package_existence

# determine user type
user_type_dialog_page
check_user_type

# check for pre-requisites
check_for_prerequisites

# interactive mode
if [ ${non_interactive} -eq 0 ] ; then

    # get install location
    update_install_location

    # identify and remove existing sep installations
    uninstall_dialog_page

    # log install options chosen by the user
    log_install_options

    if [ ${install_tool} -eq 1 ] ; then
        # show license
        show_license

        # show user consent for analytics data collection
        show_collect_consent
    fi

    clear

    print_msg ${LONG_DASH}
    print_msg "Preparing installer..."
    print_msg ${LONG_DASH}

    print_msg "This may take several minutes..."

# non-interactive mode
else

    if [ ${yocto} -eq 1 ] ; then
        make_soft_link_for_system_lib
    fi

    # log install options chosen by the user
    log_install_options

    # if -ni and -u given, uninstall
    if [ ${uninstall} -eq 1 ] ; then
        check_existing_sep_products
        uninstall_sep_itr=
        uninstall_sep
    fi
fi

# extracting the package to install directory
untar_package

# buliding the driver
build_driver

# installing the dirver
load_sep_driver

# install boot-script
install_boot_script

if [ ${non_interactive} -eq 0 ] ; then
    print_msg ${LONG_DASH}
fi

# displaying the finish diallog page
finish_dialog_page
