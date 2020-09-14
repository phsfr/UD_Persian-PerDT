"""
* Converting Dadegan features to the UD standard version
"""

from dep_tree import DependencyTree

if __name__ == '__main__':
    input_files = ['UD_Dadegan_feat/fa_dadegan-ud-train.conllu',
                   'UD_Dadegan_feat/fa_dadegan-ud-dev.conllu',
                   'UD_Dadegan_feat/fa_dadegan-ud-test.conllu']
    output_files = ['UD_Dadegan/fa_dadegan-ud-train.conllu',
                    'UD_Dadegan/fa_dadegan-ud-dev.conllu',
                    'UD_Dadegan/fa_dadegan-ud-test.conllu']

    for f_idx, inp_f in enumerate(input_files):
        tree_list = DependencyTree.load_trees_from_conllu_file(inp_f)
        for i, tree in enumerate(tree_list):
            for w, (pos, ftag, feature) in enumerate(zip(tree.tags, tree.ftags, tree.other_features)):
                if pos == 'VERB':
                    if 'tense' in tree.other_features[w].feat_dict:
                        if tree.other_features[w].feat_dict[
                            'tense'] == 'Part':  # debugging main data, VerbForm=Part was wrongly annotated as Tense=Part
                            tree.other_features[w].remove_feat('tense')
                            tree.other_features[w].add_feat('VerbForm', 'Part')
                    tma = feature.feat('tma')
                    if tma == 'HA':
                        if 'mood' not in tree.other_features[w].feat_dict:
                            tree.other_features[w].add_feat('Mood', 'Imp')
                        # if 'tense' not in tree.other_features[w].feat_dict:
                        #    tree.other_features[w].add_feat('Tense','Pres')
                    if tma == 'GNES':
                        if 'tense' not in tree.other_features[w].feat_dict:
                            tree.other_features[w].add_feat('Tense', 'Past')
                    if tma == 'GN':
                        if 'verbForm' not in tree.other_features[w].feat_dict:
                            tree.other_features[w].add_feat('VerbForm', 'Part')
                    if tma == 'H':
                        if 'tense' not in tree.other_features[w].feat_dict:
                            tree.other_features[w].add_feat('Tense', 'Pres')
                    if tma == 'GS':
                        if 'tense' not in tree.other_features[w].feat_dict:
                            tree.other_features[w].add_feat('Tense', 'Past')
                    if tma == 'HA':
                        if 'mood' not in tree.other_features[w].feat_dict:
                            tree.other_features[w].add_feat('Mood', 'Sub')
                        if 'tense' not in tree.other_features[w].feat_dict:
                            tree.other_features[w].add_feat('Tense', 'Pres')

                if pos == 'AUX' or pos == 'VERB':  # adding void feature
                    if ftag.endswith('ACT'):
                        tree.other_features[w].add_feat('Voice', 'Act')
                    elif ftag.endswith('PASS'):
                        tree.other_features[w].add_feat('Voice', 'Pass')

                tree.other_features[w].remove_feat('tma')
                tree.other_features[w].remove_feat('attachment')
                tree.other_features[w].remove_feat('senID')
                tree.other_features[w].remove_feat('dadeg_pos')
                tree.other_features[w].remove_feat('Dadeg_fpos')
                tree.other_features[w].remove_feat('Dadeg_lemma')
                tree.other_features[w].remove_feat('old_r')
                tree.other_features[w].remove_feat('old_h')
                if 'number' in tree.other_features[w].feat_dict:
                    tree.other_features[w].feat_dict['number'] = feature.feat('number').capitalize()
                if 'polarity' in tree.other_features[w].feat_dict:
                    tree.other_features[w].feat_dict['polarity'] = feature.feat('polarity').capitalize()
                #k.capitalize()
                tree.other_features[w].feat_dict = { k[0].upper()+k[1:] : v for k, v in
                                                    tree.other_features[w].feat_dict.items()}

        DependencyTree.write_to_conllu(tree_list, output_files[f_idx])

