# Overworld

Given that you're on a FE Hack-like engine's repository, I dare to assume that you know what the overworld is. This page will briefly describe how to create an overworld in the editor and manage it in-game via events.

## Overworld Editor

The Overworld Editor can be accessed via the overworld tab, in much the same fashion as the Level Editor. ![image](../uploads/edad4c8f64a54802c54c9b855140e348/image.png)

This is the overworld which ships with the `default.ltproj` project. You can use this as a base for your overworld, or create a new one. I'll make a new one for the benefit of the reader, but it'll be uninspired. You'll see.

**Click the Create New Overworld button to do the thing, and double click to enter the editor.**![image](../uploads/966be6434c52335802fbd598d1127e8c/image.png)

On the left side, there are a lot of fields that are effectively self-explanatory. 

* **Overworld ID** is the internal ID of the overworld. Make it memorable, make it count.
* **World Name** is the name of the overworld that will be displayed in the game to the player.
* **Overworld Theme** allows you to select the theme that plays on the overworld first. Don't be too attached; this can be changed via events, of course.
* **Select Tilemap** allows you to select one of the existing tilemaps to be used as the overworld background. Given that you can import any image as a tilemap, this should allow you to use an arbitrary image of your choice - maybe even one you made yourself - as your world map.
* **Border Width** is a number that indicates how thick the border of the map is. This border determines how close a cursor can get to the edge of the map. It's fine leaving this at 0, but for those with fancy borders on their maps, it may be more immersive to make use of a more restrictive cursor area.

Let's make an uninspired overworld:

![image](../uploads/9050a8d141a2e012be237e046e0359d5/image.png)

You can see that I've set the border to 1. The player cannot interact with the red zone, so be sure that you don't place anything important in it.

Now, onto **nodes** and **roads**!

The instructions are at the bottom of the screen, but to reiterate, all controls involve the mouse or the delete key. **Left-Click** selects an object; **Right-Click** creates roads. **Double-L-Click** creates nodes.

We can make two nodes and a road between:

![image](../uploads/fbfa86a4a241d67db23bcbbabae0e7b2/image.png)The fields are as follows:

* **Node ID:** The ID of the node. You can't choose this one, but that's OK, because you can name the
* **Location Name**: You can name it whatever you like.
* **Level:** The level associated with this node. This is fairly important, as it indicates, in concert with the selected level, what set of events to use upon entering the node. Make sure to label your nodes with their proper levels!
* Finally, the clickable button at the bottom is the **Icon Selector**, where you can choose which icon to use to represent the node. You can see in the image above the use of the Forest Temple icon.

## Eventing the Overworld

This is one of those sections where a picture is worth a thousand words, and a gif with 60 frames by definition would be worth sixty thousand words. Incidentally, I'll be using the default overworld instead of the pile of garbage I created above, so please open `default.ltproj` for reference.

You can find this event in `default.ltproj`, level 1, `Outro`.

![image](../uploads/819842981dca08180d9e94733857eae9/image.png)

```
speak;Eirika;Thank you, Tana.
transition;Close
end_skip
#
# Let's have some fun in the overworld. Remove the background:
change_background
# This command is necessary to load the overworld tilemap
overworld_cinematic;Magvel (0)
# The next two commands are self-explanatory. You'll use these to manipulate overworld data.
reveal_overworld_node;Border Mulan (0);t
set_overworld_position;Eirika's Group (Eirika);Border Mulan (0)
#
# Here are examples of overworld animations and sounds.
# Notice that they are the same as the normal tilemap commands.
transition;open;1500
wait;1000
sound;RefreshDance
map_anim;AOE_Mend;Frelia Castle (2)
reveal_overworld_node;Frelia Castle (2)
wait;500
sound;Mend
reveal_overworld_road;Border Mulan (0);Frelia Castle (2)
#
# Because narration is more involved than dialogue, we need some different commands
# to animate the narration window in.
toggle_narration_mode;open;1000
wait;500
narrate;Narrator;Eirika and her companions have liberated the border castle.
overworld_move_unit;Eirika's Group (Eirika);Frelia Castle (2);FLAG(no_block)
narrate;Narrator;Alongside Princess Tana of Frelia, they ride to the Frelian Capital.
wait;500
transition;close
toggle_narration_mode;close
#
```

And you can see the results below:

![demo](../uploads/974f5ebe183c3f763efa10ad660d5350/demo.gif)

Not so painful, is it? There a variety of commands that are used in the overworld. All of them are documented in the `Show Commands` button in the event editor; feel free to check them out.