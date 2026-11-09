import os
import paramiko
from typing import List, Optional
from dataclasses import dataclass
from sqlmodel import Session
from app.models import ImportSource
from app.parsers.registry import detect_and_parse
from app.services.ingestion_service import ingest_transactions
from app.services.transfer_service import pair_inter_account_transfers

@dataclass
class RemoteFileInfo:
    filename: str
    size: int
    modified_time: float

def get_ssh_client(
    host: str,
    user: str,
    port: int = 22,
    key_path: Optional[str] = None
) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Look for SSH keys in standard locations if key_path not provided
    default_keys = [
        key_path,
        os.path.expanduser("~/.ssh/id_rsa"),
        os.path.expanduser("~/.ssh/id_ed25519"),
        "/root/.ssh/id_rsa",
        "/root/.ssh/id_ed25519"
    ]
    key_file = next((k for k in default_keys if k and os.path.exists(k)), None)

    connect_kwargs = {
        "hostname": host,
        "port": port,
        "username": user,
        "timeout": 10
    }
    if key_file:
        connect_kwargs["key_filename"] = key_file

    client.connect(**connect_kwargs)
    return client

def list_remote_statement_files(
    host: str = "192.168.1.185",
    user: str = "server",
    remote_path: str = "/home/server/Scaricati/robe/Scaricati",
    key_path: Optional[str] = None
) -> List[RemoteFileInfo]:
    files: List[RemoteFileInfo] = []
    client = get_ssh_client(host, user, key_path=key_path)
    try:
        sftp = client.open_sftp()
        for attr in sftp.listdir_attr(remote_path):
            fn = attr.filename
            fn_lower = fn.lower()
            if fn_lower.endswith((".csv", ".xlsx", ".xls")):
                files.append(RemoteFileInfo(
                    filename=fn,
                    size=attr.st_size,
                    modified_time=getattr(attr, "st_mtime", 0.0)
                ))
        sftp.close()
    finally:
        client.close()

    # Sort descending by modified time
    files.sort(key=lambda x: x.modified_time, reverse=True)
    return files

def fetch_remote_file_content(
    host: str = "192.168.1.185",
    user: str = "server",
    remote_path: str = "/home/server/Scaricati/robe/Scaricati",
    filename: str = "",
    key_path: Optional[str] = None
) -> bytes:
    client = get_ssh_client(host, user, key_path=key_path)
    try:
        sftp = client.open_sftp()
        safe_filename = os.path.basename(filename)
        remote_file_path = f"{remote_path.rstrip('/')}/{safe_filename}"
        with sftp.open(remote_file_path, "rb") as f:
            content = f.read()
        sftp.close()
        return content
    finally:
        client.close()

def sync_remote_files(
    session: Session,
    host: str = "192.168.1.185",
    user: str = "server",
    remote_path: str = "/home/server/Scaricati/robe/Scaricati",
    filenames: Optional[List[str]] = None,
    key_path: Optional[str] = None
) -> List[dict]:
    available_files = list_remote_statement_files(host, user, remote_path, key_path)
    target_names = filenames or [f.filename for f in available_files]

    results = []
    for fn in target_names:
        try:
            content = fetch_remote_file_content(host, user, remote_path, fn, key_path)
            bank_name, norm_txs = detect_and_parse(content, fn)
            if norm_txs:
                batch, imported, skipped = ingest_transactions(
                    session=session,
                    transactions=norm_txs,
                    filename=fn,
                    source=ImportSource.SSH_REMOTE
                )
                results.append({
                    "filename": fn,
                    "bank": bank_name,
                    "imported": imported,
                    "skipped": skipped,
                    "status": "SUCCESS"
                })
            else:
                results.append({
                    "filename": fn,
                    "bank": bank_name,
                    "imported": 0,
                    "skipped": 0,
                    "status": "UNRECOGNIZED_OR_EMPTY"
                })
        except Exception as e:
            results.append({
                "filename": fn,
                "imported": 0,
                "skipped": 0,
                "status": f"ERROR: {str(e)}"
            })

    # Pair inter-account transfers after batch ingestion
    pair_inter_account_transfers(session)

    return results
