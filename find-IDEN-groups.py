def find_IDEN_group(iden_tok, tok_dic, lin):
    # print(lin)
    hPar = -1
    stack = []
    stack.append(iden_tok)
    noun_group = []
    childs = []
    count = 0
    possible_pos = ['N', 'PUNC', 'IDEN']
    forbid_words = [':', '،', '!', '.', 'و', 'برای', 'دیدن', 'یا']
    while len(stack) != 0:
        count += 1
        h_idx = stack.pop()
        # try:
        noun_group.append(tok_dic[h_idx][0])
        childs.append(int(h_idx))
        # except KeyError:
        #    print('ERROR tok: {} & line {}'.format(h_idx,lin))
        # h_pos=tok_dic[h_idx][1]
        # head_h_idx=tok_dic[h_idx][3]
        # head_h_pos=tok_dic[head_h_idx][1]
        for tok in tok_dic:
            # try:
            if tok_dic[tok][3].strip() == h_idx.strip() and tok_dic[tok][4].strip() != 'APP' and tok_dic[tok][
                4].strip() != 'NCONJ' and tok_dic[tok][1].strip() in possible_pos and tok_dic[tok][
                0].strip() not in forbid_words:  # tok_dic[tok][0]!=':' and tok_dic[tok][0]!='،':#(tok_dic[tok][0]!='که' or tok_dic[tok][0]!=':' or tok_dic[tok][0]!='و'): #or tok_dic[tok][0]!='،':
                stack.append(tok)
                # break
            # except IndexError:
            #    print('ERROR tok: {} & line {}'.format(tok,lin))
        # if h_pos=='N' and (head_h_pos=='N' or head_h_pos=='CONJ'): #there is consecutive nouns and just the last noun is the parent like: تشویقهای تیم محبوبشان OR رفتار و تلاش ذهنیم
        # pro_adj_file.write(' '.join(noun_group[::-1])+'\t'+tok_dic[h_idx][0]+'\t'+tok_dic[h_idx][1]+'\t'+adj_rel+'\t'+elems[6]+'\n')
        # pro_adj_file.flush()
        #    return int(h_idx)
        # break
        # if head_h_pos in posibl_pos:
        if count > 100:
            print('Error in line {}'.format(lin))
            break
        # else:
        # if len(proStack)==0 and (h_pos=='N' or h_pos=='ADJ'):
        # pro_adj_file.write(' '.join(noun_group[::-1])+'\t'+tok_dic[h_idx][0]+'\t'+tok_dic[h_idx][1]+'\t'+adj_rel+'\t'+elems[6]+'\n')
        # pro_adj_file.flush()
        # return int(h_idx)
        # else:
        # print('ERROR: ??')
    # print(childs)
    childs.sort()
    return childs


def process_data(fr):
    forbid_words = [':', '،', '!', '.', 'و', 'برای', 'دیدن', 'یا', 'کرد']
    file_lines = fr.readlines()
    tok_dict = {}
    iden_toks = []
    for indx, line in enumerate(file_lines):
        if line.strip() != '':
            elems = line.strip().split('\t')
            token_id = int(elems[0])
            word_form = elems[1].strip()
            word_lemma = elems[2].strip()
            pos = elems[3]
            cpos = elems[4]
            features = elems[5]
            feature_parts = features.split('|')
            seperated_feature = {}
            number = 'SING'
            aux_v_prefix = ''
            for part in feature_parts:
                key_val = part.split('=')
                if key_val[0] == 'number':
                    number = key_val[1]
                seperated_feature[key_val[0]] = key_val[1]
            hParent = elems[6]
            rParent = elems[7]
            semanticRoles = '\t'.join(elems[8:])
            attachment = seperated_feature['attachment']
            tok_dict[elems[0]] = [word_form.strip(), pos.strip(), cpos.strip(), hParent.strip(), rParent.strip()]
            if pos == 'IDEN' and word_form.strip() not in forbid_words:
                # if tok_dict[hParent][0].strip() not in forbid_words:
                # iden_toks.append(hParent)#(elems[0])
                # else:
                iden_toks.append(elems[0])
        else:
            for iden in iden_toks:
                iden_tok = iden
                iden_par = tok_dict[iden][3]
                if tok_dict[iden_par][0].strip() not in forbid_words:
                    iden_tok = iden_par
                group_txt = ''
                lin = seperated_feature['senID'] + ' ' + iden
                childs = find_IDEN_group(iden_tok, tok_dict, lin)
                # print(childs)
                for ch in childs:
                    group_txt += tok_dict[str(ch)][0] + ' '
                print(group_txt.strip())
            tok_dict = {}
            iden_toks = []


dadegan_train_path = "Persian_Dependency_Treebank_(PerDT)_V1.1.1/Data/train.conll"
fr = open(dadegan_train_path, 'r', encoding="utf-8")
process_data(fr)
