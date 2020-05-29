import os
import sys

reader1 = open(os.path.abspath(sys.argv[1]), 'r')
writer1 = open(os.path.abspath(sys.argv[2]), 'w')

delex = False
if len(sys.argv) > 3 and sys.argv[3] == "delex":
    delex = True

line1 = reader1.readline()

while line1:
    if len(line1.strip()) == 0:
        writer1.write(line1)
    else:
        spl = line1.strip().split('\t')
        if len(spl) > 2:
            if not '.' in spl[0] and spl[0].isdigit():
                if ':' in spl[7]:
                    spl[7] = spl[7][:spl[7].rfind(':')]
                if spl[6] == '_' or spl[6] == '-':
                    spl[6] = '-1'
                if delex:
                    spl[1] = "_"
                    spl[2] = "_"
                writer1.write('\t'.join(spl) + '\n')

    line1 = reader1.readline()
writer1.close()
