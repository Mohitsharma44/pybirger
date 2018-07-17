import telnetlib
import socket
import atexit
import time
from telnetlib import IAC, NOP
from functools import wraps
from pybirger.utils import pybirgerlogger

class Birger():
    def __init__(self, tn_host, tn_port, *args, **kwargs):
        """
        Parameters
        ----------
        tn_host: str
            birger adapter/ UDS1100 host ip or fqdn
        tn_port: int
            birger adapter/ UDS1100 host port
        """
        self.logger = pybirgerlogger.pybirgerlogger(tofile=False)
        self.TELNET_HOST = tn_host
        self.TELNET_PORT = tn_port
        self.eof = "\r\n".encode('ascii')
        self._openTelnet(self.TELNET_HOST, self.TELNET_PORT)
        self._init_aperture()
        self._learn_focus()
        atexit.register(self.cleanup)
        
    def _openTelnet(self, host, port):
        """
        Open Telnet connection with the host
        Parameters
        ----------
        host : str
            ip address/ fqdn of the host to connect to
        port : int
            port number to connect to
        Returns
        -------
        tn : telnet object
        """
        try:
            self.logger.info("Opening Telnet connection")
            self.tn = telnetlib.Telnet()
            self.tn.open(host, port)
            self.tn.read_until(self.eof, timeout=2)
            # Keep Telnet socket Alive!
            self._keepConnectionAlive(self.tn.sock)
            #return self.tn
        except Exception as ex:
            self.logger.critical("Cannot open Telnet connection: "+ str(ex))

    def _closeTelnet(self):
        """
        Close the telnet connection.
        """
        try:
            self.logger.warning("Closing Telnet connection")
            self.tn.write('\x1d'.encode('ascii')+self.eof)
            self.tn.close()
        except:
            # Telnet connection was broken, Don't do anything
            pass
            
    def _keepConnectionAlive(self, sock, idle_after_sec=1, interval_sec=1, max_fails=60):
        """
        Keep the socket alive
        Parameters
        ----------
        sock: TCP socket
        idle_after_sec: int
            activate after `idle_after` seconds of idleness
            default: 1
        interval_sec: int
            interval between which keepalive ping is to be sent
            default: 3
        max_fails: int
            maximum keep alive attempts before closing the socket
            default: 5
        """
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, idle_after_sec)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval_sec)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, max_fails)

    def _checkTelnetConnection(func):
        """
        Check the telnet connection is alive or not.
        This method should not be called outside the class
        This method should be used as a `decorator` to make sure
        that the connection to the camera is active. If not active, it will
        call the `_resetTelnetConnection` which will take care of
        closing and re-opening the telnet connection
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                if self.tn.sock:
                    self.tn.sock.send(IAC+NOP+self.eof)
                    self.tn.read_until(self.eof, timeout=2)
                    self.logger.debug("Detected Telnet connection is alive")
                    return func(self, *args, **kwargs)
                else:
                    self._resetTelnetConnection()
            except Exception as ex:
                self.logger.warning("Detected Telnet connection is dead: "+ str(ex))
                self._resetTelnetConnection()
                return wrapper(self, *args, **kwargs)
        return wrapper

    def _resetTelnetConnection(self):
        """
        Close the telnet connection and
        Reopen.
        This method should not be called
        outside the class / standalone
        """
        try:
            self.logger.warning("Restarting Telnet connection")
            self._closeTelnet()
            self.tn = None
            time.sleep(1)
            self._openTelnet(self.TELNET_HOST, self.TELNET_PORT)
        except Exception as ex:
            self.logger.critical("Cannot reset telnet connection: "+ str(ex))

    def read(self, output):
        """
        Parse the output from the camera
        by filtering the padding and other sentinels
        """
        try:
            resp = output.split()[-1]
            return resp
        except Exception as ex:
            self.logger.error("The following error was returned: {}".format(output))
            return False
            
    @_checkTelnetConnection
    def _init_aperture(self):
        """
        Initialize the aperture motor
        """
        try:
            self.tn.write("in".encode('ascii')+self.eof)
            self.read(self.tn.read_until(self.eof, timeout=2))
        except Exception as ex:
            self.logger.warning("Cannot initialize the aperture: "+ str(ex))

    @_checkTelnetConnection
    def _learn_focus(self):
        """
        Learn absolute focus range
        """
        try:
            self.tn.write("la".encode('ascii')+self.eof)
            self.read(self.tn.read_until(self.eof, timeout=2))
        except Exception as ex:
            self.logger.warning("Error learning focus range: "+ str(ex))
            
    @_checkTelnetConnection
    def version(self):
        """
        Get the version information
        of the Cannon ES232 library
        """
        try:
            self.tn.write("lv".encode('ascii')+self.eof)
            return(self.read(self.tn.read_until(self.eof, timeout=2)))
        except Exception as ex:
            self.logger.warning("Cannot obtain version: "+ str(ex))
            
    @_checkTelnetConnection
    def sn(self):
        """
        Get the Serial number of the birger adapter
        """
        try:
            self.tn.write("sn".encode('ascii')+self.eof)
            return(self.read(self.tn.read_until(self.eof, timeout=2)))
        except Exception as ex:
            self.logger.warning("Cannot obtain serial number: "+ str(ex))

    @_checkTelnetConnection
    def get_focus(self):
        """
        Get the current focus of the lens
        """
        try:
            self.tn.write("pf".encode('ascii')+self.eof)
            return(self.read(self.tn.read_until(self.eof, timeout=2)))
        except Exception as ex:
            self.logger.warning("Cannot obtain focus: "+ str(ex))

    @_checkTelnetConnection
    def set_focus(self, abs_val):
        """
        Parameters
        ----------
        abs_val: int
            Set the focus of the lens to abs_val
            .. note: -1 = infinity/ max
        """
        try:
            if abs_val == -1:
                self.tn.write("mi".encode('ascii')+self.eof)
            elif abs_val == 0:
                self.tn.write("mz".encode('ascii')+self.eof)
            else:
                self.tn.write("fa {}".format(abs_val).encode('ascii')+self.eof)
            return(self.read(self.tn.read_until(self.eof, timeout=2)))
        except Exception as ex:
            self.logger.warning("Cannot set focus: "+ str(ex))
    
    @_checkTelnetConnection
    def get_aperture(self):
        """
        Get the current aperture position of the lens
        """
        try:
            self.tn.write("pa".encode('ascii')+self.eof)
            return(self.read(self.tn.read_until(self.eof, timeout=2)))
        except Exception as ex:
            self.logger.warning("Cannot obtain aperture: "+ str(ex))
    
    @_checkTelnetConnection
    def set_aperture(self, abs_val):
        """
        Parameters
        ----------
        abs_val: int
            Set the aperture of the lens to abs_val
            .. note: -1 = infinity/ max
        """
        try:
            if abs_val == -1:
                self.tn.write("mo".encode('ascii')+self.eof)
            elif abs_val == 0:
                self.tn.write("mc".encode('ascii')+self.eof)
            else:
                self.tn.write("ma {}".format(abs_val).encode('ascii')+self.eof)
            return(self.read(self.tn.read_until(self.eof, timeout=2)))
        except Exception as ex:
            self.logger.warning("Cannot set aperture: "+ str(ex))

    @_checkTelnetConnection
    def lens_info(self):
        """
        Get the extended lens information
        """
        try:
            self.tn.write("lc".encode('ascii')+self.eof)
            return(self.read(self.tn.read_until(self.eof, timeout=2)))
        except Exception as ex:
            self.logger.warning("Cannot obtain extended lens information: "+ str(ex))

    @_checkTelnetConnection            
    def lens_present(self):
        """
        Check if the lens is present
        """
        try:
            self.tn.write("lp".encode('ascii')+self.eof)
            return(self.read(self.tn.read_until(self.eof, timeout=2)))
        except Exception as ex:
            self.logger.warning("Cannot check if lens is present: "+ str(ex))
        
    def cleanup(self):
        """
        Safely close the telnet connection before
        exiting
        """
        try:
            self._closeTelnet()
            self.tn=None
        except Exception:
            # Connection Broken, don't do anything
            pass
