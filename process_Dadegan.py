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
                    return True,pron,orig_noun #return True,pron[1:],orig_noun+'ی' #concating ی to the noun instead of pronoun => زانویم = زانوی+م
            if (orig_noun.endswith('ا') or orig_noun.endswith('و')) and orig_noun==lemma:
                return True,pron,orig_noun #return True,pron[1:],orig_noun+'ی'
   
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
        elif old_tok_id=='Z':#remove Z from the begining of the line (neither token id nor head of its parent should change)
            lin=elems[1]+'\t'+'\t'.join(elems[2:])+'\n'
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
def detect_verb_polarity(verb,v_lemma):
    v_parts=v_lemma.strip().split('#')
    correct_v=[]
    wrong_v=[]
    nan_v=[]
    verb_form=verb
    #print(verb_form)                                 #common use of افتادن
    except_lemma={'آورد#آور':['نیاور'],'افتاد#افت':['نیفت','نیافت'],'آمد#آ':['نیای','نیامد'],'افزود#افزا':['نیفز'],'اندیشید#اندیش':['نیندیش'],'انداخت#انداز':['نینداخت','نینداز'],'آفرید#آفرین':['نیافرید'],'آلود#آلا':['نیالود'],'شمرد#شمر':['نمی‌شمارد']}
    polarity='|Polarity=Pos'
    if len(v_parts)==2 and ' ' not in verb: #processing simple verbs with 
        v_past_bon=v_parts[0]
        v_pres_bon=v_parts[1]
        #print(verb)
        if verb.startswith('ن') and  (not verb.startswith(v_past_bon)) and (not verb.startswith(v_pres_bon)) :
            #print(verb)
            verb=verb[1:]
            if verb.startswith('می') and verb.startswith('می'+'\u200c'+v_pres_bon):
                polarity='|Polarity=Neg'
                #print(verb_form)
                correct_v.append(verb_form+'\t'+v_lemma+'\t'+polarity+'\n')
                #print(verb_form)
            elif verb.startswith('می') and verb.startswith('می'+'\u200c'+v_past_bon):
                polarity='|Polarity=Neg'
                correct_v.append(verb_form+'\t'+v_lemma+'\t'+polarity+'\n')
            elif verb.startswith(v_past_bon):
                polarity='|Polarity=Neg'
                correct_v.append(verb_form+'\t'+v_lemma+'\t'+polarity+'\n')
                #print(verb_form+'\t'+v_lemma+'\n')
            elif verb.startswith(v_pres_bon):
                polarity='|Polarity=Neg'
                correct_v.append(verb_form+'\t'+v_lemma+'\t'+polarity+'\n')
            elif v_lemma=='کرد#کن' and (verb.startswith('شد') or verb.startswith('شو') or verb.startswith('می‌شد') or verb.startswith('می‌شو')):
                polarity='|Polarity=Neg'
                correct_v.append(verb_form+'\t'+v_lemma+'\t'+polarity+'\n')
            elif v_lemma in list(except_lemma.keys()):
                verb_registered=False
                for verb_f in except_lemma[v_lemma]:
                    if verb_form.startswith(verb_f):
                        polarity='|Polarity=Neg'
                        correct_v.append(verb_form+'\t'+v_lemma+'\t'+polarity+'\n')
                        verb_registered=True
                        break
                if not verb_registered:
                    print('ERROR: verb without category!',verb_form)
            else:
                wrong_v.append(verb_form+'\t'+v_lemma+'\n')
        elif verb.startswith('نیست') or verb.startswith('نتوان') or verb.startswith('نمی‌توان'):
            polarity='|Polarity=Neg'
            correct_v.append(verb_form+'\t'+v_lemma+'\t'+polarity+'\n')
        else:
            polarity='|Polarity=Pos'
            correct_v.append(verb_form+'\t'+v_lemma+'\t'+polarity+'\n')
    else:
        polarity='|Polarity=NAN'
        nan_v.append(verb_form+'\t'+v_lemma+'\t'+polarity+'\n')
    wrong_v=set(wrong_v)  
    correct_v=set(correct_v) 
    nan_v=set(nan_v)     
    for v in wrong_v:
        fwvw.write(v)
        fwvw.flush()
    for v in correct_v:
        fwvc.write(v)
        fwvc.flush()
    for v in nan_v:
        fwvnan.write(v)
        fwvnan.flush()
    return polarity   
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
            aux_v_prefix=''
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
                    dadegan_senID='|senID='+seperated_feature['senID']
                    added_line_multiword=str(token_id)+'-'+str(pron_id)+'\t'+word_form+'\t'+other_parts+'\n'
                    eddited_line=str(token_id)+'\t'+orig_noun+'\t'+word_lemma+'\t'+pos+'\t'+cpos+'\t'+features+'\t'+hParent+'\t'+rParent+'\t'+semanticRoles+'\n'
                    added_line='X'+'\t'+str(pron_id)+'\t'+pronoun+'\t'+pro_info[pronoun][0]+'\t'+'PRON'+'\t'+'PRO'+'\t'+'number='+pro_info[pronoun][1]+"|person="+pro_info[pronoun][2]+'|pronType=Prs'+dadegan_senID+'\t'+str(token_id)+'\t'+'nmod:poss'+'\t'+semanticRoles+'\n'
                    sent_lines.append(added_line_multiword)
                    sent_lines.append(eddited_line)
                    sent_lines.append(added_line)
                    line_added=True 
                    contain_multiWord=True   
            #detecting verb polarity
            if pos=='V':
                polarity_v=detect_verb_polarity(word_form,word_lemma)
            #seperating multipart verbs
            if pos=='V' and (' ' in word_form): 
                verb_parts=word_form.strip().split(' ')  
                v_first_part=verb_parts[0]
                v_second_part=verb_parts[1]
                verb_lemm_parts=word_lemma.split('#')
                if len(verb_parts)==2: #normalizing two part verbs 
                    v_first_part_form=v_first_part.strip()
                    v_second_part_form=v_second_part.strip()
                    future_form=False
                    aux_form=False
                    shodeh_form=False
                    subj_pres=False #for one occurance of نمیخواهد بماند
                    polarity=''
                    mood=''
                    aux_dep_rol='aux'
                    if v_first_part.startswith('ن') and v_first_part[1:] in list(future_base.keys()): #verb is indicative future (tma=AY) in negative form like نخواهم گفت
                        future_form=True
                        polarity='|polarity=NEG'
                        v_first_part=v_first_part[1:]
                    elif v_first_part in list(future_base.keys()):#verb is indicative future (tma=AY) in positive form like خواهم گفت
                        future_form=True
                    elif len(verb_lemm_parts)>2 and  v_first_part[v_first_part.startswith(verb_lemm_parts[0]) and len(verb_lemm_parts[0]):] in list(future_base.keys()): #for verbs like فراخواهد رسید
                        future_form=True
                        v_first_part=v_first_part[len(verb_lemm_parts[0]):]
                        aux_v_prefix=verb_lemm_parts[0]+'#'
                        word_lemma='#'.join(verb_lemm_parts[1:])
                    elif len(verb_lemm_parts)>2 and v_first_part[v_first_part.startswith(verb_lemm_parts[0]+"ن") and len(verb_lemm_parts[0])+1:] in list(future_base.keys()): #for verbs like فرانخواهد رسید
                        future_form=True
                        polarity='|polarity=NEG'
                        v_first_part=v_first_part[len(verb_lemm_parts[0])+1:]
                        aux_v_prefix=verb_lemm_parts[0]+'#'
                        word_lemma='#'.join(verb_lemm_parts[1:])
                    elif (v_second_part in list(tobe_base.keys()) ) or v_second_part=='بوده':#verb is indicative Pluperfect (tma=GB) like گفته بودند. in this form, negation is conjugated with PP part: نگفته بودند also one occurance of verb گذاشته بوده
                        aux_form=True
                        aux_lemma='بود#باش'
                        if v_second_part=='بوده': #in sent_id=26076
                            aux_number='SING'
                            aux_count='3'
                            tense='Part'
                            fpos='V_PP'
                        else:
                            aux_number=tobe_base[v_second_part][0]
                            aux_count=tobe_base[v_second_part][1]
                            tense='Past'
                            fpos='V_PA' 
                    elif v_second_part in list(become_base.keys()):#verb is Subjunctive Preterite (tma=GEL) like گفته باشم. in this form, negation is conjugated with PP part: نگفته باشم
                        aux_form=True
                        aux_number=become_base[v_second_part][0]
                        aux_count=become_base[v_second_part][1]
                        mood='mood=Sub|'
                        tense='Pres'
                        fpos='V_PRS'
                        aux_lemma='بود#باش'
                        if v_second_part=='باش': #for imparative verb occurance two times in corpus: داشته باش
                            mood=''
                    elif v_second_part_form=='است':#verb is indicative Preterite (tma=GS) like گفته است
                        aux_form=True
                        tense='Pres'
                        fpos='V_PRS'
                        aux_number='SING'
                        aux_count='3'
                        aux_lemma='#است'
                    elif v_second_part in list(shod_base.keys()) or (v_second_part.startswith('ن') and v_second_part[1:] in list(shod_base.keys())) or (v_second_part.startswith('می') and v_second_part[3:] in list(shod_base.keys())) or (v_second_part.startswith('نمی') and v_second_part[4:] in list(shod_base.keys())):#verb is indicative Preterite (tma=GS) in positive or negative form like گفته شدند or گفته نشدند
                        aux_form=True
                        if v_second_part.startswith('نمی'):
                            v_second_part=v_second_part[4:]
                            polarity='|polarity=NEG'
                        elif v_second_part.startswith('ن'):
                            v_second_part=v_second_part[1:]
                            polarity='|polarity=NEG'
                        elif v_second_part.startswith('می'):
                            v_second_part=v_second_part[3:]
                        aux_number=shod_base[v_second_part][0]
                        aux_count=shod_base[v_second_part][1]
                        tense='Past'
                        fpos='V_PA'
                        aux_lemma='کرد#کن'
                        aux_dep_rol+=':pass' #???
                    elif v_second_part in list(shavad_base.keys()) or (v_second_part.startswith('ن') and v_second_part[1:] in list(shavad_base.keys())) or (v_second_part.startswith('ب') and v_second_part[1:] in list(shavad_base.keys())):#verb is Subjunctive Present (tma=HEL) in positive or negative form like گفته شوند or گفته نشوند or گفته بشوند
                        aux_form=True
                        if v_second_part.startswith('ن'):
                            v_second_part=v_second_part[1:]
                            polarity='|polarity=NEG'
                        if v_second_part.startswith('ب'):
                            v_second_part=v_second_part[1:]
                        aux_number=shavad_base[v_second_part][0]
                        aux_count=shavad_base[v_second_part][1]
                        tense='Pres'
                        fpos='V_SUB'
                        aux_lemma='کرد#کن'
                        mood='mood=Sub|'
                        aux_dep_rol+=':pass'
                    elif v_second_part.startswith('می') and v_second_part[3:] in list(shavad_base.keys()) or (v_second_part.startswith('نمی') and v_second_part[4:] in list(shavad_base.keys())):#verb is Subjunctive Present (tma=HEL) in positive or negative form like گفته میشوند or گفته نمیشوند
                        aux_form=True
                        if v_second_part.startswith('ن'):
                            v_second_part=v_second_part[4:] #one more character for '\u200c' or half-space char
                            polarity='|polarity=NEG'
                        else:
                            v_second_part=v_second_part[3:] #one more character for '\u200c' or half-space char
                        aux_number=shavad_base[v_second_part][0]
                        aux_count=shavad_base[v_second_part][1]
                        tense='Pres'
                        fpos='V_PRS'
                        aux_lemma='کرد#کن'
                        aux_dep_rol+=':pass' #؟؟؟
                    elif (v_second_part.startswith('شده') and v_second_part in list(shodeh_base.keys())) or (v_second_part.startswith('نشده') and v_second_part[1:] in list(shodeh_base.keys())):#verb is Indicative Perfect (tma=GN) in positive or negative form like گرفته شده‌اند or گرفته نشده‌اند
                        shodeh_form=True
                        if v_second_part.startswith('نشده'):
                            v_second_part=v_second_part[1:]
                            polarity='|polarity=NEG'
                        aux_number=shodeh_base[v_second_part][0]
                        aux_count=shodeh_base[v_second_part][1]
                    elif v_second_part=='شده' or v_second_part=='نشده' or v_second_part=='می‌شده':#verb is like ساخته شده or ساخته نشده when است is dropped and one occurance of رانده می‌شده
                        shodeh_form=True
                        if v_second_part.startswith('نشده'):
                            polarity='|polarity=NEG'
                        aux_number='SING'
                        aux_count='3'
                    elif word_form=='نمی‌خواهد بماند': #for just one occurance of this verb as exception in subjunctive present 
                        subj_pres=True
                    if future_form: #verb is indicative future (tma=AY) like خواهم گفت
                        num_count=future_base[v_first_part]
                        num_concate_prons=num_concate_prons+1
                        tokens_ids[token_id]=token_id+num_concate_prons 
                        v_p_id=tokens_ids[token_id]-1
                        old_dadegan_info_aux='|senID='+seperated_feature['senID']
                        old_dadegan_info_v='|tma='+seperated_feature['tma']+'|dadeg_pos='+pos+'|dadeg_fpos='+cpos+'|senID='+seperated_feature['senID']
                        added_line_verb='X'+'\t'+str(v_p_id)+'\t'+v_first_part_form+'\t'+aux_v_prefix+'خواست#خواه'+'\t'+'AUX'+'\t'+'V_AUX'+'\t'+'number='+future_base[v_first_part][0]+'|person='+future_base[v_first_part][1]+polarity+'|tense=Fut|verbForm=Fin'+old_dadegan_info_aux+'\t'+str(token_id)+'\t'+'aux'+'\t'+'_'+'\t'+'_'+'\n'
                        eddited_line=str(token_id)+'\t'+v_second_part+'\t'+word_lemma+'\t'+'VERB'+'\t'+'V_PA'+'\t'+'number=SING|person=3|tense=Past'+old_dadegan_info_v+'\t'+hParent+'\t'+rParent+'\t'+semanticRoles+'\n'
                        sent_lines.append(added_line_verb)
                        sent_lines.append(eddited_line)
                        line_added=True 
                        contain_multiWord=True 
                    if aux_form:
                        num_concate_prons=num_concate_prons+1
                        v_p_id=tokens_ids[token_id]+1
                        old_dadegan_info_aux='|senID='+seperated_feature['senID']
                        old_dadegan_info_v='|tma='+seperated_feature['tma']+'|dadeg_pos='+pos+'|dadeg_fpos='+cpos+'|senID='+seperated_feature['senID']
                        eddited_line=str(token_id)+'\t'+v_first_part+'\t'+word_lemma+'\t'+'VERB'+'\t'+'V_PP'+'\t'+'number=SING|person=3|tense=Part'+old_dadegan_info_v+'\t'+hParent+'\t'+rParent+'\t'+semanticRoles+'\n'
                        added_line_verb='X'+'\t'+str(v_p_id)+'\t'+v_second_part_form+'\t'+aux_lemma+'\t'+'AUX'+'\t'+fpos+'\t'+mood+'number='+aux_number+'|person='+aux_count+polarity+'|tense='+tense+old_dadegan_info_aux+'\t'+str(token_id)+'\t'+aux_dep_rol+'\t'+'_'+'\t'+'_'+'\n'
                        sent_lines.append(eddited_line)
                        sent_lines.append(added_line_verb)
                        line_added=True 
                        contain_multiWord=True 
                    if shodeh_form:#verb is Indicative Perfect (tma=GN) in positive or negative form like گرفته شده‌اند or گرفته نشده‌اند
                        num_concate_prons=num_concate_prons+1
                        v_p_id=tokens_ids[token_id]+1
                        old_dadegan_info_aux='|senID='+seperated_feature['senID']
                        old_dadegan_info_v='|tma='+seperated_feature['tma']+'|dadeg_pos='+pos+'|dadeg_fpos='+cpos+'|senID='+seperated_feature['senID']
                        eddited_line=str(token_id)+'\t'+v_first_part+'\t'+word_lemma+'\t'+'VERB'+'\t'+'V_PP'+'\t'+'number=SING|person=3|tense=Part'+old_dadegan_info_v+'\t'+hParent+'\t'+rParent+'\t'+semanticRoles+'\n'
                        added_line_verb='X'+'\t'+str(v_p_id)+'\t'+v_second_part_form+'\t'+'کرد#کن'+'\t'+'AUX'+'\t'+'V_PP'+'\t'+'number='+aux_number+'|person='+aux_count+polarity+'|verbForm=Part'+old_dadegan_info_aux+'\t'+str(token_id)+'\t'+'aux:pass'+'\t'+'_'+'\t'+'_'+'\n'
                        sent_lines.append(eddited_line)
                        sent_lines.append(added_line_verb)
                        line_added=True 
                        contain_multiWord=True 
                    if subj_pres: #for one occurance of the verb نمی‌خواهد بماند in subjunctive present in sent_id=41224
                        num_concate_prons=num_concate_prons+1
                        tokens_ids[token_id]=token_id+num_concate_prons 
                        v_p_id=tokens_ids[token_id]-1
                        old_dadegan_info_aux='|senID='+seperated_feature['senID']
                        old_dadegan_info_v='|tma='+seperated_feature['tma']+'|dadeg_pos='+pos+'|dadeg_fpos='+cpos+'|senID='+seperated_feature['senID']
                        added_line_verb='X'+'\t'+str(v_p_id)+'\t'+v_first_part_form+'\t'+'خواست#خواه'+'\t'+'AUX'+'\t'+'V_AUX'+'\t'+'number=SING|person=3|polarity=NEG'+'|tense=Fut|verbForm=Fin'+old_dadegan_info_aux+'\t'+str(token_id)+'\t'+'aux'+'\t'+'_'+'\t'+'_'+'\n'
                        eddited_line=str(token_id)+'\t'+v_second_part+'\t'+word_lemma+'\t'+'VERB'+'\t'+'V_SUB'+'\t'+'mood=Sub|number=SING|person=3|tense=Pres'+old_dadegan_info_v+'\t'+hParent+'\t'+rParent+'\t'+semanticRoles+'\n'
                        sent_lines.append(added_line_verb)
                        sent_lines.append(eddited_line)
                        line_added=True 
                        contain_multiWord=True 
                if len(verb_parts)==3: #normalizing three part verbs including گفته شده است, گفته شده باشد and گفته شده بود
                    v_third_part=verb_parts[2]
                    mood=''
                    if v_second_part=='شده' or v_second_part=='نشده':
                        #print('ERROR: second part of multipart verb is not shodeh',v_second_part)
                        if v_second_part=='نشده':
                            polarity='|polarity=NEG'
                        if v_third_part=='است':#like گرفته شده است
                            tense='Pres'
                            fpos='V_PRS'
                            aux_lemma='#است'
                            aux_number='SING'
                            aux_count='3'
                        elif v_third_part in list(become_base.keys()):#like گرفته شده باشد
                            aux_number=become_base[v_third_part][0]
                            aux_count=become_base[v_third_part][1]
                            tense='Pres'
                            mood='mood=Sub|'
                            fpos='V_SUB'
                            aux_lemma='بود#باش'
                        elif v_third_part in list(tobe_base.keys()):#like گرفته شده بود
                            aux_number=tobe_base[v_third_part][0]
                            aux_count=tobe_base[v_third_part][1]
                            tense='Past'
                            fpos='V_PA'
                            aux_lemma='بود#باش'
                        num_concate_prons=num_concate_prons+2 #since two aux parts are added 
                        v_p_one_id=tokens_ids[token_id]+1
                        v_p_two_id=v_p_one_id+1
                        old_dadegan_info_aux='|senID='+seperated_feature['senID']
                        old_dadegan_info_v='|tma='+seperated_feature['tma']+'|dadeg_pos='+pos+'|dadeg_fpos='+cpos+'|senID='+seperated_feature['senID']
                        eddited_line=str(token_id)+'\t'+v_first_part+'\t'+word_lemma+'\t'+'VERB'+'\t'+'V_PP'+'\t'+'number=SING|person=3|tense=Part'+old_dadegan_info_v+'\t'+hParent+'\t'+rParent+'\t'+semanticRoles+'\n'
                        added_line_verb_one='X'+'\t'+str(v_p_one_id)+'\t'+v_second_part_form+'\t'+'کرد#کن'+'\t'+'AUX'+'\t'+'V_PP'+'\t'+'number=SING|person=3'+polarity+'|tense=Part'+old_dadegan_info_aux+'\t'+str(token_id)+'\t'+'aux:pass'+'\t'+'_'+'\t'+'_'+'\n'
                        added_line_verb_two='Z'+'\t'+str(v_p_two_id)+'\t'+v_third_part+'\t'+aux_lemma+'\t'+'AUX'+'\t'+fpos+'\t'+mood+'number='+aux_number+'|person='+aux_count+polarity+'|tense='+tense+old_dadegan_info_aux+'\t'+str(v_p_one_id)+'\t'+'aux'+'\t'+'_'+'\t'+'_'+'\n'
                        sent_lines.append(eddited_line)
                        sent_lines.append(added_line_verb_one)
                        sent_lines.append(added_line_verb_two)
                        line_added=True 
                        contain_multiWord=True
                    elif (v_second_part=='خواهد' or v_second_part=='خواهند' or v_second_part=='نخواهد') and v_third_part=='شد':#for verbs like پراکنده خواهد شد
                        aux_num='SING'
                        if v_second_part=='خواهند':
                            aux_num='PLUR'
                        elif v_second_part=='نخواهد':
                            polarity='|polarity=NEG'
                        num_concate_prons=num_concate_prons+2 #since two aux parts are added 
                        v_p_one_id=tokens_ids[token_id]+1
                        v_p_two_id=v_p_one_id+1
                        old_dadegan_info_aux='|senID='+seperated_feature['senID']
                        old_dadegan_info_v='|tma='+seperated_feature['tma']+'|dadeg_pos='+pos+'|dadeg_fpos='+cpos+'|senID='+seperated_feature['senID']
                        eddited_line=str(token_id)+'\t'+v_first_part+'\t'+word_lemma+'\t'+'VERB'+'\t'+'V_PP'+'\t'+'number=SING|person=3|tense=Part'+old_dadegan_info_v+'\t'+hParent+'\t'+rParent+'\t'+semanticRoles+'\n'
                        added_line_verb_one='Z'+'\t'+str(v_p_one_id)+'\t'+v_second_part+'\t'+'خواست#خواه'+'\t'+'AUX'+'\t'+'V_َAUX'+'\t'+'number='+aux_num+'|person=3'+polarity+'|tense=Fut|verbForm=Fin'+old_dadegan_info_aux+'\t'+str(v_p_two_id)+'\t'+'aux'+'\t'+'_'+'\t'+'_'+'\n'
                        added_line_verb_two='X'+'\t'+str(v_p_two_id)+'\t'+v_third_part+'\t'+'کرد#کن'+'\t'+'AUX'+'\t'+'V_PA'+'\t'+'number=SING'+'|person=3'+polarity+'|tense=Past'+old_dadegan_info_aux+'\t'+str(token_id)+'\t'+'aux:pass'+'\t'+'_'+'\t'+'_'+'\n'
                        sent_lines.append(eddited_line)
                        sent_lines.append(added_line_verb_one)
                        sent_lines.append(added_line_verb_two)
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
    fwvw=open("polarity_v_wrong.txt",'w',encoding="utf-8")
    fwvc=open("polarity_v_correct.txt",'w',encoding="utf-8")
    fwvnan=open("polarity_v_nan.txt",'w',encoding="utf-8")
    base_prons=['م','ت','ش','شان','تان','مان']
    he_ye_prons=['ام', 'ات', 'اش','شان','تان','مان']
    alef_vav_prons=['یم', 'یت', 'یش', 'یشان', 'یتان', 'یمان']
                #lemma,number,person
    pro_info={'م':['من','SING','1']    , 'ام':['من','SING','1'] , 'یم':['من','SING','1'] , 'ت':['تو','SING','2'] , 'یت':['تو','SING','2'] , 'ات':['تو','SING','2'] , 'ش':['او','SING','3'], 'یش':['او','SING','3'], 'اش':['او','SING','3'] , 'مان':['ما','PLUR','1'] , 'یمان':['ما','PLUR','1'] , 'تان':['شما','PLUR','2'], 'یتان':['شما','PLUR','2'] , 'شان':['آنها','PLUR','3'] , 'یشان':['آنها','PLUR','3']}
                   #plural  singular
    mokasar_nouns={'روایات':'روایت', 'ابیات':'بیت', 'نعمات':'نعمت','زحمات':'زحمت','تجربیات':'تجربه','جزئیات':'جزء'}
                       #number,person
    future_base={'خواهم':['SING','1'], 'خواهی':['SING','2'],'خواهد':['SING','3'],'خواهیم':['PLUR','1'],'خواهید':['PLUR','2'],'خواهند':['PLUR','3']}
                      #number,person
    tobe_base={'بودم':['SING','1'], 'بودی':['SING','2'],'بود':['SING','3'],'بودیم':['PLUR','1'],'بودید':['PLUR','2'],'بودند':['PLUR','3']}
                       #number,person
    become_base={'باشم':['SING','1'], 'باشی':['SING','2'],'باش':['SING','2'],'باشد':['SING','3'],'باشیم':['PLUR','1'],'باشید':['PLUR','2'],'باشند':['PLUR','3']}
                    #number,person
    shod_base={'شدم':['SING','1'], 'شدی':['SING','2'],'شد':['SING','3'],'شدیم':['PLUR','1'],'شدید':['PLUR','2'],'شدند':['PLUR','3']}
                        #number,person
    shodeh_base={'شده‌ام':['SING','1'], 'شده‌ای':['SING','2'],'شده‌ایم':['PLUR','1'],'شده‌اید':['PLUR','2'],'شده‌اند':['PLUR','3']}
                      #number,person
    shavad_base={'شوم':['SING','1'], 'شوی':['SING','2'],'شود':['SING','3'],'شویم':['PLUR','1'],'شوید':['PLUR','2'],'شوند':['PLUR','3']}
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
    fwvw.close()
    fwvc.close()
    fwvnan.close()