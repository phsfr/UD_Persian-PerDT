import random
import sys

from dep_tree import *

seraji_trees = DependencyTree.load_trees_from_conllu_file(os.path.abspath(sys.argv[1]))
dadegan_trees = DependencyTree.load_trees_from_conllu_file(os.path.abspath(sys.argv[2]))

num_samples = sum([len(t.words) for t in seraji_trees])

random.shuffle(dadegan_trees)

sampled_trees = []

word_count = 0

for t in dadegan_trees:
    word_count += len(t.words)
    sampled_trees.append(t)
    if word_count >= num_samples:
        break

print("Sampled", len(sampled_trees), "trees")
DependencyTree.write_to_conllu(sampled_trees, os.path.abspath(sys.argv[3]))
print("Finished")
