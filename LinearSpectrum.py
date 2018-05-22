#!/usr/bin/env python3
import sys
import os
from multiprocessing import Process, Manager

def read(path):
    with open(path, "r") as vfile:
        temp = vfile.readline().rstrip()
        bytelen = len(temp)
        vectors = [int(x.rstrip(), 2) for x in vfile.readlines()]
        vectors.append(int(temp, 2))
        length = len(vectors)
        return (vectors, length, bytelen)

def deletezeros(vectors, setlen, bytelen):
    temp = 0
    for v in vectors:
        temp |= v
    zeros = getind(temp, bytelen)
    for z in zeros:
        for i in range(setlen):
            vectors[i] = (vectors[i] % (2**z)) + (vectors[i] // (2**(z+1)) ) * 2**z
        bytelen -= 1
    return (vectors, bytelen)

def getind(temp, bytelen):
    zeros = []
    tempstr = bin(temp)[2:]
    templen = len(tempstr)
    if templen < bytelen:
        zeros = [bytelen-1 - i for i in range(bytelen-templen)]
    for i in range(templen):
        if tempstr[i] == '0':
            zeros.append(templen-1-i)
    return zeros

def getoptbasis(vectors, setlen, bytelen):
    rank = 0
    if setlen > bytelen:
        rank = bytelen
    else:
        rank = setlen
    for r in range(rank):
        indmaxv = r
        for i in range(r, setlen):
            if vectors[i] > vectors[indmaxv]:
                indmaxv = i
        vectors[indmaxv], vectors[r] = vectors[r], vectors[indmaxv]
        currind = len(bin(vectors[r])[2:]) - 1
        for i in range(setlen):
            if (vectors[i] & 2**(currind)):
                if i != r:
                    vectors[i] ^= vectors[r]
    basis = []
    for r in range(rank):
        if vectors[r] != 0:
            basis.append(vectors[r])
        else:
            rank -= 1
    return (basis, rank)

def proc(basis, rank, setlen, bytelenwz, bytelen, threadquantity):
    wlist = []
    if rank == bytelenwz:
        wlist = [1]
        for i in range(1, rank+1):
            wlist.append(wlist[i-1]*(rank-i+1)/i)
            wlist = [int(w) for w in wlist]
    else:
        wlists = Manager().list()
        threads = [Process(target=comb, args=(basis, rank, bytelen, num, threadquantity, wlists)) for num in range(threadquantity)]

        for t in threads:
            t.start()        
        for t in threads:
            t.join()
        wlist = [0]*(bytelen+1)
        for w in wlists:
            wlist = [wlist[i] + w[i] for i in range(bytelen+1)]
    wlist = [int(w*2**(setlen - rank)) for w in wlist]
    return wlist

def comb(vectors, length, bytelen, num, threadquantity, wlists):
    wlist = [0] * (bytelen + 1)
    left = int(2**(length) / threadquantity * num)
    right = int(2**(length) / threadquantity * (num + 1))
    tempvec = createtempvec(vectors, grey(left))
    position = bin(tempvec).count('1')
    wlist[position] += 1

    old_g, new_g = grey(left), grey(left + 1)
    for i in range(left + 1, right):
        ind = bin(old_g - new_g)[::-1].find('1')
        tempvec ^= vectors[ind]
        position = bin(tempvec).count('1')
        wlist[position] += 1
        old_g, new_g = new_g, grey(i+1)
    wlists.append(wlist)

def grey(dig):
    return dig ^ (dig // 2)


def createtempvec(vectors, grey):
    tempvec = 0
    i = 0
    while grey:
        if grey%2 == 1:
            tempvec ^= vectors[i]
        i += 1
        grey //= 2
    return tempvec


def gist(wlist, path):
    with open(path, "w") as fout:
        i = 0
        for w in wlist:
            fout.write("{}\t{}\n".format(i, w))
            i += 1

def main(inputfile, outputfile, threadquantity):
    vectors, setlen, bytelen = read(inputfile)
    vectors, bytelenwz = deletezeros(vectors, setlen, bytelen)
    basis, rank = getoptbasis(vectors, setlen, bytelenwz)
    wlist = proc(basis, rank, setlen, bytelenwz, bytelen, threadquantity)   
    gist(wlist, outputfile)
    print("{} done".format(outputfile))

def parse(args):
    threadquantity = 12

    if args[0] == '-t':
        threadquantity = int(args[1])
        args = args[2:]

    typefrom = args[0]
    filesfrom = []

    if typefrom == '-f':
        i = 1
        while args[i] != '-o':
            filesfrom.append(args[i])
            i += 1
        args = args[i:]

    elif typefrom == '-i':
        inputdir = args[1]
        if inputdir[-1] != '/':
            inputdir += '/'
        if args[2] == '-e':
            i = 3
            while args[i] != '-o':
                filesfrom.append(inputdir + args[i])
                i += 1
            args = args[i:]
        else:
            filesfrom = [inputdir + file for file in os.listdir(inputdir)]
            args = args[2:]
    else:
        return 0
    
    outputdir = ''
    if args[0] == '-o':
        outputdir = args[1]
        if outputdir[-1] != '/':
            outputdir += '/'
        args = args[2:]
    else:
        return 1

    filesto = []
    typeto = ''
    if len(args) > 0:
        typeto = args[0]
        if typeto == '-m':
            filesto = [outputdir + file for file in args[1:]]

        elif typeto == '-p':
            name = args[1]
            filesto = [outputdir + name + os.path.split(file)[1] for file in filesfrom]
        else:
            return 2
    else:
        filesto = [outputdir + os.path.split(file)[1] for file in filesfrom]

    if len(filesfrom) != len(filesto):
        return 3

    return (threadquantity, filesfrom, filesto)


if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        parseret = parse(args)
        if parseret == 0:
            print("Problem with description input files")
        elif parseret == 1:
            print("Problem with description output directory")
        elif parseret == 2:
            print("Problem with description output files")
        elif parseret == 3:
            print("Quantity of input and output files is not equal")
        else:
            threadquantity, filesfrom, filesto = parse(args)
            filequantity = len(filesfrom)
            for i in range(filequantity):
                main(filesfrom[i], filesto[i], threadquantity)
    except:
        print("Error! Path or file does not exist")
