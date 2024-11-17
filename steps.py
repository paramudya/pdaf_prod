import pandas as pd
import numpy as np
from datetime import datetime

import os   
from tqdm import tqdm

import re   

#reader methods
import pdfplumber 
import fitz 

#matching methods
from fuzzywuzzy import fuzz
from tools import plumber as pl, string_matching_atwin
from tools.main_funcs import spot, correct_name

def pdf_prep(pdfs: list):
    
    # ext={}
    #fix pdf
    for pdf in tqdm(pdfs):
        #eof fix
        EOF_MARKER = b'%%EOF'
        with open(f'{pdf}', 'rb') as f:
            contents = f.read()
        # check if EOF is somewhere else in the file
        if EOF_MARKER in contents:
            # we can remove the early %%EOF and put it at the end of the file
            contents = contents.replace(EOF_MARKER, b'')
            contents = contents + EOF_MARKER
        else:
            # Some files really don't have an EOF marker
            print(contents[-8:]) # see last characters at the end of the file
            # printed b'\n%%EO%E'
            contents = contents[:-6] + EOF_MARKER
        with open(f'{pdf}', 'wb') as f: # edit lgsg difile
            f.write(contents)

def step_1(pdfs: list):
    exts=[]
    ext_tables=[]
    for i in tqdm(range(len(pdfs))):
        batas_awal_page_tabel=-133
        ext={}
        pdf=pdfs[i]
        file=f'{pdf}'
        with pdfplumber.open(file) as pdf:
        # with pdfplumber.load(feed) as pdf: #streamlit StringIO
            text = ''
            for page in reversed(pdf.pages): #reverse. cek dr yg pertama ketemu dr blkg
                text_page='\n'.join(list(reversed(page.extract_text().split('\n'))))
                typo_map=pl.typo_spotter(text_page)
                for typo,correction in typo_map.items():
                    text_page=text_page.replace(typo,correction)
                if 'PENGURUS DAN PEMEGANG SAHAM' in text_page and batas_awal_page_tabel==-133: 
                    batas_awal_page_tabel=int(re.sub('[^0-9.]', "", str(page)))-1
                    print(batas_awal_page_tabel)
                text+=text_page

            tables = []
            for page in pdf.pages[batas_awal_page_tabel:]: 
                tables.extend(page.extract_tables())
            # print("\nExtracted Tables:")
            # for table in tables:
            #     print(table)

        ext["index"]=i
        ext["Nama Perseroan"]=spot('depan',text,"Nama Perseroan")
        ext["Nomor SK Pengesahan"]=spot('depan',text,"Nomor SK Pengesahan",opsional=1)
        ext["Nomor SP Data Perseroan"]=spot('depan',text,"Nomor SP Data",opsional=1)
        ext["Alamat"]=spot('depan',text,"Alamat :",opsional=1,u_need_titik2=1)
        ext["Kelurahan"]=spot('depan',text,"Kelurahan",opsional=1)
        ext["Kabupaten"]=spot('depan',text,"Kabupaten",opsional=1)
        ext["Provinsi"]=spot('depan',text,"Provinsi",opsional=1)
        ext["Modal Disetor"]=spot('tengah',text,"MODAL DISETOR","Dalam bentuk uang.",rp=1)
        
        # print(ext)
        ext_typo_beres=pl.typo_spotter_2(file,ext) #spott ypoes by comparing with an OCR pdf reading method
        print(ext_typo_beres)
        exts.append(ext)

        idx_pdf=0
        
        stop=0
        for t1 in reversed(tables): #reverse. cek dr belakang baris pada tabel, baru berenti setelah ketemu header
            for t2 in reversed(t1):
                if len(t2)==6: 
                    # header_check=sum([elem in t2 for elem in ['Nama','Jabatan','Alamat','Klasifikasi\nSaham','\nJumlah\nLembar\nSaham','Total']])
                    # if header_check>=3:#3 out of 6 match is considered good enough, if there were already 6 cols registered (no other tables found to have 6 anyway)
                    #     print('yeah stop')
                    #     stop=1
                    ext_table={}
                    t2_1st=t2[0].split(',')
                    if (string_matching_atwin.karmila_max('Nama',t2_1st[0])>60) and ('TTL:' not in ''.join(t2_1st[1:])) and ('Nomor SK' not in ''.join(t2_1st[1:])):
                        continue #check
                    ext_table["index"]=i
                    # ext_table[f'Pemegang Saham no.']= index_pemegang   
                    
                    # shouldnt have corrected the capitalization at start
                    # ext_table[f'Nama'],ext_table[f'Tipe']=correct_name(t2_1st[0]),'Individu' if 'TTL:' in ''.join(t2_1st[1:]) else 'Non-individu'
                    ext_table[f'Nama'],ext_table[f'Tipe']=t2_1st[0],'Individu' if 'TTL:' in ''.join(t2_1st[1:]) else 'Non-individu'
                    
                    ext_table[f'Lembar Saham']=t2[-2]
                    ext_table[f'Nilai Saham']=t2[-1]
                    ext_table[f'Jabatan']=t2[1]
                    ext_table_typo_handled=pl.typo_spotter_2_table(file,ext_table,batas_awal_page_tabel=batas_awal_page_tabel) #spott ypoes by comparing with an OCR pdf reading method
                    ext_table['Nama'] = correct_name(ext_table['Nama'])
                    ext_tables.append(ext_table_typo_handled)
                    
                    # ext_tables.append(ext_table) 
    print('ext tables:',ext_table)
    return exts, ext_tables

def step_2(exts, ext_tables, path_output): 
    df=pd.DataFrame(exts)
    df_2=pd.DataFrame(ext_tables)

    angka_blkg_koma=3
    df_2['Nama']=df_2['Nama'].str.replace('\n',' ')
    df_2['Jabatan']=df_2['Jabatan'].str.replace('\n',' ')

    df_2['Lembar Saham']=df_2['Lembar Saham'].apply(lambda x: re.sub('[^0-9]', "", x)).replace('',0).astype(np.int64)
    df_2['Nilai Saham']=df_2['Nilai Saham'].apply(lambda x: re.sub('[^0-9]', "", x)).replace('',0).astype(np.int64)
    # total_lembar=sum(df_2['Lembar Saham'])

    df_2['Kepemilikan Saham (dalam %)']=df_2['Lembar Saham'] / (df_2.groupby('index')['Lembar Saham'].transform('sum'))
    df_2['Kepemilikan Saham (dalam %)']=((df_2['Kepemilikan Saham (dalam %)']*100*10**angka_blkg_koma).astype(int)/(10**angka_blkg_koma)).astype(str).str.rstrip('0').str.rstrip('.').str.replace('.',',') +' %'
    df_2=df_2.sort_values(['Lembar Saham'],ascending=[0])


    df_2['Lembar Saham']=df_2['Lembar Saham'].apply(lambda x:r"{:,}".format(x)).str.replace(',','.')
    df_2['Nilai Saham']='Rp '+df_2['Nilai Saham'].apply(lambda x:r"{:,}".format(x)).str.replace(',','.')


    df_merged=pd.merge(df,df_2,left_on='index',right_on='index',how='left')
    df_merged=df_merged.set_index(list(df_merged.columns[:-5]))

    df_merged.to_csv(f'{path_output}/tes_1.csv')
    # df_merged.to_excel(f'{path_output}/tes_1.xlsx')
    return 1
