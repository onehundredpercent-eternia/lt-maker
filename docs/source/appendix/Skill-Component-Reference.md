# Attribute Components

| Component | Description |
| ------ | ------ |
| **Hidden** |  The skill/status will not appear anywhere in the unit's info menu. |
| **Class Skill** |  The skill/status will appear in the unit's 'personal data' page in their info menu, rather than on the 'weapon and support level' page. |
| **Stack** |  The skill/status can be applied multiple times. Useful when creating skills such as "+1 Strength every time an enemy is defeated". |
| **Feat** |  The skill/status can be selected as a _Feat_.  |
| **Negative** |  Skill/status is considered _Detrimental_. This status cannot be applied to a unit with any skill using the "ImmuneStatus" skill component. This status can be cleared by an item using the "Restore" item component. |
| **Global** |  All units will be affected by this skill/status. |
| **Negate** |  Negates all effective damage. |
| **Negate Tags** |  Negates effective damage against the specified tags. For example, to recreate Iote's shield, we would select the "Flying" tag. |

# Base Components

| Component | Description |
| ------ | ------ |
| **Unselectable** |  Unit cannot be selected by the player. A use case would be for a berserked ally. |
| **Cannot Use Items** |  The unit cannot use nor equip any items. |
| **Cannot Use Magic Items** |  The unit cannot use nor equip any items that have the "Magic" item component. Also prevents using items with the "Magic At Range" component from greater than range 1. |
| **Additional Accessories** |  Trades item slots for accessory slots. |
| **Ignore Alliances** |  The affected unit can attack any team. Useful for stuff like Thracia Green units that could attack the player. |
| **Change AI** |  Changes the unit's AI to the one specified. Can accept any AI setting, including those made with the AI editor. |
| **Change Buy Price** |  Multiplies shop prices by the value given for the affected unit. For a Silver Card, one would use a value of .50 (i.e., 50% of the normal price). |
| **Exp Multiplier** |  Multiplies the amount of EXP the affected unit receives by the specified value. For Paragon, one would enter a value of 2.00 (i.e., 200% of the normal amount). |
| **Enemy Exp Multiplier** |  Alters the amount of EXP this unit gives. For Void Curse, one would give this a value of 0.00 and assign it to enemies. These enemies now give no EXP when fought. |
| **Wexp Multiplier** |  Multiplies the amount of WEXP the affected unit receives by the specified value. |
| **Can Use Weapon Type** |  Allows usage of the specified weapon type. Do note that the unit will still need a WEXP value above 0 for this to work. This component exists to allow a class to wield a weapon they normally could not use. For example, if Franz had 1 Axe WEXP and did not have this component, he would still not be able to use an Iron Axe. Once this component is applied, he will be able to use the Iron Axe.
| **Enemy Wexp Multiplier** |  Alters the amount of WEXP that units besides the affected unit receives, by the specified value. |
| **Locktouch** |  Gives the affected unit the ability to unlock. `can_unlock` will return True for this unit, allowing them to interact with regions that use `can_unlock` as a condition. Refer to the eventing tutorials for more details. |
| **Sight Range Bonus** |  Unit can illuminate additional spaces when Fog of War is active. |
| **Decreasing Sight Range Bonus** |  Unit can illuminate additional spaces when Fog of War is active. This bonus lowers by 1 every turn. |
| **Ignore Fatigue** |  The affected unit will not accumulate Fatigue. |

# Movement Components

| Component | Description |
| ------ | ------ |
| **Canto** |  Unit can move again after certain actions, excluding actions such as attacking or healing. |
| **Canto Plus** | Unit can move again after any action, including attacks. |
| **Canto Sharp** | Unit can move and attack in either order. Prevents units from moving, attacking, and then using canto. |
| **Movement Type** | Unit will have a non-default movement type. Commonly used for flying or pirates. |
| **Pass** | Unit can move through enemies. |
| **Ignore Terrain** | Unit will not be affected by terrain in any way. |
| **Ignore Rescue Penalty** | Unit will ignore the rescue penalty. |
| **Grounded** | Unit cannot be forcibly moved such as through shove or reposition. |
| **No Attack After Move** | Unit can either move or attack, but not both. |

# Combat Components

| Component | Description |
| ------ | ------ |
| **Stat Change** | Gives integer increases to the specified stats. Used by tiles to give defense bonuses. |
| **Stat Multiplier** | Multiplies the specified stat by a given value. |
| **Growth Change** | Gives integer increases to the growth rates of specified stats. |
| **Equation Growth Change** | Increases the growth of all of a units stats by the specified equation. Must evaluate to an integer. |
| **Damage** | Unit deals X more damage on attacks, where X is the specified integer value. |
| **Eval Damage** | Unit deals X more damage on attacks, where X is the result of the given equation. The equation must evaluate to an integer. |
| **Resist** | Unit gains X more resist, where X is the specified integer value. Resist includes both defense and resistance since it modifies the DEFENSE and MAGIC_DEFENSE equations. |
| **Hit** | Unit gains X more hit, where X is the specified integer. |
| **Avoid** | Unit gains X more avoid, where X is the specified integer. |
| **Crit** | Unit gains X more critical chance, where X is the specified integer. |
| **Crit Avoid** | Unit gains X more critical avoid, where X is the specified integer. Critical avoid is subtracted from the opponent's critical chance. |
| **Attack Speed** | Unit gains X more attack speed, where X is the specified integer. Attack speed increases a unit's doubling capabilities when they initiate an attack. |
| **Defense Speed** | Unit gains X more defense speed, where X is the specified integer. Defense speed increases a unit's doubling capabilities when they are under attack. |
| **Damage Multiplier** | Multiplies damage dealt by the specified decimal number. |
| **Dynamic Damage Multiplier** | Multiplies damage dealt by the result of the given equation. Equation must evaluate to either an integer or floating point number. |
| **Resist Multiplier** | Multiplies damage taken by the specified decimal number. |
| **PCC** | Multiplies critical chance by the chosen stat on any strike after the first. |

# Advanced Combat Components

| Component | Description |
| ------ | ------ |
| **Miracle** | Unit cannot be reduced below 1 HP. Often used with the charges system or Proc Rate component. |