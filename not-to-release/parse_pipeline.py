import os
import sys

udpipe = os.path.abspath(sys.argv[1])
model_path = os.path.abspath(sys.argv[2])
input_path = os.path.abspath(sys.argv[3])
output_path = os.path.abspath(sys.argv[4])

seraji_prefix = "/seraji_raw/fa_seraji-ud-"
dadegan_prefix = "/dadegan_raw/fa_dadegan-ud-"

model_names = ["dadegan", "dadegan_orig", "seraji", "d+s"]
parse_commands = "--tokenize --tag --parse --parser=embedding_form_file=/nlp/data/rasooli/ud_per/word_vector/cc.fa.300.vec --tokenizer=presegmented"
format_commands = "--output=conllu --input=horizontal"

for model_name in ["dadegan", "seraji"]:
    tag_commands = "--tokenize --tag --tokenizer=presegmented"
    tag_format_commands = "--output=conllu --input=horizontal"

    p_commands = "--parse --parser=embedding_form_file=/nlp/data/rasooli/ud_per/word_vector/cc.fa.300.vec"
    p_format_commands = "--output=conllu --input=conllu"

    for file_type in ["dev.conllu", "test.conllu"]:
        file_prefix = seraji_prefix if model_name == "seraji" else dadegan_prefix
        nt_file_prefix = seraji_prefix if model_name == "dadegan" else dadegan_prefix
        parse_model_name = "dadegan" if model_name == "seraji" else "seraji"
        ds_parse_model_name = "d+s"

        input = input_path + file_prefix + file_type[:-7] + ".txt"
        output_folder = os.path.join(output_path, model_name)
        model = os.path.join(model_path, model_name + ".model")
        pos_output = os.path.join(output_folder, model_name + ".pos." + file_type)
        tag_command = " ".join([udpipe, tag_commands, model, tag_format_commands, input, ">", pos_output])
        print(tag_command)
        os.system(tag_command)

        output_folder = os.path.join(output_path, parse_model_name)
        parse_model = os.path.join(model_path, parse_model_name + ".model")
        parse_output = os.path.join(output_folder, model_name + ".pos.parse." + file_type)
        parse_command = " ".join(
            [udpipe, p_commands, parse_model, p_format_commands, pos_output, ">", parse_output])
        print(parse_command)
        os.system(parse_command + " &")

        output_folder = os.path.join(output_path, ds_parse_model_name)
        ds_parse_model = os.path.join(model_path, ds_parse_model_name + ".model")
        ds_parse_output = os.path.join(output_folder, model_name + ".pos.parse." + file_type)
        ds_parse_command = " ".join(
            [udpipe, p_commands, ds_parse_model, p_format_commands, pos_output, ">", ds_parse_output])
        print(ds_parse_command)
        os.system(ds_parse_command + " &")

for model_name in model_names:
    output_folder = os.path.join(output_path, model_name)
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)

    for file_type in ["dev.conllu", "test.conllu"]:
        seraji_input = input_path + seraji_prefix + file_type[:-7] + ".txt"
        dadegan_input = input_path + dadegan_prefix + file_type[:-7] + ".txt"
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
