## About ##

This page is not yet finished.

## Installation ##

* Download and Install Python Plugin Loader. [Found here](http://dev.bukkit.org/server-mods/python-plugin-loader/).
* Download my plugin.
* Copy **chestlocker.py.dir/** and **chestlocker.cfg** to your plugins folder on your Minecraft server.
* Start your server!

## Configuration ##

The config file is named **chestlocker.cfg** located in the **plugins** folder.  Currently it is very simple. There is one option in there which is **maxlocks**. If you set this to -1 you give everyone unlimited locks. If you set it to 0 you no one gets a lock. And anything about zero set how many locks every gets.

## Usage ##

* /cl
	* Shows the help menu and the available commands.
* /cl lock
	* Locks the chest you are currently looking at.
* /cl unlock
	* Unlocks the chest you are looking at.
* /cl credit <user> <time>
	* Gives a credit to a user. A credit is good for one lock. For a credit that lasts forever set 0 as the time.
	You can also add a suffix after the number. m for minute, h for hour, d for day. If there is no suffix then it is
	assumed that the time is a day.
* /cl info
	* Shows some information about your chests and credits.