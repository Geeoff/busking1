# Copyright 2024 Geoffrey Cagle (geoff.v.cagle@gmail.com).
"""Implements Os2lServer and related dataclasses.
   This logic is based on spec and sample code from http://os2l.org/."""
from dataclasses import dataclass
from typing import Optional, Union, Iterable
import socket
import selectors
import json

###############################################################################
@dataclass
class BtnEvent:
    name : str
    page : Optional[str]
    is_on : bool

@dataclass
class CmdEvent:
    idnum : int
    param : float

@dataclass
class BeatEvent:
    change : bool
    pos : int
    bpm : float
    strength : float

###############################################################################
class Os2lServer:
    """This server handles OS2L messages from an OS2L client, such as VirtualDJ.
       This class can be used in a with-statement, or you can use the start and shutdown functions.
       Use the poll function to accept the client and receive events."""

    def __init__(self, ip:str="127.0.0.1", port:int=9996):
        self.listen_addr = (ip, port)
        self.listen_socket = None
        self.selector = None
        self.client_addr = None
        self.client_socket = None
        self.recv_buffer = ""

    def __enter__(self) -> None:
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self.shutdown()
        return False

    def start(self) -> None:
        """Starts the server. After this call, the server is ready to receive a client."""
        print("Starting OS2L Server...")
        
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        assert self.listen_socket is not None

        self.listen_socket.bind(self.listen_addr)
        self.listen_socket.listen(2)

        # Use a selector to avoid blocking.
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.listen_socket, selectors.EVENT_READ)
        self.listen_socket.setblocking(False)
        
        print("OS2L Server Started.")

    def shutdown(self) -> None:
        """Disconnect from the client and shutdown the server."""
        print("Shutting down OS2L Server...")
        
        self.client_addr = None

        if self.client_socket is not None:
            self.client_socket.close()
            self.client_socket = None

        if self.selector is not None:
            self.selector.close()
            self.selector = None

        if self.listen_socket is not None:
            self.listen_socket.close()
            self.listen_socket = None
            
        print("OS2L Server Shutdown.")
            
    def restart(self) -> None:
        """Restart OS2L Server.
           Use this when restarting VirtualDJ, otherwise a reconnection will cause an exception."""
        self.shutdown()
        self.start()

    def poll(self) -> Iterable[Union[BtnEvent, CmdEvent, BeatEvent]]:
        """Call this generator in your main loop.  It accepts the client and yields events from the client."""
        for key, mask in self.selector.select(0.0):
            if key.fileobj is self.listen_socket:
                assert key.data is None
                self.__accept_client()

            elif key.fileobj == self.client_socket:
                assert (mask & selectors.EVENT_READ) != 0
                yield from self.__recv_from_client()

            else:
                raise Exception("OS2L ERROR: Unexpected socket from selector!")

    def __accept_client(self) -> None:
        """Internal function for accepting the client connection."""
        assert self.client_socket is None # Only accept one client.
        self.client_socket, self.client_addr = self.listen_socket.accept()

        # Use a selector to avoid blocking.
        self.selector.register(self.client_socket, selectors.EVENT_READ)
        self.client_socket.setblocking(False)
        
        print(f"Accepted OS2L client at {self.client_addr}.")

    def __recv_from_client(self) -> Iterable[Union[BtnEvent, CmdEvent, BeatEvent]]:
        """Internal function for receiving JSON from from the client."""
        # Receive bytes from the client.
        data = self.client_socket.recv(1024)

        # Handle lost connection.
        # This logic assumes that we received selectors.EVENT_READ for this client.
        # FIXME: This doesn't seem to work. It's possible that VirtualDJ does not close the
        #        connection, but the connection never ends with a timeout either.
        if data is None:
            print(f"Lost OS2L connection to {self.client_addr}")
            self.client_socket.close()
            self.client_socket = None
            self.client_addr = None
            self.recv_buffer = ""
            return

        # Append buffer with incoming characters. In practice this will be one or more complete JSON
        # objects, but it's possible a JSON object is split over two recv calls.
        self.recv_buffer += data.decode()

        # Consume complete json nodes in the buffer.
        # FIXME: Handle nested JSON objects. This is not expected, per the current OS2L spec.
        # FIXME: Handle curleys in strings. Unlikely, but btn and cmd names could have curleys in them.
        while self.recv_buffer:
            # Find the end of the next event.
            assert self.recv_buffer[0] == "{"
            end = self.recv_buffer.find("}")

            # Exit the loop when there are no more complete JSON nodes.
            if end < 0:
                break

            # Pull next JSON node out of the buffer.
            event_str = self.recv_buffer[:end+1]
            self.recv_buffer = self.recv_buffer[end+1:]
            event_json = json.loads(event_str)

            # Convert JSON into objects.
            if event_json["evt"] == "btn":
                yield BtnEvent(
                    name = event_json["name"],
                    page = event_json.get("page", None),
                    is_on = (event_json["state"] == "on"))

            elif event_json["evt"] == "cmd":
                yield CmdEvent(
                    idnum = event_json["id"],
                    param = event_json["param"])

            elif event_json["evt"] == "beat":
                yield BeatEvent(
                    change = event_json["change"],
                    pos = event_json["pos"],
                    bpm = event_json["bpm"],
                    strength = event_json["strength"])

            else:
                print(f"OS2L ERROR! Invalid evt recieved! JSON='{event_str}'")

if __name__ == "__main__":
    def test() -> None:
        """Test Os2lServer by accepting connections and dumping the events that come in to the console."""
        with Os2lServer() as server:
            while True:
                for data in server.poll():
                    print(data)

    test()
