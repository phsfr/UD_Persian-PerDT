import os
from collections import defaultdict
from typing import Dict, List, Set

univ_dep_labels = {"nsubj", "obj", "iobj", "csubj", "ccomp", "xcomp", "obl", "vocative", "expl", "dislocated", "advcl",
                   "advmod", "discourse", "aux", "cop", "mark", "nmod", "appos", "nummod", "acl", "amod", "det", "clf",
                   "case", "conj", "cc", "fixed", "flat", "compound", "list", "parataxis", "orphan", "goeswith",
                   "reparandum", "punct", "root", "dep"}


def remove_semispace(word):
    if word.endswith('\u200c'):
        # Semi-space removal
        word = word[:-1]
    if word.startswith('\u200c'):
        # Semi-space removal
        word = word[1:]
    return word


class Features:
    def __init__(self, feat_str):  # process all features in feat_str and put them in dictionary (feat_dict)
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
        return "|".join([feat + "=" + v for feat, v in dict(sorted(self.feat_dict.items())).items()]) if len(
            self.feat_dict) > 0 else "_"

    def feat(self, feat):  # get the value of a specific feature (feat)
        return self.feat_dict[feat]

    def add_feat(self, feat_name, feat_value):
        if feat_name not in self.feat_dict:
            self.feat_dict[feat_name] = feat_value

    def remove_feat(self, feat_name):
        if feat_name in self.feat_dict:
            del self.feat_dict[feat_name]

    def empty(self):
        self.feat_dict = dict()


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
        self.sen_id = 0
        for f in other_features:
            self.other_features.append(Features(f))
        if "senID" in self.other_features[0].feat_dict:
            self.sen_id = int(self.other_features[0].feat_dict["senID"])

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

    def __len__(self):
        return len(self.words)

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

    def extend_subchildren(self, sub_children: List[int], head: int, level: int) -> List[int]:
        # The following labels are permitted to go beyond a yield subtree deep.
        allowed_yields = {"MOZ", "APP", "NPOSTMOD", "PREDEP", "POSDEP"}
        sub_children = []
        for child in self.children[head]:
            if self.labels[child - 1] in allowed_yields:
                sub_children.extend(self.children[child])
                sub_children.extend(self.extend_subchildren(sub_children, child, level + 1))
        return sub_children

    def get_flat_spans(self) -> Dict[int, Set]:
        """
        For each word index, returns words that are in the same flat chunk neighborhood wrt current tree.
        """
        spans = []
        for i in range(0, len(self.words)):
            sub_children = self.extend_subchildren([], i + 1, 0)

            all_children = sorted([i + 1] + sub_children + list(self.children[i + 1]))

            if self.labels[i] in {"MOZ"}:
                h = self.heads[i]
                all_children = sorted(all_children + [h] + list(self.children[h]))

            if len(all_children) == 1:
                continue

            conseq_spans = []
            cur_span = [all_children[0]]
            for c, child in enumerate(all_children[1:]):
                if child == cur_span[-1] + 1:
                    cur_span.append(child)
                else:
                    if len(cur_span) > 1:
                        conseq_spans.append(cur_span)
                    cur_span = list([child])
            if len(cur_span) > 1:
                conseq_spans.append(cur_span)

            spans += conseq_spans

        span_dict = {i: set() for i in range(len(self.words))}
        for subspan in spans:
            for v in subspan:
                for v2 in subspan:
                    span_dict[v - 1].add(v2 - 1)  # One index off due to Python indexing vs CONLLU indexing.
        return span_dict

    def all_in_flat(self, span_dict, flat_candidate) -> bool:
        """
        Determines of a list of words are in the same chunk (yield subtree including head of yield).
        :return:
        """
        for elem in flat_candidate[1:]:
            if elem not in span_dict[flat_candidate[0]]:
                return False
        return True

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
        return len(spans) == len(self.words) + 1 and len([x for x in self.labels if x == "root"]) == 1

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
        other_features = list()
        for i in range(0, len(lines)):
            if lines[i].startswith("# sent_id"):
                sent_descript = lines[i]
            elif lines[i].startswith("# text ="):
                sent_str = lines[i]
            elif not lines[i].startswith("#"):
                # for jumping over two first lines (one is sentence number & other is sentence's string
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
                semiFinal_tags.append(spl[8])  # semi UD_Dadegan tag
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
        for tree_str in open(file_str, 'r', encoding='utf-8').read().strip().split('\n\n'):
            tree_list.append(DependencyTree.load_tree_from_conllu_string(tree_str))  # codecs.
        return tree_list

    def conllu_str(self):
        """
        Converts a DependencyTree object to Conll string.
        """
        lst = list()
        lst.append(self.sent_descript)  # adding first line as sentence number
        lst.append(
            " ".join([w for w in self.sent_str.split(" ")]))  # adding second line as sentence string
        for i in range(len(self.words)):
            word_indx = str(i + 1)
            if word_indx in self.mw_line.keys():
                mwline = "\t".join(self.mw_line[word_indx].strip().split("\t")[:10])
                lst.append(mwline)
            feats = [word_indx, self.words[i].strip().replace(" ",""), self.lemmas[i], self.tags[i],
                     self.ftags[i], str(self.other_features[i]),
                     str(self.heads[i]), self.labels[i], self.semiFinal_tags[i], self.final_tags[i]]
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
            semiFinal_tags.append(spl[8])  # semi UD_Dadegan tag
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
            feats = [word_indx, self.words[i], self.lemmas[i], self.tags[i],
                     self.ftags[i], str(self.other_features[i]),
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
        if old_child_r.isupper():
            self.other_features[child_idx].add_feat('old_h', str(old_child_h))
            self.other_features[child_idx].add_feat('old_r', old_child_r)
        self.heads[child_idx] = self.heads[parent_idx]

        old_par_h = self.heads[parent_idx]
        old_par_r = self.labels[parent_idx]
        self.other_features[parent_idx].add_feat('old_h', str(old_par_h))
        self.other_features[parent_idx].add_feat('old_r', old_par_r)

        self.heads[parent_idx] = self.index[child_idx]
        self.labels[child_idx] = self.labels[parent_idx]
        if new_rel_child is not None:
            self.labels[child_idx] = new_rel_child
        self.labels[parent_idx] = new_rel_par

    def simple_rel_change(old_rel, new_rel):
        pass

    def verb_mood_detection(self, verb_idx):
        Dadeg_fpos = self.ftags[verb_idx]
        if 'Dadeg_fpos' in self.other_features[verb_idx].feat_dict.keys():
            Dadeg_fpos = self.other_features[verb_idx].feat_dict['Dadeg_fpos']
        return Dadeg_fpos

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
                    self.other_features[child].add_feat('old_r', self.labels[child])
                    self.other_features[child].add_feat('old_h', str(old_child_h))
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
        self.other_features[node_idx].add_feat('old_r', old_role)
        self.other_features[node_idx].add_feat('old_h', str(old_head))
        if par_idx == 0:
            par_indx = par_idx
        else:
            par_indx = self.index[par_idx]
        self.heads[node_idx] = par_indx
        self.labels[node_idx] = new_role
        return old_head, old_role

    def find_compound_num_groups(self):
        num_group_idxs = []
        all_num_groups = []
        for idx in range(len(self.tags)):
            # if self.sen_id=='23604':
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
        flat_spans = self.get_flat_spans()
        name_group_idxs = []
        all_name_groups = []
        for idx in range(len(self.tags)):
            pos = self.tags[idx]
            word = self.words[idx]
            if pos == 'PROPN':
                if self.all_in_flat(flat_spans, name_group_idxs + [idx]):
                    name_group_idxs.append(idx)
                else:
                    if len(name_group_idxs) > 1:
                        all_name_groups.append(name_group_idxs)
                    name_group_idxs = [idx]
            else:
                if len(name_group_idxs) > 1:
                    all_name_groups.append(name_group_idxs)
                name_group_idxs = []

        if len(name_group_idxs) > 1:
            all_name_groups.append(name_group_idxs)

        return all_name_groups

    def find_tag_fixed_groupds(self):
        for idx in range(0, len(self.words)):
            old_role = self.labels[idx]
            old_head = self.heads[idx]
            old_pos = self.tags[idx]
            word = self.words[idx]
            Dadeg_pos = self.other_features[idx].feat_dict['Dadeg_pos']
            rol_changed = False
            if Dadeg_pos == 'PREP' or Dadeg_pos == 'POSTP':  # because of PCONJ rel, we need to implement case, before PCONJ change
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
                        self.other_features[children[0]].add_feat('old_r', self.labels[children[0]])
                        self.other_features[children[0]].add_feat('old_h', str(self.heads[children[0]]))

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

            self.other_features[idx].add_feat('old_r', old_role)
            self.other_features[idx].add_feat('old_h', str(old_head))

    def reverse_modal(self):
        for idx in range(0, len(self.words)):
            head_id = self.heads[idx] - 1
            if head_id >= 0 and self.ftags[head_id] == "V_MODL" and self.tags[idx] in {"AUX", "VERB"}:
                for ch in self.children[head_id + 1]:
                    ch_id = ch - 1
                    if ch_id != idx:
                        self.heads[ch_id] = idx + 1
                        self.other_features[ch_id].add_feat('old_h', str(idx + 1))
                self.tags[head_id] = "AUX"
                self.exchange_child_parent(head_id, idx, 'aux')
                self.rebuild_children()

    def zero_level_dep_mapping(self):
        self.find_tag_fixed_groupds()
        simple_dep_map = {'PUNC': 'punct', 'APP': 'appos', "aux": "aux"}
        for l, label in enumerate(self.labels):
            if label in simple_dep_map:
                self.labels[l] = simple_dep_map[label]
                self.other_features[l].add_feat('old_r', label)

        for idx in range(0, len(self.words)):
            old_role = self.labels[idx]
            old_head = self.heads[idx]
            old_pos = self.tags[idx]
            word = self.words[idx]
            rol_changed = False
            Dadeg_pos = self.other_features[idx].feat_dict['Dadeg_pos']

            if Dadeg_pos == 'ADR' and (self.labels[idx] == 'PREDEP' or self.labels[idx] == 'POSDEP'):
                self.labels[idx] = 'case'
                rol_changed = True
            elif Dadeg_pos == 'ADR':
                pre_pos_child = [key for key, val in enumerate(self.heads) if val == self.index[idx] and (
                        self.labels[key] == 'PREDEP' or self.labels[key] == 'POSDEP')]
                if len(pre_pos_child) > 0:
                    self.exchange_child_parent(idx, pre_pos_child[0], 'case')
                    children = self.find_all_children(self.index[idx])
                    for ch in children:
                        old_ch_h = self.heads[ch]
                        old_ch_r = self.labels[ch]
                        self.heads[ch] = self.index[pre_pos_child[0]]
                        self.other_features[ch].add_feat('old_r', old_ch_r)
                        self.other_features[ch].add_feat('old_h', str(old_ch_h))

                    vconj_child = [key for key, val in enumerate(self.heads) if
                                   val == self.index[pre_pos_child[0]] and self.labels[key] == 'VCONJ']
                    if len(vconj_child) > 0:
                        self.exchange_child_parent(pre_pos_child[0], vconj_child[0], 'vocative')
                    rol_changed = True

            if old_role == 'MESU':
                # 'MESU':'nmod' and change child and parent position; before case because of ...kilogram of ra in sentid=23499
                self.exchange_child_parent(self.reverse_index[old_head], idx, 'nmod')
                rol_changed = True

            if old_role == 'COMPPP':
                if len(self.children[idx + 1]) == 0:
                    self.labels[idx] = "fixed"
                elif len(self.children[idx + 1]) == 1:
                    head_id = self.heads[idx]
                    dep_id = list(self.children[idx + 1])[0] - 1
                    old_r = self.labels[dep_id]

                    self.heads[dep_id] = head_id
                    self.labels[dep_id] = "obl:arg"
                    self.labels[idx] = "case"
                    self.heads[idx] = dep_id + 1
                    self.other_features[dep_id].add_feat('old_h', str(idx + 1))
                    self.other_features[dep_id].add_feat('old_r', old_r)
                else:
                    raise Exception("SHOULD NOT HAVE MORE THAN ONE DEP!")
                rol_changed = True

            if Dadeg_pos == 'PREP' or Dadeg_pos == 'POSTP':  # because of PCONJ rel, we need to implement case, before PCONJ change
                children = self.find_all_children(self.index[idx], ['PUNCT'])  # because of را in sent=44271
                if len(children) == 2:
                    if self.words[children[0]] == 'هم' or self.words[children[0]] == 'نیز':
                        self.other_features[children[0]].add_feat('old_r', self.labels[children[0]])
                        self.other_features[children[0]].add_feat('old_h', str(self.heads[children[0]]))
                        self.heads[children[0]] = self.index[children[1]]
                        children.remove(children[0])
                    elif self.words[children[1]] == 'هم' or self.words[children[1]] == 'نیز':
                        self.other_features[children[1]].add_feat('old_r', self.labels[children[1]])
                        self.other_features[children[1]].add_feat('old_h', str(self.heads[children[1]]))
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
                        self.other_features[children[0]].add_feat('old_r', self.labels[children[0]])
                        self.other_features[children[0]].add_feat('old_h', str(self.heads[children[0]]))
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
                            self.other_features[children[0]].add_feat('old_r', ch1_rol)
                            self.other_features[children[0]].add_feat('old_h', str(idx))
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
                                self.other_features[new_child_idx].add_feat('old_r', old_ch_rol)
                                self.other_features[new_child_idx].add_feat('old_h', str(old_ch_head))
                    if not should_change and len(children) > 0:
                        child_str = 'idx: ' + str(self.index[idx])
                        child_s = ''
                        for child in children:
                            child_str += '  child ' + str(self.index[child]) + ' with rel: ' + self.labels[
                                child] + ' in sent=' + str(self.sen_id)
                        children.append(idx)
                        children.sort()
                rol_changed = True

            if rol_changed:
                self.other_features[idx].add_feat('old_r', old_role)
                self.other_features[idx].add_feat('old_h', str(old_head))

    def first_level_dep_mapping(self):
        for idx in range(0, len(self.words)):
            old_role = self.labels[idx]
            old_head = self.heads[idx]
            old_pos = self.tags[idx]
            word = self.words[idx]
            rol_changed = False

            if old_role in {"NCONJ", "AJCONJ", "AVCONJ", "PCONJ", "VCONJ"}:
                if old_pos == 'CCONJ':
                    if old_role == "VCONJ":
                        _children = [key for key, val in enumerate(self.heads) if
                                     val == self.index[idx] and self.tags[key] in {'VERB', "AUX"} and self.labels[
                                         key] == 'POSDEP']
                    else:
                        _children = self.find_all_children(self.index[idx])

                    if len(_children) > 0:
                        self.heads[idx] = self.index[_children[0]]
                        self.labels[idx] = 'cc'
                        old_child_role = self.labels[_children[0]]
                        old_child_h = self.heads[_children[0]]
                        self.labels[_children[0]] = 'conj'
                        head_idx = self.reverse_index[old_head]
                        head_role = self.labels[head_idx]
                        if head_role == 'conj':
                            self.heads[_children[0]] = self.heads[head_idx]
                        else:
                            self.heads[_children[0]] = old_head
                        self.other_features[_children[0]].add_feat('old_r', old_child_role)
                        self.other_features[_children[0]].add_feat('old_h', str(old_child_h))
                else:
                    head_idx = self.reverse_index[old_head]
                    head_role = self.labels[head_idx]
                    if head_role == 'conj':
                        self.heads[idx] = self.heads[head_idx]
                        self.labels[idx] = 'conj'
                    else:
                        self.labels[idx] = 'conj'
                rol_changed = True

            if old_role == 'VCL':  # rule to find and tag csubj roles
                if self.tags[self.reverse_index[old_head]] in {'VERB', "AUX"}:
                    mos_child = self.find_children_with_role(old_head, 'MOS')
                    sbj_child = self.find_children_with_role(old_head, 'SBJ')
                    if len(sbj_child) == 0 and len(mos_child) > 0:
                        self.labels[idx] = 'csubj'
                        rol_changed = True
            if old_pos != 'VERB' and old_role == 'root' and self.tags[idx] == "INTJ":
                vconj_child = self.find_children_with_role(self.index[idx], 'VCONJ')
                if len(vconj_child) > 0:
                    self.exchange_child_parent(idx, vconj_child[0], 'vocative')
                    rol_changed = True
            if old_role == 'PREDEP':
                head_tag = self.tags[self.heads[idx] - 1]
                if head_tag == "NOUN" and self.ftags[idx] == "SEPER":
                    self.labels[idx] = 'dislocated'
                    rol_changed = True
                if head_tag == "NUM" and self.ftags[idx] in {"AJCM", "AJP", "PREP"}:
                    self.labels[idx] = 'advmod'
                    rol_changed = True

            if old_role == "APREMOD" and self.tags[idx] == "NUM":
                self.labels[idx] = 'nummod'
                rol_changed = True
            if self.tags[idx] == "PART" and self.words[idx] == "را":
                head_children = self.children[self.heads[idx]]
                head_children_labels = [self.labels[child - 1] for child in head_children]
                if "SBJ" in head_children_labels:  # No subject in children
                    child_span = self.get_span(idx + 1)
                    if min(child_span) == 1:  # should be first span
                        self.labels[idx] = 'dislocated'
                        print("dislocated", self.other_features[0].feat_dict["senID"])
                        rol_changed = True

            if self.ftags[idx] == "PREP" and self.ftags[self.heads[idx] - 1] in {"AJCM", "AJP"} \
                    and len(self.children[idx + 1]) == 0:
                self.labels[idx] = 'flat'
                rol_changed = True

            self.other_features[idx].add_feat('old_r', old_role)
            self.other_features[idx].add_feat('old_h', str(old_head))

    def second_level_dep_mapping(self):
        for idx in range(0, len(self.words)):
            old_role = self.labels[idx]
            old_head = self.heads[idx]
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
            if old_role == 'VCL' or old_role == 'ACL':
                self.exchange_pars_with_PRD(idx, 'mark', 'ccomp')
            if old_role == 'NCL':
                self.exchange_pars_with_PRD(idx, 'mark', 'acl')
            self.other_features[idx].add_feat('old_r', old_role)
            self.other_features[idx].add_feat('old_h', str(old_head))

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
            Dadeg_pos = self.other_features[idx].feat_dict['Dadeg_pos']
            # *************************************************
            # **** It's so important to put nsubj mapping after case in second level: because of this example:
            # (the dep role of child of را is SBJ)
            # وزارت دفاع افغانستان اعلام نمود که تمامی روش‌های جذب افسران در صفوف ارتش ملی افغانستان را بازنگری خواهند کرد.
            # *************************************************
            if old_role == 'SBJ':  # mapping role of SBJ
                head_idx = self.reverse_index[old_head]
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
                self.labels[idx] = 'obj'
                rol_changed = True
            if old_role == 'OBJ2':
                self.node_assign_new_role(idx, self.reverse_index[old_head], "iobj")
                rol_changed = True
            if old_role in {"MOZ", "NADV"}:
                if old_pos == 'ADV':
                    self.labels[idx] = 'advmod'
                    rol_changed = True
                elif old_pos in {'NOUN', "PRON", "PROPN"}:
                    self.labels[idx] = 'nmod'
                    rol_changed = True
                elif old_pos == 'ADJ':
                    self.labels[idx] = 'amod'
                    rol_changed = True
                elif old_role == "MOZ":
                    self.labels[idx] = 'nmod'  # todo after paper
                    rol_changed = True

                    # adj_prenums=['تک','نصف','چند','دهمین','آخرین','یکمین','سی‌امین','هفتمین','بیستمین','سومین','پنجمین','شصتمین','نهمین','دومین','اول','چهاردهمین','چهارمین','اولین','هشتمین','دوازدهمین','ششمین','یازدهمین','نخستین']
            # if word in adj_prenums and self.words[idx-1]=='و':
            #    print(self.words[idx-2]+' '+self.words[idx-1]+' '+word+' in sent='+self.sent_descript)
            if old_role == 'NPREMOD':
                Dadeg_pos = self.other_features[idx].feat_dict['Dadeg_pos']
                if Dadeg_pos == 'PREM':
                    self.labels[idx] = 'det'
                # elif Dadeg_pos=='PRENUM' and word not in adj_prenums:
                elif old_pos == 'NUM':
                    self.labels[idx] = 'nummod'
                else:
                    # if word=='نصف' or word=='تک' or word=='چند':
                    # print('word {} in sent={}'.format(word,self.sent_descript))
                    self.labels[idx] = 'amod'
                # if Dadeg_pos=='POSNUM':
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
            self.other_features[idx].add_feat('old_r', old_role)
            self.other_features[idx].add_feat('old_h', str(old_head))

    def last_step_changes(self):
        for idx in range(0, len(self.words)):
            old_role = self.labels[idx]
            old_head = self.heads[idx]
            head_pos = self.tags[old_head - 1]
            old_pos = self.tags[idx]
            head_lemma = self.lemmas[old_head - 1]
            lemma = self.lemmas[idx]
            word = self.words[idx]
            rol_changed = False
            senID = self.sen_id
            if old_role == 'MOS':
                if head_pos == "AUX":
                    self.exchange_child_parent(self.reverse_index[old_head], idx, 'cop')
                    cop_child = self.find_all_children(old_head)
                    for ch in cop_child:
                        if self.labels[ch] != 'aux' and self.labels[ch] != 'aux:pass':
                            old_ch_h = self.heads[ch]
                            old_ch_r = self.labels[ch]
                            self.heads[ch] = self.index[idx]
                            self.other_features[ch].add_feat('old_h', str(old_ch_h))
                            self.other_features[ch].add_feat('old_r', old_ch_r)
                else:
                    self.labels[idx] = "xcomp"
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
                # print('convert num group in compound in sent {}'.format(self.sen_id))
            if (self.words[idx - 1] == 'یکی' or self.words[idx - 1] == 'یک') and self.words[idx] == 'دو':
                self.labels[idx] = 'compound'
                self.heads[idx] = self.index[idx - 1]
                rol_changed = True
                # print('convert num group in compound in sent {}'.format(self.sen_id))
            if self.words[idx - 1] == 'چهارده' and self.words[idx] == 'پانزده':
                self.labels[idx] = 'compound'
                self.heads[idx] = self.index[idx - 1]
                rol_changed = True
                # print('convert num group in compound in sent {}'.format(self.sen_id))
            if (self.words[idx - 1] == 'دویست' and self.words[idx] == 'سیصد') or (
                    self.words[idx - 1] == 'سه' and self.words[idx] == 'چهار') or (
                    self.words[idx - 1] == 'هفده' and self.words[idx] == 'هیجده') or (
                    self.words[idx - 1] == 'چهار' and self.words[idx] == 'پنج') or (
                    self.words[idx - 1] == 'سیزده' and self.words[idx] == 'چهارده'):
                self.labels[idx] = 'compound'
                self.heads[idx] = self.index[idx - 1]
                rol_changed = True
            self.other_features[idx].add_feat('old_r', old_role)
            self.other_features[idx].add_feat('old_h', str(old_head))

    def final_refinement(self):
        """
        For roles for which is left behind!
        :return:
        """
        mapping = {"AJUCL": "advcl", "NCL": "acl", "MOS": "xcomp", "PRD": "ccomp"}

        for l, label in enumerate(self.labels):
            changed = False
            if label in mapping:
                self.labels[l] = mapping[label]
                changed = True

            if self.heads[l] > l and label == "VCONJ" and self.tags[l] == "CCONJ":
                self.labels[l] = "cc"
                changed = True
            elif label == "VCONJ" and self.tags[l] == "CCONJ":
                head_id = self.heads[l] - 1
                if len(self.children[head_id + 1]) > 1:
                    # This is a heuristic and is not necessarily correct! (#todo)
                    last_child = list(sorted(self.children[head_id + 1]))[0]
                    if last_child - 1 > l:
                        self.labels[l] = "cc"
                        self.heads[l] = last_child
                        changed = True

            if label == "PREDEP":
                if self.words[l] in {"نیز", "هم"}:
                    self.labels[l] = "dep"
                elif self.tags[l] == "NUM":
                    self.labels[l] = "nummod"
                elif self.tags[l] == "ADV" or self.tags[l] == "ADJ":
                    self.labels[l] = "advmod"
                else:
                    self.labels[l] = "obl"
                changed = True
            if label == "POSDEP":
                if self.words[l] in {"نیز", "هم"}:
                    self.labels[l] = "dep"
                elif self.tags[l] == "ADP" and self.tags[self.heads[l] - 1] == "ADP":
                    self.labels[l] = "fixed"
                elif self.tags[l] == "NUM":
                    self.labels[l] = "nummod"
                elif self.tags[l] == "ADV" or self.tags[l] == "ADJ":
                    self.labels[l] = "advmod"
                else:
                    self.labels[l] = "obl"

                changed = True

            if not changed and label.split(":")[0] not in univ_dep_labels:
                self.labels[l] = "dep"  # todo #Unresolved
                changed = True

            self.other_features[l].add_feat('old_r', label)

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
                self.other_features[num_idx].add_feat('old_h', str(old_num_h))
                self.other_features[num_idx].add_feat('old_r', old_num_r)
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
                    #    print('index error: group {} in sent {}'.format(group_str,self.sen_id))
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
                self.other_features[num_idx].add_feat('old_h', str(old_h))
                self.other_features[num_idx].add_feat('old_r', old_r)

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
                self.other_features[name_idx].add_feat('old_r', old_nam_r)
                self.other_features[name_idx].add_feat('old_h', str(old_nam_h))
                old_nam_h_idx = -1
                if old_nam_h != 0:
                    old_nam_h_idx = self.reverse_index[old_nam_h]
                if old_nam_h_idx not in name_group:
                    group_h = old_nam_h
                    group_h_rel = old_nam_r
                self.labels[name_idx] = 'flat:name'
                self.heads[name_idx] = self.index[name_group[0]]
            if group_h != -1:
                old_r = self.labels[name_group[0]]
                old_h = self.heads[name_group[0]]
                self.labels[name_group[0]] = group_h_rel
                self.heads[name_group[0]] = group_h
                self.other_features[name_group[0]].add_feat('old_r', old_r)
                self.other_features[name_group[0]].add_feat('old_h', str(old_h))

    def convert_PARCL_rel(self):
        parcl_nums = self.find_all_rels('PARCL')
        for idx in range(0, len(self.words)):
            old_role = self.labels[idx]
            old_head = self.heads[idx]
            old_pos = self.tags[idx]
            lemma = self.lemmas[idx]
            rol_changed = False
            if old_role == 'PARCL':
                punct_child = [key for key, val in enumerate(self.heads) if
                               val == self.index[idx] and self.labels[key] == 'punct']
                other_parcl_of_head = [key for key, val in enumerate(self.heads) if
                                       val == old_head and self.labels[key] == 'PARCL' and key != idx]
                if len(punct_child) > 0:
                    if self.tags[punct_child[0]] == 'CCONJ':
                        if old_head > self.index[idx]:
                            self.labels[idx] = 'conj'
                            if self.labels[self.reverse_index[old_head]] == 'conj':
                                self.heads[idx] = self.heads[self.reverse_index[old_head]]
                            else:
                                self.exchange_child_parent(self.reverse_index[old_head], idx, 'conj')
                        else:
                            self.labels[idx] = 'conj'
                            if self.labels[self.reverse_index[old_head]] == 'conj' and self.heads[
                                self.reverse_index[old_head]] < self.index[idx]:
                                self.heads[idx] = self.heads[self.reverse_index[old_head]]
                        if self.labels[self.reverse_index[old_head]] == 'conj':
                            conj_after_parcl = -1
                            for i in range(idx + 1, old_head):
                                if self.labels[i] == 'conj' and self.heads[i] == self.heads[
                                    self.reverse_index[old_head]]:
                                    conj_after_parcl = i
                                    break
                            if conj_after_parcl != -1:
                                old_punc_r = self.labels[punct_child[0]]
                                old_punc_h = self.heads[punct_child[0]]
                                self.labels[punct_child[0]] = 'cc'
                                self.heads[punct_child[0]] = self.index[conj_after_parcl]
                                self.other_features[punct_child[0]].add_feat('old_r', old_punc_r)
                                self.other_features[punct_child[0]].add_feat('old_h', str(old_punc_h))
                        else:
                            old_punc_r = self.labels[punct_child[0]]
                            old_punc_h = self.heads[punct_child[0]]
                            self.labels[punct_child[0]] = 'cc'
                            self.heads[punct_child[0]] = old_head
                            self.other_features[punct_child[0]].add_feat('old_r', old_punc_r)
                            self.other_features[punct_child[0]].add_feat('old_h', str(old_punc_h))
                        if len(other_parcl_of_head) > 0:
                            if self.index[other_parcl_of_head[0]] < self.heads[punct_child[0]]:
                                self.heads[punct_child[0]] = self.index[other_parcl_of_head[0]]
                        rol_changed = True
                if not rol_changed:
                    if len(other_parcl_of_head) > 0:
                        self.node_assign_new_role(other_parcl_of_head[0], idx, 'conj')
                        cconj_child = [key for key, val in enumerate(self.heads) if
                                       val == self.index[other_parcl_of_head[0]] and self.labels[key] == 'punct' and
                                       self.tags[key] == 'CCONJ']
                        if len(cconj_child) > 0:
                            conj_after_parcl = -1
                            for i in range(other_parcl_of_head[0] + 1, old_head):
                                if self.labels[i] == 'PARCL' and self.heads[i] == old_head:
                                    conj_after_parcl = i
                                    break
                            if conj_after_parcl != -1:
                                old_punc_r = self.labels[cconj_child[0]]
                                old_punc_h = self.heads[cconj_child[0]]
                                self.labels[cconj_child[0]] = 'cc'
                                self.heads[cconj_child[0]] = self.index[conj_after_parcl]
                                self.other_features[punct_child[0]].add_feat('old_r', old_punc_r)
                                self.other_features[punct_child[0]].add_feat('old_h', str(old_punc_h))
                            else:
                                old_punc_r = self.labels[cconj_child[0]]
                                old_punc_h = self.heads[cconj_child[0]]
                                self.labels[cconj_child[0]] = 'cc'
                                self.heads[cconj_child[0]] = old_head
                                self.other_features[punct_child[0]].add_feat('old_r', old_punc_r)
                                self.other_features[punct_child[0]].add_feat('old_h', str(old_punc_h))
                        self.exchange_child_parent(self.reverse_index[old_head], idx, 'conj')

                    else:
                        conj_child_head = [key for key, val in enumerate(self.heads) if
                                           val == old_head and self.labels[key] == 'conj']
                        if len(conj_child_head) > 0:
                            if old_head > self.index[idx]:
                                self.exchange_child_parent(self.reverse_index[old_head], idx, 'conj')
                                for conj_ch in conj_child_head:
                                    self.heads[conj_ch] = self.index[idx]
                            else:
                                self.node_assign_new_role(idx, self.reverse_index[old_head], 'conj')
                        else:
                            if old_head > self.index[idx]:
                                self.exchange_child_parent(self.reverse_index[old_head], idx, 'parataxis')
                            else:
                                self.node_assign_new_role(idx, self.reverse_index[old_head], 'parataxis')
                    rol_changed = True
            self.other_features[idx].add_feat('old_r', old_role)
            self.other_features[idx].add_feat('old_h', str(old_head))

    def convert_tree(self):
        # NOTE: the order of execution is important. Don't change it.
        self.reverse_modal()
        self.convert_name_groups()
        not_num_process = ['53393', '58877', '46067', '36338']
        if self.sen_id not in not_num_process:
            self.convert_num_groups()
        self.zero_level_dep_mapping()
        self.first_level_dep_mapping()
        self.convert_PARCL_rel()
        self.second_level_dep_mapping()
        self.third_level_dep_mapping()
        self.last_step_changes()
        self.final_refinement()
        self.manual_postprocess()

    def ud_validate_fix(self):
        # Fixes errors by validator
        for i in range(len(self.words)):
            if self.tags[i] == "PUNCT":
                self.labels[i] = "punct"
            if self.tags[i] == "NOUN" and self.labels[i] == "advmod":
                self.labels[i] = "obl"
            if (self.tags[i] == "PUNCT" and self.words[i]!="-") and self.heads[i]>i:
                self.final_tags[i] = "SpaceAfter=No"
        if self.sen_id == 23558:
            self.heads[16] = 19

    def manual_postprocess(self):
        if self.sen_id == 47788:
            self.tags[1] = "ADJ"
            self.labels[1] = "obl"
            self.heads[1] = 4
        elif self.sen_id == 47435:
            self.tags[23] = "NOUN"
        elif self.sen_id == 23570:
            self.tags[0] = "PROPN"
            self.tags[1] = "PROPN"
            self.tags[2] = "PROPN"
            self.labels[1] = "flat:name"
            self.labels[2] = "flat:name"
        elif self.sen_id == 51672:
            self.tags[0] = "PROPN"
            self.labels[1] = "flat:name"
            self.heads[2] = 0
            self.heads[3] = 0
        elif self.sen_id == 34084:
            self.tags[11] = "PROPN"
            self.labels[11] = "flat:name"
            self.heads[11] = 10
        elif self.sen_id == 50328:
            self.tags[10] = "NOUN"
            self.tags[11] = "NOUN"
        elif self.sen_id == 23472:
            self.tags[-6] = "NOUN"
        elif self.sen_id == 23520:
            self.labels[1] = "goeswith"
        elif self.sen_id == 23483:
            self.tags[20] = "NUM"
        elif self.sen_id == 40708:
            self.labels[1] = "goeswith"
            self.labels[0] = "nsubj"
            self.heads[0] = 5
            self.heads[1] = 1
        elif self.sen_id == 33833:
            self.tags[5] = "PROPN"
            self.tags[6] = "PROPN"
            self.heads[6] = 6
            self.labels[6] = "flat:name"
            self.heads[7] = 5

        self.ud_validate_fix()

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
    output_files = ['Universal_Dadegan_with_DepRels/train.conllu', 'Universal_Dadegan_with_DepRels/dev.conllu',
                    'Universal_Dadegan_with_DepRels/test.conllu']  # os.path.abspath(sys.argv[2])
    for idx, inp_f in enumerate(input_files):
        tree_list = DependencyTree.load_trees_from_conllu_file(inp_f)
        print('fixing tree inconsistencies in {}'.format(inp_f))
        poss = []
        for i, tree in enumerate(tree_list):
            parcle_list = tree.find_all_rels('PARCL')
            tree.convert_tree()  # (universal_tree_list[i])
        DependencyTree.write_to_conllu(tree_list, output_files[idx])
