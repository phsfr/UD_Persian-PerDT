dadegan_train_path="Persian_Dependency_Treebank_(PerDT)_V1.1.1/Data/test.conll"#'UD_Persian-Seraji-master/fa_seraji-ud-train.conllu'
fr=open(dadegan_train_path,'r',encoding="utf-8")
trainConll=open("test.conll",'w',encoding="utf-8")
prev_word_f=''
prev_word_pos=''
prev_space=False
prev_pos=''
prev_line=''
sent_i=''
preps=['از','با','بر','به','تا','در','برای', 'مانند', 'همچون', 'مثل']
new_nouns=[]
old_preps=[]
for line in fr.readlines():
    if line.strip()!='': #and (not line.strip().startswith('#')):
        elems=line.strip().split('\t')
        tok_id=elems[0]
        word_form=elems[1]
        word_lemma=elems[2]
        pos=elems[3]
        cpos=elems[4]
        features=elems[5]
        f_sp=features.split('|')
        senID=''
        for f_s in f_sp:
            if 'senID' in f_s:
                senI=f_s.split('=')
                senID=senI[1]
        rParent=elems[7]
        new_line=line
        if rParent=='ADVC' and pos=='PREP' and senID!='28639' and senID!='54138':#word_form=='کنار':
            if word_form in preps:
                new_rel='VPRT'
                new_line='\t'.join(elems[:7])+'\t'+new_rel+'\t'+'\t'.join(elems[8:])+'\n'
            else:
                new_nouns.append(word_form)
                new_pos='N'
                new_cpos='IANM'
                new_line='\t'.join(elems[:3])+'\t'+new_pos+'\t'+new_cpos+'\t'+'\t'.join(elems[5:])+'\n'
        trainConll.write(new_line)
        trainConll.flush()
        no_f=False
        if features=='_':
            no_f=True
        features=features.split('|')
        seperated_feature={}
        senId=''
        if not no_f:
            for part in features:
                key_val=part.split('=')
                seperated_feature[key_val[0]]=key_val[1]
        prev_word_f=word_form
        prev_word_pos=pos
        prev_pos=pos
        prev_line=line
    else:
        if line.strip().startswith('# sent_id'):
            sent_i=line
        trainConll.write('\n')
        trainConll.flush()
        prev_word_f=''
        prev_word_pos=''
        prev_pos=''
        prev_space=False
        prev_line=''
if line.strip()!='':
        elems=line.strip().split('\t')
        tok_id=elems[0]
        word_form=elems[1]
        word_lemma=elems[2]
        pos=elems[3]
        cpos=elems[4]
        features=elems[5]
        f_sp=features.split('|')
        senID=''
        for f_s in f_sp:
            if 'senID' in f_s:
                senI=f_s.split('=')
                senID=senI[1]
        rParent=elems[7]
        new_line=line
        if rParent=='ADVC' and pos=='PREP' and senID!='28639' and senID!='54138':#word_form=='کنار':
            if word_form in preps:
                new_rel='VPRT'
                new_line='\t'.join(elems[:7])+'\t'+new_rel+'\t'+'\t'.join(elems[8:])+'\n'
            else:
                new_nouns.append(word_form)
                new_pos='N'
                new_cpos='IANM'
                new_line='\t'.join(elems[:3])+'\t'+new_pos+'\t'+new_cpos+'\t'+'\t'.join(elems[5:])+'\n'
        trainConll.write(new_line)
        trainConll.flush()
new_nouns=set(new_nouns)
for tok in new_nouns:
    print(tok)
trainConll.close()
fr.close()