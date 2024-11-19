## Growth Mechanics

The **Lex Talionis** engine implements three different methods you can choose from for how your units will level up. You can find these options in the DifficultyEditor. 

You can choose different growth methods for the player characters and the enemy characters. For instance, you could use the classic *Random* growth method for player characters, and then select *Fixed* for enemy characters to make their stats in battle more consistent.

The remaining fourth option, *Player Choice*, is only available for non-player units and will force them to use whatever the player has chosen, if you leave that choice up to the player.

#!(Screenshot of DifficultyEditor)

The three methods are elucidated below:

*Random* - The classic Fire Emblem experience. A unit with a 40 growth rate in a stat, will have exactly a 40% chance to gain one point in that stat each time the unit levels up. A unit with a 100 or greater growth rate in a stat will automatically gain at least one point in that stat. For instance, a unit with a 260 growth rate, will automatically gain two points in that stat on level up, and then has a 60% chance to gain a third point in that stat. A unit with a negative growth rate in a stat will have a chance of losing a point in that stat. For instance, from a -20 growth rate it follows that the unit will have a 20% chance to lose a point in that stat on level up. If a stat is already at it's maximum value, it will not increase any further. In the **Lex Talionis** engine, there is no re-roll on an empty level up like there is in the GBA games.

*Fixed* - All units will always have their average stats. For instance, a unit with a 50 growth rate in a stat will gain a stat point exactly every two levels, so as to keep them as close as possible to their average value for that stat. Units start with 50 "growth points" in each stat. On each level up, they gain their growths in that stat. So, a unit with a 25 growth rate will go from 50 growth points to 75 growth points. If the new value would be greater than or equal to 100, the stat is increased by 1 and then their growth points in that stat are reduced by 100. So, for instance, a unit with a 60 growth rate in a stat will go from 50 growth points to 110 growth points, increase the stat by 1 and then reduce the growth points to 10. Their next level up will see their growth points go from 10 to 70.

# TODO (Confirm Dynamic growth rates work even if over 100)

*Dynamic* - Unit's growth rates will fluctuate to attempt to keep their stats close to the average value it ought to be. The variance value used for this is 10. Otherwise, this method works identically to the *Random* method. For instance, a unit with a 50 growth rate has a 50% chance to level up their stat. However, their growth rate will be modified for the next level up depending on whether or not they succeeded. On success, their growth rate is reduced by `(100 - true_growth_rate) / variance`. So, if they did succeed, their growth rate would go from 50 to 45. On failure, their growth rate is increased by `true_growth_rate / variance`. So, if they failed, their growth rate would go from 50 to 55. If they fail again on their next level up, their growth rate would go from 55 to 60, and so on. If they did succeed, their growth rate would go from 60 to 55. It does not completely reset in order to better nudge the unit toward their statistic average growth value.

## TODO (Does negative growth rates work with each method?)

All methods will result in the unit having the same average stat as they level up. For instance, a level 1 unit that starts with a Speed stat of 5 and a speed growth of 40, under all three methods, will end up with, on average, a Speed stat of 13 at level 20. The only difference is how wide the variance will be, with the *Fixed* method having no variance, and the *Dynamic* method have reduced variance compared to the *Random* method.

