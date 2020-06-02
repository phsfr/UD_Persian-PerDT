import os

if not os.path.exists("Universal_Dadegan"):
    os.makedirs("Universal_Dadegan")
if not os.path.exists("Universal_Dadegan_with_DepRels"):
    os.makedirs("Universal_Dadegan_with_DepRels")
if not os.path.exists("Universal_Dadegan_with_DepRels"):
    os.makedirs("Universal_Dadegan_with_DepRels")
if not os.path.exists("UD_Dadegan"):
    os.makedirs("UD_Dadegan")
if not os.path.exists("UD_Dadegan-nt"):
    os.makedirs("UD_Dadegan-nt")
if not os.path.exists("parser_data"):
    os.makedirs("parser_data")
if not os.path.exists("parser_data/dadegan"):
    os.makedirs("parser_data/dadegan")
if not os.path.exists("parser_data/dadegan-nt"):
    os.makedirs("parser_data/dadegan-nt")
if not os.path.exists("parser_data/seraji"):
    os.makedirs("parser_data/seraji")
if not os.path.exists("parser_data/seraji-nt"):
    os.makedirs("parser_data/seraji-nt")
if not os.path.exists("parser_data/d+s"):
    os.makedirs("parser_data/d+s")
if not os.path.exists("parser_data/d+s-nt"):
    os.makedirs("parser_data/d+s-nt")

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

print("converting_feats.py")
os.system("python3 -u converting_feats.py")

print("tree_checker.py")
os.system("python3 -u tree_checker.py")

print("remove_subtypes.py")
os.system("python3 -u remove_subtypes.py")

os.system("python3 remove_feat_column.py UD_Dadegan/ parser_data//dadegan/")
os.system("python3 remove_feat_column.py UD_Dadegan-nt/ parser_data//dadegan-nt/")
os.system("python3 remove_feat_column.py Dadegan_univ_tok/ parser_data//dadegan_orig/ xpos")

os.system(
    "cat parser_data/dadegan/fa_dadegan-ud-train.conllu parser_data/seraji/fa_seraji-ud-train.conllu > parser_data/d+s/train.conllu")
os.system(
    "cat parser_data/dadegan/fa_dadegan-ud-dev.conllu parser_data/seraji/fa_seraji-ud-dev.conllu > parser_data/d+s/dev.conllu")
os.system(
    "cat parser_data/dadegan/fa_dadegan-ud-test.conllu parser_data/seraji/fa_seraji-ud-test.conllu > parser_data/d+s/test.conllu")
os.system(
    "cat parser_data/dadegan-nt/fa_dadegan-ud-test.conllu parser_data/seraji-nt/fa_seraji-ud-test.conllu > parser_data/d+s-nt/test.conllu")
os.system(
    "cat parser_data/dadegan-nt/fa_dadegan-ud-train.conllu parser_data/seraji-nt/fa_seraji-ud-train.conllu > parser_data/d+s-nt/train.conllu")
os.system(
    "cat parser_data/dadegan-nt/fa_dadegan-ud-dev.conllu parser_data/seraji-nt/fa_seraji-ud-dev.conllu > parser_data/d+s-nt/dev.conllu")

os.system("python3 remove_feat_column.py UD_Dadegan/ parser_data//dadegan/ xpos")
os.system("python3 remove_feat_column.py UD_Dadegan-nt/ parser_data//dadegan-nt/ xpos")
os.system("python3 conllu2raw.py UD_Dadegan parser_data/dadegan_raw/")
os.system("python3 conllu2raw.py parser_data/seraji-nt parser_data/seraji_raw/")

print("FINISHED!")
