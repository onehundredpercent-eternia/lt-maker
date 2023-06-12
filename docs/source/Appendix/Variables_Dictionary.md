# Variables Dictionary

_Last updated v0.1_

This appendix details every special game or level variable used by the **Lex Talionis** engine. Normally, game and level variables are utilized by the game designer in events, but a special set of names are reserved by the engine for specific uses.

## Game Variables

These variables are saved for the entirety of a given game.

|Variable Name|Type|Description
|-|-|-
|`_random_seed`|**int**|The random seed used by the engine for combat RNG and random level ups. Automatically set to a number between `0` and `1023` upon creation of a **New Game**.
|`_next_level_nid`|**Level (str)**|Internal to the engine. **Do not modify yourself**.
|`_goto_level`|**Level (str)**|Set to the **NID** of the level you want to go to next. If not set, the engine will just move to the following level like normal. Reset upon the start of the next level. If set to `_force_quit`, game will end (and return to title screen) instead of moving to the following level.
|`_go_to_overworld_nid`|**Overworld (str)**|Set to the **NID** of the overworld to go to next.
|`_current_turnwheel_uses`|**int**|The number of uses of the turnwheel left in this level. Defaults to `-1`, which represents infinite uses. Automatically reset to `_max_turnwheel_uses` upon winning the a level.
|`_max_turnwheel_uses`|**int**|The maximum number of uses of the turnwheel the player has access to. Defaults to `-1`, which represents infinite uses.
|`_convoy`|**bool**|Set to `True` to give the player access to the **convoy**.
|`_turnwheel`|**bool**|Set to `True` to give the player access to the **turnwheel**.
|`_supports`|**bool**|Set to `True` to give the player access to support conversations and have characters gain support points.
|`_fatigue`|**int**|Set to `0` to turn off fatigue.<br/>Set to `1` to have fatigue prevent unit from participating in a chapter.<br/>Set to `2` to have fatigue apply a **Fatigued** status when `fatigue >= max fatigue` and **Rested** when `fatigue < max fatigue`.<br/>Set to `3` to have the engine track fatigue but not do anything with it by default.
|`_prep_market`|**bool**|Set to `True` to give the player access to the **market** in the **prep screen**.
|`_prep_music`|**Music (str)**|Set the assigned music as the background music in the **prep screen**. You don't normally need to set this manually, since it is set by the `prep` event command.
|`_base_market`|**bool**|Set to `True` to give the player access to the **market** in the **base screen**.
|`_base_bg_name`|**Panorama (str)**|Load this panorama as the background in the base screen. You don't normally need to set this manually, since it is set by the `base` event command.
|`_base_music`|**Music (str)**|Set the assigned music as the background music in the **base screen**. You don't normally need to set this manually, since it is set by the `base` event command.
|`_phase_music_fade_ms`|**int**|Number of milliseconds the phase music will take to fade in. Defaults to `400` ms.
|`_last_choice`|**str**|Always holds the most recent choice made by the player from using the `choice` event command.

## Level Variables

These variables are cleared after winning or losing the current level

|Variable Name|Type|Description
|-|-|-
|`_win_game`|**bool**|Set to `True` to force the player to win the current level. Best practice is to just call the `win_game` event command, which does the same thing.
|`_lose_game`|**bool**|Set to `True` to force the player to lose the current level. Best practice is to just call the `lose_game` event command, which does the same things.
|`_level_end_triggered`|**bool**|Internal to the engine. **Do not modify yourself**.
|`_fog_of_war`|**bool**|Determines whether there is a base fog of war.
|`_fog_of_war_type`|**int**|Defaults to `0`.<br/>Set to `0` to display the map tiles in fog and hide the enemy positions.<br/>Set to `1` to display the map tiles in fog and hide the enemy positions (kept due compatibility). <br/>Set to `2` to hide both map and enemy positions (Thracia mode).
|`_fog_of_war_radius`|**int**|The distance that player units will be able to see in the fog. Defaults to `0`. Stacks with vision skill components.
|`_ai_fog_of_war_radius`|**int**|The distance that AI units will be able to see in the fog. If not set, defaults to `_fog_of_war_radius`
|`_other_fog_of_war_radius`|**int**|The distance that other team units will be able to see in the fog. If not set, defaults to `_ai_fog_of_war_radius`
|`_prep_pick`|**bool**|Set to `True` to enable **Pick Units** in the **prep screen**. You don't normally need to set this manually, since it is set by the `prep` event command.
|`_prep_slots`|**int**|Limits the number of units that can be brought to the level. Used only when you want to limit the number of player units to a number lower than the number of Formation tiles. Defaults to `None`.
