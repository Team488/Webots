# Webots

## Pre-reqs

### Install Webots

This repo currently works with the 2022a version of webots (even though the latest is newer than that). You can install that version of Webots from:
https://github.com/cyberbotics/webots/releases/tag/R2022a

### Install Python and requirements

1. The easiest way to install python and windows and get nice contained virtual environments is to use anaconda. Follow the installation instructions on this page: https://docs.anaconda.com/anaconda/install/windows/

2. Once installation is complete, start an anaconda powershell prompt (hit your windows key and type "anaconda powershell" and it should come up as an option).
3. Create a new environment for webots by running these commands (say yes when prompted):

```bash
conda create --name webots python=3.9
conda activate webots
```

4. In your anaconda prompt, navigate (using `cd`) to the folder where this repo is cloned on your machine.
5. In the root Webots repo directory run:

```bash
pip install -r requirements.txt
```

6. Now we just need the path to this python environment so we can give it to the Webots program, to find that out, run:

```powershell
Get-Command python | %{$_.Source}
```

7. Copy what the above command returns; for me it was `C:\Users\Alex\miniconda3\envs\webots\python.exe`
8. Open the Webots program and in the top menu go Tools -> Preferences and paste the above path into the "Python command" box in the middle

## How to use

1.  Open `RobotServer\worlds\frc_rectangle.wbt` in Webots.
2.  This will start a supervisor on port 10001 that you can request robots be spawned from.

### Using curl

Spawning a robot:

```bash
curl -XPOST localhost:10001/robot -d '{"template": "HttpRobotTemplate"}' --header "Content-Type: application/json"
```

which will return the port the new robot was spawned on (10002 for the first robot by default).

Then to send motor values to the robot:

```bash
curl -XPUT localhost:10002/motors -d '{"motors": [{"id": "Motor1", "val": 1.0}]}' --header "Content-Type: application/json"
```

Which will return the current sensor values for the robot.

## Troubleshooting
##### Ubuntu 22.04

Since we are on Webots 2022a, the normal installation for Webots would result in the following error when trying to download textures on 22.04:
```
WARNING: RectangleArena (PROTO) > Parquetry (PROTO) > ImageTexture: Cannot download
```
- The reason is that the 2022a's version of libssl is incompatible w/ Ubuntu 22.04 as 2022a is written for 20.04. 

Run through the following fixes:

1. Install a newer version of libssl that is compatible with 2022a.
```bash
wget https://cyberbotics.com/files/repository/dependencies/linux64/release/libssl_1.1.tar.xz -O /tmp/libssl_1.1.tar.xz
```

2. Unzip the tar.xz file
```bash
tar xvf /tmp/libssl_1.1.tar.xz -C /tmp`
```

3. Move openssl-1.1/ into webots directory. (NOTE:  `/usr/local/` is the default installation directory but change path to where webots is installed)
```bash
mv /tmp/openssl-1.1/* /usr/local/webots/lib/webots``` 
```
