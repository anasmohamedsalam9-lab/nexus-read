import re
import os

filepath = r"A:\nile-manhwa\data.js"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix garbage prefixes before English titles that Olympus produces
content = re.sub(r'"title": "[^"]*?((?:fast break)|(?:My Disciples Are All Villains)|(?:The demon king\'s champion)|(?:Adventures of an Undead who became Paladin))"', r'"title": "\1"', content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Data clean up done.")
