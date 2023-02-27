import os
import sys
import re
from pypinyin import lazy_pinyin, BOPOMOFO
import jieba
import cn2an
import logging


# List of (Latin alphabet, bopomofo) pairs:
_latin_to_bopomofo = [(re.compile('%s' % x[0], re.IGNORECASE), x[1]) for x in [
    ('a', '�ߡ�'),
    ('b', '�Ũ�A'),
    ('c', '�٨硥'),
    ('d', '�ɨ�A'),
    ('e', '��A'),
    ('f', '�ݨ@�Ȩ�A'),
    ('g', '�Ш�A'),
    ('h', '�ݡ��Ѩ�A'),
    ('i', '�ިA'),
    ('j', '�ШߨA'),
    ('k', '�ΨߨA'),
    ('l', '�ݨ@�ۨA'),
    ('m', '�ݨ@�Ǩ�A'),
    ('n', '�㡥'),
    ('o', '�ᡥ'),
    ('p', '�ƨ硥'),
    ('q', '�Ψ�ᡥ'),
    ('r', '�ڨA'),
    ('s', '�ݨ@�٨A'),
    ('t', '�ʨ�A'),
    ('u', '��ᡥ'),
    ('v', '��硥'),
    ('w', '�ɨڨA�Ũ�A�̨��A'),
    ('x', '�ݡ��Ψ�A�٨A'),
    ('y', '��ިA'),
    ('z', '�רߨA')
]]

# List of (bopomofo, romaji) pairs:
_bopomofo_to_romaji = [(re.compile('%s' % x[0]), x[1]) for x in [
    ('�Ũ�', 'p?wo'),
    ('�ƨ�', 'p?wo'),
    ('�Ǩ�', 'mwo'),
    ('�Ȩ�', 'fwo'),
    ('��', 'p?'),
    ('��', 'p?'),
    ('��', 'm'),
    ('��', 'f'),
    ('��', 't?'),
    ('��', 't?'),
    ('��', 'n'),
    ('��', 'l'),
    ('��', 'k?'),
    ('��', 'k?'),
    ('��', 'h'),
    ('��', '??'),
    ('��', '??'),
    ('��', '?'),
    ('��', '?`?'),
    ('��', '?`?'),
    ('��', 's`'),
    ('��', '?`'),
    ('��', '??'),
    ('��', '??'),
    ('��', 's'),
    ('��', 'a'),
    ('��', 'o'),
    ('��', '?'),
    ('��', 'e'),
    ('��', 'ai'),
    ('��', 'ei'),
    ('��', 'au'),
    ('��', 'ou'),
    ('���', 'yeNN'),
    ('��', 'aNN'),
    ('���', 'iNN'),
    ('��', '?NN'),
    ('��', 'aNg'),
    ('���', 'iNg'),
    ('���', 'uNg'),
    ('���', 'yuNg'),
    ('��', '?Ng'),
    ('��', '??'),
    ('��', 'i'),
    ('��', 'u'),
    ('��', '?'),
    ('��', '��'),
    ('�@', '��'),
    ('��', '����'),
    ('�A', '��'),
    ('�B', ''),
    ('��', ','),
    ('��', '.'),
    ('��', '!'),
    ('��', '?'),
    ('��', '-')
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
    ('�Ũ�', 'p?wo'),
    ('�ƨ�', 'p?wo'),
    ('�Ǩ�', 'mwo'),
    ('�Ȩ�', 'fwo'),
    ('��', 'p?'),
    ('��', 'p?'),
    ('��', 'm'),
    ('��', 'f'),
    ('��', 't?'),
    ('��', 't?'),
    ('��', 'n'),
    ('��', 'l'),
    ('��', 'k?'),
    ('��', 'k?'),
    ('��', 'x'),
    ('��', 't??'),
    ('��', 't??'),
    ('��', '?'),
    ('��', 'ts`?'),
    ('��', 'ts`?'),
    ('��', 's`'),
    ('��', '?`'),
    ('��', 'ts?'),
    ('��', 'ts?'),
    ('��', 's'),
    ('��', 'a'),
    ('��', 'o'),
    ('��', '?'),
    ('��', '?'),
    ('��', 'a?'),
    ('��', 'e?'),
    ('��', '��?'),
    ('��', 'o?'),
    ('���', 'j?n'),
    ('���', '??n'),
    ('��', 'an'),
    ('���', 'in'),
    ('���', '?n'),
    ('��', '?n'),
    ('��', '��?'),
    ('���', 'i?'),
    ('���', '??'),
    ('���', 'j??'),
    ('��', '??'),
    ('��', '??'),
    ('��', 'i'),
    ('��', 'u'),
    ('��', '?'),
    ('��', '��'),
    ('�@', '��'),
    ('��', '����'),
    ('�A', '��'),
    ('�B', ''),
    ('��', ','),
    ('��', '.'),
    ('��', '!'),
    ('��', '?'),
    ('��', '-')
]]

# List of (bopomofo, ipa2) pairs:
_bopomofo_to_ipa2 = [(re.compile('%s' % x[0]), x[1]) for x in [
    ('�Ũ�', 'pwo'),
    ('�ƨ�', 'p?wo'),
    ('�Ǩ�', 'mwo'),
    ('�Ȩ�', 'fwo'),
    ('��', 'p'),
    ('��', 'p?'),
    ('��', 'm'),
    ('��', 'f'),
    ('��', 't'),
    ('��', 't?'),
    ('��', 'n'),
    ('��', 'l'),
    ('��', 'k'),
    ('��', 'k?'),
    ('��', 'h'),
    ('��', 't?'),
    ('��', 't??'),
    ('��', '?'),
    ('��', 't?'),
    ('��', 't??'),
    ('��', '?'),
    ('��', '?'),
    ('��', 'ts'),
    ('��', 'ts?'),
    ('��', 's'),
    ('��', 'a'),
    ('��', 'o'),
    ('��', '?'),
    ('��', '?'),
    ('��', 'a?'),
    ('��', 'e?'),
    ('��', '��?'),
    ('��', 'o?'),
    ('���', 'j?n'),
    ('���', 'y?n'),
    ('��', 'an'),
    ('���', 'in'),
    ('���', 'yn'),
    ('��', '?n'),
    ('��', '��?'),
    ('���', 'i?'),
    ('���', '??'),
    ('���', 'j??'),
    ('��', '??'),
    ('��', '??'),
    ('��', 'i'),
    ('��', 'u'),
    ('��', 'y'),
    ('��', '?'),
    ('�@', '??'),
    ('��', '???'),
    ('�A', '??'),
    ('�B', ''),
    ('��', ','),
    ('��', '.'),
    ('��', '!'),
    ('��', '?'),
    ('��', '-')
]]


def number_to_chinese(text):
    numbers = re.findall(r'\d+(?:\.?\d+)?', text)
    for number in numbers:
        text = text.replace(number, cn2an.an2cn(number), 1)
    return text


def chinese_to_bopomofo(text):
    text = text.replace('��', '��').replace('��', '��').replace('��', '��')
    words = jieba.lcut(text, cut_all=False)
    text = ''
    for word in words:
        bopomofos = lazy_pinyin(word, BOPOMOFO)
        if not re.search('[\u4e00-\u9fff]', word):
            text += word
            continue
        for i in range(len(bopomofos)):
            bopomofos[i] = re.sub(r'([\u3105-\u3129])$', r'\1��', bopomofos[i])
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
    text = re.sub('([?s?]`[??]?)([������ ]+|$)',
                  r'\1?`\2', text).replace('?', '?`')
    text = re.sub('([?s][??]?)([������ ]+|$)', r'\1?\2', text)
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
    text = re.sub('([s?]`[??]?)([������ ]+|$)',
                  r'\1?`\2', text).replace('?', '?`')
    text = re.sub('([s][??]?)([������ ]+|$)', r'\1?\2', text)
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