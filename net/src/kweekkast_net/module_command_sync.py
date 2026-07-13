import time

from kweekkast_common.logger_component import console_logger, file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.net_core_protocol import encode_signed_module_command_config_frame


class ModuleCommandTransmitter:
    def send_frame(self, frame: bytes) -> None:
        raise NotImplementedError


class ModuleCommandSyncService:
    def __init__(self, client, transmitter: ModuleCommandTransmitter, poll_seconds: float = 10.0):
        self.client = client
        self.transmitter = transmitter
        self.poll_seconds = poll_seconds
        self.running = True

    def run_once(self) -> dict | None:
        envelope = self.client.fetch_signed_config()
        if envelope is None:
            file_logger.logger.log(
                MessageSeverity.DEV,
                self.__class__.__name__,
                "Module command snapshot unchanged.",
            )
            return None

        frame = encode_signed_module_command_config_frame(envelope)
        self.transmitter.send_frame(frame)
        file_logger.logger.log(
            MessageSeverity.DEV,
            self.__class__.__name__,
            f"Sent signed module command config sequence {envelope['payload']['config_sequence']}.",
        )
        return envelope

    def run_forever(self) -> None:
        try:
            while self.running:
                try:
                    self.run_once()
                except Exception as exc:
                    message = f"Module command sync failed: {exc!r}"
                    file_logger.logger.log(MessageSeverity.ERROR, self.__class__.__name__, message)
                    console_logger.logger.log(MessageSeverity.ERROR, self.__class__.__name__, message)

                time.sleep(self.poll_seconds)
        finally:
            close = getattr(self.client, "close", None)
            if close:
                close()
            close = getattr(self.transmitter, "close", None)
            if close:
                close()

    def stop(self) -> None:
        self.running = False
