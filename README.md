# <center>CAMSS Utilities</center>
## <center>Transformation of the CAMSS Assessments, from spread-sheets to RDFs</center>
### <center>Compatible with EIF(v5), MSP(v1) and TS(v1) CAMSS Tools</center>
<center><img src="./doc/art/CAMSS Logo landscape"/></center>
<center>European Commission, ISA2 Programme, DIGIT</center>
<center><a href="mailto:camss@everis.com">camss@everis.nttdata.com</a></center>
<center><a href="https://joinup.ec.europa.eu/collection/eupl/about">UPL Licence</a><center>
<center>Build 20220118T18:00</center>
<center>Version 1.2</center>

<h2>Notebook setup</h2><br>
The camssXLS2RDF tool is a code adaptation of the previous Transformation utility (https://github.com/isa-camss/CAMSS-Ontology/blob/master/util/py/README.md).

Install requirements.txt by opening the cmd. Then, type 'cd' and copy paste the 'RDFconversor' filepath in the command line:

Example with the user 'WindowsUSER':
C:\Users\WindowsUSER> cd Downloads/RDFconversor

Finally, type the following command:

C:\Users\WindowsUSER> pip install -r requirements.txt


<h2>How can I use this notebook?</h2><br>
Place the cursor in this cell, and click on the Run buttom (in the notebook's above bar) cell by cell.<br>

<h2>What does the notebook do?</h2><br>
                            
<div>This <b>camssXLS2RDF</b> CAMSS Utilities notebook is a module that takes a spread-sheet from <a href="https://ec.europa.eu/eusurvey/home/welcome">EUSurvey</a>, in xls, xlsm or csv formats and transforms them into RDF files.<br>

It is an automated conversor designed to take any CAMSS Tools outputs from the EUSurvey platform.<br>


CAMSS Tools include several scenarios for the evaluation of standards and specifications, and ease the delivery of CAMSS Assessments grouped per scenario.<br><br> 
<h3>How do spread-sheets look like?</h3><br>
    Spread-sheets are labelled        Content_Export_CAMSSTools-VVV-XXXScenario_test_XXX<br>        (VVV: three characters for the version Tool, XXX: three characters for the Scenario, XXX: title of the specification).<br>

<h3>And then?</h3><br>
    Once the CAMSS Assessments are processed (<i>step I</i> and <i>step II</i>), RDF files are stored locally in your machine in the 'out' folder (inside the project folder) in the respective subfolders 'ass' (Assessments), 'crit' (Criteria and Scenarios) and 'specs' (standards and/or specifications) in the NQuads format, ready to be shared in CELLAR TripleStore. <br><br>Moreover, subfolders will contain the populated CAMSS Knowledge Graph: that is, the CAMSS Assessments Graphs, the CAMSS Scenarios and Critera Graphs and the Specifications Graphs, respectively.<br><br>
<b>You might want  to convert the NQuads files into Turtle or JSON-LD in <i>step III</i> and explore them in <i>step IV</i>.</b>
    </div><br>
    
## I. CAMSS Assessments extraction

A) Spread-sheets are placed in the 'in' folder. This notebook gets inside the 'in' folder and processes all the spread-sheets.<br><br>

B) Automatic identification of the CAMSS Tools scenario (see reference in EUSurvey) and extraction all the Assessments.<br><br>

C) Follow the progress of the RDF Conversor.

## II. Merging all Assessment-NQuads files into one single NQuads file 

The individual Assessment NQuads files from folders 'ass/nq', 'crit/nq' and 'specs/nq', produced after extraction, are merged in one single NQuads file and placed in folders 'ass', 'crit' and 'specs', respectively.<br><br><b>Keep running the code from this cell.<b>

## III. Transformer command: from NQuads to Turtle and JSON-LD

In this third step, NQuads files are transformed to Turtle and JSON-LD files.

## IV. Explore your results
You might want to explore any of the RDF files that were created for any format, any Graph (individual or dataset graphs).

























