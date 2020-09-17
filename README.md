# Universal Persian Dependency Treebank (v1.0)

# Summary
Universal Persian Dependency Treebank (UPerDT) is the result of automatic coversion of Persian Dependency Treebank (PerDT) with extensive manual corrections. 

# Introduction
Universal Persian Dependency Treebank (UPerDT) is based on <a href="https://www.aclweb.org/anthology/N13-1031v1.pdf"> Persian Dependency Treebank (PerDT) </a>(Rasooli et al.,2013). The original Treebank consists of 29K sentences sampled from contemporary Persian text in different genres including: news, academic papers, magazine articles and fictions. 

Treebank was annotated based on language specific schema and its automatic conversion involved three main steps: revising tokenization, POS mapping and dependency mapping. 

In tokenization step, in order to separate multiword inflections of simple verbs grouped as one token in PerDT, we followed the guidelines in (Rasooli et al., 2013, Table 3) to automatically find the main verbs. Also we automatically separated pronominal clitics. 

In POS conversion step, we used the state of the art <a href="https://arxiv.org/abs/2003.08875"> BERT-based Persian NER tagger</a> (Taher et al.,2020) with manual corrections to extend recall. Through seven different entities detected by tagger, we used Person and Location to mark PROPN tags. 

In the last step, dependency mapping, there was a lot of challenges. PerDT contains 43 syntactic relations with no straightforward mapping for most of them, conjunctions arranged from the beginning of the sentence to the end and more importantly, prepositions regarded as the head of prepositional phrases and auxiliary verbs as the head of sentences. So we rearranged the order of conjunctions from end to the beginning through a script and tailored rules to convert each kind of relation to its UD version properly. Through the whole process and at the end of each step, we investigated the results and applied manual corrections if it was needed.  

# Acknowledgements

#

# STATISTICAL OVERVIEW OF UNIVERSAL PERDT


# DATA SPLIT
We followed the same split used in PerDT.

# FEEDBACK AND BUG REPORTS
For feedback and bug reports, please contact rasooli@seas.upenn.edu and pegh.safari@gmail.com.


# REFERENCES

1. Rasooli, Mohammad Sadegh, Manouchehr Kouhestani, and Amirsaeid Moloodi. "Development of a Persian syntactic dependency treebank." Proceedings of the 2013 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies. 2013.
2. Taher, Ehsan, Seyed Abbas Hoseini, and Mehrnoush Shamsfard. "Beheshti-NER: Persian named entity recognition Using BERT." arXiv preprint arXiv:2003.08875 (2020).



# CHANGELOG




<pre>
=== Machine-readable metadata (DO NOT REMOVE!) ================================
Data available since: UD v1.0
License: CC BY-SA 4.0
Includes text: yes
Genre: news fiction nonfiction academic web blog
Lemmas: converted with corrections 
UPOS: converted from manual
XPOS: manual native
Features: converted with corrections
Relations: converted with corrections 
Contributors: Rasooli, Mohammad Sadegh; Safari, Pegah; Moloodi, AmirSaeid; Nourian, Alireza
Contributing: here source
Contact: rasooli@seas.upenn.edu, pegh.safari@gmail.com
===============================================================================
</pre>
