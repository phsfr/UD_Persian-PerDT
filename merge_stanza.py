from dep_tree import *

if __name__ == '__main__':
    input_files = ['Universal_Dadegan_with_DepRels/train.conllu', 'Universal_Dadegan_with_DepRels/dev.conllu',
                   'Universal_Dadegan_with_DepRels/test.conllu']
    stanza_files = ['stanza_output/train.conllu', 'stanza_output/dev.conllu',
                   'stanza_output/test.conllu']
    output_files = ['Universal_Dadegan_with_DepRels_stanza_merged/train.conllu',
                    'Universal_Dadegan_with_DepRels_stanza_merged/dev.conllu',
                    'Universal_Dadegan_with_DepRels_stanza_merged/test.conllu']

    for f_idx, inp_f in enumerate(input_files):
        univ_tree = DependencyTree.load_trees_from_conllu_file(inp_f)
        stanza_tree = DependencyTree.load_trees_from_conllu_file(stanza_files[f_idx])

        DependencyTree.write_to_conllu(univ_tree, output_files[f_idx])