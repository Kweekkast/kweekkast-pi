import serial.tools.list_ports
import time

from kweekkast_common.communicator_distributor import CommunicatorDistributor
from kweekkast_common.connection.connection import Connection, ConnectionDevice
from kweekkast_common.listener.connection_listener import ConnectionListener
from kweekkast_common.logger_component import console_logger, file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_core.connection.serial_connection import SerialConnection


class SerialConnectionListener(ConnectionListener):

    def __init__(self, distributor: "CommunicatorDistributor"):
        super().__init__(distributor)
        self.knownPorts: set = set()
        self.running: bool = True
        self.defaultBaudRate: int = 115200

        # Trefwoorden per apparaat — pas aan naar jouw situatie
        self.espKeywords = ("CH340", "CP210", "CP2102", "UART")
        self.piKeywords = ("Raspberry", "Pi")

    def HandleIncommingDevices(self) -> None:
        file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, "Wachten op seriële apparaten...")
        try:
            while self.running:
                current_ports = {
                    p.device
                    for p in serial.tools.list_ports.comports()
                    if self.IsKnownDevice(p.description)
                }

                for port in current_ports - self.knownPorts:
                    self.knownPorts.add(port)
                    connection = self.CreateConnection(port)
                    file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, f"Nieuw apparaat: {port} ({connection.device.name})")
                    console_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, f"Nieuw apparaat: {port} ({connection.device.name})")
                    self.distributer.AddConnection(port, connection)

                for port in self.knownPorts - current_ports:
                    self.knownPorts.discard(port)
                    file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, f"Losgekoppeld: {port}")
                    self.distributer.RemoveConnection(port)

                time.sleep(1)

        except KeyboardInterrupt:
            file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, "proces gestopt.")

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
