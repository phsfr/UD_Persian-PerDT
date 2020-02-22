dadegan_train_path="Persian_Dependency_Treebank_(PerDT)_V1.1.1/Data/train.conll"
fr=open(dadegan_train_path,'r',encoding="utf-8")
fw=open("multiPartVerbs.txt",'w',encoding="utf-8")
fw1=open("multiPartWord.txt",'w',encoding="utf-8")
verbs=[]
simple_verbs={}
simple_v_str=''
for line in fr.readlines():
    if line.strip()!='':
        elems=line.strip().split('\t')
        word_form=elems[1]
        word_lemma=elems[2]
        pos=elems[3]
        verb_str=''
        if pos=='V' and (' ' in word_form):
            verb_parts=word_form.strip().split(' ')
            verb_str=word_lemma+'\t'+word_form+'\t'
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
            fw1.write(line)
            fw1.flush()
verbs=set(verbs)
for verb in verbs:
        v_p=verb.strip().split('\t')
        new_v_str=v_p[0]+'\t'+v_p[1]
        for i in range(2,len(v_p)):
            try:
                lemm=simple_verbs[v_p[i]]
            except KeyError:
                lemm='_'
                print(v_p[i])
            new_v_str+='\t'+v_p[i]+'\t'+lemm
        fw.write(new_v_str+'\n')
        fw.flush()
fr.close()
fw.close()
fw1.close()