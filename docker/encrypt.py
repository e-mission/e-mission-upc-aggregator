import os
import socket
import subprocess
import tempfile
import time

HOST=os.environ.get('DB_HOST')
PORT=27018

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    conn, addr = s.accept()
    data = conn.recv (32)

    with tempfile.NamedTemporaryFile (mode="wb") as f:
        name = f.name
        with open ("/root/.ecryptfsrc", "w") as g:
            print ("key=passphrase:passphrase_passwd_file={}".format (name), file=g)
            print ("ecryptfs_cipher=aes", file=g)
            print ("ecryptfs_key_bytes=32", file=g)
            print ("ecryptfs_passthrough=n", file=g)
            print ("ecryptfs_enable_filename_crypto=n", file=g)
        f.write ("passphrase_passwd=".encode ("utf-8"))
        f.write (data)
        f.flush ()
        subprocess.call (["/mount_ecryptfs.sh"])
    conn.sendall (b'Received')
