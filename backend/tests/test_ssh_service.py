from unittest.mock import MagicMock, patch
import pytest
from app.services.ssh_service import (
    RemoteFileInfo,
    list_remote_statement_files,
    fetch_remote_file_content
)

def test_list_remote_statement_files():
    mock_sftp = MagicMock()
    # Mock SFTP attributes
    file1 = MagicMock()
    file1.filename = "Patrimonio - BBVA.csv"
    file1.st_size = 1024
    file1.st_mtime = 1711200000

    file2 = MagicMock()
    file2.filename = "notes.txt"
    file2.st_size = 500

    file3 = MagicMock()
    file3.filename = "movimenti.xlsx"
    file3.st_size = 2048
    file3.st_mtime = 1711250000

    mock_sftp.listdir_attr.return_value = [file1, file2, file3]

    with patch("paramiko.SSHClient") as mock_ssh_cls:
        mock_client = MagicMock()
        mock_client.open_sftp.return_value = mock_sftp
        mock_ssh_cls.return_value = mock_client

        files = list_remote_statement_files(
            host="192.168.1.185",
            user="server",
            remote_path="/home/server/Scaricati/robe/Scaricati"
        )

        assert len(files) == 2
        assert files[0].filename == "movimenti.xlsx"
        assert files[1].filename == "Patrimonio - BBVA.csv"
        assert files[1].size == 1024

def test_fetch_remote_file_content():
    mock_sftp = MagicMock()
    mock_file = MagicMock()
    mock_file.read.return_value = b"Data,Importo\n2026-03-24,-10.0"
    mock_sftp.open.return_value.__enter__.return_value = mock_file

    with patch("paramiko.SSHClient") as mock_ssh_cls:
        mock_client = MagicMock()
        mock_client.open_sftp.return_value = mock_sftp
        mock_ssh_cls.return_value = mock_client

        content = fetch_remote_file_content(
            host="192.168.1.185",
            user="server",
            remote_path="/home/server/Scaricati/robe/Scaricati",
            filename="test.csv"
        )

        assert content == b"Data,Importo\n2026-03-24,-10.0"
