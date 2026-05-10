from mutagen import File as MutagenFile
import os
import pygame
import time


class AudioController:
    def __init__(self):
        self.is_playing = False
        self.is_paused = False
        self.start_time = 0
        self.pause_time = 0
        self.duration = 0

    def init(self):
        """
        Init pygame mixer
        """

        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.set_num_channels(8)

    def load(self, file_path: str):
        """
        Load track into pygame music as stream (partial loading)
        """

        pygame.mixer.music.load(file_path)

    def unload(self):
        """
        Unload track from pygame music
        """

        pygame.mixer.music.unload()

    def shutdown(self):
        """
        Free mem and shutdown mixer
        """

        if not pygame.mixer.get_init():
            return

        try:
            pygame.mixer.music.stop()
        except pygame.error as e:
            print("Audio Controller | Error", e)

        pygame.mixer.quit()

    def play(self):
        pygame.mixer.music.play()
        self.start_time = self._now()
        self.is_playing = True
        self.is_paused = False

    def pause(self):
        pygame.mixer.music.pause()
        self.is_paused = True
        self.pause_time = self._now()

    def resume(self):
        pygame.mixer.music.unpause()
        self.is_paused = False
        self.start_time += self._now() - self.pause_time

    def stop(self):
        """
        Stop pygame music and reset audio control states back to default
        """
        
        pygame.mixer.music.stop()
        self.reset()

    def reset(self):
        """
        Reset audio control states back to default
        """
        
        self.is_playing = False
        self.is_paused = False
        self.start_time = 0
        self.pause_time = 0

    def get_position(self):
        """
        Get audio position
        """

        if not self.is_playing:
            return 0

        now = self._now()
        return (self.pause_time - self.start_time) if self.is_paused else (now - self.start_time)

    def _now(self):
        return int(time.monotonic() * 1000)
    
    def get_metadata(self, file_path: str):
        """
        Get metadata from audio file.
        Return a dict: {title:str, duration:int}
        """

        # Read metadata
        track = MutagenFile(file_path)  

        # Extract audio duration through mutagen file object
        duration = getattr(getattr(track, "info", None), "length", 0)

        if not duration:
            try:
                # Use Sound as fallback mechanic to acquire audio duration
                duration = pygame.mixer.Sound(file_path).get_length()
            except Exception:
                duration = 0

        title = None
        if track and track.tags:
            # Get track title through mutagen file object
            title = track.tags.get("title", [None])[0]
        else:
            title = os.path.basename(file_path)

        return {
            "duration": int(duration * 1000),
            "title": title
        }