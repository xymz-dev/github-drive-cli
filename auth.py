import requests
import getpass
from rich.prompt import Prompt
from utils import console, logger, log_history
from config import set_config, get_config

API_BASE = "https://api.github.com"

def verify_token(token):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        response = requests.get(f"{API_BASE}/user", headers=headers, timeout=15)
        if response.status_code == 200:
            user_data = response.json()
            return True, user_data.get("login"), user_data
        elif response.status_code == 401:
            return False, "Unauthorized: Invalid Personal Access Token.", None
        else:
            return False, f"GitHub API Error: {response.status_code} - {response.reason}", None
    except requests.exceptions.RequestException as e:
        return False, f"Network error during authentication: {e}", None

def login_interactive():
    console.print("[info]=== GitHub Authentication (Login) ===[/info]")
    console.print("[dim]Please enter your GitHub Personal Access Token (PAT) with repo scope.[/dim]")
    
    # Prompt token securely without showing on screen
    token = getpass.getpass("Enter GitHub PAT: ").strip()
    if not token:
        console.print("[error]Token cannot be empty![/error]")
        return False

    console.print("[info]Verifying token with GitHub API...[/info]")
    valid, message_or_user, user_data = verify_token(token)

    if valid:
        username = message_or_user
        set_config("token", token)
        set_config("username", username)
        
        # If active_repo not set and user has repos, set default if possible
        console.print(f"[success]Successfully logged in as [bold]{username}[/bold]![/success]")
        log_history("LOGIN", f"Logged in as {username}")
        return True
    else:
        console.print(f"[error]Login failed: {message_or_user}[/error]")
        logger.error(f"Login failed: {message_or_user}")
        return False

def check_auth():
    token = get_config("token")
    if not token:
        console.print("[error]Not logged in! Please run 'ghup login' first.[/error]")
        return None
    return token
