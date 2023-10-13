#!/usr/bin/python -B

import os
import re


def c(text, color=0):
    return f"\033[1;3{color}m{text}\033[0;m"


def install(d):
    """
    Process files and directories within the specified input directory d. Looks for patterns
    like {{variable_name}} within files and replace them with the corresponding values from
    environment variables. If the environment variables are not set and provide error messages.
    Write the processed filesto their corresponding target locations.

    Args:
        d (str): Path to the directory to process.

    Returns:
        None
    """

    for f in os.scandir(d):
        fshort = f.path.replace("/volume/", "/")
        if f.is_dir():
            if not os.path.exists(fshort):
                print("Creating destination folder " + c(fshort, 4))
                os.mkdir(fshort)
            install(f)
        if f.is_file():
            print("Copying " + c(fshort, 5))
            data = open(f).read()
            replace = set(re.findall(r"\{\{(\w+)\}\}", data))
            for k in replace:
                try:
                    if "_escaped" in k:
                        rep = os.environ[k.replace("_escaped", "")].replace(".", "\.")
                    else:
                        rep = os.environ[k]
                except Exception:
                    print("  + " + c("ERROR", 1) + ": Env variable " + k + " not set!")
                    continue
                print("  + Replacing " + c("{{" + k + "}}", 2) + " with " + c(rep, 3))
                data = re.sub(r"\{\{" + k + "\}\}", rep, data)

            open("/" + fshort, "w").write(data)


install("/volume/home")
install("/volume/etc")
