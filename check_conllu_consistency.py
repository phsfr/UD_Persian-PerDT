import sys

from dep_tree import *

if __name__ == '__main__':
    file1 = os.path.abspath(sys.argv[1])
    file2 = os.path.abspath(sys.argv[2])

    trees1: List[DependencyTree] = DependencyTree.load_trees_from_conllu_file(file1)
    trees2: List[DependencyTree] = DependencyTree.load_trees_from_conllu_file(file2)

    assert len(trees1) == len(trees2)

    for i, (t1, t2) in enumerate(zip(trees1, trees2)):
        assert t1.sent_str == t2.sent_str
        tchars1, tchars2 = [], []
        for w in t1.words:
            tchars1.extend(w)
        for w in t2.words:
            tchars2.extend(w)
        if len(t1.words) != len(t2.words):
            print(" ".join(t1.words))
            print(" ".join(t2.words))
            print("$$$")
        if tchars1 != tchars2:
            print(t1.sen_id)
        # assert tchars1 == tchars2
