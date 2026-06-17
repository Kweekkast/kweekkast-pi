import time

from kweekkast_common.communicator_distributor import CommunicatorDistributor


class Main:
    def run(self) -> None:
        distributor = CommunicatorDistributor()
        distributor.StartAllListeners()

        print("[Main] Systeem gestart. Wachten op apparaten... (Ctrl+C om te stoppen)")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("[Main] Gestopt.")


def main() -> None:
    Main().run()


if __name__ == "__main__":
    main()
