## Custom Uploader
A replacement for the bulky Gradle stuff in FRC. Lightweight, fast, and as point-and-shoot-ey as possible. C++ only.  
It might work on MacOS but probably not on Windows, because Unix directories are used. Good job, Windows.  
The idea is for it to be as simple as possible so people can edit it.

The goal is to stop using WPILib and anything provided by WPI or FRC.  
Custom Uploader will use WPILib until Firestorm Robotics Library is powerful enough to supplement it.  
We're going to support vendor libraries, but the goal is eventually to get rid of *those* too. It would be positively swaous to be a no-libraries team.
They aren't open source but a bit of clever digging in the maven repository (over HTTP) yields a few zip archives containing headers, shared objects, and you'll never believe this - source code!

Usage:
```bash
python uploader.py generate # Generate config.json. Starts a "wizard" to generate config.
python uploader.py addVendorDep <url> # Add a WPILib-style vendor dependency
python uploader.py build # Build the program
python uploader.py upload # Upload the program (calls build)
```

To use this script you need the ARM toolchain installed! This is simple enough. Download the latest arm toolchain for 32-bit Linux embedded systems from ARM Software, extract it, change the name to "arm-toolchain-gnueabihf", and put it in `/etc`. I do intend to polish this off a bit, but for now this is the only way to do it.  
If you prefer to use your own directory for the toolchain (perfectly valid), just change the toolchainInstallDir option in project.json. Just make sure that all the machines you build on have the toolchain in the same location! Adding a command-line option to uploader.py that sets the override toolchain dir is on the list.

If you're trying to hack it together to work on Windows, you'll have to change it anyways.

## Figuring out the process
If you're interested in the nitty-gritty bits of the process of roborio building and uploading and vendor libraries, here are my notes from writing this.

* The RoboRIO is, apparently, a generic ARM Linux embedded system with an SSH server.
* As it turns out, all the fancy Gradle is just there to cross-compile to ARM and copy files over SSH!