Frequently Asked Questions
========
<small>`Last Updated 2023-05-22`</small>

## Engine

**What is LT-Maker?**
<br/>LT-Maker is a fully open-source engine and editor designed to make it easy to make Fire Emblem-like SRPG style games. Originally created by **rainlash**, it now receives contributions from the community, and also **mag**.

**What features does LT-Maker have?**
<br/>All the basic features you can find in the GBA games. Additionally, it has: Thracia's fog of war, AI affected by fog of war, pair up, Three Houses ammo system, leadership stars, bonus experience, base menu, fatigue, free roam, turnwheel, mana resource, individual unit turns, additional teams with customazible alliances, and more. All of those are native optional features.

**I don't see ... feature anywhere. Will it be added eventually?**
<br/>It depends on how popular it is, how much time it takes to implement and what other things are in the works. Some of the common requests can already be built through [eventing](Editors/Events_Editor/index), such as [Skill Swap](/source/Guides/Systems_and_Mechanics_Guides/Skill_Swap) and Avatar units.

**Is LT-Maker complicated to learn/use?**
No, it is a simple to use as most other builder engines, such as RPG maker. Of course, there is quite a room for some depth and it can be a bit demanding depending on what you want to make. Many users that experienced romhack said that LT-Maker is *extremely* easy in comparison.

**Do I need to learn Python to make a game?**
<br/>Neither the **exe** nor the **git** version require Python knowledge to be used, however it is recommended to learn at least the basics to use some key features. Simple games can be built without a single snippet of Python code

**How often is the engine updated?**
<br/>The **exe** version gets an update every month or two. The **git** version is updated constantly, it seldom goes for a full week without a new update.

**How can I know when an update is available?**
<br/>Best way is to join the [Discord Server](https://discord.gg/dC6VWGh4sw). You can find an automated channel there named `#engine-updates`, though it also informs when a new update is summited to verification, including some wiki files. If you don't want to bother with it, your only option is to check it by yourself based on your version - [exe](https://gitlab.com/rainlash/lt-maker/-/releases) or [git](https://gitlab.com/rainlash/lt-maker/activity).

**How do I report a bug?**
<br/>The only way to report a bug is through the `#bugs` channel at the [Discord Server](https://discord.gg/dC6VWGh4sw). Ideally, you should go through [troubleshooting](Troubleshooting) process first. It can prevent certain user errors to be mistaken as bugs, which is somewhat common, and also provide better information for bug reports.

**How large can my game/project file be?**
<br/>As large as it has to be. You can have as many assets, levels and unique objects as you want.

**Does it has mobile support?**
<br/>Not yet. It's in the works.

**How do I make a playable demo/build of my game?**
<br/>Follow this [guide](/source/Guides/Basics_Guides/Build_Engine).

**Does LT-Maker support .tmx map files?**
<br/>No. It uses **.png** for the graphical component of its maps. Terrain data is stored separately.

**What is the default project?**
<br/>It's a game demo made in LT-Maker containing the 6 first levels of **Fire Emblem: The Sacred Stones**. Whenever you make a new project, the engine will copy all of these files into it.

**I see that the stats on right side have bars underneath them, how do I enable that for the left side?**
<br/>Unfortunately, you'll have to change the engine code to do so. It is possible to rearrange the stats position and order through the [Stats Editor](Editors/index) however.

**What's an Unique ID/NID?**
<br/>**Unique ID** or **NID** is an unique value that each object has, just like an actual ID in the real world. The player won't have access to that value aside for when the **Display Name** is auto filled. Whenever you need to reference said object, use the **NID**, not the **Display Name**.

**I've seen some games/videos where the info screen is different/has more than 3 pages. How do I do that?**
<br/>Those were done by changing the engine code directly. It isn't possible to change it through editors.

----------

## Controls
**Are LT-Maker games mouse compatible?**
<br/>Yes. It's even possible to play LT-Maker games using only a standard mouse.

**What is the default control mapping?**

|Game Key|Keyboard Key|Mouse Input
|-|-|-|
|A/SELECT|X|Left Button
|B/BACK|Z|Right Button
|R/INFO|C|Middle Button
|L/AUX|A|`(Not assigned)`
|Directionals|Arrows|
|START|S|`(Not assigned)`

It is recommended to **NOT** assign the **Enter/Return** key as a game key/button.

**Can I rebind mouse buttons?**
<br/>Not directly. It should be possible by changing the engine code.

**How do I soft reset the game?**
<br/>Press the **SELECT**, **BACK** and **START** keys/buttons at the same time. By default, these are X+Z+S.

**How do I check my unit growth rates?**
<br/>Press the **AUX** key, *default A*, on the info screen. The HP growth will be displayed over the Aid stat.

**How do I enable the typing mode in the `text_entry` prompt?**
<br/>The toggle key for it is **Enter/Return**, and cannot be changed outside the engine code. While it is active, the typing mode will disable the default key mapping until it is turned off. Keep in mind that if the <u>Enter/Return</u> key is assigned as a game key, it will activate both functions at the same time, yielding unexpected and undesirable results.

----------

## Graphics

**What's the resolution used by LT-Maker games?**
<br/>It uses the GBA standard, fixed at 240x160. The game window can be upscaled for larger sprites but the resolution itself cannot be changed.

**Can I make my game non-pixel art 2D or 3D?**
<br/>No. The engine only works with 2D assets and they must follow the predefined sizes.

**Is there a color limitation for the engine?**
<br/>Aside team colors, no.

**Can I change the colors of each team?**
<br/>Yes.

**Is the engine using the assets from Fire Emblem: The Sacred Stones? Does it has all of it?**
<br/>Yes and no. It has a lot of its assets but not all of them. Some of the chapter 7+ sprites and animations are there but a few of the chapter 6- are missing.

**Where do I check the dimensions/get references for custom sprites?**
<br/>Check the default project files for reference at the path `lt-maker\default.ltproj\resources`.

**Why does every sprite has that weird green color as its background?**
<br/>That color is coded as the engine transparency for standard recolorable sprites.

**What is the exact color hex code for transparency?**
<br/>#80a080.

**I checked the animations folder to see the sprites but it's all black. Is something wrong?**
<br/>No. Those images are all in a dark shade of green that can't is really hard to see from afar. It is monochrome to make palette coloring easier.

**Can my characters have multiple portraits for conversations?**
<br/>Yes. Dialogs aren't limited to the unit portrait.

**My character went through some radical change in the story and I want to reflect that in their portrait for the rest of the game, can I do it?**
<br/>Check the command `change_portrait` in the [event editor](Editors/Events_Editor/index).

----------

## Audio

**Why does my music sounds different?**
<br/>LT is configured at 44100 Hz. Most likely, your music was sampled at 48000 Hz. You can use [Audacity](https://superuser.com/questions/420531/audacity-resampling) to resample your track to the appropriate frequency.

**Is it possible to remove certain tracks/songs from the Sound Room?**
<br/>Yes. Any audio file in the [sound editor](Editors/index) that starts with an underscore (`_`) will be ignored by the **Sound Room** menu. Really useful for ambience sounds and the prolonged Chapter Sound.

**Can I have voice acting in my game?**
<br/>Yes, but you will have to do it through [events](Editors/Events_Editor/index). It is easy to add lines for key moments in a scene or in combat, the same can't be said from having dedicated voice acting for every line of dialogue. There's no guide available for it yet, however.

----------

## Other

**How can I contact the dev team?**
<br/>Through the [Discord Server](https://discord.gg/dC6VWGh4sw).

**Should I join the Discord Server?**
<br/>Probably. The [Discord Server](https://discord.gg/dC6VWGh4sw) quite friendly and offers a bunch of handy things for any aspiring game developer. It has dedicated channels for bug reports, engine updates, tech support, improvement ideas, resources and assets, game releases and even community projects. You can also share your project and get sneak peaks of other games in the works. A great place to find other creators and get quality feedback.

**Is it possible to make an avatar unit?**
<br/>Yes, but you will have to do it through [events](Editors/Events_Editor/index). There's no guide available for it yet, however.

**Can I have my game featured in the wiki?**
<br/>Of course, but you'll have to add it yourself. Please check the [Projects](/source/Projects/Projects) page for more information.

**Why can't I find any information about ... in the wiki?**
<br/>The wiki is building itself slowly and steadily so the corresponding article may not exist yet. If that bothered you enough and learned about it, consider writing its article.

**I just clicked a reference link and it didn't do anything/lead me to a support page, why is that?**
<br/>Some links are added pre-emptively, even if the page or structure isn't fully set. You can check if the page has been created using the search function on the left panel. If it exists, please report the occurrence as if it were a bug.
