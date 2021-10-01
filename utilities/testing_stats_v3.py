import math
from dataclasses import dataclass

@dataclass
class Character():
    name: str = ''
    LVL: int = 1
    HP: int = 1
    POW: int = 0
    SKL: int = 0
    SPD: int = 0
    BRV: int = 0
    DEF: int = 0

@dataclass
class Growths():
    name: str = ''
    HP: float = 0
    POW: float = 0
    SKL: float = 0
    SPD: float = 0
    BRV: float = 0
    DEF: float = 0

def sum_stats(char):
    return char.HP // 2 + char.POW + char.SKL + char.SPD + char.BRV + char.DEF

def create_char(char: Character, growths: Growths, lvl: int):
    new_char = Character(char.name, lvl)
    increase = lvl - char.LVL
    offset = 50 if increase > 0 else -50
    new_char.HP = char.HP + int((growths.HP * increase + offset) / 100)
    new_char.POW = char.POW + int((growths.POW * increase + offset) / 100)
    new_char.SKL = char.SKL + int((growths.SKL * increase + offset) / 100)
    new_char.SPD = char.SPD + int((growths.SPD * increase + offset) / 100)
    new_char.BRV = char.BRV + int((growths.BRV * increase + offset) / 100)
    new_char.DEF = char.DEF + int((growths.DEF * increase + offset) / 100)
    return new_char

# Sword users
myrm = Character('Myrmidon', 1, 18, 7, 12, 7, 8, 1)
myrm_growths = Growths('Myrmidon', 95, 45, 60, 60, 55, 20)
errant = Character('Errant', 1, 22, 8, 9, 5, 6, 4)
errant_growths = Growths('Errant', 105, 50, 40, 50, 50, 35)
skirm = Character('Skirmisher', 1, 17, 6, 8, 7, 9, 2)
skirm_growths = Growths('Skirmisher', 85, 40, 50, 65, 65, 25)
sword_users = [(myrm, myrm_growths), (errant, errant_growths), (skirm, skirm_growths)]
# Lance users
armor = Character('Armor', 1, 20, 11, 9, 1, 1, 6)
armor_growths = Growths('Armor', 100, 60, 55, 20, 20, 55)
cavalier = Character('Cavalier', 1, 20, 10, 7, 4, 4, 3)
cav_growths = Growths('Cavalier', 100, 50, 45, 45, 40, 30)
peg_knight = Character('Peg Knight', 1, 16, 8, 8, 8, 10, 1)
peg_growths = Growths('Peg Knight', 80, 35, 50, 70, 70, 20)
wyvern_knight = Character('Wyvern', 1, 22, 11, 6, 3, 4, 5)
wyvern_growths = Growths('Wyvern', 105, 65, 45, 35, 40, 45)
lance_users = [(armor, armor_growths), (cavalier, cav_growths), (peg_knight, peg_growths), (wyvern_knight, wyvern_growths)]
# Greatsword users
fighter = Character('Fighter', 1, 24, 13, 3, 3, 5, 2)
fighter_growths = Growths('Fighter', 110, 70, 35, 35, 45, 35)
raider = Character('Raider', 1, 24, 12, 4, 5, 6, 1)
raider_growths = Growths('Raider', 120, 60, 40, 50, 50, 25)
merc = Character('Mercenary', 1, 22, 8, 12, 4, 6, 3)
merc_growths = Growths('Mercenary', 105, 55, 60, 45, 50, 30)
knight = Character('Knight', 1, 24, 10, 4, 2, 5, 5)
knight_growths = Growths('Knight', 110, 65, 45, 25, 45, 45)
greatsword_users = [(fighter, fighter_growths), (raider, raider_growths), (merc, merc_growths), (knight, knight_growths)]
# Dagger users
thief = Character('Thief', 1, 16, 5, 10, 8, 2, 1)
thief_growths = Growths('Thief', 65, 35, 45, 65, 30, 15)
dagger_users = [(thief, thief_growths)]
# Bow users
archer = Character('Archer', 1, 18, 9, 10, 3, 3, 3)
archer_growths = Growths('Archer', 95, 55, 55, 40, 35, 30)
hunter = Character('Hunter', 1, 17, 8, 10, 7, 6, 1)
hunter_growths = Growths('Hunter', 85, 40, 50, 60, 50, 20)
nomad = Character('Nomad', 1, 20, 8, 8, 5, 6, 1)
nomad_growths = Growths('Nomad', 100, 45, 45, 50, 50, 20)
bow_users = [(archer, archer_growths), (hunter, hunter_growths), (nomad, nomad_growths)]

soldier = Character('Soldier', 1, 18, 7, 8, 3, 2, 3)
soldier_growths = Growths('Soldier', 95, 50, 55, 35, 30, 30)
brigand = Character('Brigand', 1, 24, 13, 2, 3, 2, 1)
brigand_growths = Growths('Brigand', 120, 70, 30, 35, 30, 20)
weak_users = [(soldier, soldier_growths), (brigand, brigand_growths)]

mage = Character('Mage', 5, 18, 12, 10, 9, 6, 1)
mage_growths = Growths('Mage', 105, 55, 40, 55, 40, 20)

all_stats = sword_users + lance_users + greatsword_users + dagger_users + bow_users + weak_users
level_20s = []
level_30s = []
for stat, growth in all_stats:
    c1 = create_char(stat, growth, 1)
    c5 = create_char(stat, growth, 5)
    c10 = create_char(stat, growth, 10)
    c20 = create_char(stat, growth, 20)
    c30 = create_char(stat, growth, 30)
    print(c1)
    print(c5)
    print(c10)
    print(c20)
    level_20s.append(c20)
    print(c30)
    level_30s.append(c30)
    print(sum_stats(c30))

myrm20 = create_char(myrm, myrm_growths, 20)
fighter20 = create_char(fighter, fighter_growths, 20)
armor20 = create_char(armor, armor_growths, 20)

def arena(u1, u2):
    mt1 = max(1, u1.POW - u2.DEF)
    mt2 = max(1, u2.POW - u1.DEF)
    hit1 = u1.SKL*4 + 70 - u2.SPD*4
    hit2 = u2.SKL*4 + 70 - u1.SPD*4
    as1 = u1.BRV > u2.SPD
    as2 = u2.BRV > u1.SPD

    print("%s: HP: %d Mt: %d Hit: %d Double: %s" % (u1.name, u1.HP, mt1, hit1, as1))
    print("%s: HP: %d Mt: %d Hit: %d Double: %s" % (u2.name, u2.HP, mt2, hit2, as2))
    min_num_rounds_to_ko1 = math.ceil(u2.HP / mt1 / (1.5 if as1 else 1)) if hit1 > 0 else 99
    min_num_rounds_to_ko2 = math.ceil(u1.HP / mt2 / (1.5 if as2 else 1)) if hit2 > 0 else 99
    avg_num_rounds_to_ko1 = math.ceil(u2.HP / (mt1 * min(1, hit1/100)) / (1.5 if as1 else 1)) if hit1 > 0 else 99
    avg_num_rounds_to_ko2 = math.ceil(u1.HP / (mt2 * min(1, hit2/100)) / (1.5 if as2 else 1)) if hit2 > 0 else 99
    print("%s KOs %s in %d rounds (min: %d rounds)" % (u1.name, u2.name, avg_num_rounds_to_ko1, min_num_rounds_to_ko1))
    print("%s KOs %s in %d rounds (min: %d rounds)" % (u2.name, u1.name, avg_num_rounds_to_ko2, min_num_rounds_to_ko2))

"""
arena(myrm, fighter)
print("")
arena(myrm, knight)
print("")
arena(fighter, knight)
print("")
arena(myrm20, fighter20)
print("")
arena(myrm20, knight20)
print("")
arena(fighter20, knight20)
print("")
arena(swordmaster30, warrior30)
print("")
arena(swordmaster30, general30)
print("")
arena(warrior30, general30)
print("")
arena(fighter, merc)
print("")
arena(myrm, myrm)
print("")
arena(fighter, fighter)
print("")
arena(knight, knight)
"""
import itertools
comb = [myrm, armor, fighter, merc, cavalier, peg_knight, wyvern_knight, thief, soldier, brigand, errant]
comb = [myrm, armor, fighter]
# comb = []
for pair in itertools.combinations(comb, 2):
    print("")
    arena(*pair)

comb = [myrm20, armor20, fighter20]
# comb = []
for pair in itertools.combinations(comb, 2):
    print("")
    arena(*pair)

pow_sort = sorted(level_30s, key=lambda x: x.BRV)
for char in pow_sort:
    print(char)
