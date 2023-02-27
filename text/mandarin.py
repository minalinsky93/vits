import os
import sys
import re
from pypinyin import lazy_pinyin, BOPOMOFO
import jieba
import cn2an
import logging


# List of (Latin alphabet, bopomofo) pairs:
_latin_to_bopomofo = [(re.compile('%s' % x[0], re.IGNORECASE), x[1]) for x in [
    ('a', '¨ß¡¥'),
    ('b', '¨Å¨ç¨A'),
    ('c', '¨Ù¨ç¡¥'),
    ('d', '¨É¨ç¨A'),
    ('e', '¨ç¨A'),
    ('f', '¨Ý¨@¨È¨è¨A'),
    ('g', '¨Ð¨ç¨A'),
    ('h', '¨Ý¡¦¨Ñ¨é¨A'),
    ('i', '¨Þ¨A'),
    ('j', '¨Ð¨ß¨A'),
    ('k', '¨Î¨ß¨A'),
    ('l', '¨Ý¨@¨Û¨A'),
    ('m', '¨Ý¨@¨Ç¨è¨A'),
    ('n', '¨ã¡¥'),
    ('o', '¨á¡¥'),
    ('p', '¨Æ¨ç¡¥'),
    ('q', '¨Î¨ç¨á¡¥'),
    ('r', '¨Ú¨A'),
    ('s', '¨Ý¨@¨Ù¨A'),
    ('t', '¨Ê¨ç¨A'),
    ('u', '¨ç¨á¡¥'),
    ('v', '¨è¨ç¡¥'),
    ('w', '¨É¨Ú¨A¨Å¨è¨A¨Ì¨ç¨á¨A'),
    ('x', '¨Ý¡¥¨Î¨è¨A¨Ù¨A'),
    ('y', '¨è¨Þ¨A'),
    ('z', '¨×¨ß¨A')
]]

# List of (bopomofo, romaji) pairs:
_bopomofo_to_romaji = [(re.compile('%s' % x[0]), x[1]) for x in [
    ('¨Å¨Û', 'p?wo'),
    ('¨Æ¨Û', 'p?wo'),
    ('¨Ç¨Û', 'mwo'),
    ('¨È¨Û', 'fwo'),
    ('¨Å', 'p?'),
    ('¨Æ', 'p?'),
    ('¨Ç', 'm'),
    ('¨È', 'f'),
    ('¨É', 't?'),
    ('¨Ê', 't?'),
    ('¨Ë', 'n'),
    ('¨Ì', 'l'),
    ('¨Í', 'k?'),
    ('¨Î', 'k?'),
    ('¨Ï', 'h'),
    ('¨Ð', '??'),
    ('¨Ñ', '??'),
    ('¨Ò', '?'),
    ('¨Ó', '?`?'),
    ('¨Ô', '?`?'),
    ('¨Õ', 's`'),
    ('¨Ö', '?`'),
    ('¨×', '??'),
    ('¨Ø', '??'),
    ('¨Ù', 's'),
    ('¨Ú', 'a'),
    ('¨Û', 'o'),
    ('¨Ü', '?'),
    ('¨Ý', 'e'),
    ('¨Þ', 'ai'),
    ('¨ß', 'ei'),
    ('¨à', 'au'),
    ('¨á', 'ou'),
    ('¨ç¨â', 'yeNN'),
    ('¨â', 'aNN'),
    ('¨ç¨ã', 'iNN'),
    ('¨ã', '?NN'),
    ('¨ä', 'aNg'),
    ('¨ç¨å', 'iNg'),
    ('¨è¨å', 'uNg'),
    ('¨é¨å', 'yuNg'),
    ('¨å', '?Ng'),
    ('¨æ', '??'),
    ('¨ç', 'i'),
    ('¨è', 'u'),
    ('¨é', '?'),
    ('¡¥', '¡ú'),
    ('¨@', '¡ü'),
    ('¡¦', '¡ý¡ü'),
    ('¨A', '¡ý'),
    ('¨B', ''),
    ('£¬', ','),
    ('¡£', '.'),
    ('£¡', '!'),
    ('£¿', '?'),
    ('¡ª', '-')
]]

# List of (romaji, ipa) pairs:
_romaji_to_ipa = [(re.compile('%s' % x[0], re.IGNORECASE), x[1]) for x in [
    ('?y', '?'),
    ('??y', '??'),
    ('??y', '??'),
    ('NN', 'n'),
    ('Ng', '?'),
    ('y', 'j'),
    ('h', 'x')
]]

# List of (bopomofo, ipa) pairs:
_bopomofo_to_ipa = [(re.compile('%s' % x[0]), x[1]) for x in [
    ('¨Å¨Û', 'p?wo'),
    ('¨Æ¨Û', 'p?wo'),
    ('¨Ç¨Û', 'mwo'),
    ('¨È¨Û', 'fwo'),
    ('¨Å', 'p?'),
    ('¨Æ', 'p?'),
    ('¨Ç', 'm'),
    ('¨È', 'f'),
    ('¨É', 't?'),
    ('¨Ê', 't?'),
    ('¨Ë', 'n'),
    ('¨Ì', 'l'),
    ('¨Í', 'k?'),
    ('¨Î', 'k?'),
    ('¨Ï', 'x'),
    ('¨Ð', 't??'),
    ('¨Ñ', 't??'),
    ('¨Ò', '?'),
    ('¨Ó', 'ts`?'),
    ('¨Ô', 'ts`?'),
    ('¨Õ', 's`'),
    ('¨Ö', '?`'),
    ('¨×', 'ts?'),
    ('¨Ø', 'ts?'),
    ('¨Ù', 's'),
    ('¨Ú', 'a'),
    ('¨Û', 'o'),
    ('¨Ü', '?'),
    ('¨Ý', '?'),
    ('¨Þ', 'a?'),
    ('¨ß', 'e?'),
    ('¨à', '¨»?'),
    ('¨á', 'o?'),
    ('¨ç¨â', 'j?n'),
    ('¨é¨â', '??n'),
    ('¨â', 'an'),
    ('¨ç¨ã', 'in'),
    ('¨é¨ã', '?n'),
    ('¨ã', '?n'),
    ('¨ä', '¨»?'),
    ('¨ç¨å', 'i?'),
    ('¨è¨å', '??'),
    ('¨é¨å', 'j??'),
    ('¨å', '??'),
    ('¨æ', '??'),
    ('¨ç', 'i'),
    ('¨è', 'u'),
    ('¨é', '?'),
    ('¡¥', '¡ú'),
    ('¨@', '¡ü'),
    ('¡¦', '¡ý¡ü'),
    ('¨A', '¡ý'),
    ('¨B', ''),
    ('£¬', ','),
    ('¡£', '.'),
    ('£¡', '!'),
    ('£¿', '?'),
    ('¡ª', '-')
]]

# List of (bopomofo, ipa2) pairs:
_bopomofo_to_ipa2 = [(re.compile('%s' % x[0]), x[1]) for x in [
    ('¨Å¨Û', 'pwo'),
    ('¨Æ¨Û', 'p?wo'),
    ('¨Ç¨Û', 'mwo'),
    ('¨È¨Û', 'fwo'),
    ('¨Å', 'p'),
    ('¨Æ', 'p?'),
    ('¨Ç', 'm'),
    ('¨È', 'f'),
    ('¨É', 't'),
    ('¨Ê', 't?'),
    ('¨Ë', 'n'),
    ('¨Ì', 'l'),
    ('¨Í', 'k'),
    ('¨Î', 'k?'),
    ('¨Ï', 'h'),
    ('¨Ð', 't?'),
    ('¨Ñ', 't??'),
    ('¨Ò', '?'),
    ('¨Ó', 't?'),
    ('¨Ô', 't??'),
    ('¨Õ', '?'),
    ('¨Ö', '?'),
    ('¨×', 'ts'),
    ('¨Ø', 'ts?'),
    ('¨Ù', 's'),
    ('¨Ú', 'a'),
    ('¨Û', 'o'),
    ('¨Ü', '?'),
    ('¨Ý', '?'),
    ('¨Þ', 'a?'),
    ('¨ß', 'e?'),
    ('¨à', '¨»?'),
    ('¨á', 'o?'),
    ('¨ç¨â', 'j?n'),
    ('¨é¨â', 'y?n'),
    ('¨â', 'an'),
    ('¨ç¨ã', 'in'),
    ('¨é¨ã', 'yn'),
    ('¨ã', '?n'),
    ('¨ä', '¨»?'),
    ('¨ç¨å', 'i?'),
    ('¨è¨å', '??'),
    ('¨é¨å', 'j??'),
    ('¨å', '??'),
    ('¨æ', '??'),
    ('¨ç', 'i'),
    ('¨è', 'u'),
    ('¨é', 'y'),
    ('¡¥', '?'),
    ('¨@', '??'),
    ('¡¦', '???'),
    ('¨A', '??'),
    ('¨B', ''),
    ('£¬', ','),
    ('¡£', '.'),
    ('£¡', '!'),
    ('£¿', '?'),
    ('¡ª', '-')
]]


def number_to_chinese(text):
    numbers = re.findall(r'\d+(?:\.?\d+)?', text)
    for number in numbers:
        text = text.replace(number, cn2an.an2cn(number), 1)
    return text


def chinese_to_bopomofo(text):
    text = text.replace('¡¢', '£¬').replace('£»', '£¬').replace('£º', '£¬')
    words = jieba.lcut(text, cut_all=False)
    text = ''
    for word in words:
        bopomofos = lazy_pinyin(word, BOPOMOFO)
        if not re.search('[\u4e00-\u9fff]', word):
            text += word
            continue
        for i in range(len(bopomofos)):
            bopomofos[i] = re.sub(r'([\u3105-\u3129])$', r'\1¡¥', bopomofos[i])
        if text != '':
            text += ' '
        text += ''.join(bopomofos)
    return text


def latin_to_bopomofo(text):
    for regex, replacement in _latin_to_bopomofo:
        text = re.sub(regex, replacement, text)
    return text


def bopomofo_to_romaji(text):
    for regex, replacement in _bopomofo_to_romaji:
        text = re.sub(regex, replacement, text)
    return text


def bopomofo_to_ipa(text):
    for regex, replacement in _bopomofo_to_ipa:
        text = re.sub(regex, replacement, text)
    return text


def bopomofo_to_ipa2(text):
    for regex, replacement in _bopomofo_to_ipa2:
        text = re.sub(regex, replacement, text)
    return text


def chinese_to_romaji(text):
    text = number_to_chinese(text)
    text = chinese_to_bopomofo(text)
    text = latin_to_bopomofo(text)
    text = bopomofo_to_romaji(text)
    text = re.sub('i([aoe])', r'y\1', text)
    text = re.sub('u([ao?e])', r'w\1', text)
    text = re.sub('([?s?]`[??]?)([¡ú¡ý¡ü ]+|$)',
                  r'\1?`\2', text).replace('?', '?`')
    text = re.sub('([?s][??]?)([¡ú¡ý¡ü ]+|$)', r'\1?\2', text)
    return text


def chinese_to_lazy_ipa(text):
    text = chinese_to_romaji(text)
    for regex, replacement in _romaji_to_ipa:
        text = re.sub(regex, replacement, text)
    return text


def chinese_to_ipa(text):
    text = number_to_chinese(text)
    text = chinese_to_bopomofo(text)
    text = latin_to_bopomofo(text)
    text = bopomofo_to_ipa(text)
    text = re.sub('i([aoe])', r'j\1', text)
    text = re.sub('u([ao?e])', r'w\1', text)
    text = re.sub('([s?]`[??]?)([¡ú¡ý¡ü ]+|$)',
                  r'\1?`\2', text).replace('?', '?`')
    text = re.sub('([s][??]?)([¡ú¡ý¡ü ]+|$)', r'\1?\2', text)
    return text


def chinese_to_ipa2(text):
    text = number_to_chinese(text)
    text = chinese_to_bopomofo(text)
    text = latin_to_bopomofo(text)
    text = bopomofo_to_ipa2(text)
    text = re.sub(r'i([aoe])', r'j\1', text)
    text = re.sub(r'u([ao?e])', r'w\1', text)
    text = re.sub(r'([??]??)([????? ]+|$)', r'\1?\2', text)
    text = re.sub(r'(s??)([????? ]+|$)', r'\1?\2', text)
    return text