import pandas as pd
import numpy as np

import os   
from tqdm import tqdm

import re

import pdfplumber
import fitz
from fuzzywuzzy import fuzz
from tools import string_matching_atwin

from datetime import datetime

def typo_spotter(input):
    patokans=[
    "Nama Perseroan", #belum kehandle
    "Nomor SK Pengesahan", #belum kehandle 
    "Dalam bentuk uang.","MODAL DISETOR",
    "Alamat",
    "Kelurahan",
    "Kabupaten",
    "Provinsi"
]
    typo_map={}
    # text_corrected=''
    for line in input.split('\n'):
        for patokan in patokans:
        # if type(patokan)!=list: patokan=[patokan]
        # for original_phrase in patokan:
            additional_words_tolerance=2
            evaluated_part_line_nominees={}
            max_words=len(patokan.split())+additional_words_tolerance
            evaluated_part_line_candidates=[' '.join(line.split()[j:i+j]) for j in range(len(line.split())) for i in range(1,max_words+1)]  
            for evaluated_part_line in evaluated_part_line_candidates:
                # match_ratio=fuzz.ratio(evaluated_part_line,patokan)
                match_ratio=string_matching_atwin.karmila_max(patokan,evaluated_part_line)
                if match_ratio>80:
                    evaluated_part_line_nominees[evaluated_part_line]=match_ratio
            if len(evaluated_part_line_nominees)>0: 
                evaluated_part_line_awardee=max(evaluated_part_line_nominees, key=evaluated_part_line_nominees.get)
                if evaluated_part_line_nominees[evaluated_part_line_awardee]<100:
                    print('evaluated_part_line_nominees!!!',evaluated_part_line_nominees)
                    typo_map[evaluated_part_line_awardee]=patokan
                #else: means theres no typo around here
    if len(typo_map)>0: print('!!!typo!!!',typo_map) #check for ruined word-of-interest (thanks dons!) due to goddam watermarks
                    
    return typo_map

def typo_spotter_2(filename,dct,file_pointer='str'):
    # doc = fitz.open(filename) # open a document
    # with fitz.open(filename) as doc:
    try: #streamlit ver i guess
        with fitz.open(stream=filename.read(), filetype="pdf") as doc:
            for page in doc: # iterate the document pages
                fitz_text = page.get_text().split('\n') #
                for ft in fitz_text:
                    ft=ft.replace(':','').strip() 
                    v=v.replace(':','').strip() 
                    for k,v in dct.items():
                        if k=='index' or v is None: continue
                        match_karmilamax=string_matching_atwin.karmila_max(re.sub(r'[^a-zA-Z0-9\s]+', '', ft)  ,re.sub(r'[^a-zA-Z0-9\s]+', '', v)  )
                        if match_karmilamax < 100 and match_karmilamax>80: #this where sub happens
                            if ('00' in ft or 'Rp' in ft or '00' in v or 'Rp' in v):
                                pass
                            else:
                                dct[k]=ft
                                print('typo spotted:!!!!!!!',v,'to',ft)
    except:
        with fitz.open(filename) as doc:
            for page in doc: # iterate the document pages
                fitz_text = page.get_text().split('\n') #
                for ft in fitz_text:
                    ft=ft.replace(':','').strip() 
                    for k,v in dct.items():
                        if k=='index' or v is None: continue
                        match_karmilamax=string_matching_atwin.karmila_max(re.sub(r'[^a-zA-Z0-9\s]+', '', ft)  ,re.sub(r'[^a-zA-Z0-9\s]+', '', v)  )
                        if match_karmilamax < 100 and match_karmilamax>80: #this where sub happens
                            if ('00' in ft or 'Rp' in ft or '00' in v or 'Rp' in v):
                                pass
                            else:
                                dct[k]=ft
                                print('typo spotted:',v,'to',ft)
    return dct


def spot_table_name(doc,dct,batas_awal_page_tabel):
    names=[]

    for page in reversed(doc): # iterate the document pages
        if int(re.sub('[^0-9]', "", str(page)[:10]))<batas_awal_page_tabel: continue #skip pages yg blm contain tabel
        fitz_text = page.get_text().split('\n') #

        pengambil_name_aktif=0
        for ft in reversed(fitz_text):
            name_col_indicators = [
                'Nomor SK', # non individu
                'TTL', # individu WNI
                'PASSPORT', # individu WNA
                ]
            if any(field in ft for field in name_col_indicators):
                name_temp=[]
                pengambil_name_aktif=1
            elif pengambil_name_aktif==1:
                if (ft.strip()=='Total' or 'Rp.' in ft or ft.strip()=='-'):
                    pengambil_name_aktif=0
                    names.append(' '.join([n for n in reversed(name_temp)])[:-1])
                    print('name sss:',names)
                else:
                    name_temp.append(ft)

    for k,v in dct.items():
        if k=='index' or v is None: continue
        
        top_candidate={'match_score':-1}
        v=v.replace('\n',' ')
        # cek untuk nama
        for name_candidate in names:               
            name_candidate=name_candidate.replace('\n',' ')

            match_karmilamax=string_matching_atwin.karmila_max(re.sub(r'[^a-zA-Z0-9\s]+', '', name_candidate)  ,re.sub(r'[^a-zA-Z0-9\s]+', '', v)  ) 

            print('NAME  in table check:', match_karmilamax,':',re.sub(r'[^a-zA-Z0-9\s]+', '', name_candidate),'-',re.sub(r'[^a-zA-Z0-9\s]+', '', v))
            # match_candidates=[]
            if match_karmilamax>top_candidate['match_score']: #this where candicacy comes
                top_candidate={'name':name_candidate,'match_score':match_karmilamax}
            # print('top:',top_candidate)
        if top_candidate['match_score']>=66 and top_candidate['match_score']<100:
            dct[k]=top_candidate['name']
            print('typo name from table spotted:',v,'to',top_candidate['name'])
            continue # optimize so that it does not loop the jabatans
        
        top_candidate={'match_score':-1}
        # cek untuk jabatan
        jabatans = ['DIREKTUR', 'DIREKTUR UTAMA', 'DIREKTUR', 'KOMISARIS', 'KOMISARIS UTAMA', 'KOMISARIS INDEPENDEN', 'PRESIDEN DIREKTUR']
        for jabatan_candidate in jabatans:
            jabatan_candidate=jabatan_candidate.replace('\n',' ')
            match_karmilamax=string_matching_atwin.karmila_max(re.sub(r'[^a-zA-Z0-9\s]+', '', jabatan_candidate)  ,re.sub(r'[^a-zA-Z0-9\s]+', '', v)  ) 
            print('JABATAN  in table check:', match_karmilamax,':',re.sub(r'[^a-zA-Z0-9\s]+', '', jabatan_candidate),'-',re.sub(r'[^a-zA-Z0-9\s]+', '', v))
            if match_karmilamax>top_candidate['match_score']: #this where candicacy comes
                top_candidate={'jabatan':jabatan_candidate,'match_score':match_karmilamax}
                
        if top_candidate['match_score']>40 and top_candidate['match_score']<100:
            dct[k] = top_candidate['jabatan']
            print('typo JABATAN from table spotted:',v,'to',top_candidate['jabatan'])
        # else: dct[k] = '-'
            
    return dct
def typo_spotter_2_table(filename,dct,batas_awal_page_tabel,file_pointer='str'):
    # doc = fitz.open(filename) # open a document
    # with fitz.open(filename) as doc:
    try: #streamlit ver i guess
        with fitz.open(stream=filename.read(), filetype="pdf") as doc:
            return spot_table_name(doc,dct,batas_awal_page_tabel)
    except:
        with fitz.open(filename) as doc:
            return spot_table_name(doc,dct,batas_awal_page_tabel)
    # return 
def spot(where,input,patokan_depan,patokan_belakang='',key='',rp=False,opsional=0):# 'Nomor SK Pengesahan'
    if where.lower()=='depan':
        pattern = r'{}\s*(.*)'.format(patokan_depan) 
        match = re.search(pattern, input)
        if key=='':key=patokan_depan
    elif where.lower()=='tengah':
        pattern = r'{}(.*?){}.'.format(patokan_depan,patokan_belakang)
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
        res_1=match.group(1)[1:].lstrip() 
        if rp==True:
            res_1='Rp '+re.sub('[^0-9.]', "", res_1) #extract . and int
        return res_1

def extractor(pdf):
    ext_tables=[]
    # for i in tqdm(range(len(pdfs))):
    ext={}
    # pdf=pdfs[i]
    # file=f'pdfs/{pdf}.pdf'
    with pdfplumber.open(pdf) as pdf:
    # with pdfplumber.load(feed) as pdf: #streamlit StringIO
        text = ''
        for page in pdf.pages:
            text+=page.extract_text()

        tables = []
        for page in pdf.pages:
            tables.extend(page.extract_tables())
        # print("\nExtracted Tables:")
        # for table in tables:
        #     print(table)
    typo_map=typo_spotter(text)
    for typo,correction in typo_map.items():
        text=text.replace(typo,correction)
    # ext["index"]=i
    nama_index=spot('depan',text,"Nama Perseroan")
    ext["Nama Perseroan"]=nama_index
    ext["Nomor SK Pengesahan"]=spot('depan',text,"Nomor SK Pengesahan",opsional=1)
    ext["Nomor SP Data Perseroan"]=spot('depan',text,"Nomor SP Data",opsional=1)
    ext["Alamat"]=spot('depan',text,"Alamat",opsional=1)
    ext["Kelurahan"]=spot('depan',text,"Kelurahan",opsional=1)
    ext["Kabupaten"]=spot('depan',text,"Kabupaten",opsional=1)
    ext["Provinsi"]=spot('depan',text,"Provinsi",opsional=1)
    ext["Modal Disetor"]=spot('tengah',text,"MODAL DISETOR","Dalam bentuk uang.",rp=1)
    
    print(ext)
    # exts.append(ext)
    idx_pdf=0
    
    here=0
    for t1 in tables:
        for t2 in t1:
            if here==1:
                ext_table={}
                t2_1st=t2[0].split(',')
                if (string_matching_atwin.karmila_max('Nama',t2_1st[0])>75) or ('TTL:' not in ''.join(t2_1st[1:])) and ('Nomor SK' not in ''.join(t2_1st[1:])):
                    continue
                ext_table["Nama Perseroan"]=nama_index
                ext_table[f'Pemegang Saham no.']= index_pemegang   
                ext_table[f'Nama Pemegang'],ext_table[f'Tipe']=t2_1st[0],'Individu' if 'TTL:' in ''.join(t2_1st[1:]) else 'Non-individu'
                ext_table[f'Alamat Pemegang']=t2[2]
                ext_table[f'Lembar Saham']=t2[-2]
                ext_table[f'Nilai Saham']=t2[-1]
                index_pemegang+=1
                ext_tables.append(ext_table)
            header_check=sum([elem in t2 for elem in ['Nama','Jabatan','Alamat','Klasifikasi\nSaham','\nJumlah\nLembar\nSaham','Total']])
            if header_check>=3 and len(t2)==6 and here==0: #3 out of 6 match is considered good enough, if there were already 6 cols registered (no other tables found to have 6 anyway)
                print('yeah')
                here=1
                index_pemegang=1
    print(ext_tables)
    return ext,ext_tables
            
def wrapping_it_up(exts,ext_tables):
    # exts,ext_tables=extractor(pdfs)
    
    df=pd.DataFrame(exts)
    df_2=pd.DataFrame(ext_tables)

    angka_blkg_koma=3
    df_2['Nama Pemegang']=df_2['Nama Pemegang'].str.replace('\n',' ')
    df_2['Lembar Saham']=df_2['Lembar Saham'].apply(lambda x: re.sub('[^0-9]', "", x)).replace('',0).astype(np.int64)
    df_2['Nilai Saham']=df_2['Nilai Saham'].apply(lambda x: re.sub('[^0-9]', "", x)).replace('',0).astype(np.int64)
    # total_lembar=sum(df_2['Lembar Saham'])

    df_2['Kepemilikan Saham (dalam %)']=df_2['Lembar Saham'] / (df_2.groupby('Nama Perseroan')['Lembar Saham'].transform('sum'))
    df_2['Kepemilikan Saham (dalam %)']=((df_2['Kepemilikan Saham (dalam %)']*100*10**angka_blkg_koma).astype(int)/(10**angka_blkg_koma)).astype(str).str.rstrip('0').str.rstrip('.').str.replace('.',',') +' %'
    df_2=df_2.sort_values(['Lembar Saham'],ascending=[0])

    df_2['Kepemilikan Saham (dalam %)']=df_2['Kepemilikan Saham (dalam %)'].replace('0 %','')
    df_2['Lembar Saham']=df_2['Lembar Saham'].apply(lambda x:r"{:,}".format(x)).str.replace(',','.').replace('0','')
    df_2['Nilai Saham']=('Rp '+df_2['Nilai Saham'].apply(lambda x:r"{:,}".format(x)).str.replace(',','.')).replace('Rp 0','')
    return df,df_2

def merging_it_up(df,df_2,no_pdfs=0):
    df_merged=pd.merge(df,df_2,left_on='Nama Perseroan',right_on='Nama Perseroan',how='left') 
    
    
    ###  adjustments buat antisipasi first meet ###
    df_merged=df_merged.sort_values(['Nama Perseroan','Pemegang Saham no.'],ascending=[1,1]) #ini ubah urutan jadi yang standar
    df_merged=df_merged.drop(columns=['Kepemilikan Saham (dalam %)']) #ini kolom2 yg mau didrop
    ################################################
    
    
    df_merged2=df_merged.set_index(list(df_merged.columns[:-5]))

    
    timestamp=str(datetime.now()).replace('-','').replace(':','').replace(' ','_')[:15]
    if no_pdfs>1: number_pdfs=f'{no_pdfs}-pdfs'
    elif no_pdfs==1: number_pdfs='_1-pdf'
    else: number_pdfs=''
    df_merged2.to_excel(f'spreadsheet{number_pdfs}_{timestamp}.xlsx')
    
    return df_merged #ooh ini buat munculan di streamlit, karena dia ga support multiindex
    # df_merged=df_merged.set_index(list(df_merged.columns[:-5]))



