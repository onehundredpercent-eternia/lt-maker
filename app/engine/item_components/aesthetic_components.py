from app.engine.fonts import NORMAL_FONT_COLORS
from app.data.item_components import ItemComponent, ItemTags
from app.data.components import Type

class MapHitAddBlend(ItemComponent):
    nid = 'map_hit_add_blend'
    desc = "Changes the color that appears on the unit when hit -- Use to make brighter"
    tag = ItemTags.AESTHETIC

    expose = Type.Color3
    value = (255, 255, 255)

    def on_hit(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        playback.append(('unit_tint_add', target, self.value))

class MapHitSubBlend(ItemComponent):
    nid = 'map_hit_sub_blend'
    desc = "Changes the color that appears on the unit when hit -- Use to make darker"
    tag = ItemTags.AESTHETIC

    expose = Type.Color3
    value = (0, 0, 0)

    def on_hit(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        playback.append(('unit_tint_sub', target, self.value))

class MapHitSFX(ItemComponent):
    nid = 'map_hit_sfx'
    desc = "When the target is hit by this item the selected sound is played."
    tag = ItemTags.AESTHETIC

    expose = Type.Sound
    value = 'Attack Hit 1'

    def on_hit(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        playback.append(('hit_sound', self.value))

class MapCastSFX(ItemComponent):
    nid = 'map_cast_sfx'
    desc = "When item is used the selected sound is played."
    tag = ItemTags.AESTHETIC

    expose = Type.Sound
    value = 'Attack Hit 1'

    def on_hit(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        playback.append(('cast_sound', self.value))

    def on_miss(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        playback.append(('cast_sound', self.value))

class MapCastAnim(ItemComponent):
    nid = 'map_cast_anim'
    desc = "Adds a specific animation effect when the item is used. Relevant in map combat situations."
    tag = ItemTags.AESTHETIC

    expose = Type.MapAnimation

    def on_hit(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        playback.append(('cast_anim', self.value))

    def on_miss(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        playback.append(('cast_anim', self.value))

class BattleCastAnim(ItemComponent):
    nid = 'battle_cast_anim'
    desc = "Adds a specific animation effect when the item is used. This does not change the battle animation used, think instead of the spell's effect."
    tag = ItemTags.AESTHETIC

    expose = Type.EffectAnimation

    def effect_animation(self, unit, item):
        return self.value

class BattleAnimationMusic(ItemComponent):
    nid = 'battle_animation_music'
    desc = "Uses custom battle music"
    tag = ItemTags.AESTHETIC

    expose = Type.Music
    value = None

    def battle_music(self, unit, item, target, mode):
        return self.value

class NoMapCombatDisplay(ItemComponent):
    nid = 'no_map_hp_display'
    desc = "Item does not show full map hp display when used"
    tag = ItemTags.BASE

    def no_map_hp_display(self, unit, item):
        return True

class PreCombatEffect(ItemComponent):
    nid = 'pre_combat_effect'
    desc = "Item plays a combat effect right before combat."
    tag = ItemTags.AESTHETIC

    expose = Type.EffectAnimation

    def combat_effect(self, unit, item, target, mode):
        return self.value

class Warning(ItemComponent):
    nid = 'warning'
    desc = "A yellow exclamation mark appears above the wielder's head. Often used for killing weapons."
    tag = ItemTags.AESTHETIC

    def warning(self, unit, item, target) -> bool:
        return True

class EvalWarning(ItemComponent):
    nid = 'eval_warning'
    desc = "A red exclamation mark appears above the wielder’s head if the selected unit matches the evaluated string. Often used for effective weapons."
    tag = ItemTags.AESTHETIC

    expose = Type.String
    value = 'True'

    def warning(self, unit, item, target) -> bool:
        from app.engine import evaluate
        try:
            val = evaluate.evaluate(self.value, unit, target, item)
            return bool(val)
        except Exception as e:
            print("Could not evaluate %s (%s)" % (self.value, e))
            return False

class TextColor(ItemComponent):
    nid = 'text_color'
    desc = 'Special color for item text.'
    tag = ItemTags.AESTHETIC

    expose = (Type.MultipleChoice, NORMAL_FONT_COLORS)
    value = 'white'

    def text_color(self, unit, item):
        if self.value not in NORMAL_FONT_COLORS:
            return 'white'
        return self.value
