ORION_SPOTIFY_URL = "https://open.spotify.com/track/07q0QVgO56EorrSGHC48y3"


class ModeManager:
    def __init__(self):
        self.current_mode = "normal"

    def activate_orion_mode(self):
        self.current_mode = "orion"

    def deactivate_orion_mode(self):
        self.current_mode = "normal"

    def is_orion_mode(self):
        return self.current_mode == "orion"
