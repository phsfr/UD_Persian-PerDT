from dep_tree import *

if __name__ == '__main__':
    input_files = ['Universal_Dadegan_with_DepRels/train.conllu', 'Universal_Dadegan_with_DepRels/dev.conllu',
                   'Universal_Dadegan_with_DepRels/test.conllu']
    stanza_files = ['stanza_output/train.conllu', 'stanza_output/dev.conllu',
                    'stanza_output/test.conllu']
    output_files = ['UD_Dadegan_feat/fa_dadegan-ud-train.conllu',
                    'UD_Dadegan_feat/fa_dadegan-ud-dev.conllu',
                    'UD_Dadegan_feat/fa_dadegan-ud-test.conllu']

    stanza_fixed = set()
    for f_idx, inp_f in enumerate(input_files):
        univ_trees: List[DependencyTree] = DependencyTree.load_trees_from_conllu_file(inp_f)
        stanza_trees: List[DependencyTree] = DependencyTree.load_trees_from_conllu_file(stanza_files[f_idx])

        for t, (univ_tree, stanza_tree) in enumerate(zip(univ_trees, stanza_trees)):
            stanza_label_set, univ_label_set = set(stanza_tree.labels), set(univ_tree.labels)
            if "dislocated" in stanza_label_set:
                if univ_tree.sen_id == 50307:
                    idx = stanza_tree.labels.index("dislocated")
                    dislocated_idx = [wi for wi, word in enumerate(univ_tree.words) if word == stanza_tree.words[idx]][
                        -1]
                    dislocated_head = dislocated_idx + 2
                    univ_tree.heads[dislocated_idx] = dislocated_head
                    univ_tree.labels[dislocated_idx] = "dislocated"
                pass
            if "fixed" in stanza_label_set:
                idx = stanza_tree.labels.index("fixed")
                head_idx = stanza_tree.heads[idx] - 1
                # print(stanza_tree.words[head_idx] + " " + stanza_tree.words[idx])
                fixed = stanza_tree.words[head_idx] + " " + stanza_tree.words[idx]
                if head_idx == idx - 1:
                    stanza_fixed.add(fixed)
                    univ_fixed_h, univ_fixed_m = -1, -1
                    for h in range(len(univ_tree.words)):
                        if univ_tree.words[h] == stanza_tree.words[head_idx] and \
                                univ_tree.words[h + 1] == stanza_tree.words[idx]:
                            univ_fixed_h = h
                            univ_fixed_m = h + 1

                    if univ_fixed_h >= 0 and univ_tree.labels[univ_fixed_m] != "fixed":
                        stanza_fixed.add(fixed)

                # print(" ".join(stanza_tree.words))

        DependencyTree.write_to_conllu(univ_trees, output_files[f_idx])
    # print("\n".join(stanza_fixed))
