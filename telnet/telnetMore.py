from telnetClient import *
import struct
import sys
import socket
import time
import logging

log = logging.getLogger()

class TelnetMore:
    def __init__(self, ip, port, password, commandTimeout, socketTimeout):
        # Throws ValueError if unable to connect!
        # catch in code using this class

        self.telnetClient = TelnetClient(ip, port, password, socketTimeout)
        self.__commandTimeout = commandTimeout
        self.__ip = ip
        self.__port = port

    def __runAndOk(self, command, timeout):
        result = self.telnetClient.sendCommand(command, timeout)
        return result is not None and "OK" in result

    def startApp(self, packageName):
        return self.__runAndOk("more start %s\r\n" % (packageName), self.__commandTimeout)

    def stopApp(self, packageName):
        return self.__runAndOk("more stop %s\r\n" % (packageName), self.__commandTimeout)

    def restartApp(self, packageName):
        return self.__runAndOk("more restart %s\r\n" % (packageName), self.__commandTimeout)

    def resetAppdata(self, packageName):
        return self.__runAndOk("more reset %s\r\n" % (packageName), self.__commandTimeout)

    def clearAppCache(self, packageName):
        return self.__runAndOk("more cache %s\r\n" % (packageName), self.__commandTimeout)

    def turnScreenOn(self):
        return self.__runAndOk("more screen on\r\n", self.__commandTimeout)

    def click(self, x, y):
        return self.__runAndOk("screen click %s %s\r\n" % (str(x), str(y)), self.__commandTimeout)

    def __close_socket(self, connection):
        try:
            connection.shutdown(socket.SHUT_RDWR)
        except:
            pass
        try:
            connection.close()
        except:
            pass

    def __read(self, s):
        """Read data and return the read bytes."""
        try:
            data, sender = s.recvfrom(4096)
            return data
        except (socket.timeout, AttributeError, OSError):
            return b''
        except (AttributeError):
            self.__close_socket(s)
            return b''

    def __connectImageSocket(self, s):
        try:
            s.connect((self.__ip, self.__port + 1))
            s.setblocking(1)
            return True
        except:
            log.warning("telnetMore::getScreenshot: Failed connecting to socket...")
            return False

    def getScreenshot(self, path):
        encoded = self.telnetClient.sendCommand("screen capture\r\n", self.__commandTimeout)
        if encoded is None:
            return False
        elif len(encoded) < 500 and "KO: " in encoded:
            log.error("getScreenshot: Could not retrieve screenshot. Check if mediaprojection is enabled!")
            return False
        # fh = open(path, "wb")
        # fh.write(encoded.decode('base64'))
        # fh.close()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        attempts = 0
        while not self.__connectImageSocket(s):
            attempts = attempts + 1
            time.sleep(0.5)
            if attempts > 100:
                self.__close_socket(s)
                return False

        data = self.__read(s)
        image = self.__read(s)
        try:
            values = struct.unpack(">I", bytearray(data))
        except:
            self.__close_socket(s)
            return False
        sizeToReceive = int(values[0])

        while sizeToReceive >= sys.getsizeof(image):
            received = self.__read(s)
            if received == b'':
                continue
            image = image + received

        self.__close_socket(s)
        fh = open(path, "wb")
        fh.write(image)
        fh.close()
        return True

    def backButton(self):
        return self.__runAndOk("screen back\r\n", self.__commandTimeout)

    def isScreenOn(self):
        state = self.telnetClient.sendCommand("more state screen\r\n", self.__commandTimeout)
        if state is None:
            return False
        return "on" in state

    def isPogoTopmost(self):
        topmost = self.telnetClient.sendCommand("more topmost app\r\n", self.__commandTimeout)
        if topmost is None:
            return False
        return "com.nianticlabs.pokemongo" in topmost
