import os
import glob
import time
import zipfile
import tempfile
import base64
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from utils import console, logger, log_history, human_size
from config import get_config
from github_api import upload_file_api, delete_file_api, get_repo_contents

def upload_single_file(token, owner, repo, local_path, remote_path, branch="main", retry_count=3):
    if not os.path.exists(local_path):
        return False, f"Local file not found: {local_path}"

    try:
        with open(local_path, "rb") as f:
            content_bytes = f.read()
    except Exception as e:
        return False, f"Error reading file: {e}"

    commit_msg = f"Upload {remote_path} via GHUP Termux"
    
    for attempt in range(1, retry_count + 1):
        try:
            success, result = upload_file_api(token, owner, repo, remote_path, content_bytes, commit_msg, branch)
            if success:
                log_history("UPLOAD", f"{local_path} -> {owner}/{repo}:{remote_path} ({branch})")
                return True, "Uploaded successfully"
            else:
                msg = result.get("message", "Unknown API error")
                if attempt == retry_count:
                    return False, msg
        except requests.exceptions.RequestException as e:
            if attempt == retry_count:
                return False, f"Network error after {retry_count} attempts: {e}"
        time.sleep(1.5 * attempt)
    return False, "Max retry attempts reached."

def upload_files_batch(token, owner, repo, files_list, branch="main", custom_folder="", use_parallel=True):
    retry_count = get_config("retry_count", 3)
    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task_id = progress.add_task("[cyan]Uploading files...", total=len(files_list))

        if use_parallel and len(files_list) > 1:
            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_file = {}
                for local_path, remote_sub in files_list:
                    rem_path = f"{custom_folder.strip('/')}/{remote_sub}".strip("/") if custom_folder else remote_sub
                    future = executor.submit(upload_single_file, token, owner, repo, local_path, rem_path, branch, retry_count)
                    future_to_file[future] = (local_path, rem_path)

                for future in as_completed(future_to_file):
                    l_path, r_path = future_to_file[future]
                    try:
                        success, err_msg = future.result()
                        results.append((l_path, success, err_msg))
                    except Exception as e:
                        results.append((l_path, False, str(e)))
                    progress.advance(task_id)
        else:
            for local_path, remote_sub in files_list:
                rem_path = f"{custom_folder.strip('/')}/{remote_sub}".strip("/") if custom_folder else remote_sub
                progress.update(task_id, description=f"[cyan]Uploading {os.path.basename(local_path)}...")
                success, err_msg = upload_single_file(token, owner, repo, local_path, rem_path, branch, retry_count)
                results.append((local_path, success, err_msg))
                progress.advance(task_id)

    return results

def handle_upload_target(token, owner, repo, target, folder_opt="", zip_opt=False, flat_opt=False, branch="main"):
    expanded_files = []
    
    if "*" in target or "?" in target:
        matched = glob.glob(target, recursive=True)
        for m in matched:
            if os.path.isfile(m):
                expanded_files.append((m, os.path.basename(m)))
    elif os.path.isfile(target):
        expanded_files.append((target, os.path.basename(target)))
    elif os.path.isdir(target):
        base_dir = os.path.abspath(target)
        if zip_opt or get_config("zip_compression", False):
            zip_name = f"{os.path.basename(base_dir)}.zip"
            zip_path = os.path.join(tempfile.gettempdir(), zip_name)
            console.print(f"[info]Compressing folder {target} into {zip_name}...[/info]")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(base_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.dirname(base_dir))
                        zipf.write(file_path, arcname)
            expanded_files.append((zip_path, zip_name))
        else:
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    if flat_opt:
                        rel_path = file
                    else:
                        rel_path = os.path.relpath(full_path, base_dir)
                    expanded_files.append((full_path, rel_path))
    else:
        console.print(f"[error]Target not found or invalid: {target}[/error]")
        return

    if not expanded_files:
        console.print("[warning]No files found to upload.[/warning]")
        return

    console.print(f"[info]Found {len(expanded_files)} file(s) to upload to {owner}/{repo} (branch: {branch})[/info]")
    use_parallel = get_config("parallel_upload", True)
    results = upload_files_batch(token, owner, repo, expanded_files, branch, folder_opt, use_parallel)

    success_count = sum(1 for _, ok, _ in results if ok)
    fail_count = len(results) - success_count

    console.print(f"\n[success]Upload complete![/success] Success: {success_count}, Failed: {fail_count}")
    for l_path, ok, err in results:
        if ok:
            console.print(f"  [green]✔[/green] {l_path}")
        else:
            console.print(f"  [red]✖ {l_path}: {err}[/red]")

def download_remote_file(token, owner, repo, remote_path, output_path=None, branch="main"):
    data = get_repo_contents(token, owner, repo, remote_path, branch)
    if not data:
        console.print(f"[error]Remote path not found: {remote_path}[/error]")
        return
    
    if isinstance(data, list):
        console.print(f"[error]{remote_path} is a directory, not a file. Use 'ghup ls' to view contents.[/error]")
        return

    download_url = data.get("download_url")
    content_b64 = data.get("content")
    file_name = data.get("name", os.path.basename(remote_path))
    out_file = output_path if output_path else file_name

    if content_b64:
        content_bytes = base64.b64decode(content_b64)
    elif download_url:
        res = requests.get(download_url, timeout=30)
        if res.status_code == 200:
            content_bytes = res.content
        else:
            console.print(f"[error]Failed to download from URL: {res.status_code}[/error]")
            return
    else:
        console.print("[error]Could not retrieve file content.[/error]")
        return

    try:
        with open(out_file, "wb") as f:
            f.write(content_bytes)
        console.print(f"[success]Successfully downloaded to {out_file}[/success]")
        log_history("DOWNLOAD", f"{owner}/{repo}:{remote_path} -> {out_file}")
    except Exception as e:
        console.print(f"[error]Failed to save file: {e}[/error]")
