import os
import re
import sys

import stanza


def parse(nlp, content):
    tokens = []
    doc = nlp(content)
    for s in range(len(doc.sentences)):
        for word in doc.sentences[s].words:
            if '-' in str(word.id):
                tokens.append(
                    "\t".join([str(x) for x in [word.id, word.text, "_", "_", "_", word.misc, "_", "_", "_", "_"]]))
            else:
                tokens.append("\t".join([str(x) for x in
                                         [word.id, word.text, word.lemma, word.upos, word.xpos, word.misc, word.head,
                                          word.deprel, "_", "_"]]))
    return "\n".join(tokens)


file_path = os.path.abspath(sys.argv[1])

lang = file_path
if "/" in lang:
    lang = lang[lang.rfind("/") + 1:]
lang = lang[:lang.find("-")]

parser = stanza.Pipeline("fa", processors='tokenize,lemma,mwt,pos,depparse')

output_path = os.path.abspath(sys.argv[2])

sent_num = 0
with open(output_path, "w") as writer:
    content = open(file_path, "r").read().split("\n")

    for i, l in enumerate(content):
        if l.strip().startswith('# sent_id ='):
            writer.write(l.strip() + '\n')
        if l.strip().startswith('# text ='):
            raw = l.strip()[8:].strip()
            raw = re.sub(r'\s+', ' ', raw)
            writer.write(l.strip() + '\n')
            sentence = parse(parser, u''.join(raw))
            writer.write(sentence)
            writer.write("\n\n")
            sent_num += 1
            if sent_num % 100 == 0:
                print(sent_num)

print("done!")
