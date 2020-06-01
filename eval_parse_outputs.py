import os
import sys

input_path = os.path.abspath(sys.argv[1])
output_path = os.path.abspath(sys.argv[2])

seraji_prefix = "/fa_seraji-ud-"
dadegan_prefix = "/fa_dadegan-ud-"

model_names = ["dadegan", "seraji", "d+s"]

for model_name in model_names:
    output_folder = os.path.join(output_path, model_name)
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)

    for file_type in ["test.conllu"]:
        nt_str = "-nt" if model_name.endswith("-nt") else ""
        seraji_input = input_path + "/seraji" + nt_str + seraji_prefix + file_type
        seraji_output = os.path.join(output_folder, "seraji." + file_type)
        print("\n", model_name, "Seraji", file_type)
        os.system("python3 eval/conll18_ud_eval.py " + seraji_input + " " + seraji_output + " -v")

        dadegan_input = input_path + "/dadegan" + nt_str + dadegan_prefix + file_type
        dadegan_output = os.path.join(output_folder, "dadegan." + file_type)
        print("\n", model_name, "Dadegan", file_type)
        os.system("python3 eval/conll18_ud_eval.py " + dadegan_input + " " + dadegan_output + " -v")

print("FINISHED")
