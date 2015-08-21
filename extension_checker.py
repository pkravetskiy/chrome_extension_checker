#!/usr/bin/env python3

"""
This tool checks for the installed chromium extensions
"""

import os
import json
import argparse
import platform
import sys
import logging


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


def initializeMultiLogging():
    logging.basicConfig(filename="logext.log",
                        filemode="w",
                        level=logging.INFO,
                        format="%(message)s")
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter("%(message)s")
    console.setFormatter(formatter)
    logging.getLogger("").addHandler(console)


def load_json(filename):
    if filename and os.path.isfile(filename):
        with open(filename) as fh:
            return json.load(fh)
    return None


def list_of_permissions(data):
    lst = []
    if data and "permissions" in data:
        lst = [permission for permission in data["permissions"]]
    return lst


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
        not_in_can = []
        logging.info("\n" + profile.center(60, "="))
        for ext in os.listdir(path):
            if ext == "Temp":
                continue
            logging.info(ext)
            ext_path = os.path.join(path, ext)
            for ver in os.listdir(ext_path):
                ver_path = os.path.join(ext_path, ver)
                data = extract_data(ver_path)
                logging.info("\tName: %s\n\tVersion: %s\n\tDescription: %s\n\tPermissions: %s" %
                             (data.get("name"), data.get("version"), data.get("description"),
                              ", ".join(list_of_permissions(data))))
                if can is not None:
                    if data["name"] not in can:
                        logging.warning("WARNING: this extension is not allowed or might be unwanted!")
                        not_in_can.append(data["name"])
                        res = False
                if must is not None:
                    if data.get("name") in must:
                        must.remove(data.get("name"))
                logging.info("\n")
        if not_in_can:
            logging.warning("There are not allowed or unwanted extensions:\n%s\n" % ", ".join(not_in_can))
        if must is not None and len(must) > 0:
            logging.info("There are missing extensions:")
            logging.info(", ".join(must))
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
        logging.info("No profiles found")
        return profiles
    finally:
        os.chdir(old_dir)
    if profiles:
        logging.info("Profiles to check: %s" % ", ".join(profiles))
    return profiles


def Main(args):
    initializeMultiLogging()

    if check_ext_list(args.config_path, args.must_extensions, args.can_extensions):
        return 1
    return 0


if __name__ == "__main__":
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

    sys.exit(Main(args))


permissins_info = {
    "activeTab": "Access to the currently active tab when the user invokes the extension - for example by clicking its browser action. Access to the tab lasts until the tab is navigated or closed.",
    "alarms": "Scheduling code to run periodically or at a specified time in the future.",
    "audioModem": "",
    "background": "Make Browser start up early and and shut down late, so that apps and extensions can have a longer life. Also makes Browser continue running (even after its last window is closed) until the user explicitly quits Browser.",
    "bookmarks": "Access to the chrome bookmarks, so that it can create, organize, and manipulate bookmarks.",
    "browsingData": "Remove browsing data from a user's local profile.",
    "clipboardRead": "Access data you copy and paste.",
    "clipboardWrite": "Write to clipboard.",
    "contentSettings": "Manipulate settings that specify whether websites can use features such as cookies, JavaScript, plugins, geolocation, microphone, camera etc.",
    "contextMenus": "Add items to Browser's context menu",
    "cookies": "Query and modify cookies, and to be notified when they change.",
    "copresence": "Communicate with other nearby devices using Google's copresence service.",
    "debugger": "Read and modify all your data on all websites you visit. Access to instrument network interaction, debug JavaScript, mutate the DOM and CSS, etc.",
    "declarativeContent": "Take actions depending on the content of a page, without requiring permission to read the page's content.",
    "declarativeWebRequest": "Intercept, block, or modify requests in-flight.",
    "desktopCapture": "Capture content of screen, individual windows or tabs.",
    "dns": "",
    "downloads": "Programmatically initiate, monitor, manipulate, and search for downloads.",
    "experimental": "Different experimental features",
    "fontSettings": "Manage Chrome's font settings.",
    "gcm": "Enable apps and extensions to send and receive messages through the Google Cloud Messaging Service.",
    "geolocation": "Access to geographical location information associated with the hosting device. Detect your physical location.",
    "history": "Interact with the browser's record of visited pages.",
    "identity": "Get OAuth2 access tokens.",
    "idle": "Detect when the machine's idle state changes.",
    "idltest": "",
    "location": "Retrieve the geographic location of the host machine.",
    "management": "Manage the list of extensions/apps and themes that are installed or running.",
    "mdns": "Discover devices on your local network",
    "nativeMessaging": "Exchange messages with registered native applications.",
    "notificationProvider": "",
    "notifications": "Create rich notifications using templates and show these notifications to users in the system tray.",
    "pageCapture": "Save a tab as MHTML. Read and modify all your data on all websites you visit.",
    "platformKeys": "Access to client certificates managed by the platform. If the user or policy grants the permission, an extension can use such a certficate in its custom authentication protocol. E.g. this allows usage of platform managed certificates in third party VPNs.",
    "plugin": "Read and modify all your data on your computer and the websites you visit.",
    "power": "Override the system's power management features.",
    "printerProvider": "Exposes events used by print manager to query printers controlled by extensions, to query their capabilities and to submit print jobs to these printers.",
    "privacy": "Control usage of the features in Chrome that can affect a user's privacy. Manipulate privacy-related settings.",
    "processes": "Interact with the browser's processes.",
    "proxy": "Manage Chrome's proxy settings. Read and modify all your data on all websites you visit.",
    "sessions": "Query and restore tabs and windows from a browsing session.",
    "signedInDevices": "Get a list of devices signed into chrome with the same account as the current profile.",
    "storage": "Store, retrieve, and track changes to user data.",
    "system.cpu": "Query information about CPU.",
    "system.display": "Query information about display.",
    "system.memory": "Query information about physical memory.",
    "system.storage": "Query storage device information and be notified when a removable storage device is attached and detached.",
    "tabCapture": "Interact with tab media streams",
    "tabs": "Get additional privileged tab information. Access your browsing activity.",
    "topSites": "Access to the top sites that are displayed on the new tab page. Read and modify your browsing history.",
    "tts": "Play synthesized text-to-speech (TTS).",
    "ttsEngine": "Implement a text-to-speech(TTS) engine using an extension. Access all text spoken using synthesized speech.",
    "unlimitedStorage": "Provide an unlimited quota for storing HTML5 client-side data, such as databases and local storage files. Without this permission, the extension or app is limited to 5 MB of local storage.",
    "webNavigation": "Receive notifications about the status of navigation requests in-flight. Access your browsing activity.",
    "webRequest": "Observe and analyze traffic and to intercept, block, or modify requests in-flight.",
    "webRequestBlocking": "Observe and analyze traffic and to intercept, block, or modify requests in-flight."
}
