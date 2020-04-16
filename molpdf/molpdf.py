#!/usr/bin/env python
#
# MolPDF - A publication utility package
#
# --------------------------------------

# imports
# -------
from indigo import *

# imports
# -------
import os
from functools import partial
from PIL import Image as ImagePIL

# Reportlab library modules
# -------------------------
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Reportlab platypus modules
# --------------------------
from reportlab.platypus import BaseDocTemplate, PageTemplate
from reportlab.platypus import Paragraph, Frame, Spacer, Image, Table, TableStyle, PageBreak


class RaiseMoleculeError(Exception):

    __version_error_parser__ = "1.1.0"
    __allow_update__ = False

    """

    Raise Molecule Error if for some reason we can't evaluate a SMILES, 2D, or 3D molecule.

    """
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors


class MolPDF(object):

    __version__ = '0.1.0'

    def __init__ (self, name = 'molecules.pdf'):

        """

        Arguments:
            name_of_file (String): name of the pdf file that they want to produce


        """

        if not isinstance(name, str):
            print ('Please provide a list of smiles into MolPDF')
            raise TypeError

        self.name_of_file = name
        self.doc = self._intialize_doc_template()
        self.story = []
        self.smiles = []
        self.styles = self._set_reportlab_styles()
        self.table_styles = self._set_table_styles()
        self.frame = self._create_frame()
        self.page_template = self._create_page_template()
        self.doc.addPageTemplates([self.page_template])

    def _intialize_doc_template(self):

        """

        Arguments:
            self (MolPDF Class Object): Instance of the MolPDF class

        Return:
            doc (ReportLab BaseDocTemplate Object): The initialized doc template from reportlab

        """

        # Initiate the template with the base rather than simple to install the header/footer
        doc = BaseDocTemplate(self.name_of_file, rightMargin=.1 * inch, leftMargin=.1 * inch,
                              topMargin=0.1 * inch, bottomMargin=1.5 * inch)

        return doc

    def _set_reportlab_styles(self):

        """
        Set the base stylings of the reportlab
        ​
        Returns:
            styles (Object): styles object with predefined styles to be used in the report. (Makes it easier a long the way).
        ​
        """

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))
        styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
        styles.add(ParagraphStyle(name='Line_Data', alignment=TA_LEFT, fontSize=8, leading=7))
        styles.add(ParagraphStyle(name='Line_Data_Small', alignment=TA_LEFT, fontSize=7, leading=8))
        styles.add(ParagraphStyle(name='Line_Label_Large', alignment=TA_CENTER, fontSize=12, leading=12))
        styles.add(ParagraphStyle(name='Line_Data_Largest', alignment=TA_LEFT, fontSize=14, leading=15))
        styles.add(ParagraphStyle(name='Line_Label', font='Helvetica-Bold', fontSize=7, leading=6, alignment=TA_LEFT))
        styles.add(ParagraphStyle(name='Line_Label_Spacing', font='Helvetica-Bold', fontSize=7, leading=10, alignment=TA_LEFT))
        styles.add(ParagraphStyle(name='Line_Label_Center', font='Helvetica-Bold', fontSize=7, alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='Line_Label_Center_Big', font='Helvetica-Bold', fontSize=12, alignment=TA_CENTER))

        return styles

    def _set_table_styles(self):

        """

        Return default table styles that we can use downstream for reports, will have to append as needed.
        ​
        Returns:
            table_style_with_background (Object): Table style with the background of light grey
            table_style_without_background (Object): Table style with the background as white.
        """

        table_style_with_background = TableStyle([
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightskyblue)
        ])

        table_style_without_background =TableStyle([
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN',(0,0),(-1,-1),'CENTER')
        ])

        return table_style_with_background, table_style_without_background

    def _create_frame(self):

        """

        Create the Frame for each page

        Returns:
             frame (ReportLab Frame Object): Frame of the page to prepare the canvas
        """

        frame = Frame(self.doc.leftMargin, self.doc.bottomMargin, self.doc.width, self.doc.height-0.75*inch,
                      id='footer-frame')

        return frame

    def _create_page_template(self):

        """

        Return:
            page_template (ReportLab PageTemplate Object): Set the page template


        """

        page_template = PageTemplate(id='footer-frame', frames=self.frame, onPage=partial(self._footer, styles = self.styles))

        return page_template

    def _add_spacer(self):

        """

        Add a spacer between objects. Appends to the story

        """

        self.story.append(Spacer(0.1 * inch, .3 * inch))

    def _footer(self, canvas, doc, styles):

        """

        Draw the footer
        ​
        Arguments:
            canvas (Canvas Object): Canvas to draw the footer on
            doc (ReportLab Object): Report lab document stemming from the BaseDocTemplate
            styles (Reportlab Styles Object): sample sheet styling object coming from Reportlab
        ​
        """
        #
        # Save the previous state
        canvas.saveState()

        company_address = ''

        footer_text = Paragraph(company_address, self.styles["Center"])

        # Wrap the content in
        footer_text.wrap(self.doc.width, self.doc.topMargin)
        draw_from = self.doc.topMargin
        footer_text.drawOn(canvas, self.doc.leftMargin, draw_from)

        # Restore the canvas state
        canvas.restoreState()

    def add_title(self, title):

        """

        Add a big title to the center of the page

        Arguments:
            title (String): title they would like on the page


        """

        title = Paragraph('Sample Failed Report', self.styles['Line_Label_Center_Big'])
        self.story.append(title)


    def add_image(self, path, height = 3.0, width = 1.0, alignment = "CENTER"):

        """

        Adds an image to the PDF

        Arguments:
            path (String): path to the file of the image we want to load
            height (Float): height of the image in inches
            width (Float): width of the image in inches
            alignment (String): where you would like the image to be aligned to. (CENTER, LEFT, RIGHT)


        """

        image = Image(path, height * inch, width * inch, hAlign=alignment)
        self.story.append(image)

    def _add_image_buffer(self, buffer_string):

        """

        Adds an image buffer to the pdf

        Arguments:
             buffer_string (String): the buffer string of the image

        """

        from reportlab.lib.utils import ImageReader

        report_lab_image = ImageReader(buffer_string)
        report_lab_image.getImageData()

        self.story.append(report_lab_image)

    def _generate_two_dimensional_image(self, smiles):

        """

        Arguments:
            smiles (String): smiles representation of the molecule

        Returns:
            buffer_string (String): image buffer of the string

        """

        indigo = Indigo()
        renderer = IndigoRenderer(indigo)

        molecule = indigo.loadMolecule(smiles)
        molecule.layout() # if not called, will be done automatically by the renderer
        indigo.setOption("render-output-format", "png")
        indigo.setOption("render-comment", smiles)
        indigo.setOption("render-comment-position", "top")
        indigo.setOption("render-image-size", 500, 500)
        indigo.setOption("render-background-color", 1.0, 1.0, 1.0)
        buffer_string = renderer.renderToBuffer(molecule)

        return buffer_string

    def generate(self, smiles):


        """

        Build the story and generate the final pdf

        Arguments:
            smiles (List): List of smiles you would like to pass in

        """

        self.smiles = smiles

        for smiles in self.smiles:
            self._add_image_buffer(self._generate_two_dimensional_image(smiles))

        self.doc.build(self.story)


    # def generate_ingest_failed_report(data, column_headers):
    #
    # """
    # Generates the PDF Report for wright labs according to their docx
    #
    # Arguments
    #     data (Lists of Pandas DataFrame): Data to be included in the PDF report with each row being necessary data,
    #                                         each element within the list is a dataframe transposed view of the data.
    #
    #     column_headers (List): The list of column headers associated with the ingesting.
    #
    # """
    #
    #
    #
    # # ------------------------ Overview Table ------------------------------------
    #
    # overview_information = [[
    #     Paragraph('<b>Samples Failed</b>', styles["Line_Label_Center"]),
    #     Paragraph('<b>Generated Timestamp:</b>', styles["Line_Label_Center"]),
    # ]]
    #
    # overview_table = Table(overview_information, colWidths=(2.5 * inch, 2.5 * inch))
    # overview_table.setStyle(table_style_with_background)
    # story.append(overview_table)
    # first_row = [[
    #     Paragraph(str(len(data)), styles["Line_Label_Center"]),
    #     Paragraph(str(local_now), styles["Line_Label_Center"]),
    #
    # ]]
    # first_row_table = Table(first_row, colWidths=(2.5 * inch, 2.5 *inch))
    # first_row_table.setStyle(table_style_without_background)
    # story.append(first_row_table)





# ------------ Indigo Renderer ------------------

#
# Copyright (C) 2009-2015 EPAM Systems
#
# This file is part of Indigo toolkit.
#
# This file may be distributed and/or modified under the terms of the
# GNU General Public License version 3 as published by the Free Software
# Foundation and appearing in the file LICENSE.GPL included in the
# packaging of this file.
#
# This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
# WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.

class IndigoRenderer(object):
    def __init__(self, indigo):
        self.indigo = indigo

        if os.name == 'posix' and not platform.mac_ver()[0]:
            self._lib = CDLL(indigo.dllpath + "/libindigo-renderer.so")
        elif os.name == 'nt':
            self._lib = CDLL(indigo.dllpath + "\indigo-renderer.dll")
        elif platform.mac_ver()[0]:
            self._lib = CDLL(indigo.dllpath + "/libindigo-renderer.dylib")
        else:
            raise IndigoException("unsupported OS: " + os.name)

        self._lib.indigoRender.restype = c_int
        self._lib.indigoRender.argtypes = [c_int, c_int]
        self._lib.indigoRenderToFile.restype = c_int
        self._lib.indigoRenderToFile.argtypes = [c_int, c_char_p]
        self._lib.indigoRenderGrid.restype = c_int
        self._lib.indigoRenderGrid.argtypes = [c_int, POINTER(c_int), c_int, c_int]
        self._lib.indigoRenderGridToFile.restype = c_int
        self._lib.indigoRenderGridToFile.argtypes = [c_int, POINTER(c_int), c_int, c_char_p]
        self._lib.indigoRenderReset.restype = c_int
        self._lib.indigoRenderReset.argtypes = [c_int]

    def renderToBuffer(self, obj):
        self.indigo._setSessionId()
        wb = self.indigo.writeBuffer()
        try:
            self.indigo._checkResult(self._lib.indigoRender(obj.id, wb.id))
            return wb.toBuffer()
        finally:
            wb.dispose()

    def renderToFile(self, obj, filename):
        self.indigo._setSessionId()
        self.indigo._checkResult(self._lib.indigoRenderToFile(obj.id, filename.encode('ascii')))

    def renderGridToFile(self, objects, refatoms, ncolumns, filename):
        self.indigo._setSessionId()
        arr = None
        if refatoms:
            if len(refatoms) != objects.count():
                raise IndigoException("renderGridToFile(): refatoms[] size must be equal to the number of objects")
            arr = (c_int * len(refatoms))()
            for i in range(len(refatoms)):
                arr[i] = refatoms[i]
        self.indigo._checkResult(
            self._lib.indigoRenderGridToFile(objects.id, arr, ncolumns, filename.encode('ascii')))

    def renderGridToBuffer(self, objects, refatoms, ncolumns):
        self.indigo._setSessionId()
        arr = None
        if refatoms:
            if len(refatoms) != objects.count():
                raise IndigoException("renderGridToBuffer(): refatoms[] size must be equal to the number of objects")
            arr = (c_int * len(refatoms))()
            for i in range(len(refatoms)):
                arr[i] = refatoms[i]
        wb = self.indigo.writeBuffer()
        try:
            self.indigo._checkResult(
                self._lib.indigoRenderGrid(objects.id, arr, ncolumns, wb.id))
            return wb.toBuffer()
        finally:
            wb.dispose()

# ----------------- End of Indigo Renderer -----------------

if __name__ == '__main__':


    document = MolPDF(name='test.pdf')
    document.add_title('Hello')
    smiles_list = ['C(CNC(C(C)N)=O)(=O)O']
    document.generate(smiles=smiles_list)