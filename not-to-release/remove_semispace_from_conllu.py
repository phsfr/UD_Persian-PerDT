import sys

from dep_tree import *

if __name__ == '__main__':
    inputfile = os.path.abspath(sys.argv[1])
    outputfile = os.path.abspath(sys.argv[2])

    trees: List[DependencyTree] = DependencyTree.load_trees_from_conllu_file(inputfile)

    for tree in trees:
        tree.sent_descript = tree.sent_descript.replace("‌", "")
        for i in range(len(tree.words)):
            tree.lemmas[i] = tree.lemmas[i].replace("‌", "")
            tree.words[i] = tree.words[i].replace("‌", "")
            هب

    DependencyTree.write_to_conllu(trees, outputfile)
