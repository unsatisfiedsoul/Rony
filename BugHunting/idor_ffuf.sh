# Create a quick list of common IDOR params
echo -e "id\nuser_id\nuid\naccount\nprofile\ndoc_id\norder_id" > params.txt

# Find domain
echo "url: "
read domain

# Use ffuf to see which parameter changes the response size
ffuf -u "https://$domain/endpoint?FUZZ=1" -w params.txt -mc 200
