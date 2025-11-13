# Copy Helper Setup Guide

> **IMPORTANT:** For proper installation and operation of Copy Helper, please allow all permissions when prompted.

>**If the app fails to launch after you edit a `.json` file, please use a [JSON validator](https://jsonlint.com) to verify that your syntax is correct.**

## Step 0 — Preparations

### Install Git
1.  Open **Terminal** on your Mac (Use Command+Space to open search, then type **Terminal** and press Enter).
2.  In the Terminal window, type `git` and press Enter.
3.  A pop-up window will appear. Press **Install** to install the **Xcode Command Line Tools**.

### Install Python
1.  Download the installer from [this link](https://www.python.org/ftp/python/3.13.8/python-3.13.8-macos11.pkg).
2.  Wait for the file to download.
3.  Open the downloaded `.pkg` file.
4.  Follow the on-screen prompts in the installer to complete the installation.

## Step 1 — Download Mac Shortcut

1.  Go to [this iCloud link](https://www.icloud.com/shortcuts/3ba70bd180364c1dbef0e56fa10e0853).
2.  Wait for the shortcut to load and press the **Add Shortcut** button.
3.  You will be asked to specify an installation folder for Copy Helper. If you are okay with the default, just press **Add Shortcut**.

---

## Step 2 — First Launch

1. Launch the shortcut by pressing the play button (`▶`) in the top right corner.

1.  "Run Shell Script" action should turn green.
2.  Wait for 1-2 minutes as the script runs.
3.  A Terminal window will open, and you should see the following message:
    ```
    WARNING:root:Fill secrets file!
    ```
4.  Go to the folder you chose during installation (the default is `/Documents/py-projects/`).
5.  Navigate to the `Copy-Helper/copy_maker/` subfolder.
6.  Open the `secrets.json` file with a text editor.

### Setting up the Monday Token
1.  Go to the [Monday developers page](https://epcnetwork.monday.com/apps/manage/tokens).
2.  Copy your **API Token**.
3.  In the `secrets.json` file, paste the token between the quotes for the `MONDAY_TOKEN` field, like this:
    ```json
    "MONDAY_TOKEN": "your-api-token-goes-here"
    ```
    
4.  Save the file.

### Setting up the OAuth Client
1.  Ask your mentor or unit manager for the `OAUTH_CLIENT` credentials.
2.  Copy and paste the entire JSON object into the `OAUTH_CLIENT` field. It should look similar to this:
    ```json
    "OAUTH_CLIENT": {
      "installed": {
          "client_id": {
          ...
      } 
    }
    ```
3.  Save the file.

---

## Step 3 — Continuing Installation

1.  Launch the script again. You can do this by:
    * Pressing the **Up Arrow** key (`↑`) in your Terminal and pressing Enter (to re-run the last command).
    * Running the shortcut again from the **Shortcuts** app.
2.  Your browser will open a Google sign-in page. Log in with your **epcnetwork email**. (You may be required to log in twice).
3.  When you see a message like "The authentication flow has completed. You may close this window." you can return to your Terminal.
4.  You should now see a new message in the Terminal:
    ```
    Fill general settings!
    ```
5.  Go back to your installation folder (e.g., `/Documents/py-projects/`).
6.  Open the `Copy-Helper/GeneralSettings.json` file with a text editor.
7.  Fill in the settings with the appropriate values.

> **Note on File Paths:** To get the full path to a folder, **right-click** it, select **Get Info**, and copy the path from the **Where:** field. This path is for the *parent* directory. You must add the folder's name and a trailing slash (`/`) to the end.
>
> **Example:** If your **Images** folder is on your Desktop, 'Get Info' will show `/Users/your.name/Desktop`. The correct path to enter in the settings file would be `/Users/your.name/Desktop/Images/`.


| Field | Description |
| :--- | :--- |
| **ResultsDirectory** | The full path to the folder where you want to save your completed copies. |
| **ResultsDirectoryType** | **Domain-Date**: Organizes results by domain first, then date.<br><pre>ResultsDirectory/<br>├── MyDomain.com/<br>│   ├── 13.11/<br>│   └── 14.11/<br>└── MyOtherDomain.com/<br>    └── 13.11/</code></pre>**Date-Domain**: Organizes results by date first, then domain.<br><pre>ResultsDirectory/<br>├── 13.11/<br>│   ├── MyDomain.com.txt<br>│   └── MyOtherDomain.com.txt<br>└── 14.11/<br>    └── MyDomain.com.txt</code></pre> |
| **ImagesDirectory** | The full path to the folder where you want to store images from copies. |
| **SaveImages** | `true` or `false`. Set to `true` if you want to automatically save images from copies. |


8.  Save the changes after filling in all fields.

---

## Step 4 — Final Launch
1.  Launch the script one more time (see Step 3, point 1 for methods).
2.  If everything is set up correctly, you should see:
    ```
    Welcome to copy-helper
    Available options: ...
    ```
3.  For instructions on how to add domains, please ask your mentor or unit manager.

**Pro tip for mentors:** To share a domain you can **Archive** (zip) a domain folder, send it to your junior, and have them unarchive it. They just need to place this unzipped folder into the `Domains` folder (located inside the Copy Helper installation directory).
