from collections import defaultdict
from dep_tree import Features, DependencyTree

if __name__ == '__main__':
    input_files = ['Persian_Dependency_Treebank_(PerDT)_V1.1.1/Data/train.conll',
                   'Persian_Dependency_Treebank_(PerDT)_V1.1.1/Data//dev.conll',
                   'Persian_Dependency_Treebank_(PerDT)_V1.1.1/Data//test.conll']
    output_files = ['Persian_Dependency_Treebank_(PerDT)_V1.1.1/Data/train.conll',
                    'Persian_Dependency_Treebank_(PerDT)_V1.1.1/Data//dev.conll',
                    'Persian_Dependency_Treebank_(PerDT)_V1.1.1/Data//test.conll']

    for f_idx, inp_f in enumerate(input_files):
        parcl_trees = []
        tree_list = DependencyTree.load_trees_from_conll_file(inp_f)
        for i, tree in enumerate(tree_list):
            if "PARCL" in tree.labels:
                parcl_trees.append(tree)

        print("Visiting parcl trees")
        labels = set()
        to_visit_trees = []
        for tree in parcl_trees:
            include_tree = False
            parcl_idx = [i for i, label in enumerate(tree.labels) if label == "PARCL"]
            for idx in parcl_idx:
                head_index = tree.heads[idx]
                head_id = head_index - 1

                for dep in range(0, idx):
                    if tree.heads[dep] > idx + 1:
                        if tree.labels[dep] not in {"PREDEP", "PARCL", "MOS", "NVE", "VPP", "PUNC", "OBJ", "NPP",
                                                    "VCONJ"}:
                            if tree.labels[dep] in {"SBJ", "AJUCL"}:
                                # Change the head for SBJ/AJUCL
                                tree.heads[dep] = idx + 1
                                include_tree = True
                            labels.add(tree.labels[dep])
            if include_tree:
                to_visit_trees.append(tree)

        DependencyTree.write_to_conll(tree_list, output_files[f_idx])
        print(len(parcl_trees), len(to_visit_trees))
        print(labels)
