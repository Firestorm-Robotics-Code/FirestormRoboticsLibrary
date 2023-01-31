## Dependency-aware custom upload script for FRC
## The goal: replace WPILib and all their hacky Gradle stuff with a very simple, transparent program

import json
import sys
import os
import paramiko

from requests import get



from urllib.request import urlopen ## THANKS, https://gist.github.com/hantoine/c4fc70b32c2d163f604a8dc2a050d5f6
from io import BytesIO
from zipfile import ZipFile
def download_and_unzip(url, extract_to='.'):
    http_response = urlopen(url)
    zipfile = ZipFile(BytesIO(http_response.read()))
    zipfile.extractall(path=extract_to)


def treeFindFiles(tree, filetype): ## Recursively walk the filesystem tree to find files with a certain extension
    ret = []
    for x in os.listdir(tree):
        if os.path.isdir(os.path.join(tree, x)):
            ret += treeFindFiles(os.path.join(tree, x), filetype)
        elif ("." + filetype) in x: ## Some have really stupid extensions like .so.23.0.0. This is my hacki solution.
        ## remember this is really kind of a hacked together temporary script designed as a POC.
            ret.append(os.path.join(tree, x))
    return ret

def treeFindDirsWith(tree, filetype): ## Use treeFindFiles to return paths containing this filetype
    ## may or may not use
    f = treeFindFiles(tree, filetype)
    ret = []
    for x in f:
        z = os.path.dirname(x)
        if not z in ret:
            ret.append(z)
    return ret


print("FRL Custom Uploader by Tyler Clarke")

def help():
    print("Usage: python uploader.py [generate,addVendor,build,deploy]")


def requireNumber(prompt):
    while True:
        r = input(prompt + ": ")
        if r.isnumeric():
            return int(r)
        print("Please enter a valid number")


def newProject():
    print("Generating new project now")
    config = {}
    config["teamNumber"] = requireNumber("Team number")
    config["toolchainInstallDir"] = "/etc/arm-toolchain-gnueabihf"
    config["compilerArgs"] = ""
    config["linkerArgs"] = ""
    config["inputs"] = []
    v = input("Input files (BASH wildcards acceptable for full directories; separate by spaces): ")
    for x in v.split(" "):
        if x == "":
            continue
        config["inputs"].append(x)
    file = open("project.json", "w+")
    file.write(json.dumps(config, indent=7))
    print("project.json generated. Edit it at will.")


def vendordep(jsonURL):
    print("Downloading", jsonURL)
    file = json.loads(get(jsonURL).text)
    if not os.path.isdir("vendor"):
        os.mkdir("vendor")
    for dep in file["cppDependencies"]: ## C++ only, suxx0rz
        urlBase = file["mavenUrls"][0] ## If it becomes necessary, do [thing] with the the separate urls. Until then we gonna just use the one.
        urlBase = os.path.join(urlBase, dep["groupId"].replace(".", "/"), dep["artifactId"], dep["version"], dep["artifactId"] + "-" + dep["version"])
        libUrl = urlBase + "-linuxarm32.zip"
        incUrl = urlBase + "-" + dep["headerClassifier"] + ".zip"
        if not os.path.isdir("vendor/" + dep["libName"]):
            os.mkdir("vendor/" + dep["libName"])
            os.mkdir("vendor/" + dep["libName"] + "/lib")
            os.mkdir("vendor/" + dep["libName"] + "/include")
        print("Gettin' shared objects from", libUrl)
        libFolder = "vendor/" + dep["libName"] + "/lib"
        incFolder = "vendor/" + dep["libName"] + "/include"
        download_and_unzip(libUrl, libFolder)
        print("And we gettin' them thar headers from", incUrl)
        download_and_unzip(incUrl, incFolder)


f = open("project.json")
cnf = json.loads(f.read())
f.close()

def getIP():
    global cnf
    # return a list later, for now keepin' it simple
    return "10." + str(cnf["teamNumber"])[:2] + "." + str(cnf["teamNumber"])[2:] + ".2"

def getRoboLibs():
    try:
        get("https://google.com", timeout=1)
        os.system("git clone https://github.com/wpilibsuite/ni-libraries")
        os.system("rm -rf vendor/ni")
        os.rename("ni-libraries/src/", "vendor/ni/")
        os.system("rm -rf ni-libraries")
    except:
        print("\u001b[41mWe don't appear to be online! You need to build online once to download libraries, but it's safe to stay offline the subsequent times.\u001b[0m")

def build():
    global cnf
    if not os.path.isdir("vendor/ni"):
        print("\nYou don't have roborio libraries downloaded in this project. Downloading them now. If you're not on wifi, this won't work! You can re-download them at any time with the downloadRoborioLibraries option.")
        print("Note: this requires Git!\n")
        getRoboLibs()
    ## Generate objects from vendor C
    gpp = os.path.join(cnf["toolchainInstallDir"], "bin/arm-none-linux-gnueabihf-g++")
    gcc = os.path.join(cnf["toolchainInstallDir"], "bin/arm-none-linux-gnueabihf-gcc")

    os.system(gcc + " vendor/ni/shims/embcan/main.c -shared -fPIC -o libnirio_emb_can.so.21")
    os.system(gcc + " vendor/ni/shims/fpgalv/main.c -shared -fPIC -o libNiFpgaLv.so.13")

    commandLine = gpp + " -L. "
    commandLine += "-L" + os.path.join(cnf["toolchainInstallDir"], "arm-none-linux-gnueabihf/lib")
    commandLine += " "
    commandLine += "-L" + os.path.join(cnf["toolchainInstallDir"], "arm-none-linux-gnueabihf/libc/lib")
    commandLine += " -l:libnirio_emb_can.so.21 -l:libNiFpgaLv.so.13 "
    for path in cnf["inputs"]:
        commandLine += path
        commandLine += " "
    libs = treeFindFiles("vendor", "so")
    for x in libs:
        commandLine += "-l:" + x + " "
    for x in os.listdir("vendor"):
        commandLine += "-Ivendor/" + x + "/include "

    commandLine += " -o output "
    
    commandLine += cnf["compilerArgs"]
    print("Using compiler command", commandLine)
    if os.system(commandLine) != 0:
        print("Compile failed!")
        sys.exit(1)
    print("The compilatin' were successful and faster than Gradle, you bet yer butt.")

if len(sys.argv) == 1:
    print("Error insufficient arguments")
    help()
elif sys.argv[1] == "downloadRoborioLibraries":
    getRoboLibs()
elif sys.argv[1] == "generate":
    newProject()
elif sys.argv[1] == "build":
    build()
elif sys.argv[1] == "upload":
    build()
    ssh = paramiko.SSHClient() ## THANKS, STACKOVERFLOW
    ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
    ssh.connect(getIP(), username="admin", password="")
    sftp = ssh.open_sftp()
    sftp.put("output", "/home/admin/output")
    sftp.close()
    ssh.exec_command("chmod +x /home/admin/output")
    ssh.close()
    print("The uploadatin' were successful")
    print("And, bet yer butt, prob'ly faster than gradle")
elif sys.argv[1] == "addVendordep":
    vendordep(sys.argv[2])
else:
    print("Unrecognized option", sys.argv[1])