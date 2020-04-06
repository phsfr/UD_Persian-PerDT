def process_tree(toks,senId):
    #print(toks)
    for key in toks:
        children=[]
        tok=toks[key]
        #print(toks[key])
        #print('\n')
        if (tok[3]=='PREP' or tok[3]=='POSTP'):
            for ch_key in toks:
                child=toks[ch_key]
                if child[6]==tok[0] and child[7]=='POSDEP':
                    if child[3]!='NOUN':
                        #print('sentID={} child is not noun: {}'.format(senId,child))
                    children.append(child)
            if len(children)==1:
                child=children[0]    
                tok[11]='case'
                tok[10]=child[0]
                child[11]=tok[7]
                child[10]=tok[6]    
            elif len(children)>1:
                print('more than one child for tok {} in sentID={}'.format(tok[0],senId))

dadegan_train_path="Universal_Dadegan/train.conllu"#'UD_Persian-Seraji-master/fa_seraji-ud-train.conllu'
fr=open(dadegan_train_path,'r',encoding="utf-8")
trainConll=open("Universal Dependency Dadegan/train.conllu",'w',encoding="utf-8")

tok_struct={}
for line in fr.readlines():
    if line.strip()!='':
        if line.strip().startswith('#'):
            trainConll.write(line)
            trainConll.flush()   
        else:
            elems=line.strip().split('\t')
            tok_id=elems[0]
            word_form=elems[1]
            word_lemma=elems[2]
            
            pos=elems[3]
            cpos=elems[4]
            features=elems[5]
            hParent=elems[6]
            rParent=elems[7]
            f1=elems[8]
            f2=elems[9]
            #new_line=line
            #trainConll.write(new_line)
            #trainConll.flush()
            no_f=False
            if features=='_':
                no_f=True
            tok_feature=features.split('|')
            seperated_feature={}
            senId=''
            if not no_f:
                for part in tok_feature:
                    key_val=part.split('=')
                    seperated_feature[key_val[0]]=key_val[1]
                senId=seperated_feature['senID']
            dadeg_pos=seperated_feature['dadeg_pos']
            newRP=rParent
            newHP=hParent
                                #0      1         2         3         4    5        6       7       8  9  10    11
            tok_struct[tok_id]=[tok_id,word_form,word_lemma,dadeg_pos,cpos,features,hParent,rParent,f1,f2,newHP,newRP]
    else:
        #print(tok_struct)
        process_tree(tok_struct,senId)
        for key in tok_struct:
            tok=tok_struct[key]
            #print(tok[5])
            newFeature=tok[5]+'|'+'Dadegan_hPar='+tok[6]+'|Dadegan_rP='+tok[7]
            if tok[7]=='_':
                newFeature='_'
            trainConll.write(tok[0]+'\t'+tok[1]+'\t'+tok[2]+'\t'+tok[3]+'\t'+tok[4]+'\t'+newFeature+'\t'+tok[8]+'\t'+tok[9]+'\t'+tok[10]+'\t'+tok[11]+'\n')
            trainConll.flush()
        trainConll.write('\n')
        trainConll.flush()
        tok_struct={}
if line.strip()!='':
        elems=line.strip().split('\t')
        tok_id=elems[0]
        word_form=elems[1]
        word_lemma=elems[2]
        pos=elems[3]
        cpos=elems[4]
        features=elems[5]
        rParent=elems[7]

        process_tree(tok_struct,senId)
        for tok in tok_struct:
            newFeature=tok[5]+'|'+'Dadegan_hPar='+tok[6]+'|Dadegan_rP='+tok[7]
            if tok[7]=='_':
                newFeature='_'
            trainConll.write(tok[0]+'\t'+tok[1]+'\t'+tok[2]+'\t'+tok[3]+'\t'+tok[4]+'\t'+newFeature+'\t'+tok[8]+'\t'+tok[9]+'\t'+tok[10]+'\t'+tok[11]+'\n')
            trainConll.flush()
        
trainConll.close()

fr.close()
