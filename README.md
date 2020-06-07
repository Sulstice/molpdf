MolPDF: A PDF Document Generator for SMILES!
============================================

[![License: MPL 2.0](https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)
![Python](https://img.shields.io/badge/python-3.6-blue.svg)


Welcome to MolPDF! The document generator for cheminformatics! MolPDF does one thing right now and is convert a list of 1D 
SMILES to a 2D image into a PDF! It's super lightweight and only requires python 3.4 >+. 

MolPDF is super new and under heavy development so if there are any bugs then please report them! Eventually, I will be able 
to get some docs, jupyter notebooks, and some asciis but in the meantime check out the source code and play around. 

Announcements
=============

-   June 7th 2020 First version 0.1.0 is released to the public

Installation 
============

MolPDF is going to be distribute via PyPi and as the content store grows we can expand it to other pieces of software
making it accessible to all regardless of what you use. Alternatively, you could have a glance at the source code and copy/paste
it yourself.

QuickStart
==========

Generate a PDF of SMILES

```
    
    document = MolPDF(name='example.pdf')
    document.add_title('Chemical Library Test')
    document.add_spacer()
    smiles_list = ['C(CNC(C(C)N)=O)(=O)O', 'C(CNC(C(C)N)=O)(=O)O', 'C(CNC(C(C)N)=O)(=O)O']
    document.generate(smiles=smiles_list)

```

Structure of MolPDF
=======================

Currently, the main subpackages are:

- **molpdf**: molpdf main class. 


Genesis
=======

MolPDF was developed so I could publish chemical libraries in an easy supporting information minable data for publications. 
I hope to make it easy for folk by making it a solely lightweight python package with only requirements to be reportlab. 

- Lead Developer [Suliman sharif](http://sulstice.github.io/)

* * * * *

External links
==============


