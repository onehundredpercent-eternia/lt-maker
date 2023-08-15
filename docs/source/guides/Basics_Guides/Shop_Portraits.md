# Shop Portraits

This guide will very swiftly illustrate how to update the three special shop portraits in LT maker: armory, vendor, and arena.

These portraits are not stored in the same way as standard unit portraits. Instead, to update these portraits, you must use the `resources/custom_sprites` directory in your project. If a `custom_sprites` directory does not already exist for your project, create one (make sure it's named exactly `custom_sprites`).

![File Explorer](/source/images/Guides/Shop_Portraits/Custom_Sprites.png)

Then, place the portrait you wish to use in this directory and name it one of the following file names to replace its respective default portrait:

* `arena_portrait.png`
* `armory_portrait.png`
* `vendor_portrait.png`

![Place Image Like So](/source/images/Guides/Shop_Portraits/Anna_Takeover.png)

Now when you set up a shop of that type in a shop event, you should see your replaced portrait.

![Hi Anna](/source/images/Guides/Shop_Portraits/Anna_Takeover_2.png)
