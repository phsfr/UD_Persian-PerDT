import os
from collections import defaultdict
from typing import List, Set


# import mwe

class Features:
    def __init__(self, feat_str):  # process all features in feat_str and put them in dictionary (feat_dict)
        self.feat_str = feat_str
        feat_spl = feat_str.strip().split('|')
        self.feat_dict = dict()
        for feat in feat_spl:
            try:
                k, v = feat.split('=')
                self.feat_dict[k] = v
            except:
                # No feature
                pass

    def __str__(self):
        return self.feat_str

    def feat(self, feat):  # get the value of a specific feature (feat)
        return self.feat_dict[feat]

    def add_feat(self, new_feat_dict):
        for key, val in new_feat_dict.items():
            self.feat_dict[key] = val
            self.feat_str += '|' + key + '=' + val

    def has_feat(self, feat):
        return feat in self.feat_dict.keys()


class DependencyTree:
    def __init__(self, sent_num, sent_str, words, tags, ftags, heads, labels, lemmas, other_features, semiFinal_tags,
                 final_tags, mw_line):
        self.sent_descript = sent_num
        self.sent_str = sent_str
        self.words = words
        self.lemmas = lemmas
        self.tags = tags
        self.ftags = ftags
        self.heads = heads
        self.labels = labels
        self.semiFinal_tags = semiFinal_tags
        self.final_tags = final_tags
        self.mw_line = mw_line
        self.children = defaultdict(set)
        self.other_features = list()
        for f in other_features:
            self.other_features.append(Features(f))

        self.index = dict()
        self.reverse_index = dict()
        for i in range(0, len(words)):
            self.index[i] = i + 1
            self.reverse_index[i + 1] = i

        # We need to increment index by one, because of the root.
        for i in range(0, len(heads)):
            self.children[heads[i]].add(i + 1)

    def rebuild_children(self):
        """
        Reconstruct children dictionary.
        :return:
        """
        # We need to increment index by one, because of the root.
        self.children = defaultdict(set)
        for i in range(0, len(self.heads)):
            self.children[self.heads[i]].add(i + 1)

    def __eq__(self, other):
        if isinstance(other, DependencyTree):
            return self.conllu_str() == other.conllu_str()
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.conllu_str())

    def get_span(self, node_id) -> Set[int]:
        """
        Get all children and subchildren
        :param node_id:
        :return:
        """
        spans = {node_id}
        for child in self.children[node_id]:
            for s in self.get_span(child):
                spans.add(s)
        return spans

    @staticmethod
    def trav(rev_head, h,
             visited):  # method to traverse tree rev_head: list of heads, h: the head to be visited, visited: the list of already visited heads
        if rev_head.has_key(h):
            for d in rev_head[h]:
                if d in visited:
                    return True
                visited.append(d)
                DependencyTree.trav(rev_head, d, visited)
        return False

    @staticmethod
    def is_full(heads):
        for dep1 in range(1, len(heads) + 1):
            head1 = heads[dep1 - 1]
            if head1 < 0:
                return False
        return True

    def is_valid_tree(self):
        spans = self.get_span(0)
        return len(spans) == len(self.words) + 1

    @staticmethod
    def is_nonprojective_arc(d1, h1, d2, h2):
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
            dep1, head1 = i + 1, heads[i]
            for j in range(len(heads)):
                if i == j: continue
                dep2, head2 = j + 1, heads[j]
                if DependencyTree.is_nonprojective_arc(dep1, head1, dep2, head2):
                    non_projectives.add(i + 1)
                    non_projectives.add(j + 1)
        return non_projectives

    @staticmethod
    def is_projective(heads):
        rev_head = defaultdict(list)
        for dep1 in range(1, len(heads) + 1):
            head1 = heads[dep1 - 1]
            if head1 >= 0:
                rev_head[head1].append(dep1)

        visited = list()
        # print rev_head
        if DependencyTree.trav(rev_head, 0, visited):
            return False
        if len(visited) < len(heads) and DependencyTree.is_full(heads):
            return False

        rootN = 0
        for dep1 in range(1, len(heads) + 1):
            head1 = heads[dep1 - 1]
            if head1 == 0:
                rootN += 1
            if rev_head.has_key(dep1):
                for d2 in rev_head[dep1]:
                    if (d2 < head1 and head1 < dep1) or (d2 > head1 and head1 > dep1) and head1 > 0:
                        return False

            for dep2 in range(1, len(heads) + 1):
                head2 = heads[dep2 - 1]
                if head1 == -1 or head2 == -1:
                    continue
                if dep1 > head1 and head1 != head2:
                    if dep1 > head2 and dep1 < dep2 and head1 < head2:
                        return False
                    if dep1 < head2 and dep1 > dep2 and head1 < dep2:
                        return False
                if dep1 < head1 and head1 != head2:
                    if head1 > head2 and head1 < dep2 and dep1 < head2:
                        return False
                    if head1 < head2 and head1 > dep2 and dep1 < dep2:
                        return False
        if rootN < 1:
            return False
        return True

    @staticmethod
    def load_tree_from_conllu_string(tree_str):
        """
        Loads a conllu string into a DependencyTree object.
        """
        lines = tree_str.strip().split('\n')
        mw_line = {}
        words = list()
        tags = list()
        heads = list()
        labels = list()
        lemmas = list()
        ftags = list()
        line_idx = {}
        semiFinal_tags = list()
        final_tags = list()
        sent_descript = lines[0]
        sent_str = lines[1]
        other_features = list()
        for i in range(2, len(
                lines)):  # for jumping over two first lines (one is sentence number & other is sentence's string
            spl = lines[i].split('\t')
            line_idx[i - 2] = spl[0]
            line_indx = spl[0].split('-')
            if '-' in spl[0]:
                mw_line[line_indx[0]] = lines[i].strip('\n').strip()
                continue
            words.append(spl[1])  # word form
            lemmas.append(spl[2])  # lemma
            tags.append(spl[3])  # pos
            ftags.append(spl[4])  # cpos
            heads.append(int(spl[6]))  # dep head
            other_features.append(spl[5])  # featurs
            labels.append(spl[7])  # dep_rol
            semiFinal_tags.append(spl[8])  # semi final tag
            final_tags.append(spl[9])  # last tag

        tree = DependencyTree(sent_descript, sent_str, words, tags, ftags, heads, labels, lemmas, other_features,
                              semiFinal_tags, final_tags, mw_line)
        return tree

    @staticmethod
    def load_trees_from_conllu_file(file_str) -> List:
        """
        Loads a conll file into a list of DependencyTree object.
        """
        tree_list = list()
        [tree_list.append(DependencyTree.load_tree_from_conllu_string(tree_str)) for tree_str in
         open(file_str, 'r', encoding='utf-8').read().strip().split('\n\n')]  # codecs.
        return tree_list

    def conllu_str(self):
        """
        Converts a DependencyTree object to Conll string.
        """
        lst = list()
        lst.append(self.sent_descript)  # adding first line as sentence number
        lst.append(self.sent_str)  # adding second line as sentence string
        for i in range(len(self.words)):
            word_indx = str(i + 1)
            # if word_indx in self.mw_line.keys():
            #    lst.append(self.mw_line[word_indx])
            feats = [word_indx, self.words[i], self.lemmas[i], self.tags[i], self.ftags[i], str(self.other_features[i]),
                     str(self.heads[i]), self.labels[i], self.semiFinal_tags[i], self.final_tags[i]]
            # ln = str(i+1) +'\t'+self.words[i]+'\t'+self.lemmas[i]+'\t'+self.tags[i]+'\t'+self.ftags[i]+'\t'+str(self.other_features[i])+'\t'+ str(self.heads[i])+'\t'+self.labels[i]+'\t_\t_'
            lst.append('\t'.join(feats))
        return '\n'.join(lst)

    @staticmethod
    def write_to_conllu(tree_list, output_path):
        """
        Write a list of DependencyTree objects into a conll file.
        """
        writer = open(output_path, 'w', encoding='utf-8')
        for tree in tree_list:
            writer.write(tree.conllu_str().strip() + '\n\n')
        writer.close()

    @staticmethod
    def load_tree_from_conll_string(tree_str):
        """
        Loads a conll string into a DependencyTree object.
        """
        lines = tree_str.strip().split('\n')
        mw_line = {}
        words = list()
        tags = list()
        heads = list()
        labels = list()
        lemmas = list()
        ftags = list()
        line_idx = {}
        semiFinal_tags = list()
        final_tags = list()
        sent_descript = lines[0]
        sent_str = lines[1]
        other_features = list()
        for i in range(0, len(lines)):
            spl = lines[i].split('\t')
            line_idx[i - 2] = spl[0]
            line_indx = spl[0].split('-')
            if '-' in spl[0]:
                mw_line[line_indx[0]] = lines[i].strip('\n').strip()
                continue
            words.append(spl[1])  # word form
            lemmas.append(spl[2])  # lemma
            tags.append(spl[3])  # pos
            ftags.append(spl[4])  # cpos
            heads.append(int(spl[6]))  # dep head
            other_features.append(spl[5])  # featurs
            labels.append(spl[7])  # dep_rol
            semiFinal_tags.append(spl[8])  # semi final tag
            final_tags.append(spl[9])  # last tag

        tree = DependencyTree(sent_descript, sent_str, words, tags, ftags, heads, labels, lemmas, other_features,
                              semiFinal_tags, final_tags, mw_line)
        return tree

    @staticmethod
    def load_trees_from_conll_file(file_str):
        """
        Loads a conll file into a list of DependencyTree object.
        """
        tree_list = list()
        [tree_list.append(DependencyTree.load_tree_from_conll_string(tree_str)) for tree_str in
         open(file_str, 'r', encoding='utf-8').read().strip().split('\n\n')]  # codecs.
        return tree_list

    def conll_str(self):
        """
        Converts a DependencyTree object to Conll string.
        """
        lst = list()
        for i in range(len(self.words)):
            word_indx = str(i + 1)
            # if word_indx in self.mw_line.keys():
            #    lst.append(self.mw_line[word_indx])
            feats = [word_indx, self.words[i], self.lemmas[i], self.tags[i], self.ftags[i], str(self.other_features[i]),
                     str(self.heads[i]), self.labels[i], self.semiFinal_tags[i], self.final_tags[i]]
            # ln = str(i+1) +'\t'+self.words[i]+'\t'+self.lemmas[i]+'\t'+self.tags[i]+'\t'+self.ftags[i]+'\t'+str(self.other_features[i])+'\t'+ str(self.heads[i])+'\t'+self.labels[i]+'\t_\t_'
            lst.append('\t'.join(feats))
        return '\n'.join(lst)

    @staticmethod
    def write_to_conll(tree_list, output_path):
        """
        Write a list of DependencyTree objects into a conll file.
        """
        writer = open(output_path, 'w', encoding='utf-8')
        for tree in tree_list:
            writer.write(tree.conll_str().strip() + '\n\n')
        writer.close()

    def convert_pos(self, universal_tree, ner_tree):
        """
        self is the original tree, the two others are suggestions from
        auto-tagged and auto-ner.
        """
        pass

    def find_all_rels(self, role):
        return [key for key, val in enumerate(self.labels) if val == role]

    def find_all_children(self, idx, pos_except_l=None):
        if pos_except_l != None:
            return [key for key, val in enumerate(self.heads) if val == idx and self.tags[key] not in pos_except_l]
        else:
            return [key for key, val in enumerate(self.heads) if val == idx]

    def find_children_with_role(self, h_idx, dep_role):
        return [key for key, val in enumerate(self.heads) if val == h_idx and self.labels[key] == dep_role]

    def find_children_with_pos(self, h_idx, child_pos):
        if child_pos == 'NOUN':
            return [key for key, val in enumerate(self.heads) if
                    val == h_idx and (self.tags[key] == 'NOUN' or self.tags[key] == 'PROPN')]
        else:
            return [key for key, val in enumerate(self.heads) if val == h_idx and self.tags[key] == child_pos]

    def exchange_child_parent(self, parent_idx, child_idx, new_rel_par, new_rel_child=None):
        old_child_h = self.heads[child_idx]
        old_child_r = self.labels[child_idx]
        if not self.other_features[child_idx].has_feat('dadeg_h'):
            self.other_features[child_idx].add_feat({'dadeg_h': str(old_child_h), 'dadeg_r': old_child_r})
        self.heads[child_idx] = self.heads[parent_idx]

        old_par_h = self.heads[parent_idx]
        old_par_r = self.labels[parent_idx]
        if not self.other_features[parent_idx].has_feat('dadeg_h'):
            self.other_features[parent_idx].add_feat({'dadeg_h': str(old_par_h), 'dadeg_r': old_par_r})

        self.heads[parent_idx] = self.index[child_idx]
        self.labels[child_idx] = self.labels[parent_idx]
        if new_rel_child is not None:
            self.labels[child_idx] = new_rel_child
        self.labels[parent_idx] = new_rel_par

    def simple_rel_change(old_rel, new_rel):
        pass

    def verb_mood_detection(self, verb_idx):
        dadeg_fpos = self.ftags[verb_idx]
        if 'dadeg_fpos' in self.other_features[verb_idx].feat_dict.keys():
            dadeg_fpos = self.other_features[verb_idx].feat_dict['dadeg_fpos']
        return dadeg_fpos

    def exchange_pars_with_PRD(self, par_idx, par_new_role, child_new_role):
        prd_child = self.find_children_with_role(self.index[par_idx], 'PRD')
        all_children = self.find_all_children(self.index[par_idx])
        if len(prd_child) == 1:
            for child in all_children:
                # if child!=prd_child[0] and self.labels[child]=='conj':
                #    print('EXCEPT: conjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjj in {}'.format(self.sent_descript))
                if child != prd_child[0] and self.labels[
                    child] != 'conj':  # checking conj rel for AJUCL mapping after AVCONJ in sent=24269
                    old_child_h = self.heads[child]
                    self.heads[child] = self.index[prd_child[0]]
                    if not self.other_features[child].has_feat('dadeg_h'):
                        self.other_features[child].add_feat(
                            {'dadeg_h': str(old_child_h), 'dadeg_r': self.labels[child]})
            self.exchange_child_parent(par_idx, prd_child[0], par_new_role, child_new_role)  # 'mark','advcl')
        else:
            # print('Error in processing AJUCL!')
            self.labels[par_idx] = child_new_role  # 'advcl'
            # print(self.other_features[par_idx].feat('senID'))
            # print(self.sent_str)

    def find_main_noun(self, idx):
        pos = self.tags[idx]
        prev_pos = ''
        # if pos!='ADJ':
        #    print('not adj {}'.format(self.sent_descript))
        # print('pos is:::::: {}'.format(pos))
        count = 0
        while pos == 'ADJ' or pos == 'CCONJ':
            count += 1
            # print('inside while')
            head = self.heads[idx]
            prev_idx = idx
            idx = self.reverse_index[head]
            prev_pos = pos
            pos = self.tags[idx]
            # print('prev pos {} new pos {}'.format(prev_pos,pos))
            # if count>120:
            #    print('stuck in while loop APOSTMOD in sent {} with rol {} & idx {} & pos {}'.format(self.sent_descript,self.labels[idx],idx,pos))
        # print(pos)
        if pos == 'NOUN' or pos == 'PROPN':
            # print(self.sent_descript)
            return idx
        elif prev_pos == 'ADJ':
            return prev_idx
        else:
            return -1

    def reverse_vconj_rels(self, node_idx):
        head = self.heads[node_idx]
        head_idx = self.reverse_index[head]
        head_pos = self.tags[head_idx]
        head_word = self.words[head_idx]
        # verb_child=self.find_children_with_pos(self.index[node_idx],pos)
        # print(verb_child)
        # if len(verb_child)>1:
        #    print('ERROR: more than one verb child for VCONJ rel with main node {} with childs {} in sent {}'.format(self.index[node_idx],verb_child,self.sent_descript))
        children_chain = []
        # children_chain.append(verb_child[0])
        count = 0
        while head_pos == 'VERB' or head_pos == 'CCONJ':
            # if len(verb_child)>1:
            #    print('ERROR: more than one verb child for VCONJ rel with inside node {} with childs {} in sent {}'.format(self.index[node_idx],verb_child,self.sent_descript))
            children_chain.append(head_idx)
            node_idx = head_idx
            head = self.heads[node_idx]
            role = self.labels[node_idx]
            if head == 0:
                break
            head_idx = self.reverse_index[head]
            head_pos = self.tags[head_idx]
            head_word = self.words[head_idx]
            # role=self.labels[head_idx]
            count += 1
            if count > 100:
                print('stuck into while loop idx {} with head {} rel {} in sent {}'.format(node_idx, head, role,
                                                                                           self.sent_descript))
            # children_chain.append(verb_child[0])
            # verb_child=self.find_children_with_pos(self.index[node_idx],pos)
        # print(children_chain)
        # print(children_chain.sort())
        children_chain.sort()
        return children_chain

    def reverse_conj_rels(self, node_idx, pos):
        verb_child = self.find_children_with_pos(self.index[node_idx], pos)
        # print(verb_child)
        # if len(verb_child)>1:
        #    print('ERROR: more than one verb child for VCONJ rel with main node {} with childs {} in sent {}'.format(self.index[node_idx],verb_child,self.sent_descript))
        children_chain = []
        # children_chain.append(verb_child[0])

        while len(verb_child) > 0:
            # if len(verb_child)>1:
            #    print('ERROR: more than one verb child for VCONJ rel with inside node {} with childs {} in sent {}'.format(self.index[node_idx],verb_child,self.sent_descript))
            node_idx = verb_child[0]
            children_chain.append(verb_child[0])
            verb_child = self.find_children_with_pos(self.index[node_idx], pos)
        if len(children_chain) > 1:
            print('heads {} | labels {}'.format(self.heads, self.labels))
            print('children {} in {}'.format(children_chain, self.sent_descript))
        # print(children_chain.sort())
        children_chain.sort()
        # for i in range(len(children_chain)-1):
        #    if self.labels[i]!='VCONJ':

        return children_chain

    def reverse_conj_rels_v3(self, node_idx):
        pos = 'VERB'
        verb_child = self.find_children_with_pos(self.index[node_idx], pos)
        # print(verb_child)
        # if len(verb_child)>1:
        #    print('ERROR: more than one verb child for VCONJ rel with main node {} with childs {} in sent {}'.format(self.index[node_idx],verb_child,self.sent_descript))
        children_chain = []
        # children_chain.append(verb_child[0])
        if len(verb_child) > 0:
            if self.labels[verb_child[0]] == 'PREDEP':
                children_chain.append(verb_child[0])
        while len(verb_child) > 0:
            # if len(verb_child)>1:
            #    print('ERROR: more than one verb child for VCONJ rel with inside node {} with childs {} in sent {}'.format(self.index[node_idx],verb_child,self.sent_descript))
            node_idx = verb_child[0]
            children_chain.append(verb_child[0])
            verb_child = self.find_children_with_pos(self.index[node_idx], pos)
        if len(children_chain) > 1:
            print('heads {} | labels {}'.format(self.heads, self.labels))
            print('children {} in {}'.format(children_chain, self.sent_descript))
        # print(children_chain.sort())
        children_chain.sort()
        # for i in range(len(children_chain)-1):
        #    if self.labels[i]!='VCONJ':

        return children_chain

    def reverse_conj_rels_v2(self, node_idx):
        # verb_child=self.find_children_with_pos(self.index[node_idx],pos)
        verb_child = [key for key, val in enumerate(self.heads) if
                      val == node_idx and self.tags[key] == 'VERB' and self.labels[key] == 'PREDEP']
        children_chain = []
        if len(verb_child) > 0:
            children_chain.append(verb_child[0])
        h = self.heads[node_idx]
        node_rel = self.labels[node_idx]
        if h_pos == 'VERB' and node_rel == 'VCONJ':
            children_chain.append(node_idx)
        node_idx = self.reverse_index[h]
        while True:
            h = self.heads[node_idx]
            node_rel = self.labels[node_idx]
            if h == 0:
                break
            h_idx = self.reverse_index[h]
            h_rel = self.labels[h_idx]
            h_pos = self.tags[h_idx]
            h_h_idx = self.reverse_index[self.heads[h_idx]]
            if h_pos == 'VERB' and ((h_rel == 'PREDEP' and self.tags[h_h_idx] == 'CCONJ') or (
                    h_rel == 'VCONJ' and self.tags[h_h_idx] == 'VERB')):
                children_chain.append(h_idx)
                node_idx = h_idx
            else:
                if h_pos == 'VERB' and node_rel == 'VCONJ':
                    children_chain.append(node_idx)
                break
        children_chain.sort()
        return children_chain

    def node_assign_new_role(self, node_idx, par_idx, new_role):
        try:
            old_head = self.heads[node_idx]
        except IndexError:
            print('node_idx {} with par_idx {} in sent {}'.format(node_idx, par_idx, self.sent_descript))
        old_role = self.labels[node_idx]
        if not self.other_features[node_idx].has_feat('dadeg_r'):
            self.other_features[node_idx].add_feat({'dadeg_h': str(old_head), 'dadeg_r': old_role})
        if par_idx == 0:
            par_indx = par_idx
        else:
            par_indx = self.index[par_idx]
        self.heads[node_idx] = par_indx
        self.labels[node_idx] = new_role
        return old_head, old_role

    def map_obj2_role(self, idx):
        iobj_l = [56498, 57047, 38194, 43357, 26296, 26302, 57151]
        comp_l = [26621, 30910, 31081, 31682, 47333, 38599, 38600, 38601, 38604, 39924, 41245, 41857, 46975, 51705,
                  53316, 53769, 54158, 54346, 54349, 54350, 48985, 36024, 26621, 30910, 31081, 31682]
        obj2_new_role = ''
        if int(self.other_features[idx].feat_dict['senID']) in iobj_l:
            obj2_new_role = 'iobj'
        elif int(self.other_features[idx].feat_dict['senID']) in comp_l:
            obj2_new_role = 'compound:lvc'
        return obj2_new_role

    def find_compound_num_groups(self):
        num_group_idxs = []
        all_num_groups = []
        for idx in range(len(self.tags)):
            # if self.other_features[idx].feat_dict['senID']=='23604':
            #    print('pos {} word {} idx {}'.format(pos,word,idx))
            pos = self.tags[idx]
            word = self.words[idx]
            if pos == 'NUM':
                num_group_idxs.append(idx)
            elif pos == 'CCONJ' and word == 'و' and len(num_group_idxs) > 0:
                nxt_idx = idx + 1
                pos_nxt = self.tags[nxt_idx]
                if pos_nxt == 'NUM':
                    num_group_idxs.append(idx)
                else:
                    if len(num_group_idxs) > 1:
                        all_num_groups.append(num_group_idxs)
                    num_group_idxs = []
            else:
                if len(num_group_idxs) > 1:
                    all_num_groups.append(num_group_idxs)
                num_group_idxs = []
        return all_num_groups

    def find_name_groups(self):
        name_group_idxs = []
        all_name_groups = []
        for idx in range(len(self.tags)):
            # if self.other_features[idx].feat_dict['senID']=='23604':
            #    print('pos {} word {} idx {}'.format(pos,word,idx))
            dadeg_pos = self.other_features[idx].feat_dict['dadeg_pos']
            pos = self.tags[idx]
            word = self.words[idx]
            if (dadeg_pos == 'IDEN' or pos == 'PROPN'):
                name_group_idxs.append(idx)
            else:
                if len(name_group_idxs) > 1:
                    head_candids = []
                    for item in name_group_idxs:
                        h_idx = -1
                        if self.heads[item] != 0:
                            h_idx = self.reverse_index[self.heads[item]]
                        if h_idx not in name_group_idxs:
                            head_candids.append(item)
                    head_candids.sort()
                    if len(head_candids) > 1:
                        name_group_idxs.remove(head_candids[0])
                    all_name_groups.append(name_group_idxs)
                name_group_idxs = []
        return all_name_groups

    def find_tag_fixed_groupds(self):
        for idx in range(0, len(self.words)):
            old_role = self.labels[idx]
            old_head = self.heads[idx]
            old_pos = self.tags[idx]
            word = self.words[idx]
            dadeg_pos = self.other_features[idx].feat_dict['dadeg_pos']
            rol_changed = False
            if dadeg_pos == 'PREP' or dadeg_pos == 'POSTP':  # because of PCONJ rel, we need to implement case, before PCONJ change
                children = self.find_all_children(self.index[idx], ['PUNCT'])
                if len(children) == 2:
                    ch1_w = self.words[children[0]]
                    if ((word == 'پس' or word == 'پیش' or word == 'قبل' or word == 'بعد') and ch1_w == 'از') or (
                            word == 'نسبت' and ch1_w == 'به') or (word == 'غیر' and ch1_w == 'از') or (
                            word == 'بر' and ch1_w == 'ضد') or (word == 'بنا' and ch1_w == 'به') or (
                            word == 'بر' and ch1_w == 'علیه') or (word == 'در' and ch1_w == 'پس') or (
                            word == 'بر' and ch1_w == 'روی') or (word == 'جز' and ch1_w == 'با') or (
                            word == 'در' and ch1_w == 'زیر') or (word == 'راجع' and ch1_w == 'به') or (
                            word == 'به' and ch1_w == 'نزد'):
                        if not self.other_features[children[0]].has_feat('dadeg_r'):
                            self.other_features[children[0]].add_feat(
                                {'dadeg_h': str(self.heads[children[0]]), 'dadeg_r': self.labels[children[0]]})
                        self.labels[children[0]] = 'fixed'
                        ch_ch = self.find_children_with_role(self.index[children[0]], 'POSDEP')
                        if len(ch_ch) == 0:
                            # print('idx {} in sent {}'.format(idx,self.sent_descript))
                            self.exchange_child_parent(idx, children[0], 'case')
                            rol_changed = True
                        else:
                            self.exchange_child_parent(idx, ch_ch[0], 'case')
                            rol_changed = True
                    else:
                        self.exchange_child_parent(idx, children[0], 'case')
                        rol_changed = True

            if rol_changed and not self.other_features[idx].has_feat('dadeg_r'):
                self.other_features[idx].add_feat({'dadeg_h': str(old_head), 'dadeg_r': old_role})

    def zero_level_dep_mapping(self):
        self.find_tag_fixed_groupds()
        simple_dep_map = {'ROOT': 'root', 'PUNC': 'punct', 'APP': 'appos'}
        for idx in range(0, len(self.words)):
            old_role = self.labels[idx]
            old_head = self.heads[idx]
            old_pos = self.tags[idx]
            word = self.words[idx]
            rol_changed = False
            dadeg_pos = self.other_features[idx].feat_dict['dadeg_pos']

            if dadeg_pos == 'ADR' and (self.labels[idx] == 'PREDEP' or self.labels[idx] == 'POSDEP'):
                self.labels[idx] = 'case'
                rol_changed = True
            elif dadeg_pos == 'ADR':
                pre_pos_child = [key for key, val in enumerate(self.heads) if val == self.index[idx] and (
                        self.labels[key] == 'PREDEP' or self.labels[key] == 'POSDEP')]
                if len(pre_pos_child) > 0:
                    self.exchange_child_parent(idx, pre_pos_child[0], 'case')
                    children = self.find_all_children(self.index[idx])
                    for ch in children:
                        old_ch_h = self.heads[ch]
                        old_ch_r = self.labels[ch]
                        self.heads[ch] = self.index[pre_pos_child[0]]
                        if not self.other_features[ch].has_feat('dadeg_r'):
                            self.other_features[ch].add_feat({'dadeg_h': str(old_ch_h), 'dadeg_r': old_ch_r})

                    vconj_child = [key for key, val in enumerate(self.heads) if
                                   val == self.index[pre_pos_child[0]] and self.labels[key] == 'VCONJ']
                    if len(vconj_child) > 0:
                        self.exchange_child_parent(pre_pos_child[0], vconj_child[0], 'vocative')
                    rol_changed = True

            if old_role == 'MESU':  # 'MESU':'nmod' and change child and parent position; before case because of ...kilogram of ra in sentid=23499
                # old_head_idx=self.reverse_index[old_head]
                self.exchange_child_parent(self.reverse_index[old_head], idx, 'nmod')
                # old_head_chs=self.find_all_children(old_head)
                # for child in old_head_chs:
                #    self.heads[child]=self.index[idx]
                rol_changed = True

            if dadeg_pos == 'PREP' or dadeg_pos == 'POSTP':  # because of PCONJ rel, we need to implement case, before PCONJ change
                children = self.find_all_children(self.index[idx], ['PUNCT'])  # because of را in sent=44271
                if len(children) == 2:
                    if self.words[children[0]] == 'هم' or self.words[children[0]] == 'نیز':
                        if not self.other_features[children[0]].has_feat('dadeg_r'):
                            self.other_features[children[0]].add_feat(
                                {'dadeg_h': str(self.heads[children[0]]), 'dadeg_r': self.labels[children[0]]})
                        self.heads[children[0]] = self.index[children[1]]
                        children.remove(children[0])
                    elif self.words[children[1]] == 'هم' or self.words[children[1]] == 'نیز':
                        if not self.other_features[children[1]].has_feat('dadeg_r'):
                            self.other_features[children[1]].add_feat(
                                {'dadeg_h': str(self.heads[children[1]]), 'dadeg_r': self.labels[children[1]]})
                        self.heads[children[1]] = self.index[children[0]]
                        children.remove(children[1])
                    # print('ham in group with len {} child {} in sent {}'.format(len(children),self.words[children[1]],self.sent_descript))

                if len(children) == 1:
                    ch1_w = self.words[children[0]]
                    if ((word == 'پس' or word == 'پیش' or word == 'قبل' or word == 'بعد') and ch1_w == 'از') or (
                            word == 'نسبت' and ch1_w == 'به') or (word == 'غیر' and ch1_w == 'از') or (
                            word == 'بر' and ch1_w == 'ضد') or (word == 'بنا' and ch1_w == 'به') or (
                            word == 'بر' and ch1_w == 'علیه') or (word == 'در' and ch1_w == 'پس') or (
                            word == 'بر' and ch1_w == 'روی') or (word == 'جز' and ch1_w == 'با') or (
                            word == 'در' and ch1_w == 'زیر') or (word == 'راجع' and ch1_w == 'به') or (
                            word == 'به' and ch1_w == 'نزد'):
                        if not self.other_features[children[0]].has_feat('dadeg_r'):
                            self.other_features[children[0]].add_feat(
                                {'dadeg_h': str(self.heads[children[0]]), 'dadeg_r': self.labels[children[0]]})
                        self.labels[children[0]] = 'fixed'
                        ch_ch = self.find_children_with_role(self.index[children[0]], 'POSDEP')
                        if len(ch_ch) == 0:
                            # print('idx {} in sent {}'.format(idx,self.sent_descript))
                            self.exchange_child_parent(idx, children[0], 'case')
                        else:
                            self.exchange_child_parent(idx, ch_ch[0], 'case')
                    else:
                        self.exchange_child_parent(idx, children[0], 'case')
                else:
                    should_change = False
                    if len(children) == 2:
                        ch1_rol = self.labels[children[0]]
                        ch2_rol = self.labels[children[1]]
                        ch1_w = self.words[children[0]]
                        ch2_w = self.words[children[1]]
                        # print(ch1_w)
                        if (ch1_w == 'جمله' and word == 'از'):
                            self.labels[children[0]] = 'fixed'
                            #    self.exchange_child_parent(idx,children[0],'fixed')
                            self.exchange_child_parent(idx, children[1], 'case')
                            if not self.other_features[children[0]].has_feat('dadeg_r'):
                                self.other_features[children[0]].add_feat({'dadeg_h': str(idx), 'dadeg_r': ch1_rol})
                            should_change = True
                        else:
                            if ch1_rol == 'POSDEP' and ch2_rol == 'PCONJ':
                                should_change = True
                                new_par_idx = children[0]
                                new_child_idx = children[1]
                            elif ch2_rol == 'POSDEP' and ch1_rol == 'PCONJ':
                                should_change = True
                                new_par_idx = children[1]
                                new_child_idx = children[0]
                            if should_change:
                                self.exchange_child_parent(idx, new_par_idx, 'case')
                                old_ch_head = self.heads[new_child_idx]
                                old_ch_rol = self.labels[new_child_idx]
                                self.heads[new_child_idx] = self.index[new_par_idx]
                                if not self.other_features[new_child_idx].has_feat('dadeg_r'):
                                    self.other_features[new_child_idx].add_feat(
                                        {'dadeg_h': str(old_ch_head), 'dadeg_r': old_ch_rol})
                    if not should_change and len(children) > 0:
                        child_str = 'idx: ' + str(self.index[idx])
                        child_s = ''
                        for child in children:
                            child_str += '  child ' + str(self.index[child]) + ' with rel: ' + self.labels[
                                child] + ' in sent=' + self.other_features[idx].feat_dict['senID']
                        children.append(idx)
                        children.sort()
                        # print(child_str+' '+' '.join([self.words[key] for key in children]))
                rol_changed = True

            # if old_role=='PARCL':
            #    child=self.find_children_with_role(self.index[idx],'PUNC')
            #    if len(child)==0:
            #        child=self.find_children_with_role(self.index[idx],'punct')
            #    if len(child)==1:
            #        if self.tags[child[0]]=='CCONJ':
            #            self.exchange_child_parent(idx,child[0],'PREDEP','VCONJ')
            #            rol_changed=True

            if old_role in list(simple_dep_map.keys()):
                self.labels[idx] = simple_dep_map[old_role]
                rol_changed = True
            if rol_changed and not self.other_features[idx].has_feat('dadeg_r'):
                self.other_features[idx].add_feat({'dadeg_h': str(old_head), 'dadeg_r': old_role})

    def convert_PARCL_rel(self):
        for idx in range(0, len(self.words)):
            old_role = self.labels[idx]
            old_head = self.heads[idx]
            old_pos = self.tags[idx]
            word = self.words[idx]
            rol_changed = False
            dadeg_pos = self.other_features[idx].feat_dict['dadeg_pos']
            if old_role == 'PARCL':
                punct_child = [key for key, val in enumerate(self.heads) if
                               val == self.index[idx] and self.labels[key] == 'punct']
                # if len(punct_child)==0:
                #    print('punct_child zero in sent {}'.format(self.sent_descript))
                if len(punct_child) > 0:
                    if self.tags[punct_child[0]] == 'CCONJ':
                        # self.exchange_child_parent(punct_child[0],idx,'VCONJ','PREDEP')
                        latest_vconj_child = -1
                        for i in range(0, idx):
                            if self.labels[i] == 'VCONJ':
                                latest_vconj_child = i
                        self.node_assign_new_role(idx, punct_child[0], 'PREDEP')
                        self.node_assign_new_role(punct_child[0], self.reverse_index[old_head], 'VCONJ')
                        if latest_vconj_child != -1:
                            self.node_assign_new_role(latest_vconj_child, idx, 'VCONJ')
                        rol_changed = True
                    else:
                        self.node_assign_new_role(idx, self.reverse_index[old_head], 'parataxis')
                        # paratax_child=self.find_children_with_role(old_head,'parataxis')
                        # asigned_to_h=False
                        # h_h_idx=self.heads[old_head]
                        # if h_h_idx!=0:
                        # if self.labels[self.reverse_index[old_head]]=='parataxis':
                        #        self.node_assign_new_role(idx,self.reverse_index[h_h_idx],'parataxis')
                        #        asigned_to_h=True
                        # if not asigned_to_h:
                        #    self.exchange_child_parent(self.reverse_index[old_head],idx,'parataxis')
                        rol_changed = True
                else:
                    self.node_assign_new_role(idx, self.reverse_index[old_head], 'parataxis')
                    # paratax_child=self.find_children_with_role(old_head,'parataxis')
                    # asigned_to_h=False
                    # h_h_idx=self.heads[old_head]
                    # if h_h_idx!=0:
                    # if self.labels[self.reverse_index[old_head]]=='parataxis':
                    #        self.node_assign_new_role(idx,self.reverse_index[h_h_idx],'parataxis')
                    #        asigned_to_h=True
                    # if not asigned_to_h:
                    #    self.exchange_child_parent(self.reverse_index[old_head],idx,'parataxis')
                    rol_changed = True
            if rol_changed and not self.other_features[idx].has_feat('dadeg_r'):
                self.other_features[idx].add_feat({'dadeg_h': str(old_head), 'dadeg_r': old_role})

    def first_level_dep_mapping(self):
        for idx in range(0, len(self.words)):
            old_role = self.labels[idx]
            old_head = self.heads[idx]
            old_pos = self.tags[idx]
            word = self.words[idx]
            rol_changed = False
            if old_role == 'VCL':  # rule to find and tag csubj roles
                # if self.other_features[idx].feat_dict['senID']=='23513':
                #    print('changed {} idx {} old role is {} with head {} & pos {}'.format(self.other_features[idx].has_feat('dadeg_r'),idx,self.labels[idx],old_head,self.tags[self.reverse_index[old_head]]))
                if self.tags[self.reverse_index[old_head]] == 'VERB':
                    mos_child = self.find_children_with_role(old_head, 'MOS')
                    sbj_child = self.find_children_with_role(old_head, 'SBJ')
                    if len(sbj_child) == 0 and len(mos_child) > 0:
                        self.labels[idx] = 'csubj'
                        rol_changed = True
            if old_pos != 'VERB' and old_role == 'root':
                vconj_child = self.find_children_with_role(self.index[idx], 'VCONJ')
                if len(vconj_child) > 0:
                    self.exchange_child_parent(idx, vconj_child[0], 'vocative')
                    rol_changed = True
            if old_role == 'ROOT':
                self.labels[idx] = 'root'
            if old_role == 'PREDEP':
                head_tag = self.tags[self.heads[idx] - 1]
                if head_tag == "NOUN" and self.ftags[idx] == "SEPER":
                    self.labels[idx] = 'dislocated'
                if head_tag == "NUM" and self.ftags[idx] in {"AJCM", "AJP", "PREP"}:
                    self.labels[idx] = 'advmod'
            if old_role == "APREMOD" and self.tags[idx] == "NUM":
                self.labels[idx] = 'nummod'
            if self.tags[idx] == "PART" and self.words[idx] == "را":
                head_children = self.children[self.heads[idx]]
                head_children_labels = [self.labels[child - 1] for child in head_children]
                if "SBJ" in head_children_labels:  # No subject in children
                    child_span = self.get_span(idx + 1)
                    if min(child_span) == 1:  # should be first span
                        self.labels[idx] = 'dislocated'
                        print("dislocated", self.other_features[0].feat_dict["senID"])
            if self.ftags[idx] == "PREP" and self.ftags[self.heads[idx] - 1] in {"AJCM", "AJP"} \
                    and len(self.children[idx + 1]) == 0:
                self.labels[idx] = 'flat'

            if old_role == 'VCONJ':  # this mapping should take place before که with predicate (VCL) cause #sentID=23816
                if old_pos == 'CCONJ':
                    verb_child = [key for key, val in enumerate(self.heads) if
                                  val == self.index[idx] and self.tags[key] == 'VERB' and self.labels[key] == 'POSDEP']
                    # child=self.find_all_children(self.index[idx])
                    # if len(child)>1:
                    #    print('ERROR in NCONJ: child of CCONJ is more than ONE!!! in sent {}'.format(self.sent_descript))                  
                    if len(verb_child) > 0:
                        self.heads[idx] = self.index[verb_child[0]]
                        self.labels[idx] = 'cc'
                        old_child_role = self.labels[verb_child[0]]
                        old_child_h = self.heads[verb_child[0]]
                        self.labels[verb_child[0]] = 'conj'
                        head_idx = self.reverse_index[old_head]
                        head_role = self.labels[head_idx]
                        # if self.tags[child[0]]=='NUM' and self.tags[head_idx]=='NUM' and word=='و': #like هفتصد و سی و دو. word (CCONJ) only should be و to avoid mistakes: یک یا دو
                        #    self.labels[child[0]]='flat:num'#'compound:num'
                        #    self.labels[idx]='flat:num'
                        #    self.heads[idx]=old_head
                        if head_role == 'conj':
                            self.heads[verb_child[0]] = self.heads[head_idx]

                            # if old_role=='AJCONJ':
                            #    print('conj head for AJCONJ {}'.format(self.sent_descript)) 
                        else:
                            self.heads[verb_child[0]] = old_head
                        if not self.other_features[verb_child[0]].has_feat('dadeg_r'):
                            self.other_features[verb_child[0]].add_feat(
                                {'dadeg_h': str(old_child_h), 'dadeg_r': old_child_role})
                    # else:
                    #    print('child {} in {}'.format(child,self.sent_descript))  
                else:
                    head_idx = self.reverse_index[old_head]
                    head_role = self.labels[head_idx]
                    # if self.other_features[idx].feat_dict['senID']=='24269':
                    #    print('in sent 24269, head_idx is {} & head_role is {}'.format(head_idx,head_role))
                    if head_role == 'conj':
                        self.heads[idx] = self.heads[head_idx]
                        self.labels[idx] = 'conj'
                    else:
                        self.labels[idx] = 'conj'
                    # if self.other_features[idx].feat_dict['senID']=='24269':
                    #    print('in sent 24269, role is {} & head is: {}'.format(self.labels[idx],self.heads[idx]))
                rol_changed = True
            #    if len(verb_child)>0:
            #            if old_pos=='CCONJ':
            #                old_hd,old_child_r=self.node_assign_new_role(idx,self.reverse_index[old_head],'cc') 
            #            else:
            #                old_hd=self.index[idx]
            #            if self.labels[verb_child[0]]=='conj':
            #                new_h=self.reverse_index[self.heads[verb_child[0]]]
            #            else:
            #                new_h=verb_child[0]
            #            old_hd,old_child_r=self.node_assign_new_role(self.reverse_index[old_hd],new_h,'conj')
            #            old_hd_idx=old_hd
            #            if old_hd!=0:
            #                old_hd_idx=self.reverse_index[old_hd]
            #            old_hd,old_child_r=self.node_assign_new_role(new_h,old_hd_idx,old_child_r)
            #            rol_changed=True
            #    if len(verb_child)==0: #means it's a verb with VCONJ rel with the other verb
            #        head_idx=self.reverse_index[old_head]
            #        if self.labels[head_idx]=='conj':
            #            new_h=self.reverse_index[self.heads[head_idx]]
            #        else:
            #            new_h=head_idx
            #        old_hd,old_child_r=self.node_assign_new_role(idx,new_h,'conj')
            #        rol_changed=True

            if old_role in {"NCONJ", "AJCONJ", "AVCONJ", "PCONJ"}:
                if old_pos == 'CCONJ':
                    child = self.find_all_children(self.index[idx])
                    # if len(child)>1:
                    #    print('ERROR in NCONJ: child of CCONJ is more than ONE!!! in sent {}'.format(self.sent_descript))                  
                    if len(child) > 0:
                        self.heads[idx] = self.index[child[0]]
                        self.labels[idx] = 'cc'
                        old_child_role = self.labels[child[0]]
                        old_child_h = self.heads[child[0]]
                        self.labels[child[0]] = 'conj'
                        head_idx = self.reverse_index[old_head]
                        head_role = self.labels[head_idx]
                        # if self.tags[child[0]]=='NUM' and self.tags[head_idx]=='NUM' and word=='و': #like هفتصد و سی و دو. word (CCONJ) only should be و to avoid mistakes: یک یا دو
                        #    self.labels[child[0]]='flat:num'#'compound:num'
                        #    self.labels[idx]='flat:num'
                        #    self.heads[idx]=old_head
                        if head_role == 'conj':
                            self.heads[child[0]] = self.heads[head_idx]

                            # if old_role=='AJCONJ':
                            #    print('conj head for AJCONJ {}'.format(self.sent_descript)) 
                        else:
                            self.heads[child[0]] = old_head
                        if not self.other_features[child[0]].has_feat('dadeg_r'):
                            self.other_features[child[0]].add_feat(
                                {'dadeg_h': str(old_child_h), 'dadeg_r': old_child_role})
                    # else:
                    #    print('child {} in {}'.format(child,self.sent_descript))  
                else:
                    head_idx = self.reverse_index[old_head]
                    head_role = self.labels[head_idx]
                    # if self.other_features[idx].feat_dict['senID']=='24269':
                    #    print('in sent 24269, head_idx is {} & head_role is {}'.format(head_idx,head_role))
                    if head_role == 'conj':
                        self.heads[idx] = self.heads[head_idx]
                        self.labels[idx] = 'conj'
                    else:
                        self.labels[idx] = 'conj'
                    # if self.other_features[idx].feat_dict['senID']=='24269':
                    #    print('in sent 24269, role is {} & head is: {}'.format(self.labels[idx],self.heads[idx]))
                rol_changed = True
            # if old_role in list(simple_dep_map.keys()):
            #    self.labels[idx]=simple_dep_map[old_role]
            #    rol_changed=True
            if rol_changed and not self.other_features[idx].has_feat('dadeg_r'):
                self.other_features[idx].add_feat({'dadeg_h': str(old_head), 'dadeg_r': old_role})

    def second_level_dep_mapping(self):
        for idx in range(0, len(self.words)):
            old_role = self.labels[idx]
            old_head = self.heads[idx]
            old_pos = self.tags[idx]
            lemma = self.lemmas[idx]
            rol_changed = False
            if old_role == 'PARCL':
                punct_child = [key for key, val in enumerate(self.heads) if
                               val == self.index[idx] and self.labels[key] == 'punct']
                if len(punct_child) > 0:
                    if self.tags[punct_child[0]] == 'CCONJ':
                        if old_head > self.index[idx]:
                            self.labels[idx] = 'conj'
                            if self.labels[self.reverse_index[old_head]] == 'conj':
                                self.heads[idx] = self.heads[self.reverse_index[old_head]]
                                if self.index[idx] < self.heads[self.reverse_index[old_head]]:
                                    print('ERROR: first parcle is before first conj in sent {}'.format(
                                        self.sent_descript))
                            else:
                                self.exchange_child_parent(self.reverse_index[old_head], idx, 'conj')
                        else:
                            self.labels[idx] = 'conj'
                            if self.labels[self.reverse_index[old_head]] == 'conj' and self.heads[
                                self.reverse_index[old_head]] < self.index[idx]:
                                self.heads[idx] = self.heads[self.reverse_index[old_head]]
                            elif self.labels[self.reverse_index[old_head]] == 'conj' and self.index[idx] < self.heads[
                                self.reverse_index[old_head]]:
                                self.exchange_child_parent(self.heads[self.reverse_index[old_head]], idx, 'conj')
                                head_v_child = [key for key, val in enumerate(self.heads) if
                                                val == self.heads[self.reverse_index[old_head]] and self.labels[
                                                    key] == 'conj']
                                for v_ch in head_v_child:
                                    self.heads[v_ch] = self.index[idx]
                                print('big exchange: first parcle is before first conj in sent {}'.format(
                                    self.sent_descript))
                        # latest_vconj_child=-1
                        # for i in range(0,idx):
                        #    if self.other_features[i].feat_dict['']=='VCONJ':
                        #        latest_vconj_child=i
                        # self.node_assign_new_role(idx,punct_child[0],'PREDEP')
                        # self.node_assign_new_role(punct_child[0],self.reverse_index[old_head],'VCONJ')
                        # if latest_vconj_child!=-1:
                        #    self.node_assign_new_role(latest_vconj_child,idx,'VCONJ')
                        rol_changed = True
                    # else:
                    #    self.node_assign_new_role(idx,self.reverse_index[old_head],'parataxis')
                    #    rol_changed=True
                # else:
                #    self.node_assign_new_role(idx,self.reverse_index[old_head],'parataxis')
                #    rol_changed=True
            if old_role == 'AJUCL':
                self.exchange_pars_with_PRD(idx, 'mark', 'advcl')
                rol_changed = True
            if old_role == 'VCL' or old_role == 'ACL':
                # if self.other_features[idx].feat_dict['senID']=='23513':
                #    print('changed {} idx {} old role is {} with head {} & pos {}'.format(self.other_features[idx].has_feat('dadeg_r'),idx,self.labels[idx],old_head,self.tags[self.reverse_index[old_head]]))
                # if self.tags[self.reverse_index[old_head]]=='VERB':
                #    mos_child=self.find_children_with_role(old_head,'MOS')
                #    sbj_child=self.find_children_with_role(old_head,'SBJ')
                #    if len(sbj_child)==0 and len(mos_child)>0:
                #        self.labels[idx]='csubj'
                #        rol_changed=True

                # if not rol_changed:
                self.exchange_pars_with_PRD(idx, 'mark', 'ccomp')
                rol_changed = True
                # if self.other_features[idx].feat_dict['senID']=='23513':
                #    print('old role is {}'.format(self.labels[idx]))
            if old_role == 'NCL':
                # if lemma!='که':
                #    print('idx {} lemma {} in sent {}'.format(idx,lemma,self.sent_descript))
                self.exchange_pars_with_PRD(idx, 'mark', 'acl')
                rol_changed = True
            if rol_changed and not self.other_features[idx].has_feat('dadeg_r'):
                self.other_features[idx].add_feat({'dadeg_h': str(old_head), 'dadeg_r': old_role})

    def third_level_dep_mapping(self):
        # TAM is third level cause: اخطارهای نیروهای دولتی را به هیچ انگاشتند.
        simple_dep_map = {'TAM': 'xcomp', 'VPP': 'obl:arg', 'PART': 'mark', 'NPRT': 'compound:lvc',
                          'NVE': 'compound:lvc', 'ENC': 'compound:lvc', 'LVP': 'compound:lv', 'NE': 'compound:lvc',
                          'APREMOD': 'advmod', 'ADVC': 'obl:arg', 'AJPP': 'obl:arg', 'NEZ': 'obl:arg',
                          'VPRT': 'compound:lvc'}
        v_copula = ['کرد#کن', 'گشت#گرد', 'گردید#گرد']
        for idx in range(0, len(self.words)):
            old_role = self.labels[idx]
            old_head = self.heads[idx]
            old_pos = self.tags[idx]
            lemma = self.lemmas[idx]
            word = self.words[idx]
            rol_changed = False
            dadeg_pos = self.other_features[idx].feat_dict['dadeg_pos']
            # *************************************************
            # **** It's so important to put nsubj mapping after case in second level: because of this example:
            # (the dep role of child of را is SBJ)
            # وزارت دفاع افغانستان اعلام نمود که تمامی روش‌های جذب افسران در صفوف ارتش ملی افغانستان را بازنگری خواهند کرد.
            # *************************************************
            if old_role == 'SBJ':  # mapping role of SBJ
                head_idx = self.reverse_index[old_head]
                # if self.tags[head_idx]!='VERB':
                #    print(self.sent_descript)
                #    print(self.sent_str)
                v_mood = self.verb_mood_detection(head_idx)
                v_lemma = self.lemmas[head_idx]
                if v_mood == 'PASS' and v_lemma not in v_copula:  # for copula verbs listed above, although verb mood is passive but subject is active for Mosnad
                    self.labels[idx] = 'nsubj:pass'
                else:
                    self.labels[idx] = 'nsubj'
                rol_changed = True
            if old_role == 'PROG':  # mapping role of PROG: مستمرساز
                head_idx = self.reverse_index[old_head]
                v_mood = self.verb_mood_detection(head_idx)
                v_lemma = self.lemmas[head_idx]
                if v_mood == 'PASS' and v_lemma not in v_copula:  # for copula verbs listed above, although verb mood is passive but subject is active for Mosnad
                    self.labels[idx] = 'aux:pass'
                else:
                    self.labels[idx] = 'aux'
                rol_changed = True
            if old_role == 'OBJ':  # mapping role of OBJ
                # if self.tags[head_idx]!='VERB':
                #    print(self.sent_descript)
                #    print(self.sent_str)
                # head_obj2_children=self.find_children_with_role(old_head,'OBJ2')
                # if len(head_obj2_children)>0:
                # self.labels[head_obj2_children[0]]='obj'
                #    obj2_new_role=self.map_obj2_role(head_obj2_children[0])
                #    if obj2_new_role=='':
                #        obj2_new_role='obj'
                #    self.node_assign_new_role(head_obj2_children[0],self.reverse_index[old_head],obj2_new_role)    
                #    self.labels[idx]='iobj'
                #    rol_changed=True
                # else:
                self.labels[idx] = 'obj'
                rol_changed = True
            if old_role == 'OBJ2':
                obj2_new_role = self.map_obj2_role(idx)
                # if obj2_new_role=='':
                #    print('obj2 not mapped!!!!!!!!!! in sent {}'.format(self.sent_descript))
                # else:
                self.node_assign_new_role(idx, self.reverse_index[old_head], obj2_new_role)
                rol_changed = True
            if old_role in {"MOZ", "NADV", "COMPPP"}:
                if old_pos == 'ADV':
                    self.labels[idx] = 'advmod'
                    rol_changed = True
                elif old_pos in {'NOUN', "PRON", "PROPN"}:
                    self.labels[idx] = 'nmod'
                    rol_changed = True
                elif old_pos == 'ADJ':
                    self.labels[idx] = 'amod'
                    rol_changed = True

                    # adj_prenums=['تک','نصف','چند','دهمین','آخرین','یکمین','سی‌امین','هفتمین','بیستمین','سومین','پنجمین','شصتمین','نهمین','دومین','اول','چهاردهمین','چهارمین','اولین','هشتمین','دوازدهمین','ششمین','یازدهمین','نخستین']
            # if word in adj_prenums and self.words[idx-1]=='و':
            #    print(self.words[idx-2]+' '+self.words[idx-1]+' '+word+' in sent='+self.sent_descript)
            if old_role == 'NPREMOD':
                dadeg_pos = self.other_features[idx].feat_dict['dadeg_pos']
                if dadeg_pos == 'PREM':
                    self.labels[idx] = 'det'
                # elif dadeg_pos=='PRENUM' and word not in adj_prenums:
                elif old_pos == 'NUM':
                    self.labels[idx] = 'nummod'
                else:
                    # if word=='نصف' or word=='تک' or word=='چند':
                    # print('word {} in sent={}'.format(word,self.sent_descript))
                    self.labels[idx] = 'amod'
                # if dadeg_pos=='POSNUM':
                #    print('POSTNUM in NPREMOD {}'.format(self.sent_descript))
                rol_changed = True
            if old_role == 'NPOSTMOD':
                new_pos = self.tags[idx]
                if new_pos == 'NUM':
                    self.labels[idx] = 'nummod'
                else:
                    self.labels[idx] = 'amod'
                rol_changed = True
            if old_role == 'ADV':
                if old_pos == 'ADV' or old_pos == 'ADJ':
                    self.labels[idx] = 'advmod'
                    rol_changed = True
                else:
                    if old_pos not in poss:
                        #    print(old_pos,self.sent_descript)
                        poss.append(old_pos)
                    # print(poss)
                    self.labels[idx] = 'obl'
                    rol_changed = True
            if old_role == 'NPP':
                if old_head == 0:
                    print(self.sent_descript)
                    print(self.heads)
                    print(self.labels)
                head_idx = self.reverse_index[old_head]
                head_dep = self.labels[head_idx]
                if head_dep == 'NVE' or head_dep == 'ENC':
                    # print(self.sent_descript)
                    head_of_head = self.heads[head_idx]
                    self.labels[idx] = 'obl:arg'
                    self.heads[idx] = head_of_head
                else:
                    self.labels[idx] = 'nmod'
                    # if old_pos!='NOUN' and old_pos!='PROPN':
                    #    print(old_pos,self.sent_descript)
                rol_changed = True
            if old_role == 'APOSTMOD':
                old_head_idx = self.reverse_index[old_head]
                head_idx = self.find_main_noun(old_head_idx)
                # print(self.sent_descript)
                # print('word_idex {}'.format(idx))
                # print('old_head {}'.format(old_head))
                # print('return head {}'.format(head_idx))
                # if head_idx!=old_head_idx:
                #    print(self.sent_descript)
                # if head_idx==-1:
                #    print('heas is -1 in {}'.format(self.sent_descript))
                if head_idx != -1:
                    self.heads[idx] = self.index[head_idx]
                    if old_pos == 'ADV':
                        self.labels[idx] = 'advmod'
                    elif old_pos == 'NOUN' or old_pos == 'PROPN' or old_pos == 'PRON':
                        self.labels[idx] = 'nmod'
                    elif old_pos == 'ADJ':
                        self.labels[idx] = 'amod'
                    rol_changed = True

                    # else:
                    # print('in vconj sent is: {}'.format(self.sent_descript))
                    # print('children_chain is: {}'.format(children_chain))
            if old_role in list(simple_dep_map.keys()):
                self.labels[idx] = simple_dep_map[old_role]
                rol_changed = True
            if rol_changed and not self.other_features[idx].has_feat('dadeg_r'):
                self.other_features[idx].add_feat({'dadeg_h': str(old_head), 'dadeg_r': old_role})

    def last_step_changes(self):
        for idx in range(0, len(self.words)):
            old_role = self.labels[idx]
            old_head = self.heads[idx]
            old_pos = self.tags[idx]
            lemma = self.lemmas[idx]
            word = self.words[idx]
            rol_changed = False
            senID = self.other_features[idx].feat_dict['senID']
            if old_role == 'MOS':
                self.exchange_child_parent(self.reverse_index[old_head], idx, 'cop')
                cop_child = self.find_all_children(old_head)
                if self.other_features[idx].feat_dict['senID'] == '43948':
                    print(old_head)
                    print(cop_child)
                    print(self.heads)
                    print(self.labels)
                for ch in cop_child:
                    if self.labels[ch] != 'aux' and self.labels[ch] != 'aux:pass':
                        old_ch_h = self.heads[ch]
                        old_ch_r = self.labels[ch]
                        self.heads[ch] = self.index[idx]
                        if not self.other_features[ch].has_feat('dadeg_r'):
                            self.other_features[ch].add_feat({'dadeg_h': str(old_ch_h), 'dadeg_r': old_ch_r})
                rol_changed = True
            if (word == 'نیز' or word == 'هم') and old_pos == 'ADV':
                head_pos = self.tags[self.reverse_index[old_head]]
                if head_pos != 'VERB':
                    if old_role == 'POSDEP' or old_role == 'PREDEP':
                        self.labels[idx] = 'dep'
                        rol_changed = True
                        # print('idx {} in sent {}'.format(idx,senID))
                    # else:
                    #    print('not changed idx {} in sent {} with role {}'.format(idx,senID,old_role))
            if senID == '52778' and word == 'متر' and self.index[idx] == 16:  # for سانتی متر
                self.labels[idx] = 'goeswith'
                self.heads[idx] = 15
                rol_changed = True
            if senID == '53013' and word == 'دل' and self.index[idx] == 8:  # for بیمار دل
                self.labels[idx] = 'goeswith'
                self.heads[idx] = 7
                rol_changed = True
            if senID == '36147' and word == 'الارض' and self.index[idx] == 22:  # for مفسد فی الارض
                self.labels[idx] = 'goeswith'
                self.heads[idx] = 21
                rol_changed = True
            if senID == '51401' and word == 'هزار' and self.index[idx] == 18:  # for هزار هزار
                self.labels[idx] = 'compound'
                self.heads[idx] = 17
                rol_changed = True
            if senID == '39766' and word == 'هزار' and self.index[idx] == 15:  # for هزار هزار
                self.labels[idx] = 'compound'
                self.heads[idx] = 14
                rol_changed = True
            if senID == '50835' and word == 'حال' and self.index[idx] == 11:  # for سر حال
                self.labels[idx] = 'compound'
                self.heads[idx] = 10
                rol_changed = True
            if self.words[idx - 1] == 'دو' and self.words[idx] == 'سه':
                self.labels[idx] = 'compound'
                self.heads[idx] = self.index[idx - 1]
                rol_changed = True
                # print('convert num group in compound in sent {}'.format(self.other_features[idx].feat_dict['senID']))
            if (self.words[idx - 1] == 'یکی' or self.words[idx - 1] == 'یک') and self.words[idx] == 'دو':
                self.labels[idx] = 'compound'
                self.heads[idx] = self.index[idx - 1]
                rol_changed = True
                # print('convert num group in compound in sent {}'.format(self.other_features[idx].feat_dict['senID']))
            if self.words[idx - 1] == 'چهارده' and self.words[idx] == 'پانزده':
                self.labels[idx] = 'compound'
                self.heads[idx] = self.index[idx - 1]
                rol_changed = True
                # print('convert num group in compound in sent {}'.format(self.other_features[idx].feat_dict['senID']))
            if (self.words[idx - 1] == 'دویست' and self.words[idx] == 'سیصد') or (
                    self.words[idx - 1] == 'سه' and self.words[idx] == 'چهار') or (
                    self.words[idx - 1] == 'هفده' and self.words[idx] == 'هیجده') or (
                    self.words[idx - 1] == 'چهار' and self.words[idx] == 'پنج') or (
                    self.words[idx - 1] == 'سیزده' and self.words[idx] == 'چهارده'):
                self.labels[idx] = 'compound'
                self.heads[idx] = self.index[idx - 1]
                rol_changed = True
                # print('convert num group in compound in sent {}'.format(self.other_features[idx].feat_dict['senID']))
            if rol_changed and not self.other_features[idx].has_feat('dadeg_r'):
                self.other_features[idx].add_feat({'dadeg_h': str(old_head), 'dadeg_r': old_role})

    def convert_num_groups(self):
        all_num_group = self.find_compound_num_groups()
        for num_group in all_num_group:
            group_h = -1
            group_h_rel = ''
            group_str = self.words[num_group[0]]
            for i in range(1, len(num_group)):
                num_idx = num_group[i]
                group_str += ' ' + self.words[num_idx]
                old_num_h = self.heads[num_idx]
                old_num_r = self.labels[num_idx]
                pos_num = self.tags[num_idx]
                # if self.other_features[num_idx].feat_dict['senID']=='23604':
                #    print('word pos is: {} {}'.format(pos_num,self.words[num_idx]))
                if not self.other_features[num_idx].has_feat('dadeg_r'):
                    self.other_features[num_idx].add_feat({'dadeg_h': str(old_num_h), 'dadeg_r': old_num_r})
                if self.reverse_index[old_num_h] not in num_group:
                    group_h = old_num_h
                    group_h_rel = old_num_r
                    head_child = self.find_all_children(self.index[num_idx])
                    # if self.other_features[num_idx].feat_dict['senID']=='23591':
                    #    print(,head_child)
                    for child in head_child:
                        self.heads[child] = self.index[num_group[0]]
                if pos_num == 'CCONJ':
                    self.labels[num_idx] = 'cc'
                    # try:
                    self.heads[num_idx] = self.index[num_group[i + 1]]
                    # except IndexError:
                    #    print('index error: group {} in sent {}'.format(group_str,self.other_features[idx].feat_dict['senID']))
                    #    return
                else:
                    self.labels[num_idx] = 'flat:num'
                    self.heads[num_idx] = self.index[num_group[0]]
                    # num_child=self.find_all_children(self.index[num_idx])
                    # for child in num_child:
                    #    self.heads[child]=num_group[0]
            if group_h != -1:
                old_r = self.labels[num_group[0]]
                old_h = self.heads[num_group[0]]
                self.labels[num_group[0]] = group_h_rel
                self.heads[num_group[0]] = group_h
                if not self.other_features[num_group[0]].has_feat('dadeg_r'):
                    self.other_features[num_group[0]].add_feat({'dadeg_h': str(old_h), 'dadeg_r': old_r})
                # rol_changed=True
            # print('convert num group {} in sent {}'.format(group_str,self.other_features[idx].feat_dict['senID']))
            # elif self.reverse_index[self.heads[num_group[0]]] in num_group:
            #    print('ERROR: in num convertion no head found in group {} sent {}'.format(group_str,self.other_features[idx].feat_dict['senID']))

    def convert_name_groups(self):
        all_name_group = self.find_name_groups()
        for name_group in all_name_group:
            group_h = -1
            group_h_rel = ''
            group_str = self.words[name_group[0]]
            for i in range(1, len(name_group)):
                name_idx = name_group[i]
                group_str += ' ' + self.words[name_idx]
                old_nam_h = self.heads[name_idx]
                old_nam_r = self.labels[name_idx]
                pos_nam = self.tags[name_idx]
                # if self.other_features[num_idx].feat_dict['senID']=='23604':
                #    print('word pos is: {} {}'.format(pos_num,self.words[num_idx]))
                if not self.other_features[name_idx].has_feat('dadeg_r'):
                    self.other_features[name_idx].add_feat({'dadeg_h': str(old_nam_h), 'dadeg_r': old_nam_r})
                old_nam_h_idx = -1
                if old_nam_h != 0:
                    old_nam_h_idx = self.reverse_index[old_nam_h]
                if old_nam_h_idx not in name_group:
                    group_h = old_nam_h
                    group_h_rel = old_nam_r
                    # head_child=self.find_all_children(self.index[name_idx])
                    # if self.other_features[num_idx].feat_dict['senID']=='23591':
                    #    print(,head_child)
                    # for child in head_child:
                    #    self.heads[child]=self.index[name_group[0]]
                self.labels[name_idx] = 'flat:name'
                self.heads[name_idx] = self.index[name_group[0]]
                # num_child=self.find_all_children(self.index[num_idx])
                # for child in num_child:
                #    self.heads[child]=num_group[0]
            if group_h != -1:
                old_r = self.labels[name_group[0]]
                old_h = self.heads[name_group[0]]
                self.labels[name_group[0]] = group_h_rel
                self.heads[name_group[0]] = group_h
                if not self.other_features[name_group[0]].has_feat('dadeg_r'):
                    self.other_features[name_group[0]].add_feat({'dadeg_h': str(old_h), 'dadeg_r': old_r})
                # rol_changed=True
            # print('convert name group {} in sent {}'.format(group_str,self.other_features[idx].feat_dict['senID']))
            # elif self.reverse_index[self.heads[num_group[0]]] in num_group:
            #    print('ERROR: in num convertion no head found in group {} sent {}'.format(group_str,self.other_features[idx].feat_dict['senID']))

    def convert_tree(self):
        self.zero_level_dep_mapping()
        # self.convert_PARCL_rel()
        self.first_level_dep_mapping()
        not_num_process = ['53393', '58877', '46067', '36338']
        if self.other_features[0].feat_dict['senID'] not in not_num_process:
            self.convert_num_groups()
        self.convert_name_groups()
        self.second_level_dep_mapping()
        self.third_level_dep_mapping()
        self.last_step_changes()

    @staticmethod
    def fix_mwe_entries(tree_list):
        tmas = dict()
        tmas_count = defaultdict(int)
        mwe_file = os.path.dirname(os.path.abspath(__file__)) + '/mwe_conversion.txt'
        mwe_replacements = {line.strip().split('\t')[0]: [line.strip().split('\t')[1], line.strip().split('\t')[2]] for
                            line in open(mwe_file, 'r')}

        lemma_dict = dict()
        for tree in tree_list:
            for i in range(len(tree.words)):
                word, lemma, pos = tree.words[i], tree.lemmas[i], tree.tags[i]
                if len(word.split(' ')) > 1:
                    assert pos == 'V'
                elif pos == 'V' and word not in lemma_dict:
                    lemma_dict[word] = lemma

        count_wrong = 0
        # replacing mwes
        for tree in tree_list:
            for i in range(len(tree.words)):
                word, lemma, pos = tree.words[i], tree.lemmas[i], tree.tags[i]
                tree.words[i], tree.lemmas[i], tree.tags[i] = mwe.fix_word_entries(word, lemma, pos, mwe_replacements,
                                                                                   lemma_dict)
                if len(word.split()) > 1:
                    entry = tree.other_features[i].feat('tma') + '\t' + tree.ftags[i]
                    if tree.other_features[i].feat('tma') == "H" and tree.ftags[i] == 'ACT':
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
    input_files = ['Universal_Dadegan/train.conllu', 'Universal_Dadegan/dev.conllu',
                   'Universal_Dadegan/test.conllu']  # os.path.abspath(sys.argv[1])
    # universal_file = os.path.abspath(sys.argv[1])
    # ner_file = os.path.abspath(sys.argv[3])
    output_files = ['Universal_Dadegan_with_DepRels/train.conllu', 'Universal_Dadegan_with_DepRels/dev.conllu',
                    'Universal_Dadegan_with_DepRels/test.conllu']  # os.path.abspath(sys.argv[2])
    for idx, inp_f in enumerate(input_files):
        tree_list = DependencyTree.load_trees_from_conllu_file(inp_f)
        # print('fixing MWE inconsistencies')
        # DependencyTree.fix_mwe_entries(tree_list)

        # universal_tree_list = DependencyTree.load_trees_from_conllu_file(universal_file)
        # ner_tree_list = DependencyTree.load_trees_from_conll_file(ner_file)

        # First pass: convert POS tags
        # print('fixing POS inconsistencies')
        # for i, tree in enumerate(tree_list):
        #    tree.convert_pos(universal_tree_list[i], ner_tree_list[i])    

        print('fixing tree inconsistencies in {}'.format(inp_f))
        # Second pass: convert tree structure
        poss = []
        for i, tree in enumerate(tree_list):
            parcle_list = tree.find_all_rels('PARCL')
            # if len(parcle_list)>1:
            #    print('multi PARCL in sent {}'.format(tree.sent_descript))
            tree.convert_tree()  # (universal_tree_list[i])
            # w_list=['پیغمبر','انا','سوگند','خوش','جای','فلانی','نعوذ','بصیرت']
            # for indx in range(0,len(tree.words)):
            #    role=tree.labels[indx]
            #    word=tree.words[indx]
            #    pos=tree.tags[indx]
            #   prev_pos=''
            #    prev_w=''
            #    next_pos=''
            #    next_w=''
            #    if indx>0:
            #        prev_pos=tree.tags[indx-1]
            #        prev_w=tree.words[indx-1]
            #    if indx<len(tree.tags)-1:
            #        next_pos=tree.tags[indx+1]
            #        next_w=tree.words[indx+1]
            #    if pos=='PROPN' and next_pos!='PROPN' and prev_pos!='PROPN':
            #        print('{} word {} {} in sent={}'.format(prev_w,word,next_w,tree.other_features[indx].feat('senID')))

            #    if tree.tags[indx]=='PSUS' and tree.words[indx] in w_list:
            #        print('idx {} with word {} in sent={}'.format(tree.index[indx],word,tree.other_features[indx].feat('senID')))

            #    head=tree.heads[indx]
            # print(tree.other_features[indx].feat('senID'))
            # print(tree.tags)
            # print(head)
            #    if role=='VCL':
            # if tree.tags[tree.reverse_index[head]]!='VERB':
            #    print('head is not verb in sent={}'.format(tree.other_features[idx].feat('senID')))
            #        if tree.tags[tree.reverse_index[head]]=='VERB':
            #            mos_child=tree.find_children_with_role(head,'MOS')
            #            sbj_child=tree.find_children_with_role(head,'SBJ')
            #            if len(sbj_child)==0 and len(mos_child)>0:
            #                tree_list_sub.append(tree)
            #                print('idx {} with verb head {} in sent={}'.format(tree.index[idx],head,tree.other_features[idx].feat('senID')))
            # old_pos=self.tags[idx]
            # lemma=self.lemmas[idx]
        DependencyTree.write_to_conllu(tree_list, output_files[idx])

        # poss=set(poss)
        # for p in poss:
        #    print(p)
