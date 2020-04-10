def is_potentioal_pronounContained(noun,lemma,line,file_type,noun_num='SING'):
    orig_noun=noun
    for pron in base_prons:
        if noun.endswith(pron):
            orig_noun=noun[:-len(pron)]
            if orig_noun.endswith('های'):
                    sing_noun=orig_noun[:-3]
                    if  sing_noun==lemma:
                        return True,pron,orig_noun
            if orig_noun.endswith('ان'):# another form of plural noun -> ان جمع
                sing_noun=orig_noun[:-2]
                if  sing_noun==lemma:
                    return True,pron,orig_noun
            if orig_noun.endswith('گان'): # another form of plural noun -> گان جمع like پرندگان
                sing_noun=orig_noun[:-3]
                sing_noun=sing_noun+'ه' #adding droped ه so پرند converted into پرنده
                if  sing_noun==lemma:
                    return True,pron,orig_noun
            if orig_noun.endswith('یان'): # another form of plural noun -> یان like ملایان
                sing_noun=orig_noun[:-3]
                if  sing_noun==lemma:
                    return True,pron,orig_noun
            if orig_noun.endswith('ات'):# another form of plural noun -> ات جمع عربی like انتقادات
                sing_noun=orig_noun[:-2]
                if  sing_noun==lemma:
                    return True,pron,orig_noun
                if  sing_noun+'ه'==lemma: #some words loose their ending ه when they are concatinated with ات like نمره-> نمرات or آیه-> آیات
                    return True,pron,orig_noun
            if orig_noun.endswith('جات'):# another form of plural noun -> جات جمع عربی like ترشیجات
                sing_noun=orig_noun[:-3]
                if  sing_noun==lemma:
                    return True,pron,orig_noun  
            if orig_noun.endswith('ین'):# another form of plural noun -> ین جمع عربی like مدرسین
                sing_noun=orig_noun[:-2]
                if  sing_noun==lemma:
                    return True,pron,orig_noun    
            if orig_noun.endswith('ون'):# another form of plural noun -> ون جمع عربی like انقلابیون
                sing_noun=orig_noun[:-2]
                if  sing_noun==lemma:
                    return True,pron,orig_noun 
            if orig_noun in mokasar_nouns: #checking nouns in their mokasar form like بیت-> ابیات روایت-> روایات
                if mokasar_nouns[orig_noun]==lemma:
                    return True,pron,orig_noun 
            if orig_noun==lemma:
                return True,pron,orig_noun
    for pron in he_ye_prons:
        if noun.endswith(pron):
            orig_noun=noun[:-len(pron)]
            if orig_noun.endswith('\u200c'):
                orig_noun=orig_noun[:-1]
            if orig_noun.endswith('ه') or orig_noun.endswith('ی'): 
                if orig_noun.endswith('های'):
                    sing_noun=orig_noun[:-3]
                    if  sing_noun==lemma:
                        return True,pron,orig_noun
                elif pron=='ات' and noun_num=='PLUR' and orig_noun==lemma: #like اشتباهات with lemma=اشتباه , in this word ات is mokasar sign not pronoun 
                    return False,'',''
                if orig_noun==lemma:
                    return True,pron,orig_noun
            if pron=='ات' and noun_num=='PLUR' and orig_noun==lemma: #like مقامات with lemma=مقام , in this word ات is mokasar sign not pronoun 
                return False,'',''
            elif orig_noun==lemma:
                return True,pron,orig_noun
    for pron in alef_vav_prons:
        if noun.endswith(pron):
            orig_noun=noun[:-len(pron)]
            if orig_noun.endswith('ها'):
                sing_noun=orig_noun[:-2]
                if sing_noun==lemma:
                    return True,pron,orig_noun #return True,pron[1:],orig_noun+'ی' #concating ی to the noun instead of pronoun => زانویم = زانوی+م
            if (orig_noun.endswith('ا') or orig_noun.endswith('و')) and orig_noun==lemma:
                return True,pron,orig_noun #return True,pron[1:],orig_noun+'ی'
   
    return False,'',''


base_prons=['م','ت','ش','شان','تان','مان']
he_ye_prons=['ام', 'ات', 'اش','شان','تان','مان']
alef_vav_prons=['یم', 'یت', 'یش', 'یشان', 'یتان', 'یمان']
mokasar_nouns={'روایات':'روایت', 'ابیات':'بیت', 'نعمات':'نعمت','زحمات':'زحمت','تجربیات':'تجربه','جزئیات':'جزء'}

dadegan_train_path="Persian_Dependency_Treebank_(PerDT)_V1.1.1/Data/train.conll"
fr=open(dadegan_train_path,'r',encoding="utf-8")
fw=open("multiPartVerbs.txt",'w',encoding="utf-8")
fw1=open("wrong_adj.txt",'w',encoding="utf-8")
fw3=open("punctList.txt",'w',encoding="utf-8")
#log_pron_noun=open("adj_pronoun.txt",'w',encoding="utf-8")
log_adj=open("adj_pos_false.txt",'w',encoding="utf-8")
verbs=[]
simple_verbs={}
simple_v_str=''
punc_l=[]
adjCPos=['ANM','IANM']#['AJCM','AJSUP','AJP']#
poss={}
idens=[]
for line in fr.readlines():
    if line.strip()!='':
        elems=line.strip().split('\t')
        token_id=int(elems[0])
        word_form=elems[1].strip()
        word_lemma=elems[2].strip()
        pos=elems[3]
        cpos=elems[4]
        features=elems[5]
        hParent=elems[6]
        rParent=elems[7]
        feature_parts=features.split('|')
        seperated_feature={}
        for part in feature_parts:
            key_val=part.split('=')
            seperated_feature[key_val[0]]=key_val[1]
        verb_str=''
        if pos=='V' and (' ' in word_form):
            verb_parts=word_form.strip().split(' ')
            verb_str=word_lemma+'\t'+word_form+'\t'+str(seperated_feature['senID'])+'\t'+str(token_id)
            #fw.write(word_lemma+'\t'+word_form+'\t')
            for part in verb_parts:
                verb_str+=part+'\t'
                #fw.write(part+'\t')
                #fw.flush()
            #verb_str+='\n'
            verbs.append(verb_str)
            #fw.write('\n')
            #fw.flush()
        elif pos=='V' and (' ' not in word_form):#for simple verbs
            simple_v_str=word_lemma+'\t'+word_form
            simple_verbs[word_form]=word_lemma
        elif pos!='V' and (' ' in word_form):#for checking errors in word forms
            #print(line)
            fw1.write(line)
            fw1.flush()
        elif pos=='PUNC':
            punc_l.append(word_form)#+'\t'+str(seperated_feature['senID']))
        number='SING'
        file_type='train'
        if pos=='ADJ' and word_form!=word_lemma:
                result,pronoun,orig_noun=is_potentioal_pronounContained(word_form,word_lemma,line,file_type,number)
                #if result==True: 
                    #log_pron_noun.write(word_form+'\t'+orig_noun+'\t'+word_lemma+'\t'+pronoun+'\t'+rParent+'\t'+str(seperated_feature['senID'])+'\n')
                    #log_pron_noun.flush()
                #else:
                #    fw1.write(word_form+'\t'+word_lemma+'\n')
                #    fw1.flush()
        if pos in list(poss.keys()):
            if cpos not in poss[pos]:
                poss[pos].append(cpos)
        else:
            poss[pos]=[]
            poss[pos].append(cpos)
        if pos=='N' and (cpos not in adjCPos):
            log_adj.write(line+'\n')
            log_adj.flush()
        #if word_form=='و' and rParent=='OBJ':
        #    print(word_form+'\t'+seperated_feature['senID']+'\t'+str(token_id)+'\t'+rParent)
        if pos=='PREM'and word_form=='تعدادی':#word_form!='را' and word_form!='رو': #and word_form!='ی' and word_form!='و':
            idens.append(word_form+'\t'+seperated_feature['senID']+'\t'+str(token_id))
            #print(word_form+'\t'+seperated_feature['senID']+'\t'+str(token_id))
#idens=set(idens)
for k in idens:
    print(k)
#for k in poss:
#    print(k,poss[k])

    #print('****',k,'****')
    #for m in v:
    #    print(m)
    #print('**********')
#verbs=set(verbs)
#for verb in verbs:
#        v_p=verb.strip().split('\t')
#        new_v_str=v_p[0]+'\t'+v_p[1]
#        for i in range(2,len(v_p)):
#            try:
#                lemm=simple_verbs[v_p[i]]
#            except KeyError:
#                lemm='_'
#                print(v_p[i])
#            new_v_str+='\t'+v_p[i]+'\t'+lemm
#        fw.write(new_v_str+'\n')
#        fw.flush()
#punc_l=set(punc_l)
#for s in punc_l:
#    fw3.write(s+'\n')
#    fw3.flush()
fr.close()
fw.close()
fw1.close()
fw3.close()
#log_pron_noun.close()
log_adj.close()