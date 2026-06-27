import os
font_path = '/home/bowen/dorm-clean/NotoSansSC-Regular.ttf'
from fontTools.ttLib import TTFont
font = TTFont(font_path)
cmap = font.getBestCmap()
chars = {'\u25b6':'play', '\u23f8':'pause', '\u25a0':'stop', '\u21bb':'cycle', '\u2699':'gear', '\u2684':'dice', '\u4f60':'CJK'}
for c, d in chars.items():
    cp = ord(c)
    ok = "YES" if cp in cmap else "NO "
    print(f'U+{cp:04X} {d}: {ok}')
