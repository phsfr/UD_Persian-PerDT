from dep_tree import *

if __name__ == '__main__':
    input_files = ['Universal_Dadegan/train.conllu', 'Universal_Dadegan/dev.conllu',
                   'Universal_Dadegan/test.conllu']
    output_files = ['Dadegan_univ_tok/train.conllu',
                    'Dadegan_univ_tok/dev.conllu',
                    'Dadegan_univ_tok/test.conllu']

    stanza_fixed = set()
    for f_idx, inp_f in enumerate(input_files):
        trees: List[DependencyTree] = DependencyTree.load_trees_from_conllu_file(inp_f)

        for tree in trees:
            for t, ftag in enumerate(tree.ftags):
                tree.other_features[t].remove_feat("dadeg_pos")
                tag, fpos = ftag.split("_") if "_" in ftag else (ftag, ftag)
                tree.tags[t] = tag
                tree.ftags[t] = fpos

        DependencyTree.write_to_conllu(trees, output_files[f_idx])
