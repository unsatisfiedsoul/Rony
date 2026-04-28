# Full run
python red_team_workflow.py example.com

# Specific stages
python red_team_workflow.py example.com --stages recon scan

# Skip a tool
python red_team_workflow.py example.com --skip-tools google_dork whois_lookup

# List all tools
python red_team_workflow.py --list-tools

# Resume session
python red_team_workflow.py example.com --resume abc123 

# Past sessions
python red_team_workflow.py --list-sessions
