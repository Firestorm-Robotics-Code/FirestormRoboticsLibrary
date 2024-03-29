from requests import get
import os


try:
    print("Note: it is a known bug that builds may sometimes fail the first time downloading FRL. Never fear, just run it again! This is a problem with Gradle and the WpiLIB toolchain.")
    r = get("https://firestorm-robotics-code.github.io/FirestormRoboticsLibrary/exports", timeout=1)
    FRLPath = "src/main/include/FRL/"
    if not os.path.isdir("src/main/include"): ## This probably isn't a gradlerio project, so don't bother with their stupid gradle directory stuff
        FRLPath = "FRL/"
    try:
        os.mkdir(FRLPath)
    except:
        pass
    if r.status_code == 200:
        for x in r.text.split("\n"):
            if len(x) == 0:
                continue
            if x[0] == "D":
                try:
                    os.mkdir(FRLPath + x[1:])
                except:
                    pass
            if x[0] == "F":
                f = get("https://firestorm-robotics-code.github.io/FirestormRoboticsLibrary/" + x[1:])
                if f.status_code == 200:
                    open(FRLPath + x[1:], "w+").write(f.text)
                else:
                    print("Couldn't download", x[1:] + "!", "This is probably because somebody wrote a malformed dependency line. Please submit a bug report.\nNote: This is not a breaking issue; if your code (or another file you're using) doesn't depend on", x[1:], "you're fine.")
except:
    print("No internet connection, so the FRL files were not downloaded. This is not a problem if they've already been downloaded.")
    print("You may have compilation problems if you haven't already run this with an internet connection. That's nothing to worry about; just connect to the internet and build again to download the files.")
