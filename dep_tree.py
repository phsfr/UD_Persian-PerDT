import codecs, os, sys
from collections import defaultdict
#import mwe

class Features:
    def __init__(self, feat_str):#process all features in feat_str and put them in dictionary (feat_dict)
        self.feat_str = feat_str
        feat_spl = feat_str.strip().split('|')
        self.feat_dict = dict()
        for feat in feat_spl:
            k,v = feat.split('=')
            self.feat_dict[k] = v

    def __str__(self):
        return self.feat_str

    def feat(self, feat):#get the value of a specific feature (feat)
        return self.feat_dict[feat]
    def add_feat(self,new_feat_dict):
        for key,val in new_feat_dict.items():
            self.feat_dict[key]=val
            self.feat_str+='|'+key+'='+val
    def has_feat(self,feat):
        return feat in self.feat_dict.keys()

class DependencyTree:
    def __init__(self, sent_num, sent_str, words, tags, ftags, heads, labels, lemmas, other_features,semiFinal_tags,final_tags):
        self.sent_descript=sent_num
        self.sent_str=sent_str
        self.words = words
        self.lemmas = lemmas
        self.tags = tags
        self.ftags = ftags
        self.heads = heads
        self.labels = labels
        self.semiFinal_tags=semiFinal_tags
        self.final_tags=final_tags
        self.reverse_tree = defaultdict(set)
        self.other_features = list()
        for f in other_features:
            self.other_features.append(Features(f))

        self.index = dict()
        self.reverse_index = dict()
        for i in range(0,len(words)):
            self.index[i]=i+1
            self.reverse_index[i+1]=i

        # We need to increment index by one, because of the root.
        for i in range(0,len(heads)):
            self.reverse_tree[heads[i]].add(i+1)

    def __eq__(self, other):
        if isinstance(other, DependencyTree):
            return self.conllu_str() == other.conllu_str()
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.conllu_str())

    @staticmethod
    def trav(rev_head,h,visited): #method to traverse tree rev_head: list of heads, h: the head to be visited, visited: the list of already visited heads
        if rev_head.has_key(h):
            for d in rev_head[h]:
                if d in visited:
                    return True
                visited.append(d)
                DependencyTree.trav(rev_head,d,visited)
        return False

    @staticmethod
    def is_full(heads):
        for dep1 in range(1,len(heads)+1):
            head1=heads[dep1-1]
            if head1<0:
                return False
        return True

    @staticmethod
    def is_nonprojective_arc(d1,h1,d2,h2):
        if d1 > h1 and h1 != h2:
            if (d1 > h2 and d1 < d2 and h1 < h2) or (d1 < h2 and d1 > d2 and h1 < d2):
                return True
        if d1 < h1 and h1 != h2:
            if (h1 > h2 and h1 < d2 and d1 < h2) or (h1 < h2 and h1 > d2 and d1 < d2):
                return True
        return False

    @staticmethod
    def get_nonprojective_arcs(heads):
        non_projectives = set()
        for i in range(len(heads)):
            if i in non_projectives:
                continue
            dep1,head1 = i+1,heads[i]
            for j in range(len(heads)):
                if i==j: continue
                dep2,head2 = j+1, heads[j]
                if DependencyTree.is_nonprojective_arc(dep1, head1, dep2, head2):
                    non_projectives.add(i+1)
                    non_projectives.add(j+1)
        return non_projectives

    @staticmethod
    def is_projective(heads):
        rev_head=defaultdict(list)
        for dep1 in range(1,len(heads)+1):
            head1=heads[dep1-1]
            if head1>=0:
                rev_head[head1].append(dep1)

        visited=list()
        #print rev_head
        if DependencyTree.trav(rev_head,0,visited):
            return False
        if len(visited)<len(heads) and DependencyTree.is_full(heads):
            return False

        rootN=0
        for dep1 in range(1,len(heads)+1):
            head1=heads[dep1-1]
            if head1==0:
                rootN+=1
            if rev_head.has_key(dep1):
                for d2 in rev_head[dep1]:
                    if (d2<head1 and head1<dep1) or (d2>head1 and head1>dep1) and head1>0:
                        return False

            for dep2 in range(1,len(heads)+1):
                head2=heads[dep2-1]
                if head1==-1 or head2==-1:
                    continue
                if dep1>head1 and head1!=head2:
                    if dep1>head2 and dep1<dep2 and head1<head2:
                        return False
                    if dep1<head2 and dep1>dep2 and head1<dep2:
                        return False
                if dep1<head1 and head1!=head2:
                    if head1>head2 and head1<dep2 and dep1<head2:
                        return False
                    if head1<head2 and head1>dep2 and dep1<dep2:
                        return False
        if rootN<1:
            return False
        return True


    @staticmethod
    def load_tree_from_conllu_string(tree_str):
        """
        Loads a conllu string into a DependencyTree object.
        """
        lines = tree_str.strip().split('\n')
        mw_line=list()
        words = list()
        tags = list()
        heads = list()
        labels = list()
        lemmas = list()
        ftags = list()
        line_idx={}
        semiFinal_tags = list()
        final_tags = list()
        sent_descript=lines[0]
        sent_str=lines[1]
        other_features = list()
        for i in range(2,len(lines)):#for jumping over two first lines (one is sentence number & other is sentence's string
            spl = lines[i].split('\t')
            line_idx[i-2]=spl[0]
            if '-' in spl[0]:
                mw_line.append(lines[i].strip('\n').strip())
                continue
            words.append(spl[1])          #word form
            lemmas.append(spl[2])         #lemma
            tags.append(spl[3])           #pos
            ftags.append(spl[4])          #cpos
            heads.append(int(spl[6]))     #dep head
            other_features.append(spl[5]) #featurs
            labels.append(spl[7])         #dep_rol
            semiFinal_tags.append(spl[8]) #semi final tag 
            final_tags.append(spl[9])     #last tag

        tree = DependencyTree(sent_descript, sent_str, words, tags, ftags, heads, labels, lemmas, other_features,semiFinal_tags,final_tags)
        return tree

    @staticmethod
    def load_trees_from_conllu_file(file_str):
        """
        Loads a conll file into a list of DependencyTree object.
        """
        tree_list = list()
        [tree_list.append(DependencyTree.load_tree_from_conllu_string(tree_str)) for tree_str in open(file_str,'r',encoding='utf-8').read().strip().split('\n\n')]#codecs.
        return tree_list


    def conllu_str(self):
        """
        Converts a DependencyTree object to Conll string.
        """
        lst = list()
        lst.append(self.sent_descript) #adding first line as sentence number
        lst.append(self.sent_str)      #adding second line as sentence string
        for i in range(len(self.words)):
            feats = [str(i+1),self.words[i],self.lemmas[i], self.tags[i],self.ftags[i],str(self.other_features[i]),str(self.heads[i]),self.labels[i],self.semiFinal_tags[i],self.final_tags[i]]
            # ln = str(i+1) +'\t'+self.words[i]+'\t'+self.lemmas[i]+'\t'+self.tags[i]+'\t'+self.ftags[i]+'\t'+str(self.other_features[i])+'\t'+ str(self.heads[i])+'\t'+self.labels[i]+'\t_\t_'
            lst.append('\t'.join(feats))
        return '\n'.join(lst)

    @staticmethod
    def write_to_conllu(tree_list, output_path):
        """
        Write a list of DependencyTree objects into a conll file.
        """
        writer = open(output_path, 'w',encoding='utf-8')
        for tree in tree_list:
            writer.write(tree.conllu_str().strip()+'\n\n')
        writer.close()
    
    def convert_pos(self, universal_tree, ner_tree):
        """
        self is the original tree, the two others are suggestions from
        auto-tagged and auto-ner.
        """
        pass
    def find_all_children(self,idx):
        return [key for key,val in enumerate(self.heads) if val==idx]
    def find_children_with_role(self,h_idx,dep_role):
        return [key for key,val in enumerate(self.heads) if val==h_idx and self.labels[key]==dep_role]
    def find_children_with_pos(self,h_idx,child_pos):
        return [key for key,val in enumerate(self.heads) if val==h_idx and self.tags[key]==child_pos]
    def exchange_child_parent(self,parent_idx,child_idx,new_rel_par,new_rel_child=None):
        old_child_h=self.heads[child_idx]
        old_child_r=self.labels[child_idx]
        self.other_features[child_idx].add_feat({'dadeg_h':str(old_child_h),'dadeg_r':old_child_r})
        self.heads[child_idx]=self.heads[parent_idx]
        self.heads[parent_idx]=self.index[child_idx]
        self.labels[child_idx]=self.labels[parent_idx]
        if new_rel_child is not None:
            self.labels[child_idx]=new_rel_child
        self.labels[parent_idx]=new_rel_par
    def simple_rel_change(old_rel,new_rel):
        pass
    def verb_mood_detection(self,verb_idx):
        dadeg_fpos=self.ftags[verb_idx]
        if 'dadeg_fpos' in self.other_features[verb_idx].feat_dict.keys():
            dadeg_fpos=self.other_features[verb_idx].feat_dict['dadeg_fpos']
        return dadeg_fpos
    def exchange_pars_with_PRD(self,par_idx,par_new_role,child_new_role):
        prd_child=self.find_children_with_role(self.index[par_idx],'PRD')
        all_children=self.find_all_children(self.index[par_idx])
        if len(prd_child)==1:
            for child in all_children:
                if child!=prd_child[0]:
                    old_child_h=self.heads[child]
                    self.heads[child]=prd_child[0]
                    if not self.other_features[child].has_feat('dadeg_h'):
                        self.other_features[child].add_feat({'dadeg_h':str(old_child_h),'dadeg_r':self.labels[child]})
            self.exchange_child_parent(par_idx,prd_child[0],par_new_role,child_new_role)#'mark','advcl')  
        else:
            #print('Error in processing AJUCL!')
            self.labels[par_idx]= child_new_role #'advcl'
            #print(self.other_features[par_idx].feat('senID'))
            #print(self.sent_str) 
    def find_main_noun(self,idx):
        pos=self.tags[idx]
        prev_pos=''
        if pos!='ADJ':
            print('not adj {}'.format(self.sent_descript))
        #print('pos is:::::: {}'.format(pos))
        while pos=='ADJ' or pos=='CCONJ':
            #print('inside while')
            head=self.heads[idx]
            prev_idx=idx
            idx=self.reverse_index[head]
            prev_pos=pos
            pos=self.tags[idx]
            #print('prev pos {} new pos {}'.format(prev_pos,pos))
        #print(pos)
        if pos=='NOUN' or pos=='PROPN':
            #print(self.sent_descript)
            return idx
        elif prev_pos=='ADJ':
            return prev_idx
        else:
            return -1
    def reverse_conj_rels(self,node_idx):
        verb_child=self.find_children_with_pos(self.index[node_idx],'VERB')
        #print(verb_child)
        #if len(verb_child)>1:
        #    print('ERROR: more than one verb child for VCONJ rel with main node {} with childs {} in sent {}'.format(self.index[node_idx],verb_child,self.sent_descript))
        children_chain=[]
        #children_chain.append(verb_child[0])
        while len(verb_child)>0:
            #if len(verb_child)>1:
            #    print('ERROR: more than one verb child for VCONJ rel with inside node {} with childs {} in sent {}'.format(self.index[node_idx],verb_child,self.sent_descript))
            node_idx=verb_child[0]
            children_chain.append(verb_child[0])
            verb_child=self.find_children_with_pos(self.index[node_idx],'VERB')
        #print(children_chain)
        #print(children_chain.sort())
        children_chain.sort()
        return children_chain
    def node_assign_new_role(self,node_idx,par_idx,new_role):
        old_head=self.heads[node_idx]
        old_role=self.labels[node_idx]
        if not self.other_features[node_idx].has_feat('dadeg_r'):
            self.other_features[node_idx].add_feat({'dadeg_h':str(old_head),'dadeg_r':old_role})
        self.heads[node_idx]=self.index[par_idx]
        self.labels[node_idx]=new_role
        return old_head,old_role
    def first_level_dep_mapping(self):
        simple_dep_map={'ROOT':'root','PUNC':'punct','APP':'appos'}
        for idx in range(0,len(self.words)):
            old_role=self.labels[idx]
            old_head=self.heads[idx]
            old_pos=self.tags[idx]
            rol_changed=False
            dadeg_pos=self.other_features[idx].feat_dict['dadeg_pos']
            if dadeg_pos=='PREP' or dadeg_pos=='POSTP':
                children=self.find_all_children(self.index[idx])
                if len(children)==1:
                    self.exchange_child_parent(idx,children[0],'case')
                rol_changed=True
            if old_role=='VCONJ': #this mapping should take place before که with predicate (VCL) cause #sentID=23816
                children_chain=self.reverse_conj_rels(idx)
                #print(children_chain)
                #print(self.sent_descript)
                for i in range(1,len(children_chain)):
                    child_idx=children_chain[i]
                    old_hd,old_child_r=self.node_assign_new_role(child_idx,children_chain[0],'conj')  
                if len(children_chain)>0:
                    #print('in vconj sent is: {}'.format(self.sent_descript))
                    #print('children_chain is: {}'.format(children_chain))
                    old_hd,old_child_r=self.node_assign_new_role(self.reverse_index[old_head],children_chain[0],'conj') 
                    first_child_h=self.heads[children_chain[0]]
                    first_child_r=self.labels[children_chain[0]]
                    self.heads[children_chain[0]]=old_hd
                    self.labels[children_chain[0]]=old_child_r
                    if not self.other_features[children_chain[0]].has_feat('dadeg_r'):
                        self.other_features[children_chain[0]].add_feat({'dadeg_h':str(first_child_h),'dadeg_r':first_child_r})
                    if old_pos=='CCONJ':
                        self.labels[idx]='cc'
                    rol_changed=True
            if old_role in list(simple_dep_map.keys()):
                self.labels[idx]=simple_dep_map[old_role]
                rol_changed=True
            if rol_changed and not self.other_features[idx].has_feat('dadeg_r'):
                self.other_features[idx].add_feat({'dadeg_h':str(old_head),'dadeg_r':old_role})
    def second_level_dep_mapping(self):
        for idx in range(0,len(self.words)):
            old_role=self.labels[idx]
            old_head=self.heads[idx]
            old_pos=self.tags[idx]
            lemma=self.lemmas[idx]
            rol_changed=False
            if old_role=='AJUCL':
                self.exchange_pars_with_PRD(idx,'mark','advcl')
                rol_changed=True
            if old_role=='VCL':
                self.exchange_pars_with_PRD(idx,'mark','ccomp')
                rol_changed=True                
            if rol_changed and not self.other_features[idx].has_feat('dadeg_r'):
                self.other_features[idx].add_feat({'dadeg_h':str(old_head),'dadeg_r':old_role})
    def third_level_dep_mapping(self):
        #TAM is second level cause: اخطارهای نیروهای دولتی را به هیچ انگاشتند.
        simple_dep_map={'TAM':'xcomp','VPP':'obl','PART':'mark','NPRT':'compound:lvc','NVE':'compound:lvc','ENC':'compound:lvc','LVP':'compound','NE':'compound:lvc','MESU':'nmod','APREMOD':'advmod','ADVC':'obl:arg','AJPP':'obl:arg','NEZ':'obl:arg'} 
        v_copula=['کرد#کن','گشت#گرد','گردید#گرد']
        for idx in range(0,len(self.words)):
            old_role=self.labels[idx]
            old_head=self.heads[idx]
            old_pos=self.tags[idx]
            lemma=self.lemmas[idx]
            rol_changed=False
            dadeg_pos=self.other_features[idx].feat_dict['dadeg_pos']
            #*************************************************
            #**** It's so important to put nsubj mapping after case in second level: because of this example: 
            #(the dep role of child of را is SBJ)
            #وزارت دفاع افغانستان اعلام نمود که تمامی روش‌های جذب افسران در صفوف ارتش ملی افغانستان را بازنگری خواهند کرد.
            #*************************************************
            if old_role=='SBJ': #mapping role of SBJ
                head_idx=self.reverse_index[old_head]
                #if self.tags[head_idx]!='VERB':
                #    print(self.sent_descript)
                #    print(self.sent_str)
                v_mood=self.verb_mood_detection(head_idx)
                v_lemma=self.lemmas[head_idx]
                if v_mood=='PASS' and v_lemma not in v_copula: #for copula verbs listed above, although verb mood is passive but subject is active for Mosnad 
                    self.labels[idx]='nsubj:pass'
                else:
                    self.labels[idx]='nsubj'
                rol_changed=True
            if old_role=='PROG': #mapping role of PROG: مستمرساز
                head_idx=self.reverse_index[old_head]
                v_mood=self.verb_mood_detection(head_idx)
                v_lemma=self.lemmas[head_idx]
                if v_mood=='PASS' and v_lemma not in v_copula: #for copula verbs listed above, although verb mood is passive but subject is active for Mosnad 
                    self.labels[idx]='aux:pass'
                else:
                    self.labels[idx]='aux'
                rol_changed=True
            if old_role=='OBJ': #mapping role of OBJ
                #if self.tags[head_idx]!='VERB':
                #    print(self.sent_descript)
                #    print(self.sent_str)
                head_obj2_children=self.find_children_with_role(old_head,'OBJ2')
                if len(head_obj2_children)>0:
                    self.labels[head_obj2_children[0]]='obj'
                    self.labels[idx]='iobj'
                    rol_changed=True
                else:
                    self.labels[idx]='obj'
                    rol_changed=True
            if old_role=='MOZ' or old_role=='NADV' or old_role=='COMPPP':
                if old_pos=='ADV':
                    self.labels[idx]='advmod'
                    rol_changed=True
                elif old_pos=='NOUN' or old_pos=='PROPN' or old_pos=='PRON':
                    self.labels[idx]='nmod'
                    rol_changed=True                    
                elif old_pos=='ADJ':
                    self.labels[idx]='amod'
                    rol_changed=True  
            if old_role=='NPREMOD' or old_role=='NPOSTMOD':
                new_pos=self.tags[idx]
                if new_pos=='NUM':
                    self.labels[idx]='nummod'
                else:
                    self.labels[idx]='amod'
                rol_changed=True 
            if old_role=='ADV':
                if old_pos=='ADV' or old_pos=='ADJ':
                    self.labels[idx]='advmod'
                    rol_changed=True
                else:
                    if old_pos not in poss:
                    #    print(old_pos,self.sent_descript)
                        poss.append(old_pos)
                        #print(poss)
                    self.labels[idx]='obl'
                    rol_changed=True
            if old_role=='NPP':
                head_idx=self.reverse_index[old_head]
                head_dep=self.labels[head_idx]
                if head_dep=='NVE' or head_dep=='ENC':
                    #print(self.sent_descript)
                    head_of_head=self.heads[head_idx]
                    self.labels[idx]='obl'
                    self.heads[idx]=head_of_head
                else:
                    self.labels[idx]='nmod'
                    #if old_pos!='NOUN' and old_pos!='PROPN':
                    #    print(old_pos,self.sent_descript)
                rol_changed=True
            if old_role=='APOSTMOD':
                old_head_idx=self.reverse_index[old_head]
                head_idx=self.find_main_noun(old_head_idx)
                #print(self.sent_descript)
                #print('word_idex {}'.format(idx))
                #print('old_head {}'.format(old_head))
                #print('return head {}'.format(head_idx))
                #if head_idx!=old_head_idx:
                #    print(self.sent_descript)
                if head_idx==-1:
                    print('heas is -1 in {}'.format(self.sent_descript))
                if head_idx!=-1:
                    self.heads[idx]=self.index[head_idx]
                    if old_pos=='ADV':
                        self.labels[idx]='advmod'
                    elif old_pos=='NOUN' or old_pos=='PROPN' or old_pos=='PRON':
                        self.labels[idx]='nmod'                   
                    elif old_pos=='ADJ':
                        self.labels[idx]='amod'
                    rol_changed=True 

                #else:
                    #print('in vconj sent is: {}'.format(self.sent_descript))
                    #print('children_chain is: {}'.format(children_chain))
            if old_role in list(simple_dep_map.keys()):
                self.labels[idx]=simple_dep_map[old_role]
                rol_changed=True
            if rol_changed and not self.other_features[idx].has_feat('dadeg_r'):
                self.other_features[idx].add_feat({'dadeg_h':str(old_head),'dadeg_r':old_role})
    def convert_tree(self):
        self.first_level_dep_mapping()
        self.second_level_dep_mapping()
        self.third_level_dep_mapping()
                

    @staticmethod
    def fix_mwe_entries(tree_list):
        tmas = dict()
        tmas_count = defaultdict(int)
        mwe_file = os.path.dirname(os.path.abspath(__file__)) + '/mwe_conversion.txt'
        mwe_replacements = {line.strip().split('\t')[0]:[line.strip().split('\t')[1],line.strip().split('\t')[2]] for line in open(mwe_file, 'r')}

        lemma_dict = dict()
        for tree in tree_list:
            for i in range(len(tree.words)):
                word, lemma, pos = tree.words[i], tree.lemmas[i], tree.tags[i]
                if len(word.split(' '))>1:
                    assert pos=='V'
                elif pos=='V' and word not in lemma_dict:
                    lemma_dict[word] = lemma

        count_wrong = 0
        # replacing mwes
        for tree in tree_list:
            for i in range(len(tree.words)):
                word, lemma, pos = tree.words[i], tree.lemmas[i], tree.tags[i]
                tree.words[i], tree.lemmas[i], tree.tags[i] = mwe.fix_word_entries(word, lemma, pos, mwe_replacements, lemma_dict)
                if len(word.split())>1:
                    entry = tree.other_features[i].feat('tma')+'\t'+tree.ftags[i]
                    if tree.other_features[i].feat('tma')=="H" and tree.ftags[i]=='ACT':
                        print(tree.words[i])
                        print(" ".join(tree.words))
                        count_wrong += 1
                    if entry not in tmas:
                        tmas[entry] = tree.words[i]
                    tmas_count[entry] += 1
        for entry in sorted(tmas.keys()):
            print(tmas_count[entry], entry, tmas[entry])
        print(count_wrong)

if __name__ == '__main__':
    input_files = ['Universal_Dadegan/train.conllu','Universal_Dadegan/dev.conllu','Universal_Dadegan/test.conllu']#os.path.abspath(sys.argv[1])
    #universal_file = os.path.abspath(sys.argv[1])
    #ner_file = os.path.abspath(sys.argv[3])
    output_files = ['Universal_Dadegan_with_DepRels/train.conllu','Universal_Dadegan_with_DepRels/dev.conllu','Universal_Dadegan_with_DepRels/test.conllu']#os.path.abspath(sys.argv[2])
    for idx,inp_f in enumerate(input_files):
        tree_list = DependencyTree.load_trees_from_conllu_file(inp_f)
        #print('fixing MWE inconsistencies')
        #DependencyTree.fix_mwe_entries(tree_list)

        #universal_tree_list = DependencyTree.load_trees_from_conllu_file(universal_file)
        #ner_tree_list = DependencyTree.load_trees_from_conll_file(ner_file)

        # First pass: convert POS tags
        #print('fixing POS inconsistencies')
        #for i, tree in enumerate(tree_list):
        #    tree.convert_pos(universal_tree_list[i], ner_tree_list[i])    

        print('fixing tree inconsistencies in {}'.format(inp_f))
        # Second pass: convert tree structure
        poss=[]
        for i, tree in enumerate(tree_list):
            tree.convert_tree()#(universal_tree_list[i])    
        
        DependencyTree.write_to_conllu(tree_list, output_files[idx])
        #poss=set(poss)
        #for p in poss:
        #    print(p)
