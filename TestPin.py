#!/usr/bin/env python3
import time

try:
    from gpiozero import OutputDevice
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("[GpioController] gpiozero niet beschikbaar, simulatiemodus actief")


from Esp32.CommunicatorDistributer import CommunicatorDistributer

_PIN           = 4   # GPIO-pin (BCM-nummering), maakt verder niet uit welke
_CYCLE_SECONDS = 5   # Totale lengte van één cyclus
_ON_SECONDS    = 1   # Hoe lang de pin aan staat binnen die cyclus


class TestPin:

    def TestPin(self, pin: int = _PIN) -> None:
        """
        Eenvoudige hardwaretest, los van de Connection/Communicator-architectuur.
        Gebruikt gpiozero's generieke OutputDevice (werkt op de Pi 5 via de
        lgpio-backend) om puur een pin aan/uit te zetten, zonder led-specifieke
        klasse — dezelfde aanpak die straks ook voor pompen en lampen gebruikt
        wordt. Zet de pin elke _CYCLE_SECONDS seconden, _ON_SECONDS seconden
        aan (dus 1 seconde aan, 4 seconden uit, herhalen).

        Welke pin gebruikt wordt maakt niet uit, zolang het een geldige
        GPIO-pin is (niet 5V/3.3V/GND).
        """
        output = OutputDevice(pin)  # Setting pin als output

        try:
            print(f"[TEST] GPIO{pin} aan {_ON_SECONDS}s elke {_CYCLE_SECONDS}s... (Ctrl+C om te stoppen)")
            while True:
                output.on()                                    # Pin aan (1 = on)
                time.sleep(_ON_SECONDS)
                output.off()                                    # Pin uit (0 = off)
                time.sleep(_CYCLE_SECONDS - _ON_SECONDS)
        except KeyboardInterrupt:
            print("\n[TEST] Gestopt door gebruiker.")
        finally:
            output.close()
            print("[TEST] GPIO-pin vrijgegeven.")  # Cleans up used ports
