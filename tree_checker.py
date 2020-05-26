from dep_tree import *
from typing import List


univ_pos_tags = {"ADJ", "ADP", "PUNCT", "ADV", "AUX", "SYM", "INTJ", "CCONJ", "X", "NOUN", "DET", "PROPN", "NUM", "VERB", "PART", "PRON", "SCONJ"}
univ_dep_labels = {"nsubj", "obj", "iobj", "csubj", "ccomp", "xcomp", "obl", "vocative", "expl", "dislocated", "advcl", "advmod", "discourse", "aux", "cop", "mark", "nmod", "appos", "nummod", "acl", "amod", "det", "clf", "case",  "conj", "cc", "fixed", "flat", "compound", "list", "parataxis", "orphan", "goeswith", "reparandum", "punct", "root", "dep"}



if __name__ == '__main__':
    input_files = ['Universal_Dadegan_with_DepRels_stanza_merged/train.conllu',
                    'Universal_Dadegan_with_DepRels_stanza_merged/dev.conllu',
                    'Universal_Dadegan_with_DepRels_stanza_merged/test.conllu']
    illegal_tags = set()
    illegal_labels = set()
    for file in input_files:
        trees: List[DependencyTree] = DependencyTree.load_trees_from_conllu_file(file)

        for tree in trees:
            tags = set(tree.tags)
            labels = set(tree.labels)

            for t in tags:
                if t not in univ_pos_tags:
                    #print("Illegal tag", t, "in", tree.other_features[0].feat_dict["senID"])
                    illegal_tags.add(t)

            for l in labels:
                label = l.split(":")[0]
                if label not in univ_dep_labels:
                    illegal_labels.add(l)
                    #print("Illegal label", l, "in", tree.other_features[0].feat_dict["senID"])

            if not tree.is_valid_tree():
                print("Malformed tree in", tree.other_features[0].feat_dict["senID"])

    print("Illegal tags:", " ".join(illegal_tags))
    print("Illegal labels:", " ".join(illegal_labels))
