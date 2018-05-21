#!/usr/bin/env python3
import sys
import os
from multiprocessing import Process, Manager


def read(path):
    """
    Чтение файла по указанному пути.
    
    Arguments:
    path -- путь к файлу. Путь может быть абсолютным или относительным.
    
    Return:
    vectors -- набор базисных векторов, прочитанный из файла.
    lenght -- количество векторов, прочитанных из файла.
    bytelen -- длина вектора.

    Если во время чтения файла произошла ошибка, возвращается -1
    """
    try:
        with open(path, "r") as vfile:
            temp = vfile.readline().rstrip()
            bytelen = len(temp)
            vectors = [int(x.rstrip(), 2) for x in vfile.readlines()]
            vectors.append(int(temp, 2))
            length = len(vectors)
            return (vectors, length, bytelen)
    except:
        return -1


def grey(dig):
    """
    Возвращает число, двоичное представление которого является кодом Грея.
    
    Arguments: 
    dig -- число, для которого необходимо сгенерировать год Грея
    """
    return dig ^ (dig // 2)


def createtempvec(vectors, grey):
    """
    Генерирует вектор, необходимый для начала работы потока вычисления векторов.
    Arguments:
    vectors -- набор базисных векторов.
    grey -- число, двоичное представление которого является кодом Грея.
    
    Return:
    tempvec -- вектор, необходимый для начала работы потока вычисления векторов.
    """
    tempvec = 0
    i = 0
    while grey:
        if grey%2 == 1:
            tempvec ^= vectors[i]
        i += 1
        grey //= 2
    return tempvec


def comb(vectors, length, bytelen, num, threadquantity, wlists):
    """
    Генерирует набор векторов, считает их веса и записывает в список весов.

    Arguments:
    vectors -- набор базисных векторов.
    length -- размер списка базисных векторов.
    bytelen -- длина базисного вектора.
    num -- номер потока.
    threadquantity -- общее количество потоков.
    wlists -- контейнер для записи списка весов
    """

    # создание пустого вектора весов
    wlist = [0] * (bytelen + 1)

    # вычисление границ
    left = int(2**(length) / threadquantity * num)
    right = int(2**(length) / threadquantity * (num + 1))

    # создание вектора, относительно которого начинаются вычисления в данном потоке
    tempvec = createtempvec(vectors, grey(left))

    # заполнение веса для начального вектора
    position = bin(tempvec).count('1')
    wlist[position] += 1
    # цикл генерации векторов и подсчета весов
    old_g, new_g = grey(left), grey(left + 1)
    for i in range(left + 1, right):
        ind = bin(old_g - new_g)[::-1].find('1')
        tempvec ^= vectors[ind]
        position = bin(tempvec).count('1')
        wlist[position] += 1
        old_g, new_g = new_g, grey(i+1)
    wlists.append(wlist)
    # конец работы потока


def gist(path, weigths):
    """
    Запись гистограммы весов в файл.
    Файл с гистограммой сохраняется в директории, где лежит файл с базисными векторами.
    Имя файла получается добавлением "gist_" к имени исходного файла

    Arguments:
    path -- путь к файлу с базисными векторами.
    weigths -- список с гистограммой весов. На i-ой позиции списка количество векторов с весом i.
    """
    head, tail = os.path.split(path)
    if len(head) == 0:
        tail = "gist_" + tail
    else:
        tail = "/gist_" + tail
    with open(head + tail, "w") as w:
        i = 0
        for wh in weigths:
            w.write("{}\t{}\n".format(i, wh))
            i += 1



def getpath(readflag = 0):
    """
    Возвращает путь к исходному файлу.
    
    Arguments:
    readflag -- необходим чтобы узнать откуда вызывается функция.
    Нужен для интерфейса пользователя.

    Return:
    path -- путь к файлу.
    """
    path = ''
    if readflag == 2:
        path = input("Enter the new filename: ")
    elif len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = input("Enter the filename: ")
    if path == ':q':
        return -2
    while not os.path.exists(path):
        if readflag == 1:
            path = input("Enter the filename: ")
            readflag = 0
        else:
            path = input("File does not exist. Please, choose another file.\nEnter the filename: ")
        if path == ':q':
            return -2
    return path

def getind(temp, bytelen):
    """
    Вычисление индексов нулевых столбцов.
    
    Arguments:
    temp -- дизъюнкция векторов.
    bytelen -- длина векторов.

    Return:
    zeros -- список, состоящий из индексов нулевых столбцов.
    """
    zeros = []
    tempstr = bin(temp)[2:]
    templen = len(tempstr)
    # если все вектора начинаются с нулей
    if templen < bytelen:
        zeros = [bytelen-1 - i for i in range(bytelen-templen)]
    # вычисление индексов нулевых строк
    for i in range(templen):
        if tempstr[i] == '0':
            zeros.append(templen-1-i)
    return zeros

def deletezeros(vec, setlength, bytelen):
    """
    Удаление всех нулевых столбцов

    Arguments:
    vec -- вектора
    setlength -- количество векторов
    bytelen -- длина вектора

    Return:
    vec -- вектора
    bytelen -- измененная длина вектора
    """
    temp = 0
    for v in vec:
        temp |= v
    zeros = getind(temp, bytelen)
    for z in zeros:
        for i in range(setlength):
            vec[i] = (vec[i] % (2**z)) + (vec[i] // (2**(z+1)) ) * 2**z
        bytelen -= 1
    return (vec, bytelen)

def getoptbas(vec, setlength, bytelen):
    """
    Вычисление оптимального базиса

    Arguments:
    vec -- вектора
    setlength -- количество векторов
    bytelen -- длина вектора
    
    Return:
    basis -- набор базисных векторов
    rank -- ранг матрицы из базисных векторов

    """
    rank = 0
    if setlength > bytelen:
        rank = bytelen
    else:
        rank = setlength
    r = 0
    while r < rank:
        # нахождение наибольшего вектора
        indmaxv = r
        for i in range(r, setlength):
            if vec[i] > vec[indmaxv]:
                indmaxv = i
        vec[indmaxv], vec[r] = vec[r], vec[indmaxv]
        # если на главной диагонали 1, то xor-им все вектора, где на этой позиции тоже 1
        if (vec[r] & 2**(bytelen - 1 - r)):
            for i in range(setlength):
                if (vec[i] & 2**(bytelen - 1 - r)):
                    if i != r:
                        vec[i] ^= vec[r]
        r += 1

    basis = []
    # удаление нулевых векторов из базиса
    for r in range(rank):
        if vec[r] != 0:
            basis.append(vec[r])
        else:
            rank -= 1
    return (basis, rank)



def main():
    """
    Выполняет чтение файла, генерацию потов для решения задачи и запись гистограммы в новый файл.

    """
    print("\nWeight Spectrum Of Linear Subspace\nFor exit enter ':q'")
    path = getpath()
    while path != -2:
        try:
            # чтение файла
            fromread = read(path)
            while fromread == -1:
                print("Bad file. Please, choose another file.")
                path = getpath(1)
                fromread = read(path)
                if fromread == -2:
                    break
            if fromread == -2:
                break
            print("File {} is found. Start processing.".format(os.path.split(path)[1]))
            # удаление нулевых столбцов
            vec, bytelen = deletezeros(fromread[0], fromread[1], fromread[2])
            setlength = fromread[1]
            # приведение к оптимальному базису
            vec, rank = getoptbas(vec, setlength, bytelen)
            wlist = []
            # если случай тривиальный, то вычисляем гистограмму сразу
            if rank == bytelen:
                wlist = [1*2**(setlength-rank)]
                for i in range(1, rank+1):
                    wlist.append(wlist[i-1]*(rank-i+1)/i)
                wlist = [int(w) for w in wlist]

            else:
                # создание потоков для выполнения задачи
                # количество потоков может быть не только степенью числа 2
                threadquantity = 12
                wlists = Manager().list()
                threads = [Process(target=comb, args=(vec, rank, bytelen, num, threadquantity, wlists)) for num in range(threadquantity)]
                # запуск потоков для выполнения задачи
                for t in threads:
                    t.start()
                
                for t in threads:
                    t.join()
                wlist = [0]*len(wlists[0])
                for w in wlists:
                    wlist = [wlist[i] + w[i] for i in range(len(w))]
            # создание файла с гистограммой
            gist(path, wlist)
            print("Success")
        except:
            print("Bad file. Please, choose another file.")
        path = getpath(2)


if __name__ == "__main__":
    main()