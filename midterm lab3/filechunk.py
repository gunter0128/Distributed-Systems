#!/usr/bin/python3
import os
import sys
import hashlib
import requests
import msgpackrpc
from chunker import FileChunker

def debug_upload(filename: str, node_ip: str):
    chunker = FileChunker(size=1024*1024*4)  # 以 4MB 為單位分割檔案
    print("Processing file:", filename)

    chunks, metadata = chunker.split_file(filename)
    print(f"Split into {len(chunks)} chunks")

    client = msgpackrpc.Client(msgpackrpc.Address(node_ip, 5657))

    for i, (chunk_hash, chunk_data) in enumerate(chunks):
        node = client.call('find_successor', chunk_hash)
        print(f"Uploading chunk {i+1}/{len(chunks)} to target {node['ip']}")

        chunk_filename = f"{os.path.basename(filename)}.{chunk_hash}"
        files = {'file': (chunk_filename, chunk_data)}
        response = requests.post(
            f"http://{node['ip']}:5000/upload",
            files=files
        )
        print(f"Response status: {response.status_code}")

    target_hash = hashlib.md5(f"{filename}{metadata}".encode()).hexdigest()[:16]
    target_node = client.call('find_successor', target_hash)
    print(f"Uploading metadata to {target_node['ip']}")

    with open(f"{filename}.metadata", 'wb') as f:
        f.write(metadata)

    with open(f"{filename}.metadata", 'rb') as f:
        files = {'file': (f"{filename}.metadata", f)}
        response = requests.post(
            f"http://{target_node['ip']}:5000/upload",
            files=files
        )
        print(f"Metadata upload response: {response.status_code}")

if __name__ == "__main__":
    debug_upload(sys.argv[1], sys.argv[2])
