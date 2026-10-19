==================================

LEX TALIONIS "LT" README TEMPLATE

==================================

CHAPTERS
A) Playing Lex Talionis games (Windows, Linux, Itch.io)
B) Controls
C) Known Issues
D) Save Data
E) Advanced installations - Build from source (Linux), MacOS & Android

==================================

A) - PLAYING LEX TALIONIS GAMES (WINDOWS, LINUX, ITCH.IO)

==================================
WINDOWS

1) Extract the game folder from the .zip/archive file and store it in any folder you wish, !!AS LONG AS THAT FOLDER IS NOT BACKED UP BY ONEDRIVE OR OTHER CLOUD STORAGE!!.
2) Double-click "GAMENAME.exe" or "double_click_to_play.bat" to start the game. Both options do the same thing.

=================
LINUX - PROTON (No terminal required, recommended):

1) Extract the game folder from the .zip/archive file and store it in any folder you wish, !!AS LONG AS THAT FOLDER IS NOT BACKED UP BY CLOUD STORAGE!!.
2) Install the Steam client via your preferred package manager or from the Steam website.
3) In the lower left corner of your Steam library, click the "Add a Game" button, and select "Add a non-Steam game...".
4) Click "Browse...", navigate to the folder where you stored the game, and select "GAMENAME.exe". Then, click "Add selected programs" and the game now shows up in your Steam library (typically in the unsorted category at the bottom of your library list).

Normally, Steam will automatically recognize the .exe file and force the game to run with Proton. If it does not, follow these instructions:
5) Right-click on the game in your library list and select "Properties...". Navigate to the "Compatibility" tab and select "Force the use of a specific Steam Play compatibility tool". Proton 10.0-4 is known to be stable. Newer versions may offer performance benefits, but may also introduce unknown issues.

=================
LINUX - WINE

1) Extract the game folder from the .zip/archive file and store it in any folder you wish, !!AS LONG AS THAT FOLDER IS NOT BACKED UP BY CLOUD STORAGE!!.
2) Install your preferred version of Wine from the WineHQ website;
    https://www.winehq.org/
        It is recommended to install Wine manually, as the package distributed by many package managers are outdated. Version 11.0 is known to run LT games in a stable manner. Older versions are untested.
3) Run "winecfg" in your terminal to make sure Wine functions as intended. You do not need to make any changes, and can close the window that pops up.
4) Open "GAMENAME.exe" with Wine (right-click, open with > Wine Windows Program Loader).

NOTE: Wine 11.0 can cause stuttering if you manually resize/maximize the game window. This can be avoided by simply using the in-game screen size settings.

=================
ITCH.IO

LT-games running in a web browser should run natively on all systems. No additional setup is required, though do note the first boot may take 10-20 seconds, due to the browser installing Python.
==================================

B) - CONTROLS

==================================

Function   | Keyboard | Mouse | Xbox Controller | PS Controller
===============================================================
Select     | X        | Left  | A               | Cross
Back       | Z        | Right | B               | Circle
Info       | C        | Middle| X               | Square
AUX        | A        |       | Back            | Share
Move       | Arrows   | Hover | Left Stick      | Left Stick
Start      | S        |       | Start / Y       | Options / Triangle
Screenshot | ` / F12  |       |                 |
Speedup    | Tab      |       |                 |

=================
EXTRA FUNCTIONALITIES

- The AUX key is used to focus the cursor on your units when on the map and to toggle the Growth Rate display on the Unit Info Menu.
- Screenshots are saved as .bmp files if the ` key was pressed or .png files if F12 was pressed. Screenshots are saved within the game folder.
- To soft reset, press Select, Back, and Start at the same time.
- Keys can be rebound in the Options > Controls menu in-game. Controller button remapping is also supported in that same window.
- Mouse controls can be enabled/disabled in the settings menu.

==================================

C) - KNOWN ISSUES

==================================
- Windows Defender and other common anti-virus programs often block LT-Maker games on first boot. The given warning can be safely disregarded, though it may be necessary to add an exception for the specified .exe file in your antivirus software.

- The EXP gain SFX may sound weird on some computers. The most common source of this issue is a computer having a standalone sound card. To adjust this, follow these instructions:
1) Close the game.
2) Go into the "saves" folder and look for a file called "config.ini." Make a back-up of this file, in case something goes wrong.
3) Open "config.ini" with a text editor of choice. Change the value of "sound_buffer_size" to a SMALL, EVEN NUMBER.
4) Save your changes, close the "config.ini" file check if the issue is resolved by booting up the game again. If the issue persists, close the game and repeat step 3 until the sound is correct.

- The fullscreen option is not recommended for use. Maximizing the window instead is recommended.

==================================

D) - SAVE DATA

==================================
Developer(s) may update their game to fix bugs or add new content. If you wish to transfer your old save file(s) to the new version, follow these instructions:

1) Download the new version of the LT game and store it in any folder you wish, !!AS LONG AS THAT FOLDER IS NOT BACKED UP BY ONEDRIVE OR OTHER CLOUD STORAGE!!. In addition, !!DO NOT OVERRIDE FILES FROM THE OLD VERSION!!. Store the new version in a separate location.
2) Navigate to the "GAMENAME" folder of the OLD version and open the "saves" folder.
3) Move all the files within the "saves" folder of the OLD version into the "saves" folder of the NEW version.
4) After booting up the game, restart the chapter of your save file to ensure the changes are implemented.

==================================

E) ADVANCED INSTALLATIONS - BUILD FROM SOURCE (LINUX), MACOS & ANDROID (!!NOTE TO DEVELOPERS: CHANGE THE "lt-maker" FOLDER NAME IN THIS DOCUMENT WITH YOUR OWN FOLDER NAME WHERE NECESSARY!!)

==================================
LINUX - BUILD FROM SOURCE

Building Lex Talionis games from source is possible under the following circumstances:
- The developer(s) have published a repository of the python version of their game with all engine hacking/changes included.
- The developer(s) have published the .exe engine, and have NOT modified the engine.

Building Lex Talionis games from source is NOT possible under the following circumstances:
- The developer(s) have only published the .exe engine, which includes engine hacking/changes.

If you are unsure, contact the developer(s) of the LT game you wish to play.

========

1) Set up a virtual environment for Python;
Consult the following documentation on setting up the correct Linux environment: https://lt-maker.readthedocs.io/en/latest/source/getting_started/Installation-Linux.html

If the developer has made their game available in a repository, you should clone that repository instead of the master branch that is listed in the installation guide.

2) If the developer(s) have only published the .exe engine, without engine hacks:
Grab the folder named "GAMETITLE.ltproj" from the .exe version and put it inside the "lt-maker" folder. Delete the "default.ltproj" folder. When next launching the engine, the desired game should boot up.*
    *If the desired game does not boot up, launch the editor instead of the engine with "python3 run_editor.py", click the "Open other" button and select the "GAMENAME.ltproj" folder. Once the editor opens, click the play icon in the icon bar and then select the "Test Full Game..." option. From there, you can play as normal.

=================
MacOS - WINE

!!WARNING - OUTDATED!!
!!THESE INSTRUCTIONS NEED TO BE UPDATED FOR PYTHON 3.12!!

Building Lex Talionis games from source is possible under the following circumstances:
- The developer(s) have published a repository of the python version of their game with all engine hacking/changes included.
- The developer(s) have published the .exe engine, and have NOT modified the engine.

Building Lex Talionis games from source is NOT possible under the following circumstances:
- The developer(s) have only published the .exe engine, which includes engine hacking/changes.

MacOS requires the native python versions of LT games for maximum stability. If this is not available, running LT games on MacOS is not recommended. If you are unsure, contact the developer(s) of the LT game you wish to play.

========

1.1) If the developer(s) have only published the .exe engine:
Clone the following repository to your preferred storage location;
    https://gitlab.com/rainlash/lt-maker.git
Grab the folder named "GAMETITLE.ltproj" from the .exe version and put it inside the "lt-maker" folder. Delete the "default.ltproj" folder.

1.2) If the developer(s) have published the python version of their game:
Download that repository and store it in your preferred storage location.

2) Install Homebrew
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
3) Install Wine
    brew install wine-stable
4) Install Miniconda
    brew install --cask miniconda
5) Initialize conda in your shell
    conda init "$(basename "${SHELL}")"

6) Execute the following commands before first boot;
    cd lt-maker
    conda create -n fe-i-lt python=3.11.7
    conda activate fe-i-lt
7) Setup Windows Python;
    curl -O https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe
    wine python-3.11.7-amd64.exe
8) Install the following requirements IN Wine Python;
    wine pip install -r
    python3pip
    pygame-ce==2.3.2
    pyinstaller==6.2.0
    typing-extensions==4.8.0
    PyQt5==5.15.10
    mypy==1.8.0
    mypy-extensions==1.0.0

9) Execute the following commands;
    cd lt-maker
    conda activate fe-i-lt
    wine python run_engine.py
EX) If the desired game does not boot up, change the command to "python3 run_editor.py", click the "Open other" button and select the "GAMENAME.ltproj" folder. Once the editor opens, click the play icon in the icon bar and then select the "Test Full Game..." option. From there, you can play as normal.

=================
ANDROID

Refer to the following links;
1) https://feuniverse.us/t/lex-talionis-on-android-its-time/28374
2) https://feuniverse.us/t/lex-talionis-on-android-its-time/28374/6

==================================
