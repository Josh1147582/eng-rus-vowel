# Author: Josh Bicking

from praatio import tgio
import sys
from os.path import join
import numpy
import subprocess

if len(sys.argv) != 4:
    print("Usage: {} FOLDER LANG TIER-NAME".format(sys.argv[0]))
    print("FOLDER contains the 15 annotated voice samples.")
    print("LANG is the language (the prefix of the sound/TextGrid files, english or russian).")
    print("TIER-NAME is the name of the ipa tier. Either 'ipa' or 'IPA-phones'.")
    exit(1)

folder = sys.argv[1]
langname = sys.argv[2]
tiername = sys.argv[3]

# list of vowels
vowels = ["i","y","ɨ","ʉ","ɯ","u","ɪ","ʏ","ɪ̈","ʊ̈",
          "ʊ","e","ø","ɘ","ɵ","ɤ","o","e̞","ø̞",
          "ə","ɤ̞","o̞","ɛ","œ","ɜ","ɞ","ʌ","ɔ",
          "æ","ɐ","a","ɶ","ä","ɑ","ɒ"]

# List of all VOTs discovered
vot = {}

# Open all Files
lang = []
russian = []

for i in range(1,16):
    lang.append(tgio.openTextgrid(join(folder, "{}{}.TextGrid".format(langname, i))).tierDict[tiername].entryList)


# Find all stop consonants with a vowel after them
stop_consonants = ["t", "d", "k", "g", "p", "b", "ʔ"]

for i in range(0,15):
    for j in range(0, len(lang[i])):
        if (lang[i][j].label != ""                      # Not silence
            and lang[i][j].label[0] in stop_consonants  # Is a stop consonant
            and j + 1 < len(lang[i])                    # Has an entry after it
            and lang[i][j+1].label != ""                 # Not silence either
            and lang[i][j+1].label[0] in vowels):       # Is a vowel or dipthong
            # Build a script to find where pitch stops

            # We're estimating VOT as "the time between where the
            # consonant Interval of the TextGrid ends, and the
            # beginning of pitch (voicing) starts".
            start = lang[i][j].start
            end = lang[i][j+1].end
            zero = lang[i][j].end

            script = [
                'Read from file: "{}"'.format(join(folder, '{}{}.wav'.format(langname, i+1))),
                'To Pitch: 0, 75, 600']

            for k in numpy.arange(start, end, .001):
                script.append('p = Get value at time: {:.3f}, "Hertz", "Linear"'.format(k))
                script.append('appendInfoLine: p')

            script.append('')

            script = "\n".join(script)

            f = open(join(folder, "tempscript.praat"), "w")
            f.write(script)
            f.close()

            s = subprocess.run(["praat", join(folder, "tempscript.praat")], stdout=subprocess.PIPE)

            s = str(s.stdout)[2:].split("\\n")
            pitch_start = 0
            for line in s:
                if line == "--undefined--":
                    pitch_start += 1
                else:
                    break

            if not (pitch_start == 0 or pitch_start == len(s)):
                # Find where the pitch starts, relative to the sound file
                results = (start + pitch_start) - zero
                if lang[i][j].label[0] + lang[i][j+1].label[0] not in vot:
                    vot[lang[i][j].label[0] + lang[i][j+1].label[0]] = []
                vot[lang[i][j].label[0] + lang[i][j+1].label[0]].append(str(results))

for key in sorted(vot):
    print("{},{},{}".format(key[0], key[1], ",".join(vot[key])))
