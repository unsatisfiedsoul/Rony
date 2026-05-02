#!/bin/bash
python snowcrash_1.0_modified_3_new.py -ip=84.238.50.197 -mode=read -address=4010 -count=10 -slave=1
python snowcrash_1.0_modified_3_new.py -ip=84.238.50.197 -mode=read -address=4000 -count=20 -slave=1

#[+] Targeting 84.238.50.197:502
#[!] Data Found: [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0,# 0, 0, 4, 291, 0, 0, 0]
#[*] Disconnected.
