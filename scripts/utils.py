import os
from pathlib import Path

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient

CONNECTION_STRING_FORMAT = "DefaultEndpointsProtocol=https;AccountName={account_name};" \
                           "AccountKey={account_key};EndpointSuffix=core.windows.net"


def authenticate_blob_client(account_name: str, account_key: str) -> BlobServiceClient:
    return BlobServiceClient.from_connection_string(
        CONNECTION_STRING_FORMAT.format(
            account_name=account_name,
            account_key=account_key
        )
    )


def upload_blob(file_path: str, container: str, client: BlobServiceClient, dest_path: str = None):
    # dest_path = dest_path or os.path.split(file_path)[1]
    if dest_path is None:
        dest_path = file_path
    
    blob_client = client.get_blob_client(
        container=container,
        blob=dest_path
    )
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data)

    return blob_client.url


def download_blob(client: BlobServiceClient, container: str, filename: str, download_dir: str):
    blob_client = client.get_blob_client(container, filename)

    path = os.path.join(download_dir, os.path.basename(filename))
    with open(path, "wb") as download_file:
        download_file.write(blob_client.download_blob().readall())


def upload_folder(folder_path: str, container: str, client: BlobServiceClient):
    all_files = [str(x.relative_to(Path())) for x in Path(folder_path).glob("**/*") if x.is_file()]
    for f in all_files:
        try:
            print(f"Uploading: {f}")
            upload_blob(f, container, client)
        except ResourceExistsError as e:
            print(f"{f} already exists in container")


def download_folder(folder_path: str, dest_path: str, container: str, client: BlobServiceClient):
    container_client = client.get_container_client(container)
    all_files = container_client.list_blobs(name_starts_with=folder_path)

    os.makedirs(dest_path, exist_ok=True)
    for f in all_files:
        print(f"Downloading {f.name} to {dest_path}")
        download_blob(client, container, f.name, dest_path)
