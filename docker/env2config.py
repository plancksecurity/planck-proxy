#!/usr/local/bin/python -B

import os
import re
import shutil

def c(text, color=0):
    return f"\033[1;3{color}m{text}\033[0;m"

def install(d):
    """
    Process files and directories within the specified input directory d. Looks for patterns
    like {{variable_name}} within files and replace them with the corresponding values from
    environment variables. If the environment variables are not set either construct them or
    provide an error message. Write the processed files to their target locations.

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
                    if k == "relay_domains_nexthop_maps":
                        rd = os.environ["relay_domains"].split(" ")
                        nh = os.environ["nexthop"].split(" ")
                        if len(nh) == 1:
                            # print("We have one nexthop, inflating to a list of the size of relay_domains")
                            nh = list(nh * len(rd))
                        rep = ""
                        if len(rd) != len(nh):
                            print(c("ERROR", 1) + ": Size of relay_domains and nexthop doesn't match!")
                        else:
                            for i in range(len(rd)):
                                rep += "/.*@" + rd[i].replace(".", "\.") + "/ smtp:[" + nh[i] + "]\n"

                    elif k == "relay_domains_list":
                        rep = str(os.environ["relay_domains"].split(" ")).replace("'", "\"")

                    elif k == "tls_server_sni_maps":
                        rep = open("/tmp/tls_server_sni_maps", "r").read()

                    elif k == "smtp_tls_chain_files":
                        rep = open("/tmp/smtp_tls_chain_files", "r").read()

                    elif "servers_" in k:
                        port = k.split("_")[1]
                        print("Port: " + port)
                        print("Replicas: " + os.environ["replicas"])
                        replicas = int(os.environ["replicas"])
                        if replicas == 1:
                            rep = f"server hub_{port} hub:{port} send-proxy\n"
                        else:
                            rep = ""
                            for i in range(1, replicas + 1):
                                rep += f"server hub_{i}_{port} proxy-hub-{i}:{port} send-proxy\n\t"

                    elif "_escaped" in k:
                        rep = os.environ[k.replace("_escaped", "")].replace(".", "\.")

                    else:
                        rep = os.environ[k]
                except Exception as e:
                    print("  + " + c("ERROR", 1) + ": Env variable " + k + " not set! Error: " + str(e))
                    continue
                print("  + Replacing " + c("{{" + k + "}}", 2) + " with " + c(rep, 3))
                data = re.sub(r"\{\{" + k + "\}\}", rep, data)

            open(fshort, "w").write(data)
            shutil.copymode(f, fshort)
            shutil.copystat(f, fshort)

install("/volume/haproxy")
install("/volume/home")
install("/volume/etc")
