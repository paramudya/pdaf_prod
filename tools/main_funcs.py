import pandas as pd
import numpy as np
from datetime import datetime

import os   
from tqdm import tqdm

import re   

#reader methods
import pdfplumber #conventional?
import fitz #ocr based

#matching methods
from fuzzywuzzy import fuzz
from tools import plumber as pl,string_matching_atwin



def spot(where,input,patokan_depan,patokan_belakang='',key='',rp=False,opsional=0,u_need_titik2=0):# 'Nomor SK Pengesahan'
    if where.lower()=='depan':
        pattern = r'{}\s*(.*)'.format(patokan_depan) 
        match = re.search(pattern, input)
        if key=='':key=patokan_depan
    elif where.lower()=='tengah':
        pattern = r'{}(.*?){}.'.format(patokan_belakang,patokan_depan) #dibalik patokan depan dan belakang
        match = re.search(pattern, input,re.DOTALL) #DOTALL allowing multiline assessment
        if key=='':key=patokan_depan+' *any char* '+patokan_belakang
    if match is None: 
        if opsional==1:
            print(f' contains no {key}')
            return None
        else:
            print(f'error on {key}, re.Match is {match}')
            match.group(1)[1:].lstrip() #break the whole process
    else: 
        if u_need_titik2==1:
            res_1=match.group(1)[0:].lstrip() 
        else:
            res_1=match.group(1)[1:].lstrip() 

        if rp==True:
            res_1='Rp '+re.sub('[^0-9.]', "", res_1) #extract . and int
        return res_1

def correct_name(name: str) -> str:
    name = name.title()
    name = name.replace('Pt.','PT.').replace('Pt ','PT ')
    return name