from dep_tree import *

univ_pos_tags = {"ADJ", "ADP", "PUNCT", "ADV", "AUX", "SYM", "INTJ", "CCONJ", "X", "NOUN", "DET", "PROPN", "NUM",
                 "VERB", "PART", "PRON", "SCONJ"}
univ_dep_labels = {"nsubj", "obj", "iobj", "csubj", "ccomp", "xcomp", "obl", "vocative", "expl", "dislocated", "advcl",
                   "advmod", "discourse", "aux", "cop", "mark", "nmod", "appos", "nummod", "acl", "amod", "det", "clf",
                   "case", "conj", "cc", "fixed", "flat", "compound", "list", "parataxis", "orphan", "goeswith",
                   "reparandum", "punct", "root", "dep"}

if __name__ == '__main__':
    dadegan_files = ['Persian_Dependency_Treebank_(PerDT)_V1.1.1/Data/train.conll',
                     'Persian_Dependency_Treebank_(PerDT)_V1.1.1/Data//dev.conll',
                     'Persian_Dependency_Treebank_(PerDT)_V1.1.1/Data//test.conll']
    for file in dadegan_files:
        trees: List[DependencyTree] = DependencyTree.load_trees_from_conll_file(file)
        for tree in trees:
            if not tree.is_valid_tree():
                print("Malformed Dadegan tree in", tree.sen_id)

    input_files = ['UD_Dadegan/fa_dadegan-ud-train.conllu',
                   'UD_Dadegan/fa_dadegan-ud-dev.conllu',
                   'UD_Dadegan/fa_dadegan-ud-test.conllu']
    illegal_tags = defaultdict(int)
    illegal_labels = defaultdict(int)
    illegal_tokenization = set()
    problematic_sens = set()
    for file in input_files:
        trees: List[DependencyTree] = DependencyTree.load_trees_from_conllu_file(file)

        for tree in trees:
            tags = set(tree.tags)
            labels = set(tree.labels)

            for t in tags:
                if t not in univ_pos_tags:
                    print("Illegal tag", t, "in", tree.sen_id)
                    illegal_tags[t] += 1
                    problematic_sens.add(tree.sen_id)

            for idx, l in enumerate(labels):
                label = l.split(":")[0]
                if label not in univ_dep_labels:
                    illegal_labels[l] += 1
                    problematic_sens.add(tree.sen_id)
                    print("Illegal label", l, "in", tree.sen_id)

            if not tree.is_valid_tree():
                problematic_sens.add(tree.sen_id)
                print("Malformed tree in", tree.sen_id)

            all_chars = tree.sent_str[len("# text ="):].strip().replace(" ", "")
            all_word_chars = "".join(tree.words).replace(" ", "")
            if all_chars != all_word_chars:
                illegal_tokenization.add(tree.sen_id)
                print("Wrong tokenization", tree.sen_id)

    if len(illegal_tags) > 0:
        print("Illegal tags:", " ".join([t + ":" + str(c) for t, c in illegal_tags.items()]))
    if len(illegal_labels) > 0:
        print("Illegal labels:", " ".join([l + ":" + str(c) for l, c in illegal_labels.items()]))
    if len(problematic_sens) > 0:
        print("Number of wrong sentences", len(problematic_sens))
    if len(illegal_tokenization) > 0:
        print("Number of wrong tokenization", len(illegal_tokenization))
