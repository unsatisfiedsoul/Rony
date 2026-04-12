#!/bin/bash

echo "What is the ip address: "
read ip
#echo "What is the domain: "
#read domain
domain="2million.htb"
#echo "What is the port number: "
#read port
port=80

resolve="$domain:$port:$ip"
echo "Resolve string: $resolve"

echo -e "What do you want?\n1.frontend.js\n2.inviteapi.js\n3.backend.js"
read n

# Define the base command (Note the trailing space)
cl="curl -iv -c cookie.txt --resolve $resolve http://$domain"

case $n in
    1)
        cl_path="/js/htb-frontpage.min.js"
        cl_hold="${domain}_frontend.js"
        ;;
    2)
        cl_path="/js/inviteapi.min.js"
        cl_hold="${domain}_inviteapi.js"
        ;;
    3)
        cl_path="/js/htb-backend.min.js"
        cl_hold="${domain}_backend.js"
        ;;
    *)
        echo "Invalid choice"
        exit 1 # Exit if the choice is bad
        ;;
esac

# Now run the final command using the variables set in the case statement
echo -e "Getting $cl_path and saving to $cl_hold\n"
eval "$cl$cl_path" > "$cl_hold"
cat cookie.txt
cat $cl_hold
#xdg-open $cl_hold
