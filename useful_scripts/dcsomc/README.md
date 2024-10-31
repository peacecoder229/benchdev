# **Tele-Metric Collector** (tmc)

Python application to collect emon, sar, iostat, vmstat and other metadata on Linux machines during workload runs & push them to [DCSO Metrics Processing Server](https://dcsometrics.intel.com) for post-processing telemetric data for visualization. <sup>[note 1](#serverusage)</sup>

## Setup 

### Step 1 (Setup EMON)

- Setup Emon/SEP on the target linux system ( Download the latest EMON/SEP https://goto/sep)
- Copy the latest sep (sepint_x.y_uz_linux_.tar.bz2) into your server temp (e.g. /root/devtools/) directory and extract it
- Navigate to /root/devtool/sepint_x.y_uz_linux_ and run "./install.sh"

You also need to install sysstat tool if you would like to collect SAR, IOSTAT, VMSTAT info 

Debian Family : `apt install sysstat`  |   RHEL Family : `dnf install sysstat`

### Step 2 (Setup GitHub Proxy)

Before cloning the repo make sure you have SSH-connect + Proxy setup on your Linux machine.  Steps available in [1Source Guide](https://1source.intel.com/docs/faq/github#how-to-connect-github-with-ssh)

Debian Family 
```
sudo apt install connect-proxy

echo "
host github.com
    ProxyCommand connect -a none -S proxy-dmz.intel.com:1080 %h %p
" >>  ~/.ssh/config 
```
CentOS/RHEL/Fedora Family 
```
sudo dnf install connect-proxy

echo "
host github.com
    ProxyCommand connect-proxy -a none -S proxy-dmz.intel.com:1080 %h %p
" >>  ~/.ssh/config 
```

### Step 3 (Clone & Install TMC)

- Clone the edp client & emon trace collecting scripts from DCSO Metrics client repo.

    HTTPS
    ```
    git clone https://github.com/intel-sandbox/tools.dcso.telemetry.client.git ~/dcsotmc
    cd ~/dcsotmc && ./install.sh && . ~/.bashrc
    ```
    
    SSH
    ```
    git clone git@github.com:intel-sandbox/tools.dcso.telemetry.client.git ~/dcsotmc
    cd ~/dcsotmc && ./install.sh && . ~/.bashrc
    ```

## Getting Started

- First check if your tmc can detect installed emon and other tools by colleting telemetry for 10 seconds (`tmc -t10 -T ALL`) 
- Use help section of the tool to grab more info... (`tmc --help`)
- TMC Client will try to grab required events file from [dcsometrics server](https://dcsometrics.intel.com)

## Windows Support (experimental)

- Adding experimental support for Windows. Currently it works based on initial testing.

- On the SUT do the following things

	1. Download and install Python - https://www.python.org/ftp/python/3.10.5/python-3.10.5-amd64.exe
	
		Custom option -> Enable for all users, Add to path
	
		Make sure to disable Path Length after Python Installation successful 
	
	2. Clone the TMC repo (Make sure to have git installed)
		
		Sign with you github login when it asks or you can use sign in by code option.
	
		```
		git clone https://github.com/intel-sandbox/tools.dcso.telemetry.client.git c:\devtools\tmc
		git checkout windows
		```
		
		OR
		
		Download the windows branch as archive and extract it into c:\devtools\tmc direcotry.
	
	3. Add proxy to the system by adding following content into a PS1 script and run it as ADMIN 
		```	
		[Environment]::SetEnvironmentVariable("http_proxy", "http://proxy-chain.intel.com:911", "Machine")
		[Environment]::SetEnvironmentVariable("https_proxy", "http://proxy-chain.intel.com:912", "Machine")
		[Environment]::SetEnvironmentVariable("ftp_proxy", "http://proxy-chain.intel.com:911", "Machine")
		[Environment]::SetEnvironmentVariable("socks_proxy", "http://proxy-us.intel.com:1080", "Machine")
		[Environment]::SetEnvironmentVariable("no_proxy",  "intel.com,.intel.com,localhost,127.0.0.1", "Machine")
		```
	4. Install SEP for Windows (https://goto/sep) with default options. 
	
	5. Then run install.cmd to make sure all the required pip dependencies are installed properly. 
	
	6. That's all your ready to run TMC client.. In Windows you may need to run with python command (python c:\devtools\tmc\tmc.py)


## Usage Guide
```
root@JF5300-B11A171T:~# tmc --help
# Host dcsometrics.intel.com found: line 38
/root/.ssh/known_hosts updated.
Original contents retained as /root/.ssh/known_hosts.old
2021-04-24 14:29:20-utils   - INFO - Version : 0.1
2021-04-24 14:29:20-analyzer- INFO - Version : 0.1
2021-04-24 14:29:20-dcsomc  - INFO - Version : 0.3
2021-04-24 14:29:20-metadata- INFO - Version : 0.1
2021-04-24 14:29:20-utils   - INFO - Required modules are available...!
2021-04-24 14:29:20-tmc     - INFO - Version : 0.1
2021-04-24 14:29:20-tmc     - WARNING - It's recommended using latest (i.e. git pull) DCSO Client to have better experience.
usage: tmc.py [-h] [-v] [-n] [-u] [-d DIR] [-a APPEND] [-D DEST_DIR_NAME] [-t TIME_DURATION] [-e EVENTS_FILE] [-b BINARY_EMON] [-s TIME_STAMP] [-p PROCESS_ID] [-o MAX_TIMEOUT]
              [-c TARGET_CMD] [-g TARGET_GAP] [-r RAMP_TIME] [-w CHART_VIEWS] [-i IDENTITY_COMMENT] [-G GROUP] [-S START_TRACE] [-E END_TRACE] [-A BUOY_START_TIME] [-B BUOY_STOP_TIME]
              [-x USER] [-T TELEMETRY]

Process commandline arguments

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Enable verbose logs
  -n, --non-interactive
                        Push data in non-interactive mode (without user confirmation), useful for automations
  -u, --upload          Enable uploading the traces to server after ending
  -d DIR, --dir DIR     Output directory where the emon traces to be stored. Default - current working directory
  -a APPEND, --append APPEND
                        Append this string to sample name
  -D DEST_DIR_NAME, --dest-dir-name DEST_DIR_NAME
                        Destination sub directory where the emon traces to be pushed.
  -t TIME_DURATION, --time-duration TIME_DURATION
                        Amount of duration to collect the data. Default 0 (i.e. forever until user pressed ctl+c)
  -e EVENTS_FILE, --events-file EVENTS_FILE
                        Emon events file. If not provided and its not available in system then it will try to download from dungeon share
  -b BINARY_EMON, --binary-emon BINARY_EMON
                        Emon installation path. Default : /opt/intel/sep
  -s TIME_STAMP, --time-stamp TIME_STAMP
                        timestamp value that has to added into the output dir. Default autogenerated
  -p PROCESS_ID, --process-id PROCESS_ID
                        Target process ID that collector has to wait to stop. Default None
  -o MAX_TIMEOUT, --max-timeout MAX_TIMEOUT
                        Max time (sec) to wait for a target process to finish. default=0 (i.e. forever) (valid only with --process-id option)
  -c TARGET_CMD, --target-cmd TARGET_CMD
                        Target command to start after stating the Emon
  -g TARGET_GAP, --target-gap TARGET_GAP
                        Time (sec) to wait before starting the target command. Default 1 (valid only with --target-cmd option)
  -r RAMP_TIME, --ramp-time RAMP_TIME
                        Time (sec) to wait before collecting data. Default 0 (valid only with --target-cmd option)
  -w CHART_VIEWS, --chart-views CHART_VIEWS
                        Kind of chart views (thread, core, socket) to be processed in remote server -w socket | -w thread,socket,core -w thread,core | -w core
  -i IDENTITY_COMMENT, --identity-comment IDENTITY_COMMENT
                        Comment to identify the emon logs in server
  -G GROUP, --group GROUP
                        provide group name to your emon trace, this is useful to group your traces on server side
  -S START_TRACE, --start-trace START_TRACE
                        Provide start sample number for edp.
  -E END_TRACE, --end-trace END_TRACE
                        Provide end sample number for edp.
  -A BUOY_START_TIME, --buoy-start-time BUOY_START_TIME
                        Provide start time for buoy in seconds.
  -B BUOY_STOP_TIME, --buoy-stop-time BUOY_STOP_TIME
                        Provide end time for buoy in seconds.
  -x USER, --user USER  Username to be tagged in DCSO metrics server
  -T TELEMETRY, --telemetry TELEMETRY
                        List of telemetries to collect (e.g. -T all | -T emon | -T emon,sar | -T emon,sar,iostat) to be collected (Default : emon)
```


<a name="serverusage">note 1</a>: **DCSO Metrics Server is meant only for DPG PAIV SO Team usage. Please reach out to Author for help setting you your own server**
