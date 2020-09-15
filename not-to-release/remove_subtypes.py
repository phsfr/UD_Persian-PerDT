from dep_tree import *

# For removing subtypes after : in labels.

if __name__ == '__main__':
    input_files = ['../fa_perdt-ud-train.conllu',
                   '../fa_perdt-ud-dev.conllu',
                   '../fa_perdt-ud-test.conllu']
    output_files = ['UD_Dadegan-nt/fa_dadegan-ud-train.conllu',
                    'UD_Dadegan-nt/fa_dadegan-ud-dev.conllu',
                    'UD_Dadegan-nt/fa_dadegan-ud-test.conllu']

    for f_idx, inp_f in enumerate(input_files):
        univ_trees: List[DependencyTree] = DependencyTree.load_trees_from_conllu_file(inp_f)

        for t, univ_tree in enumerate(univ_trees):
            for l, label in enumerate(univ_tree.labels):
                univ_tree.labels[l] = univ_tree.labels[l].split(":")[0]
        DependencyTree.write_to_conllu(univ_trees, output_files[f_idx])
