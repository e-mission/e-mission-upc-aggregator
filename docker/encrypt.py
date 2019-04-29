import socket
import subprocess
import tempfile
import time

HOST="127.0.0.1"
PORT=27017

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    data = conn.recv (32)

with tempfile.NamedTemporaryFile () as f:
    name = f.name
    with open ("/root/.ecryptfsrc", "w") as g:
        print ("key=passphrase:passphrase_passwd_file={}".format (name), file=g)
        print ("ecryptfs_cipher=aes", file=g)
        print ("ecryptfs_key_bytes=32", file=g)
        print ("ecryptfs_passthrough=n", file=g)
        print ("ecryptfs_enable_filename_crypto=n", file=g)
    f.write ("passphrase_passwrd={}".format (data))

subprocess.run (["/mount_ecryptfs.sh"])

time.sleep (10)
