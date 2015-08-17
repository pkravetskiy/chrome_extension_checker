#!/usr/bin/env python3

"""
This tool checks for the installed chromium extensions
"""

import os
import json
import argparse
import platform
import sys


def locale_lookup(path, default_locale, key):
    """
    Lookup a specific string in the locale file

    :param path: Path to the extension
    :param default_locale: Name of the default locale
    :param key: The key to look up
    :return:
    """
    key = key.replace("__MSG_", "")
    key = key[0:-2]

    locale_file = os.path.join(path, "_locales", default_locale, "messages.json")
    with open(locale_file) as fh:
        ldata = json.load(fh)
        if key in ldata:
            return ldata[key]["message"]
        key = key.lower()
        if key in ldata:
            return ldata[key]["message"]

    return "ERROR: " + key


def i18n(path, data):
    """
    Fix I18N stuff in manifest file

    :param path: path to extension data
    :param data: data so far (will be parsed for stuff to I18N)
    :return:
    """
    translate_me = ["default_title", "description", "name", "short_name"]
    for i in translate_me:
        if i in data and data[i].startswith("__MSG_"):
            data[i] = locale_lookup(path, data["default_locale"], data[i])


def extract_data(path):
    """
    Extract data from the manifest file
    :param path:
    :return:
    """
    manifest_name = os.path.join(path, "manifest.json")
    with open(manifest_name) as fh:
        data = json.load(fh)
        i18n(path, data)
        return data


def logtofile(txt="\n"):
    with open("logext.txt", "a") as f:
        f.write(txt)
    f.close()


def load_json(filename):
    if filename is None:
        return None
    with open(filename) as fh:
        return json.load(fh)


def check_ext_list(path, must_file=None, can_file=None):
    """
    Get data for installed extensions
    :param path: Path of the config to iterate through
    :param must_file: json file containing the must have extensions
    :param can_file: json file containing the allowed extensions
    :return: True if everything was allright
    """
    if not os.path.isdir(path):
        sys.exit("%s does not exist" % path)
    must = load_json(must_file)
    can = load_json(can_file)

    not_in_can = []
    res = True
    if args.all_profiles:
        profiles = get_profiles()
    else:
        profiles = get_profiles(True)

    path_bak = path

    for profile in profiles:
        path = os.path.join(path_bak, profile, "Extensions")
        if not os.path.isdir(path):
            continue
        print(profile.center(60, "="))
        logtofile("\n" + profile.center(60, "="))
        for ext in os.listdir(path):
            if ext == "Temp":
                continue
            print(ext)
            logtofile("\nExtension ID:  " + ext)
            ext_path = os.path.join(path, ext)
            for ver in os.listdir(ext_path):
                ver_path = os.path.join(ext_path, ver)
                data = extract_data(ver_path)
                print("\t Name: %s" % data.get("name"))
                logtofile("\nName: %s" % data.get("name"))
                logtofile("     Version: %s   " % data.get("version"))
                print("\t Version: %s" % data.get("version"))
                print("\t Description: %s" % data.get("description"))
                logtofile("Description: %s" % data.get("description"))
                if can is not None:
                    if data["name"] not in can:
                        print("  ERROR: this extension is not allowed or might be unwanted! ")
                        logtofile("      ERROR: this extension is not allowed or might be unwanted!")
                        not_in_can.append(data)
                        res = False
                if must is not None:
                    if data.get("name") in must:
                        must.remove(data.get("name"))
                print("\n")
                logtofile()
        if must is not None and len(must) > 0:
            print("There are missing extensions:")
            print(", ".join(must))
            logtofile("ERROR!   There are missing extensions:  ")
            logtofile("> ".join(must))
            res = False
    return res


def get_profiles(only_current=False):
    profiles = []
    try:
        old_dir = os.getcwd()
        os.chdir(args.config_path)
        if only_current:
            profiles = [load_json("Local State")["profile"].get("last_used", "Default")]
        else:
            profiles = [profile for profile in load_json("Local State")["profile"]["info_cache"]]
    except:
        print("No profiles found")
        return profiles
    finally:
        os.chdir(old_dir)
    if profiles:
        print("Profiles to check: %s" % ", ".join(profiles))
        logtofile("Profiles to check: %s" % ", ".join(profiles))
    return profiles


if __name__ == "__main__":
    if os.path.isfile("logext.txt"):
        os.remove("logext.txt")
    parser = argparse.ArgumentParser(description="Checks the extensions installed in Chrome/Chromium/Avira Browser")
    if "windows" in platform.system().lower():
        parser.add_argument("--config_path", help="The browser config path",
                            default=os.path.join(os.path.expanduser("~"),
                                                 "AppData", "local", "Avira-Browser", "User Data"))
    elif "darwin" in platform.system().lower():
        parser.add_argument("--config_path", help="The browser config path",
                            default=os.path.join(os.path.expanduser("~"),
                                                 "Library", "Application Support", "Avira-Browser"))
    else:
        parser.add_argument("--config_path", help="The browser config path",
                            default=os.path.join(os.path.expanduser("~"),
                                                 ".config", "avira-browser"))
    parser.add_argument("--must_extensions", help="json file with extensions that must be installed",
                        default="must.json")
    parser.add_argument("--can_extensions", help="json file with extensions that can be installed",
                        default="can.json")
    parser.add_argument("--all_profiles", "--all", help="Shows extensions info for all profiles", action="store_true")

    args = parser.parse_args()

    if not check_ext_list(args.config_path, args.must_extensions, args.can_extensions):
        exit(1)
    exit(0)
