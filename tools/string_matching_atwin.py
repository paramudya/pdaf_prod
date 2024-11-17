#karmila functions as *typo hunter*. the first string (A) typically being the reference, the latter (B) being the potential typo string
def karmila_min(stra, strb): 
    #counts how much of the characters of string A,put in order, is in B (ordered match right from the start, case-sensitive, no substitution, proportion in %)
    #in proportion to length of string A
    lena = len(stra)
    lenb= len(strb)
    
    same_character_counter=0
    ia=0
    for charb in strb:
        if ia==len(stra):
            break
        elif charb==stra[ia]:
            same_character_counter+=1
            ia+=1
    return same_character_counter/len(stra)*100

    # karmila_min('Nama Perseroan','BNama B PerseroBanM')
    # 100

    # karmila_min('Nama Perseroan','Data Perseroan')
    # 0
    
def karmila_max(stra, strb): #patokannya harus bener
    #counts how much of the characters of string A,put in order, is in B (ordered match right from the start, case-sensitive, no substitution, proportion in %)
    #in proportion to length of string B
    lena = len(stra) 
    lenb= len(strb)
    # print('comparing stra to strb',stra,strb)
    same_character_counter=0
    ia=0
    for charb in strb:
        if ia==len(stra):
            break
        elif charb==stra[ia]:
            same_character_counter+=1
            ia+=1
        # elif charb!=stra[ia]:
            
    pembagi=max(len(stra),len(strb))
    if pembagi==0:
        return 0
    return same_character_counter/pembagi*100

    # karmila_max('Nama Perseroan','BNama B PerseroBanM')
    # 73.68

    # karmila_max('Nama Perseroan','Data Perseroan')
    # 0
    
    
    
