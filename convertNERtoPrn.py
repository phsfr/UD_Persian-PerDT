import unicodedata


def find_foreign(word):
    except_words = ['5شنبه‌ها', 'ان‌شاا…', '[واحد', "''ایمیل''", '55گانه', '!‌', '"مرد"', '"زن"', 'غیرشاعر-', '-شاعر',
                    '"اثر"', '7پله‌ای', 'م.', 'B.C', 'B.C', 'پ.م']
    hyphen_free = word.replace('-', '')
    slash_free = word.replace('/', '')
    dot_free = word.replace('.', '')
    cent_free = word.replace('%', '')
    quote_free = word.replace(':', '')
    # not_allowed_chars=[',','×','ْ','٫']
    if word.isnumeric() or len(
            word) <= 1 or word in except_words or hyphen_free.isnumeric() or dot_free.isnumeric() or slash_free.isnumeric() or quote_free.isnumeric() or cent_free.isnumeric():
        return False
    for ch in word:
        if ch == '\u200c':
            continue
        name = unicodedata.name(ch).lower()
        if ('arabic' not in name) and ('persian' not in name):
            if ',' in word or '×' in word or 'ْ' in word or '٫' in word:
                return False
            else:
                # print(word)
                return True


def main_process(fr, fw):
    lines = fr.readlines()
    possible_tags = ['LOC', 'PER', 'ORG']
    for line in lines:
        if line.strip() != '':
            tok_p = line.strip().split('\t')
            Ner_tag = tok_p[1]
            new_tag = 'O'
            old_tag = 'O'
            strg = tok_p[0]
            is_foreign = find_foreign(strg.strip())
            if Ner_tag != 'O':
                n_tag = Ner_tag.split('-')
                old_tag = n_tag[1]
                if n_tag[1] in possible_tags:
                    # print(n_tag[0])
                    if tok_p[0].strip() == '(':  # if tok_p[0].strip()=='(' and prev_tag=='PER':
                        ind = lines.index(line)
                        next_toks = lines[ind + 1].strip().split('\t')
                        # print(next_toks)
                        if next_toks[1].strip() == 'O':
                            new_tag = 'O'
                    else:
                        new_tag = 'PROPN'
            if is_foreign:
                new_tag = 'PROPN'
                if Ner_tag == 'O':
                    Ner_tag = 'Foreign'
            fw.write(tok_p[0] + '\t' + new_tag + '\t' + Ner_tag + '\n')
            fw.flush()
        else:
            fw.write('\n')
            fw.flush()
    if line.strip() != '':
        tok_p = line.strip().split('\t')
        Ner_tag = tok_p[1]
        new_tag = 'O'
        old_tag = 'O'
        if Ner_tag != 'O':
            n_tag = Ner_tag.split('-')
            old_tag = n_tag[1]
            if n_tag[1] in possible_tags:
                if tok_p[0] == '(':  # if tok_p[0].strip()=='(' and prev_tag=='PER':
                    ind = lines.index(line)
                    next_toks = lines[ind + 1].strip().split('\t')
                    if next_toks[1] == 'O':
                        new_tag = 'O'
                else:
                    new_tag = 'PROPN'
        fw.write(tok_p[0] + '\t' + new_tag + '\t' + tok_p[1] + '\n')
        fw.flush()


def post_process(fr, fw):
    droped_words = ['عاشورا', 'قرآن', 'دماوند', 'تورات', 'انجیل', 'ویندوز', 'شاهنامه']
    shamsi_months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن',
                     'اسفند']
    ghamari_months = ['محرم', 'صفر', 'ربیع‌الاول', 'ربیع‌الثانی', 'جمادی‌الاول', 'جمادی‌الثانی', 'رجب', 'شعبان',
                      'رمضان', 'شوال', 'ذیقعده', 'ذیحجه']
    lines = fr.readlines()
    for line in lines:
        if line.strip() != '' and not line.startswith('**********'):
            tok_p = line.strip().split('\t')
            Ner_tag = tok_p[1]
            auto_tag = tok_p[2]
            word = tok_p[0]
            if Ner_tag == 'O' and word in droped_words:
                fw.write(word + '\t' + 'PROPN' + '\t' + 'my' + '\n')
                fw.flush()
            elif 'DAT' in auto_tag:
                # print(word)
                if word.endswith('ماه'):
                    cliped_word = word.replace('ماه', '')
                    if cliped_word.endswith('\u200c'):
                        cliped_word = cliped_word.replace('\u200c', '')
                        if cliped_word in shamsi_months:
                            fw.write(word + '\t' + 'PROPN' + '\t' + auto_tag + '\n')
                            fw.flush()
                            # print(word)
                if word in ghamari_months or word in shamsi_months:
                    fw.write(word + '\t' + 'PROPN' + '\t' + auto_tag + '\n')
                    fw.flush()
            else:
                fw.write(line)
                fw.flush()
        elif line.strip() == '':
            fw.write('\n')
            fw.flush()
        elif line.startswith('**********'):
            fw.write(line)
            fw.flush()


def put_PROPN_on_org(forg, ftagged, fw):
    tagged_lines = ftagged.readlines()
    org_lines = forg.readlines()
    print('org line length {}'.format(len(org_lines)))
    print('tagged line length {}'.format(len(tagged_lines)))
    for i in range(len(org_lines)):
        org = org_lines[i]
        tagged = tagged_lines[i]
        if (org.strip() != '' and tagged.strip() != ''):
            org_parts = org.strip().split('\t')
            org_word = org_parts[1]
            tagged_parts = tagged.strip().split('\t')
            tag_word = tagged_parts[0]
            if tag_word.strip() == org_word.strip():
                fw.write()
                fw.flush()
            else:
                print('Error in alignment')
                print(org_lines[i])
                print(tagged_lines[i])
                break
        elif org.strip() != '' or tagged.strip() != '':
            # print(org.strip()=='')
            # print(tagged.strip()=='')
            print('one line is empty')
            print(org_lines[i])
            print(tagged_lines[i])
            break


def write_align_conll_tagged(forg, ftagged, fw):
    tagged_lines = ftagged.readlines()
    org_lines = forg.readlines()
    i = 0
    for tagged in tagged_lines:
        org = org_lines[i]
        if (org.strip() != '' and tagged.strip() != ''):
            org_parts = org.strip().split('\t')
            org_word = org_parts[1]
            tagged_parts = tagged.strip().split('\t')
            tag_word = tagged_parts[0]
            if tag_word.strip() == org_word.strip():
                if tagged_parts[1] == 'PROPN':
                    fw.write(
                        org.strip() + '\t' + 'isPROPN' + '\n')  # ('\t'.join(org_parts[:3])+'\t'+org_parts[3]+'|PROPN'+'\t'+'\t'.join(org_parts[4:])+'\n')
                else:
                    fw.write(org)  # +'\n')
            else:
                print('ERROR: in this line {}'.format(org))
                break
            i = i + 1
        elif org.strip() == '':
            fw.write('\n')
            i = i + 1


def write_align_conllu_tagged(forg, ftagged, fw):
    tagged_lines = ftagged.readlines()
    org_lines = forg.readlines()
    i = 0
    for tagged in tagged_lines:
        curr_idx = tagged_lines.index(tagged)
        org = org_lines[i]
        while org.startswith('#'):
            i = i + 1
            org = org_lines[i]
        if (org.strip() != '' and tagged.strip() != ''):
            org_parts = org.strip().split('\t')
            org_word = org_parts[1]
            tagged_parts = tagged.strip().split('\t')
            tag_word = tagged_parts[0]
            next_word = ''
            if tag_word.strip() != org_word.strip():
                next_line = tagged_lines[curr_idx + 1]
                next_parts = next_line.strip().split('\t')
                next_word = next_parts[0]
            has_multi_part = False
            while tag_word.strip() != org_word.strip():
                # if ' ' not in org_word.strip() or not org_word.strip().startswith(tag_word):
                fw.write(org_word + '\t' + 'O' + '\t' + 'clipped' + '\n')
                fw.flush()
                i = i + 1
                org = org_lines[i]
                org_parts = org.strip().split('\t')
                org_word = org_parts[1]
                print(tag_word)
                print(org_word)
                if next_word.strip() == org_word.strip():
                    fw.write(org_word + '\t' + tagged_parts[1] + '\t' + tagged_parts[2] + '\n')
                    fw.flush()
                    has_multi_part = True
                    break
            # elif ' ' in org_word.strip() and org_word.strip().startswith(tag_word):
            #    tag_word=org_word
            if not has_multi_part:
                fw.write(tag_word + '\t' + tagged_parts[1] + '\t' + tagged_parts[2] + '\n')
                fw.flush()
                i = i + 1
            else:
                i = i - 1
        elif org.strip() == '':
            fw.write('\n')
            fw.flush()
            i = i + 1


def write_align_org_tagged(forg, ftagged, fw):
    tagged_lines = ftagged.readlines()
    org_lines = forg.readlines()
    i = 0
    for tagged in tagged_lines:
        org = org_lines[i]
        if (org.strip() != '' and tagged.strip() != ''):
            org_parts = org.strip().split('\t')
            org_word = org_parts[1]
            tagged_parts = tagged.strip().split('\t')
            tag_word = tagged_parts[0]
            while tag_word.strip() != org_word.strip():
                if len(tag_word) == 1 and len(org_word) == 1 and tag_word == '،':
                    tag_word = org_word
                elif ' ' not in org_word.strip() or not org_word.strip().startswith(tag_word):
                    fw.write(org_word + '\t' + 'O' + '\t' + 'dropped' + '\n')
                    fw.flush()
                    i = i + 1
                    org = org_lines[i]
                    org_parts = org.strip().split('\t')
                    org_word = org_parts[1]
                    print(tag_word)
                    print(org_word)
                elif ' ' in org_word.strip() and org_word.strip().startswith(tag_word):
                    tag_word = org_word
            fw.write(tag_word + '\t' + tagged_parts[1] + '\t' + tagged_parts[2] + '\n')
            fw.flush()
            i = i + 1
        elif org.strip() == '':
            fw.write('\n')
            fw.flush()
            i = i + 1


if __name__ == "__main__":
    fileName = 'Dadegan with NER tag/train_with_PROPN_tag_handCorrected.txt'
    orgFileN = 'Dadegan with NER tag/train_with_NER_tag.txt'
    # fr=open(fileName,'r',encoding="utf-8")
    # fw=open('Dadegan with NER tag/train_with_PROPN_tag.txt','w',encoding="utf-8")
    # fTagged=open('Dadegan with NER tag/train_with_PROPN_tag.txt','r',encoding="utf-8")
    for file_name in ["train", "dev", "test"]:
        print(file_name)
        fOrg = open('Persian_Dependency_Treebank_(PerDT)_V1.1.1/Data/' + file_name + '.conll', 'r', encoding="utf-8")
        # fOrgconllu=open('Universal_Dadegan/train.conllu','r',encoding="utf-8")
        # fwCorrect=open('Dadegan with NER tag/train_with_PROPN_Corrected.txt','w',encoding="utf-8")
        frCorrect = open('Dadegan with NER tag/' + file_name + '_with_PROPN_Corrected.txt', 'r', encoding="utf-8")
        # fw=open('Dadegan with NER tag/train_aligned_conllu.txt','w',encoding="utf-8")
        fw_aligned = open('Dadegan with NER tag/' + file_name + '_aligned_morecolumn.conll', 'w', encoding="utf-8")
        # align_org_tagged(fOrg,fTagged)
        # write_align_org_tagged(fOrg,fTagged,fwCorrect)
        # post_process(fr,fw)
        write_align_conll_tagged(fOrg, frCorrect, fw_aligned)
        # write_align_conllu_tagged(fOrgconllu,frCorrect,fw)
        # fTagged.close()
        fOrg.close()
    # fr.close()
    # fw.close()
