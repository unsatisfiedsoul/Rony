# Delete the old one
rm $PREFIX/share/nmap/scripts/s7-enumerate.nse

# Download a modernized version
curl -o $PREFIX/share/nmap/scripts/s7-enumerate.nse https://raw.githubusercontent.com/nmap/nmap/master/scripts/s7-info.nse

# Update the database
nmap --script-updatedb
