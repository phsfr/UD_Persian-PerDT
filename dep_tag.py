def process_tree(toks,senId,i):
    #print(toks)
    i=0
    for key in toks:
        children=[]
        tok=toks[key]
        #print(toks[key])
        #print('\n')

        if tok[7]=='ROOT':
            tok[11]='root'
            tok[10]=tok[6]
        elif tok[7]=='PUNC':
            tok[11]='punct'
            tok[10]=tok[6]
        #elif tok[7]=='APP':
        #    tok[11]='appos'
        #    tok[10]=tok[6]
            
    return i
dadegan_train_path="Universal_Dadegan/train.conllu"#'UD_Persian-Seraji-master/fa_seraji-ud-train.conllu'
fr=open(dadegan_train_path,'r',encoding="utf-8")
trainConll=open("Universal_Dadegan_with_DepRels/train.conllu",'w',encoding="utf-8")

tok_struct={}
i=0
case_inflectedSents=[]
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
            dadeg_pos='_'
            if not no_f:
                for part in tok_feature:
                    key_val=part.split('=')
                    seperated_feature[key_val[0]]=key_val[1]
                senId=seperated_feature['senID']
                dadeg_pos=seperated_feature['dadeg_pos']
            newRP=rParent
            newHP=hParent
                                #0      1         2         3         4    5        6       7       8  9  10    11    12
            tok_struct[tok_id]=[tok_id,word_form,word_lemma,dadeg_pos,cpos,features,hParent,rParent,f1,f2,newHP,newRP,senId]
    else:
        #print(tok_struct)
        m=process_tree(tok_struct,senId,i)
        i+=m
        #print(i)
        for key in tok_struct:
            tok=tok_struct[key]
            #print(tok[5])
            newFeature=tok[5]+'|'+'dadeg_hPar='+tok[6]+'|dadeg_rP='+tok[7]
            if tok[7]=='_':
                newFeature='_'
            trainConll.write(tok[0]+'\t'+tok[1]+'\t'+tok[2]+'\t'+tok[3]+'\t'+tok[4]+'\t'+newFeature+'\t'+tok[10]+'\t'+tok[11]+'\t'+tok[8]+'\t'+tok[9]+'\n')
            trainConll.flush()
        trainConll.write('\n')
        trainConll.flush()
        tok_struct={}
print(i)
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
            newFeature=tok[5]+'|'+'dadeg_hPar='+tok[6]+'|dadeg_rP='+tok[7]
            if tok[7]=='_':
                newFeature='_'
            trainConll.write(tok[0]+'\t'+tok[1]+'\t'+tok[2]+'\t'+tok[3]+'\t'+tok[4]+'\t'+newFeature+'\t'+tok[10]+'\t'+tok[11]+'\t'+tok[8]+'\t'+tok[9]+'\n')
            trainConll.flush()
        
#for sent in case_inflectedSents:
#    print(sent)

trainConll.close()

fr.close()
