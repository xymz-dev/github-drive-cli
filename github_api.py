import requests
import base64
import time
from utils import logger

API_BASE = "https://api.github.com"

def get_headers(token):
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GHUP-Termux-Client"
    }

def get_user_info(token):
    res = requests.get(f"{API_BASE}/user", headers=get_headers(token), timeout=15)
    if res.status_code == 200:
        return res.json()
    return None

def list_repos(token, per_page=100):
    repos = []
    page = 1
    while True:
        url = f"{API_BASE}/user/repos?per_page={per_page}&page={page}&sort=updated"
        res = requests.get(url, headers=get_headers(token), timeout=15)
        if res.status_code != 200:
            break
        data = res.json()
        if not data:
            break
        repos.extend(data)
        if len(data) < per_page:
            break
        page += 1
    return repos

def get_repo_info(token, owner, repo):
    url = f"{API_BASE}/repos/{owner}/{repo}"
    res = requests.get(url, headers=get_headers(token), timeout=15)
    if res.status_code == 200:
        return res.json()
    return None

def get_repo_contents(token, owner, repo, path="", branch="main"):
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path}"
    params = {"ref": branch} if branch else {}
    res = requests.get(url, headers=get_headers(token), params=params, timeout=15)
    if res.status_code == 200:
        return res.json()
    elif res.status_code == 404:
        if branch:
            res2 = requests.get(url, headers=get_headers(token), timeout=15)
            if res2.status_code == 200:
                return res2.json()
        return None
    else:
        return None

def get_file_sha(token, owner, repo, path, branch="main"):
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path}"
    params = {"ref": branch} if branch else {}
    res = requests.get(url, headers=get_headers(token), params=params, timeout=15)
    if res.status_code == 200:
        data = res.json()
        if isinstance(data, dict):
            return data.get("sha")
    else:
        res2 = requests.get(url, headers=get_headers(token), timeout=15)
        if res2.status_code == 200:
            data = res2.json()
            if isinstance(data, dict):
                return data.get("sha")
    return None

def upload_file_api(token, owner, repo, path, content_bytes, commit_message, branch="main", sha=None):
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path}"
    encoded_content = base64.b64encode(content_bytes).decode("utf-8")
    payload = {
        "message": commit_message,
        "content": encoded_content,
        "branch": branch
    }
    if sha:
        payload["sha"] = sha
    else:
        existing_sha = get_file_sha(token, owner, repo, path, branch)
        if existing_sha:
            payload["sha"] = existing_sha

    res = requests.put(url, headers=get_headers(token), json=payload, timeout=30)
    if res.status_code in [200, 201]:
        return True, res.json()
    
    if res.status_code in [404, 422] or "branch" in res.text.lower() or "not found" in res.text.lower():
        payload.pop("branch", None)
        res2 = requests.put(url, headers=get_headers(token), json=payload, timeout=30)
        if res2.status_code in [200, 201]:
            return True, res2.json()
        return False, res2.json()

    return False, res.json()

def delete_file_api(token, owner, repo, path, commit_message, branch="main"):
    sha = get_file_sha(token, owner, repo, path, branch)
    if not sha:
        # Try without branch ref to find SHA
        sha = get_file_sha(token, owner, repo, path, branch=None)
    if not sha:
        return False, {"message": "File not found on repository."}
    
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path}"
    payload = {
        "message": commit_message,
        "sha": sha,
        "branch": branch
    }
    res = requests.delete(url, headers=get_headers(token), json=payload, timeout=30)
    if res.status_code == 200:
        return True, res.json()
    
    # Fallback: if branch not found or 422, try deleting without branch parameter
    if res.status_code in [404, 422] or "branch" in res.text.lower() or "not found" in res.text.lower():
        payload.pop("branch", None)
        res2 = requests.delete(url, headers=get_headers(token), json=payload, timeout=30)
        if res2.status_code == 200:
            return True, res2.json()
        return False, res2.json()

    return False, res.json()

def get_branches(token, owner, repo):
    url = f"{API_BASE}/repos/{owner}/{repo}/branches"
    res = requests.get(url, headers=get_headers(token), timeout=15)
    if res.status_code == 200:
        return res.json()
    return []

def get_rate_limit(token):
    url = f"{API_BASE}/rate_limit"
    res = requests.get(url, headers=get_headers(token), timeout=10)
    if res.status_code == 200:
        return res.json()
    return None
