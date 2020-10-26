#!/usr/bin/python3
# -*- coding: utf-8 -*-

import numpy as np
import sys
from collections import deque
import matplotlib.pyplot as plt
import scipy.signal

def ShortTimeEnergy(signal, windowLength, step):
    """
    计算短时能量
    Parameters
    ----------
    signal : 原始信号.
    windowLength : 帧长.
    step : 帧移.
    
    Returns
    -------
    E : 每一帧的能量.
    """
    signal = signal / np.max(signal) # 归一化
    curPos = 0
    L = len(signal)
    numOfFrames  = np.asarray(np.floor((L-windowLength)/step) + 1, dtype=int)
    E = np.zeros((numOfFrames, 1))
    for i in range(numOfFrames):
        window = signal[int(curPos):int(curPos+windowLength-1)];
        E[i] = (1/(windowLength)) * np.sum(np.abs(window**2));
        curPos = curPos + step;
    return E

def SpectralCentroid(signal,windowLength, step, fs):
    """
    计算谱质心
    Parameters
    ----------
    signal : 原始信号.
    windowLength : 帧长.
    step : 帧移.
    fs : 采样率.

    Returns
    -------
    C : 每一帧的谱质心.
    """
    signal = signal / np.max(signal) # 归一化
    curPos = 0
    L = len(signal)
    numOfFrames  = np.asarray(np.floor((L - windowLength) / step) + 1, dtype=int)
    H = np.hamming(windowLength)
    # m = ((fs / (2 * windowLength)) * [1 : windowLength]).T
    m = ((fs / (2 * windowLength)) * np.arange(1, windowLength, 1)).T
    C = np.zeros((numOfFrames, 1))
    for i in range(numOfFrames):
        window = H * (signal[int(curPos) : int(curPos + windowLength)])
        FFT = np.abs(np.fft.fft(window, 2 * int(windowLength)))
        FFT = FFT[1 : windowLength]
        FFT = FFT / np.max(FFT)
        C[i] = np.sum(m * FFT) / np.sum(FFT)
        if np.sum(window**2) < 0.010:
            C[i] = 0.0
        curPos = curPos + step;
    C = C / (fs/2)
    return C

def findMaxima(f, step):
    """
    寻找局部最大值
    Parameters
    ----------
    f : 输入序列.
    step : 搜寻窗长.

    Returns
    -------
    Maxima : 最大值索引 最大值
    countMaxima : 最大值的数量
    """
    ## STEP 1: 寻找最大值
    countMaxima = 0
    Maxima = []
    for i in range(len(f) - step - 1): # 对于序列中的每一个元素:
        if i >= step:
            if (np.mean(f[i - step : i]) < f[i]) and (np.mean(f[i + 1 : i + step + 1]) < f[i]): 
                # IF the current element is larger than its neighbors (2*step window)
                # --> keep maximum:
                countMaxima = countMaxima + 1
                Maxima.append([i, f[i]])
                # Maxima[0, countMaxima] = i
                # Maxima[1, countMaxima] = f[i]
        else:
            if (np.mean(f[0 : i + 1]) <= f[i]) and (np.mean(f[i + 1 : i + step + 1]) < f[i]):
                # IF the current element is larger than its neighbors (2*step window)
                # --> keep maximum:
                countMaxima = countMaxima + 1
                Maxima.append([i, f[i]])
                # Maxima[0, countMaxima] = i
                # Maxima[1, countMaxima] = f[i]

    ## STEP 2: 对最大值进行进一步处理
    
    MaximaNew = []
    countNewMaxima = 0
    i = 0
    while i < countMaxima:
        # get current maximum:
        
        curMaxima = Maxima[i][0]
        curMavVal = Maxima[i][1]

        tempMax = [Maxima[i][0]]
        tempVals = [Maxima[i][1]]
        i = i + 1

        # search for "neighbourh maxima":
        while (i < countMaxima) and (Maxima[i][0] - tempMax[len(tempMax) - 1] < step / 2):
            
            tempMax.append(Maxima[i][0])
            tempVals.append(Maxima[i][1])
            i = i + 1
            
        MM = np.max(tempVals)
        MI = np.argmax(tempVals) 
        if MM > 0.02 * np.mean(f): # if the current maximum is "large" enough:
            
            # keep the maximum of all maxima in the region:
            MaximaNew.append([tempMax[MI], f[tempMax[MI]]])
            countNewMaxima = countNewMaxima + 1   # add maxima

    Maxima = MaximaNew
    countMaxima = countNewMaxima
    
    return Maxima, countMaxima

def VAD(signal, fs):
    win = 0.05
    step = 0.05
    Eor = ShortTimeEnergy(signal, int(win * fs), int(step * fs));
    Cor = SpectralCentroid(signal, int(win * fs), int(step * fs), fs);
    # Eor = np.arange(0, 1, 0.1)
    E = scipy.signal.medfilt(Eor[:, 0], 5)
    E = scipy.signal.medfilt(E, 5)
    C = scipy.signal.medfilt(Cor[:, 0], 5)
    C = scipy.signal.medfilt(C, 5)
    
    E_mean = np.mean(E);
    Z_mean = np.mean(C);
    Weight = 100 # 阈值估计的参数
    # 寻找短时能量的阈值
    Hist = np.histogram(E, bins=10) # 计算直方图
    HistE = Hist[0]
    X_E = Hist[1]
    MaximaE, countMaximaE = findMaxima(HistE, 3) # 寻找直方图的局部最大值
    if len(MaximaE) >= 2: # 如果找到了两个以上局部最大值
        T_E = (Weight*X_E[MaximaE[0][0]] + X_E[MaximaE[1][0]]) / (Weight + 1)
    else:
        T_E = E_mean / 2

    # print(T_E)
    
    # 寻找谱质心的阈值
    Hist = np.histogram(C, bins=10)
    HistC = Hist[0]
    X_C = Hist[1]
    MaximaC, countMaximaC = findMaxima(HistC, 3)
    if len(MaximaC)>=2:
        T_C = (Weight*X_C[MaximaC[0][0]]+X_C[MaximaC[1][0]]) / (Weight+1)
    else:
        T_C = Z_mean / 2
    # print(T_C)
    
    # 阈值判断
    Flags1 = (E>=T_E)
    # print('E_mean:' + str(E_mean))
    # if E_mean < 0.005:
    #     Flags1 = np.zeros(np.shape(Flags1), dtype=int)
    Flags2 = (C>=T_C)
    flags = np.array(Flags1 & Flags2, dtype=int)
    
    # plt.plot(Eor)
    # plt.plot(E)
    # plt.show()
    # plt.plot(Cor)
    # plt.plot(C)
    # plt.show()
    # plt.plot(flags)
    # plt.show()
    
    ## 提取语音片段
    count = 1
    segments = []
    while count < len(flags): # 当还有未处理的帧时
        # 初始化
        curX = []
        countTemp = 1
        while ((flags[count - 1] == 1) and (count < len(flags))):
            if countTemp == 1: # 如果是该语音段的第一帧
                Limit1 = np.round((count-1)*step*fs)+1 # 设置该语音段的开始边界
                if Limit1 < 1:
                    Limit1 = 1
            count = count + 1 		# 计数器加一
            countTemp = countTemp + 1	# 当前语音段的计数器加一
            
        if countTemp > 1: # 如果当前循环中有语音段
            Limit2 = np.round((count - 1) * step * fs) # 设置该语音段的结束边界
            if Limit2 > len(signal):
                Limit2 = len(signal)
            # 将该语音段的首尾位置加入到segments的最后一行
            # segments(end + 1, 1) = Limit1
            # segments(end,     2) = Limit2
            segments.append([Limit1, Limit2])
        count = count + 1
        
    # 合并重叠的语音段
    for i in range(len(segments) - 1): # 对每一个语音段进行处理
        if segments[i][1] >= segments[i + 1][0]:
            segments[i][1] = segments[i + 1][1]
            segments[i + 1, :] = []
            i = 1
    
    # plt.plot(signal)
    
    # for seg in segments:
        # plt.vlines(seg[0], -5000, 5000)
        # plt.vlines(seg[1], -5000, 5000)
    # plt.show()
    
    isVoice = True
    if sum(flags) / len(flags) > 0.6 or sum(flags) / len(flags) < 0.3 / 3:
        isVoice = False
    # print(sum(flags) / len(flags))

    return isVoice, segments

if __name__ == "__main__":
    fs = 16000
    signal = data_decode
    isVoice, segments = VAD(signal, fs)
    