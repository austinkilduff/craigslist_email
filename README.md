# craigslist_email
Get email alerts for cars on Craigslist

You need:
* neomutt installed and set up
* `requests` and `bs4` installed from pip
* The cutting-edge database library [austinDB](https://github.com/austinkilduff/austinDB) (copy `austinDB.py` into this folder)
* To create `config.py`

`config.py` should look like this:

    craigslist_url = "https://..."
    email_address = "example@website.com"
    project_dir = "/home/me/craigslist_email"
    
I'm using this as a handy statusbar node with dwmblocks. But you could also use cron, systemd timers, or run it manually.
