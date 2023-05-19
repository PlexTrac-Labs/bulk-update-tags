# bulk-update-tags
This scripts is meant to help make bulk tag operations across different objects tags can be added to. Most commonly you can tag clients, assets, reports, findings, or writeups in the WriteupsDB. This script allows you search across all these objects for a specific tags and replace it with a new value.

Tags also exist at the tenant level. The list of tenant tags is what poplates the dropdown whenever adding a tag to an object. This script will add any tag to the tenant level if it was added to an object. It will also remove tags from the tenant level after sucessfully replacing the tag with a new value on all objects.

# Requirements
- [Python 3+](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/installation/)
- [pipenv](https://pipenv.pypa.io/en/latest/install/)

# Installing
After installing Python, pip, and pipenv, run the following commands to setup the Python virtual environment.
```bash
git clone this_repo
cd path/to/cloned/repo
pipenv install
```

# Setup
After setting up the Python environment the script will run in, you will need to setup a few things to configure the script before running.

## Credentials
In the `config.yaml` file you should add the full URL to your instance of Plextrac.

The config also can store your username and password. Plextrac authentication lasts for 15 mins before requiring you to re-authenticate. The script is set up to do this automatically through the authentication handler. If these 3 values are set in the config, and MFA is not enabled for the user, the script will take those values and authenticate automatically, both initially and every 15 mins. If any value is not saved in the config, you will be prompted when the script is run and during re-authentication.

# Usage
After setting everything up you can run the script with the following command. You should run the command from the folder where you cloned the repo.
```bash
pipenv run python main.py
```
You can also add values to the `config.yaml` file to simplify providing the script with custom parameters needed to run.

## Required Information
The following values can either be added to the `config.yaml` file or entered when prompted for when the script is run.
- PlexTrac Top Level Domain e.g. https://yourapp.plextrac.com
- Username
- Password

## Script Execution Flow
Since the script has to load a lot of objects from the DB, ideally you input multiple tag replacements that the script will then update as it runs through the data once.
- Authenticates user to Plextrac instance with tags to be refactored
- Prompts use to start entering tags that need to be replaced. Continue entering all tags that need to be replaced individually.
- Once all tags to be replaced are entered, if will run through each tag entered and ask for the replacement for each tag
- After confirming reractions to be made, will create lists of all objects by making multiple API requests to the Plextrac instance
- After confirming the objects that were loaded, will go through lists and make API requests to update any object found to have tags that need to be refactored

The script will create a log file each time it is run. The script should only stop if it fails to load data at the beginning. As it runs, if an object couldn't be updated, it will log the exception and continue running. You can Ctrl+F and search for `exception` in the generateed log file to see any problems during runtime.
