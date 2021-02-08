#!/usr/bin/env python3

import os
import redis
import sqlite3
import struct

def version():
	return '0.0.1'

class StarDict():
    def __init__(self, path):
        basename = os.path.basename(path)
        i0 = basename.index('-')
        i1 = basename.rindex('-')
        star = basename[:i0]
        name = basename[i0+1: i1]
        version = basename[i1+1:]
        self.ifo = os.path.join(path, name+'.ifo')
        self.idx = os.path.join(path, name+'.idx')
        self.dic = os.path.join(path, name+'.dict')
        self.word_dic = {}
        self.parse()

    def parse(self):
        ff = open(self.dic, 'rb')
        with open(self.idx, 'rb') as fd:
            d = fd.read()
        t = 0
        i = 0
        while i < len(d):
            if d[i] == 0:
                o,l = struct.unpack('!ii', d[i+1:i+9])
                ff.seek(o)
                e = ff.read(l).decode('utf-8')
                e = '; '.join([i for i in e.split('\n')])
                k = d[t:i].decode('utf-8')
                self.word_dic[k]=e
                # print(f'[{o}][{l}]:[{k}][{e}]')
                i += 9
                t = i
            else:
                i += 1

class FyDict():
    def __init__(self):
        self.dbname = os.path.join(os.path.expanduser("~"), 'Library/Dictionaries/fy.db')
        self.cache = redis.Redis(host='localhost', port=6379, decode_responses=True)

    def fy(self, k):
        d = self.get(k)
        if not d:
            d = self.getdb(k)
            if d: self.set(k, d)
        return d

    def set(self, k, v):
        self.cache.set(f'fy:{k}', v, ex=24*60*60)

    def get(self, k):
        return self.cache.get(f'fy:{k}')

    def clean(self):
        d = self.cache.keys('fy:*')
        for i in d:
            self.cache.delete(i)

    def getdb(self, k):
        db = sqlite3.connect(self.dbname)
        cursor = db.cursor()
        d = cursor.execute(f"select * from en where k='{k}' or k='{k.lower()}' or k='{k.title()}' or k='{k.upper()}'")
        r = d.fetchall()
        e = [i for i in r]
        if not e:
            return
        return f'{k}:{e[0][2]}'.replace(';', ';\n')

    def load(self, p):
        db = sqlite3.connect(self.dbname)
        cursor = db.cursor()
        cursor.execute('create table if not exists en(i integer primary key autoincrement, k text not null, v text not null)')
        db.commit()
        d = StarDict(p)
        for i,k in enumerate(d.word_dic):
            s = f"""insert into en (k,v) values ('{k.replace("'", "''")}', '{d.word_dic[k].replace("'", "''")}')"""
            cursor.execute(s)
        db.commit()

    def __sel__(self):
        self.cache.close()

if __name__ == '__main__':
    fy = FyDict()
    #fy.load('/Users/admin/Work/tmp/stardict/stardict-langdao-ec-gb-2.4.2')
    #fy.load('/Users/admin/Work/tmp/stardict/stardict-langdao-ec-gb-2.4.2')
    print(fy.fy('hi'))
    fy.clean()
