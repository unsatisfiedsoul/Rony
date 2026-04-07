import socket
s = socket.socket()
s.connect(('14.102.93.125', 2000))
s.send(b'bandwidth-test 1 1 1 1\r\n')
s.send(b'/system resource print\r\n')
print(s.recv(4096))
