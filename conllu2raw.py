import sys

from dep_tree import *

if __name__ == '__main__':
    input_folder = os.path.abspath(sys.argv[1])
    output_folder = os.path.abspath(sys.argv[2])

    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)

    for file in os.listdir(input_folder):
        input_path = os.path.join(input_folder, file)
        output_path = os.path.join(output_folder, file)
        if output_path.endswith(".conllu"):
            output_path = output_path[:-6] + "txt"
        print(input_path)
        with open(output_path, "w") as writer:
            univ_trees: List[DependencyTree] = DependencyTree.load_trees_from_conllu_file(input_path)
            for t, univ_tree in enumerate(univ_trees):
                sent_str = univ_tree.sent_str.strip()
                if sent_str.startswith("# text ="):
                    sent_str = sent_str[len("# text ="):].strip()
                writer.write(sent_str)
                writer.write("\n")
