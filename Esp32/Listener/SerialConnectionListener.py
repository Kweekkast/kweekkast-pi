from __future__ import annotations
import serial.tools.list_ports
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Esp32.CommunicatorDistributer import CommunicatorDistributer

from Esp32.Connection.Connection import Connection, ConnectionDevice
from Esp32.Connection.SerialConnection import SerialConnection
from Esp32.Listener.ConnectionListener import ConnectionListener


class SerialConnectionListener(ConnectionListener):

    def __init__(self, distributer: "CommunicatorDistributer"):
        super().__init__(distributer)
        self.knownPorts: set = set()
        self.running: bool = True
        self.defaultBaudRate: int = 115200

        # Trefwoorden per apparaat — pas aan naar jouw situatie
        self.espKeywords = ("CH340", "CP210", "CP2102", "UART")
        self.piKeywords = ("Raspberry", "Pi")

    def HandleIncommingDevices(self) -> None:
        print("[SerialConnectionListener] Wachten op seriële apparaten...")
        try:
            while self.running:
                currentPorts = {
                    p.device
                    for p in serial.tools.list_ports.comports()
                    if self.IsKnownDevice(p.description)
                }

                for port in currentPorts - self.knownPorts:
                    self.knownPorts.add(port)
                    connection = self.CreateConnection(port)
                    print(f"[SerialConnectionListener] Nieuw apparaat: {port} ({connection.device.name})")
                    self.distributer.AddConnection(port, connection)

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
        description = self.GetDescription(identifier)
        device = self.DetectDevice(description)
        return SerialConnection(identifier, device, self.defaultBaudRate)

    def IsKnownDevice(self, description: str) -> bool:
        allKeywords = self.espKeywords + self.piKeywords
        return any(kw in description for kw in allKeywords)

    def DetectDevice(self, description: str) -> ConnectionDevice:
        if any(kw in description for kw in self.piKeywords):
            return ConnectionDevice.PI
        return ConnectionDevice.ESP

    def GetDescription(self, port: str) -> str:
        for p in serial.tools.list_ports.comports():
            if p.device == port:
                return p.description
        return ""