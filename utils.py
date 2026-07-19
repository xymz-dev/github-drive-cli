import os
import json
import logging
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme

# Setup Rich console and theme
custom_theme = Theme({
    "info": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "bold red",
    "highlight": "magenta"
})
console = Console(theme=custom_theme)

# Setup logging using user home directory (~/.ghup/logs and ~/.ghup/data)
LOG_DIR = os.path.expanduser("~/.ghup/logs")
DATA_DIR = os.path.expanduser("~/.ghup/data")
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "ghup.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("GHUP")

def display_banner():
    banner = """[bold cyan]
   ██████╗ ██╗  ██╗██╗   ██╗██████╗ 
  ██╔════╝ ██║  ██║██║   ██║██╔══██╗
  ██║  ███╗███████║██║   ██║██████╔╝
  ██║   ██║██╔══██║██║   ██║██╔═══╝ 
  ╚██████╔╝██║  ██║╚██████╔╝██║     
   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝     
[/bold cyan]
[bold green]GitHub Uploader (GHUP) for Termux[/bold green] - v1.0.0
[dim]CLI tool to manage and upload files/folders to GitHub via REST API[/dim]
"""
    console.print(Panel(banner, border_style="cyan", expand=False))

def human_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {units[i]}"

def log_history(action, details):
    history_file = os.path.join(DATA_DIR, "history.json")
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                history = json.load(f)
        except Exception:
            history = []
    
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "details": details
    }
    history.insert(0, entry)
    # Keep last 100 entries
    history = history[:100]
    try:
        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to write history: {e}")
    logger.info(f"Action: {action} - {details}")
