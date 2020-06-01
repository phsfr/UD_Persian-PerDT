import sys

from dep_tree import *

gold_standard: List[DependencyTree] = DependencyTree.load_trees_from_conllu_file(os.path.abspath(sys.argv[1]))
system_output: List[DependencyTree] = DependencyTree.load_trees_from_conllu_file(os.path.abspath(sys.argv[2]))

correct_head, all_head = 0, 0
correct_label = 0

tp =defaultdict(int)
fp = defaultdict(int)
fn = defaultdict(int)

label_freq = defaultdict(int)

for gtree, stree in zip(gold_standard, system_output):
    s_id = {}
    try:
        if len(gtree) > len(stree):
            j = 0
            for i in range(len(stree)):
                if remove_semispace(gtree.words[j]) == remove_semispace(stree.words[i]):
                    s_id[i] = j
                    j += 1
                else:
                    s_id[i] = j
                    j += 2

        elif len(gtree) < len(stree):
            j = 0
            for i in range(len(gtree)):
                if remove_semispace(gtree.words[i]) == remove_semispace(stree.words[j]):
                    s_id[j] = i
                    j += 1
                else:
                    s_id[j] = i
                    j += 1
                    s_id[j] = i
                    j += 1

        else:
            s_id = {i:i for i in range(len(stree))}

        for label in gtree.labels:
            label_freq[label] += 1

        for i in range(min(len(stree), len(gtree))):
            sys_head = stree.heads[i]
            sys_head = 0 if sys_head == 0 else s_id[sys_head-1] + 1
            sys_id = s_id[i]

            gold_head = gtree.heads[sys_id]
            gold_label = gtree.labels[sys_id]

            if gold_head == sys_head:
                correct_head += 1
                if gold_label == stree.labels[i]:
                    correct_label += 1
                    tp[gold_label] += 1
            else:
                fp[stree.labels[i]] += 1
                fn[gold_label] += 1
        all_head += len(stree)

    except:
        print(gtree.sent_descript)

print(round(100.*correct_head/all_head,2))
print(round(100.*correct_label/all_head,2))

lowest, lowest_label = 100, "root"
fscores = {}
for label in label_freq.keys():
    precision =round(100* tp[label] / (fp[label] + tp[label]), 2) if fp[label] + tp[label]>0 else 0
    recall = round(100*tp[label] / (fn[label] + tp[label]), 2) if fn[label] + tp[label]>0 else 0
    f = round(2*precision*recall / (precision + recall), 2) if precision + recall>0 else 0
    if f<lowest:
        lowest = f
        lowest_label = label
    fscores[label] = f
    print (label, precision, recall, f)

print(lowest, lowest_label)

all_count = sum(label_freq.values())
label_freq = {x:round(100.*v/all_count, 2) for x,v in label_freq.items()}
print(sorted(label_freq.items(), key=lambda x: x[1]))
print(sorted(fscores.items(), key=lambda x: x[1]))