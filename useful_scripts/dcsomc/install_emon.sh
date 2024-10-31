sep_version="sep_private_5_24_linux_0219170677e3a80"
sep_version="sep_private_5_25_linux_04081320c6a62b2"
sep_version="sep_private_5_26_linux_05250602a139d66"
sep_version="sep_private_5_27_linux_07070609b1641b1"
sep_version="sep_private_5_28_linux_08052000ddfc9ff"
sep_version="sep_private_5_29_linux_09162200a7108a4"
sep_version="sep_private_5_30_linux_111018263d8165d"
#sep_version="sep_private_5_31_linux_121516364bb91f7"
sep_version="sep_private_5_34_linux_050122015feb2b5"

cd ~;
mkdir devtools 
cd devtools 
wget --no-check-certificate --no-proxy https://dcsorepo.jf.intel.com:8080/utils/emon/${sep_version}.tar.bz2 
tar xvf ${sep_version}.tar.bz2 
cd ${sep_version} 
./sep-installer.sh --accept-license -ni -u -i


