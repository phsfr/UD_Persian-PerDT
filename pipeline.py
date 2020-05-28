import os

print("fix_dadegan_deps.py")
os.system("python3 -u fix_dadegan_deps.py")

print("convertNERtoPrn.py")
os.system("python3 -u convertNERtoPrn.py")

print("process_Dadegan_PROPN.py")
os.system("python3 -u process_Dadegan_PROPN.py")

print("generate_dadegan_w_univ_tokenization.py")
os.system("python3 -u generate_dadegan_w_univ_tokenization.py")

print("dep_tree.py")
os.system("python3 -u dep_tree.py")

print("merge_stanza.py")
os.system("python3 -u merge_stanza.py")

print("tree_checker.py")
os.system("python3 -u tree_checker.py")

print("remove_subtypes.py")
os.system("python3 -u remove_subtypes.py")

print("FINISHED!")
