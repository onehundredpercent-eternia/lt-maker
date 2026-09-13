import os
import unittest
from unittest.mock import patch

import pygame

from app.engine import sound

BATTLE_SONG = 'Battle Song'
PLAIN_SONG = 'Plain Song'

class FakeClock:
    def __init__(self):
        self.time = 1000

    def get_time(self):
        return self.time

def silence() -> pygame.mixer.Sound:
    frequency, size, channels = pygame.mixer.get_init()
    return pygame.mixer.Sound(buffer=bytes(frequency * abs(size) // 8 * channels))

class FakeSong:
    """Stands in for a SongObject with silent tracks, so no project audio is needed"""
    def __init__(self, nid, has_battle):
        self.nid = nid
        self.song = silence()
        self.battle = silence() if has_battle else None
        self.intro = None
        self.channel = None

class SoundCrossfadeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except pygame.error as e:
                raise unittest.SkipTest("No audio mixer available: %s" % e)

    def setUp(self):
        self.clock = FakeClock()
        engine_patch = patch.object(sound, 'engine', self.clock)
        engine_patch.start()
        self.addCleanup(engine_patch.stop)
        music_patch = patch.dict(sound.MUSIC, {BATTLE_SONG: FakeSong(BATTLE_SONG, True),
                                               PLAIN_SONG: FakeSong(PLAIN_SONG, False)})
        music_patch.start()
        self.addCleanup(music_patch.stop)

        self.controller = sound.DefaultSoundController()
        self.controller.set_music_volume(1.0)

    def advance(self, ms):
        for _ in range(ms // 16):
            self.clock.time += 16
            self.controller.update([])

    def volume(self, channel: sound.Channel) -> float:
        return channel._channel.get_volume()

    def _reuse_battle_mode_pair(self, next_song) -> sound.ChannelPair:
        """Crossfades a pair to its battle track, then clears the music and plays
        next_song until that same pair is handed out again"""
        self.controller.fade_in(BATTLE_SONG)
        self.advance(1000)
        self.controller.battle_fade_in(BATTLE_SONG)
        self.advance(1000)
        battle_pair = self.controller.current_channel
        self.assertTrue(battle_pair.battle_mode)
        for _ in range(len(self.controller.channel_stack)):
            self.controller.clear()  # as leaving the sound room does
            self.controller.fade_in(next_song)
            self.advance(1000)
            if self.controller.current_channel is battle_pair:
                return battle_pair
        self.fail("The crossfaded channel pair was never reused")

    def test_aux_during_fade_in_leaves_battle_track_at_full_volume(self):
        '''
        Eon 3/22/26: pressing AUX right after SELECT in the sound room left the battle
        track stuck at whatever volume it had faded in to -- a few percent, which sounds
        like silence
        '''
        self.controller.fade_in(BATTLE_SONG)
        self.advance(16)
        self.controller.battle_fade_in(BATTLE_SONG)
        self.advance(1000)
        pair = self.controller.current_channel
        self.assertTrue(pair.battle_mode)
        self.assertAlmostEqual(self.volume(pair.battle), 1, places=2)
        self.assertAlmostEqual(self.volume(pair.channel), 0, places=2)

    def test_reused_channel_pair_plays_normal_track(self):
        '''
        Eon 3/22/26: a channel pair left in battle mode kept its crossfade when cleared,
        so the next song without a battle track to land on it played at volume 0
        '''
        pair = self._reuse_battle_mode_pair(PLAIN_SONG)
        self.assertFalse(pair.battle_mode)
        self.assertAlmostEqual(self.volume(pair.channel), 1, places=2)

    def test_battle_variant_song_on_reused_channel_pair_starts_on_normal_track(self):
        '''
        ...and a song with a battle track started on it, so AUX switched it to normal
        '''
        pair = self._reuse_battle_mode_pair(BATTLE_SONG)
        self.assertFalse(pair.battle_mode)
        self.assertAlmostEqual(self.volume(pair.channel), 1, places=2)
        self.assertAlmostEqual(self.volume(pair.battle), 0, places=2)

if __name__ == '__main__':
    unittest.main()
