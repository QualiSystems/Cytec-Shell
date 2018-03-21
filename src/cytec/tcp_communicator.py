import socket


class TcpCommunicator(object):
    SOCKET_TIMEOUT = 2
    NEW_LINE = '\r\n'
    MAX_ATTEMPTS = 3

    def __init__(self, address, port, logger=None):
        self.logger = logger
        self.address = address
        self.port = port
        self._socket = None
        self._initialize_socket()

    def _initialize_socket(self):
        self.logger.debug('Initialize connection to {0}:{1}'.format(self.address, self.port))
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self.address, int(self.port)))
        self._socket.settimeout(self.SOCKET_TIMEOUT)

    def _reconnect_socket(self):
        self.logger.debug('Reconnect socket')
        self._socket.close()
        self._initialize_socket()

    def _validate_socket(self):
        self.logger.debug('Validate socket')
        attempt = 0
        while attempt < self.MAX_ATTEMPTS:
            try:
                self._socket.recv(4096)
                self._socket.send(self.NEW_LINE)
                self._socket.recv(4096)
                self._reconnect_socket()
            except socket.timeout, e:
                self.logger.debug('Validation done')
                return
            except socket.error, e:
                self._reconnect_socket()
            finally:
                attempt += 1
        raise Exception(self.__class__.__name__, 'Socket validation failed')

    def send_command(self, command):
        self._validate_socket()
        command += self.NEW_LINE
        self.logger.debug('Send command: {}'.format(command))
        self._socket.send(command)
        attempt = 0
        data = ''
        while attempt < self.MAX_ATTEMPTS:
            try:
                data += self._socket.recv(4096)
            except socket.timeout, e:
                return data
            except socket.error, e:
                self._reconnect_socket()
            finally:
                attempt += 1

    def __del__(self):
        if self._socket:
            self._socket.close()

    def close(self):
        self.__del__()
