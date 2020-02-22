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
                    return True,pron[1:],orig_noun+'ی' #concating ی to the noun instead of pronoun => زانویم = زانوی+م
            if (orig_noun.endswith('ا') or orig_noun.endswith('و')) and orig_noun==lemma:
                return True,pron[1:],orig_noun+'ی'
   
    return False,'',''

def process_line_to_write(lin,tokens_ids):
    elems=lin.strip().split('\t')
    old_tok_id=elems[0]
    if '-' in old_tok_id:
        old_tok_parts=old_tok_id.split('-')
        new_token_id=tokens_ids[int(old_tok_parts[0])]
        lin=str(new_token_id)+'-'+old_tok_parts[1]+'\t'+'\t'.join(elems[1:])+'\n'
    else:
        if old_tok_id=='X':#remove X from the begining of the line (token id shouldn't change but head of parent could be changed)
            new_hParent_id=tokens_ids[int(elems[7])]
            lin=elems[1]+'\t'+'\t'.join(elems[2:7])+'\t'+str(new_hParent_id)+'\t'+'\t'.join(elems[8:])+'\n'
        elif old_tok_id=='Y': #remove Y from the begining of the line (token id of both previous token and the next one could be updated)
            old_tok_parts=elems[1].split('-')
            new_first_token_id=tokens_ids[int(old_tok_parts[0])]
            new_second_token_id=tokens_ids[int(old_tok_parts[1])]
            lin=str(new_first_token_id)+'-'+str(new_second_token_id)+'\t'+'\t'.join(elems[2:])+'\n'         
        else:
            new_hParent_id=tokens_ids[int(elems[6])]
            new_token_id=tokens_ids[int(old_tok_id)]
            lin=str(new_token_id)+'\t'+'\t'.join(elems[1:6])+'\t'+str(new_hParent_id)+'\t'+'\t'.join(elems[7:])+'\n'
    return lin
    
def convert_to_universal(old_fileP,new_fileP,file_type):
    fr=open(old_fileP,'r',encoding="utf-8")
    UD_file=open(new_fileP,'w',encoding="utf-8")
    multi_words=[]
    sent_lines=[]
    sent_text=''
    sent_id=1
    contain_multiWord=False
    num_concate_prons=0
    already_parent_changed=[]
    tokens_ids={0:0} #by default insert 0 for root
    prev_attachment=''
    prev_token_id=-1
    prev_word_form=''
    for line in fr.readlines():
        if line.strip()!='':
            elems=line.strip().split('\t')
            token_id=int(elems[0])
            word_form=elems[1].strip()
            word_lemma=elems[2].strip()
            pos=elems[3]
            cpos=elems[4]
            features=elems[5]
            feature_parts=features.split('|')
            seperated_feature={}
            number='SING'
            for part in feature_parts:
                key_val=part.split('=')
                if key_val[0]=='number':
                    number=key_val[1]
                seperated_feature[key_val[0]]=key_val[1]
            hParent=elems[6]
            rParent=elems[7]
            semanticRoles='\t'.join(elems[8:])
            attachment=seperated_feature['attachment']
            tokens_ids[token_id]=token_id
            if contain_multiWord:
                tokens_ids[token_id]=token_id+num_concate_prons      
            if pos=='PUNC' or attachment=='PRV': #punctuations should be concated to the previous word
                sent_text=sent_text+word_form
            elif '_' in word_form: #to replace _ in multiwords with space or half-space (now replace with space)
                sent_text=sent_text+' '+word_form.replace('_',' ')
            elif attachment=='PRV':#already splited multi-words should be written without full space (half or zero space)
                if word_form=='ام' or word_form=='ایم' or word_form=='ای' or word_form=='اند' or word_form=='اش' or word_form=='اید':
                    sent_text=sent_text+'u200c'+word_form
                else: 
                    sent_text=sent_text+word_form
            else:
                sent_text=sent_text+' '+word_form
                
            #normalizing already splited multiwords
            if attachment=='NXT':
                prev_attachment='NXT'
                prev_token_id=token_id
                prev_word_form=word_form
            if attachment=='PRV' and prev_attachment=='NXT':
                other_parts='\t'.join("_"*len(elems[2:]))
                if word_form=='ام' or word_form=='ایم' or word_form=='ای' or word_form=='اند' or word_form=='اش' or word_form=='اید': #insert half-space for cases such as شرمنده ام
                    new_word_form=prev_word_form+'\u200c'+word_form
                else:
                    new_word_form=prev_word_form+word_form
                multi_words.append(new_word_form)
                new_line_multiword='Y'+'\t'+str(prev_token_id)+'-'+str(token_id)+'\t'+new_word_form+'\t'+other_parts+'\n'
                last_line=sent_lines.pop(-1)
                sent_lines.append(new_line_multiword)
                sent_lines.append(last_line)
            
            #seperating concatinated pronouns to nouns 
            line_added=False
            if pos=='N' and word_form!=word_lemma:
                result,pronoun,orig_noun=is_potentioal_pronounContained(word_form,word_lemma,line,file_type,number)
                if result==True: 
                    log_pron_noun.write(word_form+'\t'+orig_noun+'\t'+word_lemma+'\t'+pronoun+'\n')
                    log_pron_noun.flush()
                    num_concate_prons=num_concate_prons+1
                    pron_id=token_id+num_concate_prons
                    other_parts='\t'.join("_"*len(elems[2:]))
                    added_line_multiword=str(token_id)+'-'+str(pron_id)+'\t'+word_form+'\t'+other_parts+'\n'
                    eddited_line=str(token_id)+'\t'+orig_noun+'\t'+word_lemma+'\t'+pos+'\t'+cpos+'\t'+features+'\t'+hParent+'\t'+rParent+'\t'+semanticRoles+'\n'
                    added_line='X'+'\t'+str(pron_id)+'\t'+pronoun+'\t'+pro_info[pronoun][0]+'\t'+'PRON'+'\t'+'PRO'+'\t'+'Number='+pro_info[pronoun][1]+"|Person="+pro_info[pronoun][2]+'|PronType=Prs'+'\t'+str(token_id)+'\t'+'nmod:poss'+'\t'+semanticRoles+'\n'
                    sent_lines.append(added_line_multiword)
                    sent_lines.append(eddited_line)
                    sent_lines.append(added_line)
                    line_added=True 
                    contain_multiWord=True   
            
            #seperating multipart verbs
            if pos=='V' and (' ' in word_form): 
                verb_parts=word_form.strip().split(' ')  
                if len(verb_parts)==2: #normalizing two part verbs 
                    v_first_part=verb_parts[0]
                    v_first_part_form=v_first_part.strip()
                    v_second_part=verb_parts[1]
                    v_second_part_form=v_second_part.strip()
                    future_form=False
                    aux_form=False
                    polarity=''
                    mood=''
                    aux_dep_rol='aux'
                    if v_first_part.startswith('ن') and v_first_part[1:] in list(future_base.keys()): #verb is indicative future (tma=AY) in negative form like نخواهم گفت
                        future_form=True
                        polarity='|Polarity=Neg'
                        v_first_part=v_first_part[1:]
                    elif v_first_part in list(future_base.keys()):#verb is indicative future (tma=AY) in positive form like خواهم گفت
                        future_form=True
                    elif v_second_part in list(tobe_base.keys()):#verb is indicative Pluperfect (tma=GB) like گفته بودند. in this form, negation is conjugated with PP part: نگفته بودند
                        aux_form=True
                        aux_number=tobe_base[v_second_part][0]
                        aux_count=tobe_base[v_second_part][1]
                        tense='Past'
                        fpos='V_PA'
                        aux_lemma='بود#باش'
                    elif v_second_part in list(become_base.keys()):#verb is Subjunctive Preterite (tma=GEL) like گفته باشم. in this form, negation is conjugated with PP part: نگفته باشم
                        aux_form=True
                        aux_number=become_base[v_second_part][0]
                        aux_count=become_base[v_second_part][1]
                        mood='Mood=Sub|'
                        tense='Pres'
                        fpos='V_PRS'
                        aux_lemma='بود#باش'
                    elif v_second_part_form=='است':#verb is indicative Preterite (tma=GS) like گفته است
                        aux_form=True
                        tense='Pres'
                        fpos='V_PRS'
                        aux_number='Sing'
                        aux_count='3'
                        aux_lemma='#است'
                    elif v_second_part in list(shod_base.keys()):#verb is indicative Preterite (tma=GS) like گفته شدند.
                        aux_form=True
                        aux_number=shod_base[v_second_part][0]
                        aux_count=shod_base[v_second_part][1]
                        tense='Past'
                        fpos='V_PA'
                        aux_lemma='کرد#کن'
                        aux_dep_rol+=':pass'
                    #elif v_second_part.startswith('ن') and v_second_part[1:] in list(shod_base.keys()):#verb is indicative Preterite (tma=GS) like گفته شدند.
                    #    polarity='|Polarity=Neg'
                    #    v_second_part=v_second_part[1:]
                    if future_form: #verb is indicative future (tma=AY) like خواهم گفت
                        num_count=future_base[v_first_part]
                        num_concate_prons=num_concate_prons+1
                        tokens_ids[token_id]=token_id+num_concate_prons 
                        v_p_id=tokens_ids[token_id]-1
                        v_bon=word_lemma.strip().split('#')
                        #if v_bon[0]!=v_second_part and v_second_part!='شد':
                            #print(line)
                        #    print('ERROR: bon mazi is not the same as verb core: ',v_second_part,v_bon)
                        added_line_verb='X'+'\t'+str(v_p_id)+'\t'+v_first_part_form+'\t'+'خواست#خواه'+'\t'+'AUX'+'\t'+'V_AUX'+'\t'+'Number='+future_base[v_first_part][0]+'|Person='+future_base[v_first_part][1]+polarity+'|Tense=Fut|VerbForm=Fin'+'\t'+str(token_id)+'\t'+'aux'+'\t'+'_'+'\t'+'_'+'\n'
                        eddited_line=str(token_id)+'\t'+v_second_part+'\t'+word_lemma+'\t'+'VERB'+'\t'+'V_PA'+'\t'+'Number=Sing|Person=3|Tense=Past'+'\t'+hParent+'\t'+rParent+'\t'+semanticRoles+'\n'
                        sent_lines.append(added_line_verb)
                        sent_lines.append(eddited_line)
                        line_added=True 
                        contain_multiWord=True 
                    if aux_form:
                        num_concate_prons=num_concate_prons+1
                        v_p_id=tokens_ids[token_id]+1
                        #v_bon=word_lemma.strip().split('#')
                        #v_bon_past=''.join(v_bon[:-1])
                        #elif v_second_part_form=='است':#verb is indicative Preterite (tma=GS) like گفته است
                        #    if v_bon_past==v_first_part[:-1] or 'ن'+v_bon_past==v_first_part[:-1] or ((v_first_part[:-1]!='شد' or v_first_part[:-1]!='نشد') and v_bon_past=='کرد'):
                        #        exc=False
                        #    else:
                        #        print(line)
                        #        print('ERROR: bon mazi is not the same as verb core: ',v_first_part,v_bon_past)
                        eddited_line=str(token_id)+'\t'+v_first_part+'\t'+word_lemma+'\t'+'VERB'+'\t'+'V_PP'+'\t'+'Number=Sing|Person=3|Tense=Part'+'\t'+hParent+'\t'+rParent+'\t'+semanticRoles+'\n'
                        added_line_verb='X'+'\t'+str(v_p_id)+'\t'+v_second_part_form+'\t'+aux_lemma+'\t'+'VERB'+'\t'+fpos+'\t'+mood+'Number='+aux_number+'|Person='+aux_count+polarity+'|Tense='+tense+'\t'+str(token_id)+'\t'+aux_dep_rol+'\t'+'_'+'\t'+'_'+'\n'
                        sent_lines.append(eddited_line)
                        sent_lines.append(added_line_verb)
                        line_added=True 
                        contain_multiWord=True 
                
            if line_added==False:
                sent_lines.append(line)
        
        else:
            UD_file.write('# sent_id = '+file_type+'-s'+str(sent_id)+'\n')
            UD_file.write('# text = '+sent_text.strip()+'\n')
            for lin in sent_lines:
                lin=process_line_to_write(lin,tokens_ids)
                UD_file.write(lin)
                UD_file.flush()
            UD_file.write('\n')
            sent_id=sent_id+1
            sent_lines=[]
            sent_text=''
            contain_multiWord=False
            num_concate_prons=0
            parent_changed=[]
            tokens_ids={0:0}
        
    if len(sent_lines)>0: #to write down the last sentence 
            UD_file.write('# sent_id = s'+str(sent_id)+'\n')
            UD_file.write('# text = '+sent_text.strip()+'\n')
            for lin in sent_lines:
                lin=process_line_to_write(lin,tokens_ids)    
                UD_file.write(lin)
                UD_file.flush() 
    fr.close()
    UD_file.close()
    
if __name__=="__main__":
    log_pron_noun=open("pronoun-nouns.txt",'w',encoding="utf-8")
    #pronouns=['م','ت','ش','شان','تان','مان',  'ام', 'ات', 'اش',  'یم', 'یت', 'یش', 'یشان', 'یتان', 'یمان']
    base_prons=['م','ت','ش','شان','تان','مان']
    he_ye_prons=['ام', 'ات', 'اش','شان','تان','مان']
    alef_vav_prons=['یم', 'یت', 'یش', 'یشان', 'یتان', 'یمان']
                #lemma,number,person
    pro_info={'م':['من','Sing','1']    , 'ام':['من','Sing','1'] , 'ت':['تو','Sing','2'] , 'ات':['تو','Sing','2'] , 'ش':['او','Sing','3'], 'اش':['او','Sing','3'] , 'مان':['ما','Plur','1'] , 'تان':['شما','Plur','2'] , 'شان':['آنها','Plur','3']}
                   #plural  singular
    mokasar_nouns={'روایات':'روایت', 'ابیات':'بیت', 'نعمات':'نعمت','زحمات':'زحمت','تجربیات':'تجربه','جزئیات':'جزء'}
                       #number,person
    future_base={'خواهم':['Sing','1'], 'خواهی':['Sing','2'],'خواهد':['Sing','3'],'خواهیم':['Plur','1'],'خواهید':['Plur','2'],'خواهند':['Plur','3']}
                      #number,person
    tobe_base={'بودم':['Sing','1'], 'بودی':['Sing','2'],'بود':['Sing','3'],'بودیم':['Plur','1'],'بودید':['Plur','2'],'بودند':['Plur','3']}
                       #number,person
    become_base={'باشم':['Sing','1'], 'باشی':['Sing','2'],'باشد':['Sing','3'],'باشیم':['Plur','1'],'باشید':['Plur','2'],'باشند':['Plur','3']}
                    #number,person
    shod_base={'شدم':['Sing','1'], 'شدی':['Sing','2'],'شد':['Sing','3'],'شدیم':['Plur','1'],'شدید':['Plur','2'],'شدند':['Plur','3']}
                      #number,person
    shavad_base={'شوم':['Sing','1'], 'شوی':['Sing','2'],'شود':['Sing','3'],'شویم':['Plur','1'],'شوید':['Plur','2'],'شوند':['Plur','3']}
    dadegan_train_path="Persian_Dependency_Treebank_(PerDT)_V1.1.1/Data/train.conll"
    dadegan_test_path="Persian_Dependency_Treebank_(PerDT)_V1.1.1/Data/test.conll"
    dadegan_dev_path="Persian_Dependency_Treebank_(PerDT)_V1.1.1/Data/dev.conll"
    UD_train_file="Universal_Dadegan/train.conllu"
    UD_test_file="Universal_Dadegan/test.conllu"
    UD_dev_file="Universal_Dadegan/dev.conllu"
    convert_to_universal(dadegan_train_path,UD_train_file,"train")
    convert_to_universal(dadegan_test_path,UD_test_file,"test")
    convert_to_universal(dadegan_dev_path,UD_dev_file,"dev")
    log_pron_noun.close()