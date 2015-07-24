Extension tool
==============

This tool tests for the presence of extensions in the browser. The extensions are looked up in the config directory (which is at a different place for the operating systems windows/mac/linux).

It can verify chrome/chromium and the Avira browser.

To see the options, use the -h command

Specific tests
--------------

It can test for the presence of a list of extensions. Their name is defined in must.json. If one is missing, there will be an error

It can also detect unexpected new extensions (like the Google Hotwords, that caused some trouble). For that there is the can.json. Any found extension that is not in can.json will trigger an alert.

Hidden extensions
-----------------

This tool will find more extensions than the ones you can see in the browser extension dialog. This is normal. Some browser features are implemented in extensions. To not clutter the extension menu with those, they are hidden.

You can also view the extensions visiting this URL:

chrome://inspect/#extensions


