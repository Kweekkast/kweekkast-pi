from kweekkast_core.image_capturing.triggers.abstract_trigger import AbstractTrigger


class ButtonTrigger(AbstractTrigger):
    def __init__(self):
        super().__init__()

    def trigger_loop(self) -> None:
        while True:
            input("Press enter to capture...")
            super().notify_all_observers()
