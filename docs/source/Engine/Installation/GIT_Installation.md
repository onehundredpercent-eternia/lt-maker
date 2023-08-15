Git Installation
========
<small>`Last Updated 2023-05-22`</small>

<div class="note">
This guide will focus on the windows installation process. While the process should be the same, Mac and Linux users will have to adapt as it goes on their own.
</div>

## Index
* [Requirements](#requirements)
* [Installing Git](#installing-git)
  * [Testing Git](#testing-git)
* [Installing Python](#installing-python)
  * [Testing Python](#testing-python)
  * [Python Overview](#python-overview)
* [Installing Pip](#installing-pip)
* [Installing the Engine and other Packages](#installing-the-engine-and-other-packages)
* [What's next?](#what-s-next?)

---------------------

## Requirements
* Git
* Python 3.7.9
* Pip
* Pygame 1.9.6
* PyQt

<div class="note">
Make sure before installing any of these, that you have uninstalled any previous versions of these tools from your machine. Some of these tools newer versions can have compatibility or performance issues. Python in particular can become quite problematic when multiple versions are installed in the same machine.
</div>

## Installing Git
* [Windows](https://git-scm.com/download/win)
* [Mac](https://git-scm.com/download/mac)
* [Linux](https://git-scm.com/download/win)

Open the file and click **[Next >]** until you reach the following screen.

![GIT Options](/source/images/Engine/GIT_Installation/Installation_Git1.png)

This is a recommend setup for first time git users. The **Git Bash** options is extremely convenient and Git GUI is rather useless. There shouldn't be a need Git LFS for this project.

Make sure you change the text editor to your text editor of choice. *Sublime Text Editor* is a great free option that has coding support.

Choose the second option under **Adjusting your PATH Environment**, unless you are sure you never want to use git outside of **Git Bash** (if so, choose the first).

![GIT Bash Radio](/source/images/Engine/GIT_Installation/Installation_Git2.png)

Everything else can use the default settings.

### Testing Git

Git should be successfully installed installed by this point. Right-click in the File Explorer and open <u>Git Bash</u> by left-clicking **Git Bash**

![GIT Bash Explorer](/source/images/Engine/GIT_Installation/Installation_Git3.png)

A command line terminal will pop up. Type `git --version` to make sure git responds.

## Installing Python

<div class="note">
The standard version used by most contributors is Python 3.7. Newer versions may present compatibility issues with certain libraries and frameworks used in the project.
</div>

Go to the bottom of the page below and click on the appropriated option for your operating system. We recommend **Windows x86-64 executable installer** for 64-bit windows users.

[https://www.python.org/downloads/release/python-379/](https://www.python.org/downloads/release/python-379/)

Run the installer file once the download is complete.

In case you're a new to Python, select the option to add Python 3.7 to PATH. It makes so many of the errors that new users may run into just disappear. Just click **Install Now** and follow through, the default installation options are enough.

![Python Wizard](/source/images/Engine/GIT_Installation/Installation_Python1.png)

### Testing Python

Now you should have Python installed on your machine. Right-click anywhere on your machine and click on Git Bash, then type one of the following to confirm that Python works.

* `python --version`
* `py --version`
* `python3 --version`

Whichever one works of these three will be the command you will use in the future to call Python. We will be using `python` for the rest of the tutorial so replace it with yours whenever it is used.

### Python Overview

At this point, you can type just `python` on the Git Bash command line to get the interactive Python REPL, which allows you to enter in python commands interactively. Typing in "2 + 2" results in the following.

![Python Command Line](/source/images/Engine/GIT_Installation/Installation_Python2.png)

To run a Python script, just type `python` followed by a space and the script's file name. The script must be in the same folder that you used the <u>Git Bash</u>, otherwise you must give Python the relative path to it.

This means that in order to run python scripts in the lt-maker directory, you should run python from within the lt-maker directory.

<details><summary><strong>[Error] Python Command Not Found</strong></summary><p>

If the python command is not found, and you didn't add Python to your PATH during installation, you will need to update your PATH so that Windows knows where Python lives.

Newer versions of Python like the one you installed generally live in `C:\Users\{Your User}\AppData\Local\Programs\Python\Python37`

If you navigate to there, you should see a python.exe executable. This is the actual python you would be running if the PATH was set up correctly.

In Windows 10, type "env" in the search bar and click the **Edit the System Environment Variables** option.

![Python Path 1](/source/images/Engine/GIT_Installation/Python_Path1.png)

A dialog box will pop up. Click **[Environment Variables...]**.

![Python Path 2](/source/images/Engine/GIT_Installation/Python_Path2.png)

Under **User Variables** (the top table), click on the **Path** row, then click **[Edit...]**.

![Python Path 3](/source/images/Engine/GIT_Installation/Python_Path3.png)

Click **New** on the right. Type the location of your Python executable, in this case: `C:\Users\{Your User}\AppData\Local\Programs\Python\Python37`, then hit Enter. Click **[New]** again and type in the path to the associated Scripts directory. `C:\Users\{Your User}\AppData\Local\Programs\Python\Python37\Scripts`.

![Python Path 4](/source/images/Engine/GIT_Installation/Python_Path4.png)

Now click **[OK]** and close all of the windows opened in this process. Next, go back to the [testing step](#testing-python).

-------
</p></details><br/>

## Installing Pip

Pip is the Python package manager. It means from here on out, we don't need to download stuff off random websites to get the rest of our tools. If you install Python with the defaults, pip should come as an extra.

You can check if it is available by typing one of the following in the <u>Git Bash</u> terminal.

* `pip --version`
* `python -m pip --version`

<div class="note">
In case any of the installations demmand administrator privileges to install for all users, you can install for just yourself with <b>pip install {package_name} --user</b>.
</div>

## Installing the Engine and other Packages

Select the location you want the engine to be in and use <u>Git Bash</u>, then type the following.

``` Text
git clone --depth=1 https://gitlab.com/rainlash/lt-maker.git
```

This command will create a new folder containing all the files from the repository. Git will register the folder as a clone which will make it both associated to the repository and a standalone folder at local level. None of the changes you make in it will affect the others, yet you will be able to use <u>Git</u> commands to update and restore files to match the latest version.

You can know if the current folder is associated to git by checking if it has a branch name in cyan.

<!---
Adding it later
![Fetching GIT Link]()
-->

Next, type one of the following at the terminal.

- `pip install -r requirements_editor.txt`
- `python -m pip install -r requirements_editor.txt`

<div class="note">
If you followed the steps in order, you should be at the right folder and be able to see the file <b>requirements_editor.txt</b> in it. If for any reason that isn't the case, use <u>Git Bash</u> in the folder that has that file and run the commands again.
</div>

<div class="danger">
Some users have reported that on Linux systems (specifically Ubuntu), PyQt5 installation does not work. In that case, try: <b>sudo apt-get install python3-pyqt5</b> instead.
</div>

The pygame version 1.9.6 seems to be the most stable version available for the engine. Newer versions have presented several outstanding bugs in the past and they may not have been fixed yet.

### Testing Engine

By now, everything should be done. Last step is to check if everything is working.

<u>Git Bash</u> any folder and type `python -m pygame.examples.aliens`.  This should run a space invaders like game.

Next, <u>Git Bash</u> the lt-maker directory and type `python run_engine.py`. This time the **default project** (that uses The Lion Throne start screen) should open and be playable.

![Title Screen](/source/images/Engine/GIT_Installation/Title_Screen.png)

At last, we can boot the engine by typing `python run_editor.py`. The editor should pop up and you should be able to begin making your own fangame.

![Boot Completed!](/source/images/Engine/Editor_Screen.png)

Be sure to either make a new project or save the default project as a new project before you start working on your game.

<div class="danger">
Don't save your project as <b>default</b> or <b>autosave</b>. These projects are already used in the editor.
</div>

Congratulations, <u>Lex Talionis</u> has been successfully installed!

## What's next?
Most of the features in the engine can be self taught by navigation. Along that, the default project has multiple examples on how to implement staples from the **Fire Emblem** series.

In case you need extra assistance, check the other wiki articles at the panel over the left. The best places to start are the [basics guides](/source/Guides/Basics_Guides/index) page. You can also join the official [Discord Server](https://discord.gg/dC6VWGh4sw) to learn with other users and get the latest news on updates.
