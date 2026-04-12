#!/bin/bash

echo "What is the ip address: "
read ip

domain="2million.htb"
port=80

resolve="$domain:$port:$ip"
echo "Resolve string: $resolve"

echo -e "What do you want?\n1.generate\n2.howtogenerate\n3.verify\n4.register\n5.login"
read n

case $n in
    1)
        cl_path="/api/v1/invite/generate"
        cl_hold="${domain}_generate.txt"
        data=""
        ;;
    2)
        cl_path="/api/v1/invite/how/to/generate"
        cl_hold="${domain}_howtogenerate.txt"
        data=""
        ;;
    3)
        cl_path="/api/v1/invite/verify"
        cl_hold="${domain}_verify.txt"
        echo "Enter invite code:"
        read code
        data="code=$code"
        ;;
    4)
        cl_path="/api/v1/user/register"
        cl_hold="${domain}_register.txt"
        read -p "code: " code
        read -p "username: " username
        read -p "email: " email
        read -sp "password: " password
        echo # New line for formatting
        data="code=$code&username=$username&email=$email&password=$password&password_confirmation=$password"
        ;;
    5)
        cl_path="/api/v1/user/login"
        cl_hold="${domain}_login.txt"
        read -p "email: " email
        read -sp "password: " password
        echo # New line for formatting
        data="email=$email&password=$password"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo -e "Sending request to $cl_path...\n"

# The refined curl command
# -c saves cookies, -b loads them
curl -s -iv -L -b cookie.txt -c cookie.txt \
     --resolve "$resolve" \
     "http://$domain$cl_path" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "$data" > "$cl_hold"

echo -e "\n--- Response Body ---"
cat "$cl_hold"
