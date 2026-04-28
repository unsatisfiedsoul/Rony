# Ensure curl is installed
pkg install curl

# Go to Nmap's script directory in Termux
cd $PREFIX/share/nmap/scripts/

# Download the s7-enumerate script
curl -O https://raw.githubusercontent.com/digitalbond/Redpoint/master/s7-enumerate.nse

# Update nmap
nmap --script-updatedb

