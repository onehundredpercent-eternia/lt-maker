Update
========
<small>`Last Updated 2023-05-22`</small>
## Exe

The **exe** version of the engine isn't updated, it has to be reinstalled. Do the same process as the [installation](/source/Engine/Installation/EXE_Installation), selecting the [latest build](https://gitlab.com/rainlash/lt-maker/-/releases).

After that, select the project you were working on and everything will behave as usual. There shouldn't be a reason to keep the old versions but you may if you want to.

## Git/Python

For the **git** version, use **Git Bash** on the engine folder and then type the command `git pull`. Any file that doesn't match the source will be replaced with the latest counterpart.

<div class="note">
If the GIT console path has (master), in cyan, after the folder location, it means you got the right path. It should look like the following.<br/>
<div style="background-color:#000000;padding: 4px;font-family:'Lucida Console';font-size: 9px;">
<t style="color:#00FF00;">Eirika@Grados</t> <t style="color:#FF00FF;">MINGW64</t> <t style="color:#FFFF00;">~/Desktop/lt-maker</t> <t style="color:#00FFFF;">(master)</t>
</div>
</div>

<details><summary><strong>[Error] 'git pull' doesn't work</strong></summary><p>
If you changed a file that has also been changed in the repository, the `git pull` won't work. You will have to do the following to update it properly.

```
git stash
git pull
git stash pop
```

Your changes will be saved on `git stash` and restored on `git stash pop`.

Alternatively, you can use `git restore .` to revert all changes made locally.
</p></details><br/>
