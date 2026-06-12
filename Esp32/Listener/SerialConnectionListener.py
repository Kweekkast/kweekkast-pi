from __future__ import annotations
import serial.tools.list_ports
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Esp32.CommunicatorDistributer import CommunicatorDistributer

from Esp32.Connection.Connection import Connection
from Esp32.Connection.SerialConnection import SerialConnection
from Esp32.Listener.ConnectionListener import ConnectionListener


class SerialConnectionListener(ConnectionListener):

    def __init__(self, distributer: "CommunicatorDistributer"):
        super().__init__(distributer)
        self.knownPorts: set = set()
        self.running: bool = True
        self.defaultBaudRate: int = 115200

    def HandleIncommingDevices(self) -> None:
        print("[SerialConnectionListener] Wachten op seriële apparaten...")
        try:
            while self.running:
                currentPorts = {
                    p.device
                    for p in serial.tools.list_ports.comports()
                    if any(kw in p.description for kw in ("USB", "CH340", "CP210", "UART"))
                }

                for port in currentPorts - self.knownPorts:
                    self.knownPorts.add(port)
                    print(f"[SerialConnectionListener] Nieuw apparaat: {port}")
                    self.distributer.AddConnection(port, self.CreateConnection(port))

                for port in self.knownPorts - currentPorts:
                    self.knownPorts.discard(port)
                    print(f"[SerialConnectionListener] Losgekoppeld: {port}")
                    self.distributer.RemoveConnection(port)

                time.sleep(1)

        except KeyboardInterrupt:
            print("[SerialConnectionListener] Gestopt.")

    def StopReadingIncommingDevices(self) -> None:
        self.running = False

    def CreateConnection(self, identifier: str) -> Connection:
        return SerialConnection(identifier, self.defaultBaudRate)