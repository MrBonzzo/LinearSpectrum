#!/usr/bin/env python3
import sys
import os
from multiprocessing import Process, Queue, Lock
import math


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


def comb(vectors, length, bytelen, num, threadquantity, queue, lock):
    """
    Генерирует набор векторов, считает их веса и записывает в список весов.

    Arguments:
    vectors -- набор базисных векторов.
    length -- размер списка базисных векторов.
    bytelen -- длина базисного вектора.
    num -- номер потока.
    threadquantity -- общее количество потоков.
    queue -- очередь для записи списка весов. 
    lock -- блокировка. Необходима для синхноризации очереди.
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
        tempvec ^= vectors[int(math.log2(abs(old_g - new_g)))]
        position = bin(tempvec).count('1')
        wlist[position] += 1
        old_g, new_g = new_g, grey(i+1)

    # блокировка перед отправкой результатов в очередь
    lock.acquire()
    queue.put(wlist)
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
            vec, setlength, bytelen = fromread[0], fromread[1], fromread[2]

            # создание потоков для выполнения задачи
            print("File {} is found. Start processing.".format(os.path.split(path)[1]))
            threadquantity = int(2**2)
            queue = Queue()
            lock = Lock()
            threads = [Process(target=comb, args=(vec, setlength, bytelen, num, threadquantity, queue, lock)) for num in range(threadquantity)]
            
            # запуск потоков для выполнения задачи
            for t in threads:
                t.start()
            
            # подсчёт итогового списка весов
            wlist = queue.get()
            lock.release()
            for i in range(len(threads) - 1):
                temp = queue.get()
                lock.release()
                wlist = [wlist[i] + temp[i] for i in range(len(wlist))]
            for t in threads:
                t.join()
            
            # создание файла с гистограммой
            gist(path, wlist)
            print("Success")
        except:
            print("Bad file. Please, choose another file.")
        path = getpath(2)


if __name__ == "__main__":
    main()