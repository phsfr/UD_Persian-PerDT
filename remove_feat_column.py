import sys

from dep_tree import *
from dep_tree import remove_semispace

# For removing feature column!

if __name__ == '__main__':
    input_folder = os.path.abspath(sys.argv[1])
    output_folder = os.path.abspath(sys.argv[2])
    remove_xpos = True
    if len(sys.argv)>3:
        if sys.argv[3] == "xpos":
            remove_xpos = False

    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)

    for file in os.listdir(input_folder):
        input_path = os.path.join(input_folder, file)
        output_path = os.path.join(output_folder, file)
        print(input_path)
        univ_trees: List[DependencyTree] = DependencyTree.load_trees_from_conllu_file(input_path)
        for t, univ_tree in enumerate(univ_trees):
            for l, label in enumerate(univ_tree.labels):
                univ_tree.other_features[l].feat_str = "_"
                if remove_xpos:
                    univ_tree.ftags[l] = "_"
                univ_tree.words[l] = remove_semispace(univ_tree.words[l])

        DependencyTree.write_to_conllu(univ_trees, output_path)
