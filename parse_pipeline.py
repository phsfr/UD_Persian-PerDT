import os
import sys

udpipe = os.path.abspath(sys.argv[1])
model_path = os.path.abspath(sys.argv[2])
input_path = os.path.abspath(sys.argv[3])
output_path = os.path.abspath(sys.argv[4])

seraji_prefix = "/seraji_raw/fa_seraji-ud-"
dadegan_prefix = "/dadegan_raw/fa_dadegan-ud-"

model_names = ["dadegan", "dadegan-nt", "dadegan_orig", "seraji", "seraji-nt", "d+s", "d+s-nt"]
parse_commands = "--tokenize --tag --parse --parser=embedding_form_file=/nlp/data/rasooli/ud_per/word_vector/cc.fa.300.vec --tokenizer=presegmented"
format_commands = "--output=conllu --input=horizontal"

for model_name in model_names:
    output_folder = os.path.join(output_path, model_name)
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)

    for file_type in ["train.conllu", "dev.conllu", "test.conllu"]:
        seraji_input = input_path + seraji_prefix + file_type
        dadegan_input = input_path + dadegan_prefix + file_type
        seraji_output = os.path.join(output_folder, "seraji." + file_type)
        dadegan_output = os.path.join(output_folder, "dadegan." + file_type)
        model = os.path.join(model_path, model_name + ".model")
        seraji_command = " ".join([udpipe, parse_commands, model, format_commands, seraji_input, ">", seraji_output])
        print(seraji_command)
        os.system(seraji_command + " &")
        dadegan_command = " ".join([udpipe, parse_commands, model, format_commands, dadegan_input, ">", dadegan_output])
        print(dadegan_command)
        os.system(dadegan_command)

print("FINISHED")
