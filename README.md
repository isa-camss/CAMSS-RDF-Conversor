<h1><center>CAMSS Utilities</center></h1>
<h1><center>Transformation of the CAMSS Assessments, from spread-sheets to RDFs</center></h1>
<h2><center>Compatible with EIF(v5), MSP(v1) and TS(v1) CAMSS Tools</center></h2>
<center><img src="./img/CAMSS Logo landscape"/></center>
<center>European Commission, ISA2 Programme, DIGIT</center>
<center><a href="mailto:camss@everis.com">camss@everis.nttdata.com</a></center>
<center><a href="https://joinup.ec.europa.eu/collection/eupl/about">UPL Licence</a><center>
<center>Build 20220118T18:00</center>
<center>Version 1.2</center>

<h2>Folder setup</h2><br>
See instructions in arti README.md.

<h2>Notebook setup</h2><br>
The camssXLS2RDF tool is a code adaptation of the previous Transformation utility (https://github.com/isa-camss/CAMSS-Ontology/blob/master/util/py/README.md).

After have cloned the CAMSS-RDF-Conversor repository, install requirements.txt by: opening the cmd, the typing 'cd' and copy-pasting the 'CAMSS-RDF-Conversor' filepath in the command line.

Example with the user 'WindowsUSER':
C:\Users\WindowsUSER> cd path_to/CAMSS-RDF-Conversor

Finally, type the following command:

C:\Users\WindowsUSER\path_to\CAMSS-RDF-Conversor> pip install -r requirements.txt


<h2>How can I use this notebook?</h2><br>
Place the cursor in this cell, and click on the Run buttom (in the notebook's above bar) cell by cell.<br>

<h2>What does the notebook do?</h2><br>
                            
<div>This <b>camssXLS2RDF</b> CAMSS Utilities notebook is a module that takes a spread-sheet from <a href="https://ec.europa.eu/eusurvey/home/welcome">EUSurvey</a>, in xls, xlsm or csv formats and transforms them into RDF files.<br>

It is an automated conversor designed to take any CAMSS Tools outputs from the EUSurvey platform.<br>


CAMSS Tools include several scenarios for the evaluation of standards and specifications, and ease the delivery of CAMSS Assessments grouped per scenario.<br><br> 
<h3>How do spread-sheets look like?</h3><br>
    Spread-sheets are labelled        <center>Content_Export_XXXScenario_vVVV _NAME</center><br>        (VVV: three characters for the version Tool, XXX: three characters for the Scenario, NAME: naming of the CAMSS Assessment Scenario -which should be a representative name).<br>

<h3>And then?</h3><br>
    Once the CAMSS Assessments are processed (<i>step I</i> and <i>step II</i>), RDF files are stored locally in your machine in the 'out' folder (inside the project folder) in the respective subfolders 'ass' (Assessments), 'crit' (Criteria and Scenarios) and 'specs' (standards and/or specifications) in the NQuads format, ready to be shared in CELLAR TripleStore. <br><br>Moreover, subfolders will contain the populated CAMSS Knowledge Graph: that is, the CAMSS Assessments Graphs, the CAMSS Scenarios and Critera Graphs and the Specifications Graphs, respectively.<br><br>
<b>You might want  to convert the NQuads files into Turtle or JSON-LD in <i>step III</i> and explore them in <i>step IV</i>.</b>
    </div><br>
    
<h2><b>I. CAMSS Assessments extraction</h2></b>

A) Spread-sheets are placed in the 'in' folder. This notebook gets inside the 'in' folder and processes all the spread-sheets.<br><br>

B) Automatic identification of the CAMSS Tools scenario (see reference in EUSurvey) and extraction all the Assessments.<br><br>

C) Follow the progress of the RDF Conversor.

<h2><b>II. Merging all Assessment-NQuads files into one single NQuads file</h2></b>

The individual Assessment NQuads files from folders 'arti/out/ass/nq', 'arti/out/crit/nq' and 'arti/out/specs/nq', produced after extraction, are merged in one single NQuads file and placed in folders 'arti/out/ass', 'arti/out/crit' and 'arti/out/specs', respectively.<br><br><b>Keep running the code from this cell.<b>

<h2><b>III. Transformer command: from NQuads to Turtle and JSON-LD</h2></b>

In this third step, NQuads files are transformed to Turtle and JSON-LD files.

<h2><b>IV. Explore your results</h2></b>
You might want to explore any of the RDF files that were created for any format, any Graph (individual or dataset graphs).


























