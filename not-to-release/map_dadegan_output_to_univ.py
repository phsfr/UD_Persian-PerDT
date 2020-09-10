import sys

from dep_tree import *

gold_standard: List[DependencyTree] = DependencyTree.load_trees_from_conllu_file(os.path.abspath(sys.argv[1]))
system_output: List[DependencyTree] = DependencyTree.load_trees_from_conllu_file(os.path.abspath(sys.argv[2]))

convert_path = os.path.abspath(sys.argv[3])

mapping = {"PR": "PRON", "AUX": "AUX", "N": "NOUN"}
for gtree, stree in zip(gold_standard, system_output):
    for t, tag in enumerate(stree.tags):
        stree.other_features[t].add_feat("dadeg_pos", tag)
        stree.other_features[t].add_feat("dadeg_fpos", stree.ftags[t])

    if len(gtree) > len(stree):
        j = 0
        for i in range(len(stree)):
            if gtree.words[j] == stree.words[i]:
                stree.tags[i] = gtree.tags[j]
                stree.ftags[i] = gtree.ftags[j]
                j += 1
            else:
                stree.tags[i] = gtree.tags[j]
                stree.ftags[i] = gtree.ftags[j]
                j += 2

    elif len(gtree) < len(stree):
        j = 0
        for i in range(len(gtree)):
            if gtree.words[i] == stree.words[j]:
                stree.tags[j] = gtree.tags[i]
                stree.ftags[j] = gtree.ftags[i]
                j += 1
            else:
                stree.tags[j] = gtree.tags[i]
                stree.ftags[j] = gtree.ftags[i]
                j += 1
                stree.ftags[j] = stree.tags[j] if stree.tags[j] == stree.ftags[j] else stree.tags[j] + "_" + \
                                                                                       stree.ftags[j]
                stree.ftags[j] = mapping[stree.tags[j]]
                j += 1

    else:
        stree.tags = gtree.tags
        stree.ftags = gtree.ftags

    stree.convert_tree()

DependencyTree.write_to_conllu(system_output, convert_path)
