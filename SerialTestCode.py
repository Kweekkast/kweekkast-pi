import threading
import serial
import serial.tools.list_ports
import time


def handle_device(port: str, baudrate: int = 115200) -> None:
    """Draait in een eigen thread, leest continu data van één ESP32."""
    try:
        ser = serial.Serial(port=port, baudrate=baudrate, timeout=1)
        print(f"[{port}] Verbonden")

        while True:
            if ser.in_waiting:
                line = ser.readline().decode("utf-8", errors="replace").strip()
                if line:
                    print(f"[{port}] {line}")

    except serial.SerialException as e:
        print(f"[{port}] Verbinding verloren: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print(f"[{port}] Verbinding gesloten")


class Main:
    def __init__(self):
        self._known_ports: set = set()
        self._threads: dict = {}

    def _start_thread(self, port: str) -> None:
        t = threading.Thread(target=handle_device, args=(port,), name=port, daemon=True)
        self._threads[port] = t
        t.start()
        print(f"[MAIN] Nieuwe thread gestart voor {port}")

    def run(self) -> None:
        print("[MAIN] Wachten op apparaten... (Ctrl+C om te stoppen)\n")

        try:
            while True:
                # Haal alle huidige ESP32/Arduino poorten op
                current_ports = {
                    p.device
                    for p in serial.tools.list_ports.comports()
                    if "USB" in p.description or "CH340" in p.description
                       or "CP210" in p.description or "UART" in p.description
                }

                # Nieuw apparaat aangesloten?
                for port in current_ports - self._known_ports:
                    self._known_ports.add(port)
                    self._start_thread(port)

                # Apparaat verwijderd?
                for port in self._known_ports - current_ports:
                    self._known_ports.discard(port)
                    print(f"[MAIN] {port} losgekoppeld")

                time.sleep(1)  # Check elke seconde op nieuwe apparaten

        except KeyboardInterrupt:
            print("\n[MAIN] Gestopt door gebruiker.")


if __name__ == "__main__":
    Main().run()