#!/bin/bash

echo '-----------|Patching go path|------------'
echo 'export PATH="$PATH:$HOME/go/bin"' >> ~/.zshrc
echo 'export PATH="$PATH:$HOME/go/bin"' >> ~/.bashrc
#source ~/.zshrc
source ~/.bashrc

echo '------------|Patching msfconsole|---------'
gem install mini_portile2 -v 2.8.2

cp -r ~/Tools/Metasploit-termux ~/
bash ~/Metasploit-termux/metasploit.sh

