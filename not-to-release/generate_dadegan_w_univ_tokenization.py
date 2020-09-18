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
            # Fixes errors by validator
            if len(tree.mw_line) > 0:
                for mw in tree.mw_line.values():
                    drange = [int(x) for x in mw.strip().split("\t")[0].split("-")]
                    for dh in range(drange[0], drange[1]):
                        for dhc in tree.children[dh]:
                            if tree.labels[dhc - 1] == "PUNC":
                                tree.heads[dhc - 1] = drange[-1]
            for t, ftag in enumerate(tree.ftags):
                tree.other_features[t].remove_feat("Dadeg_pos")
                tag, fpos = ftag.split("_") if "_" in ftag else (ftag, ftag)
                tree.tags[t] = tag
                tree.ftags[t] = fpos
            if tree.sen_id == 35524:
                tree.final_tags[16] = '_'
            if tree.sen_id == 54442:
                tree.tags[6] = 'PROPN'
                tree.ftags[6] = "N_ANM"

        DependencyTree.write_to_conllu(trees, output_files[f_idx])
