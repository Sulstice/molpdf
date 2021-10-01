#!/usr/bin/env python
#
# MolPDF - A publication utility package
#
# --------------------------------------

# imports
# -------
import os
import tempfile
import shutil
from indigo import *
from functools import partial
from pathlib import Path
import platform

# PDFRW library modules
# ---------------------
from pdfrw import PdfReader, PdfWriter

# PDF library modules
# -------------------
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument

# Reportlab library modules
# -------------------------
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Reportlab platypus modules
# --------------------------
from reportlab.platypus import BaseDocTemplate, PageTemplate, Table
from reportlab.platypus import Paragraph, Frame, Spacer, Image, TableStyle, Flowable

# Reportlab utils modules
# -----------------------
from reportlab.lib.utils import ImageReader

# Reportlab pdfgen modules
# ------------------------
from reportlab.pdfgen import canvas

import time

def timeit(method):

    def timed(*args, **kwargs):
        time_start = time.time()
        result = method(*args, **kwargs)
        time_end = time.time()


        if 'log_time' in kwargs:
            name = kwargs.get('log_name', method.__name__.upper())
            kwargs['log_time'][name] = int((time_end -time_start))
        else:
            print ('Method: %r Time: %2.2f seconds' % (method.__name__, ((time_end - time_start))))
        return result

    return timed

class RaiseMoleculeError(Exception):

    __version_error_parser__ = "1.1.0"
    __allow_update__ = False

    """

    Raise Molecule Error if for some reason we can't evaluate a SMILES, 2D, or 3D molecule.

    """
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors

class flowable_fig(Flowable):

    def __init__(self, imgdata):
        Flowable.__init__(self)
        self.img = ImageReader(imgdata)

    def draw(self):
        self.canv.drawImage(self.img, 0, 0, height = -2*inch, width=4*inch)


class MolPDFParser(object):

    __version__ = '0.1.0'

    def __init__ (self, file_path):

        self.file_path = file_path
        self.molpdf = open(self.file_path, 'rb')
        self.parser = PDFParser(self.molpdf)
        self.document = PDFDocument(self.parser)


    def extract_smiles(self):

        """

        Extract the smiles data coming out the PDF

        Returns:
            smiles_list (List): List of SMILES strings from the metadata of the PDF


        """

        smiles_list = self.document.info[0]['smiles_list']

        return smiles_list

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

        self.name = name
        self.doc = self._intialize_doc_template()
        self.story = []
        self.temp_dir_name = ''
        self.smiles = []
        self.styles = self._set_reportlab_styles()
        self.table_style_with_background, self.table_style_without_background = self._set_table_styles()
        self.frame = self._create_frame()
        self.canvas = canvas.Canvas(self.name)
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
        doc = BaseDocTemplate(self.name, rightMargin=.1 * inch, leftMargin=.1 * inch,
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
        styles.add(ParagraphStyle(name='Line_Label_Center', font='Roboto', fontSize=5, alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='Line_Label_Center_Big', font='Helvetica-Bold', fontSize=9, alignment=TA_CENTER))

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
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.lightblue),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.lightblue),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightsalmon),
        ])

        table_style_without_background =TableStyle([
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.lightblue),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.lightblue),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
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

    def add_spacer(self):

        """

        Add a spacer between objects. Appends to the story

        """

        self.story.append(Spacer(0.1 * inch, .3 * inch))

    def _header(self, canvas, doc, styles):
        """
        Draws the header on a canvas.

        Arguments:
            canvas (Canvas Object): Canvas to draw the header on
            doc (ReportLab Object): Report lab document stemming from the BaseDocTemplate

        """
        # Save the previous state
        canvas.saveState()

        header_text = ''

        header_text = Paragraph("<b></b> <br />" + header_text, styles["Right"])

        # Wrap the content in
        width, height = header_text.wrap(doc.width, doc.topMargin)
        draw_from = doc.height + doc.topMargin + height

        header_text.drawOn(canvas, doc.leftMargin, draw_from)
        canvas.setLineWidth(0.9)
        canvas.setStrokeColor(colors.teal)
        canvas.line(3,draw_from-3,600,draw_from-3)

        # Restore the canvas state
        canvas.restoreState()

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

        footer_text = ''

        footer_text = Paragraph(footer_text, self.styles["Center"])

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

        title = Paragraph(title, self.styles['Line_Label_Center_Big'])
        self.story.append(title)

    def add_image(self, temporary_directory, include_failed_smiles=False):

        """

        Arguments:
            temporary_directory (tempfile object): Temporary directory of the module
            include_failed_smiles (Bool): whether the user would like to include failed smiles.

        """

        indigo = Indigo()
        renderer = IndigoRenderer(indigo)

        chemical_data = []

        for smiles in self.smiles:

            try:
                molecule = indigo.loadMolecule(smiles)
            except IndigoException as e:
                if include_failed_smiles:
                    self.add_row("Failed Rendering", smiles)
                return

            molecule.layout() # if not called, will be done automatically by the renderer
            indigo.setOption("render-output-format", "png")
            indigo.setOption("render-image-size", 200, 200)
            indigo.setOption("render-background-color", 1.0, 1.0, 1.0)

            import uuid

            path = os.path.join(temporary_directory,  str(uuid.uuid4()) + '.png')

            renderer.renderToFile(molecule, filename=path)
            image = Image(path, 0.5 * inch, 0.5 * inch, hAlign='CENTER')

            chemical_data.append([image, smiles])

        self.add_table(chemical_data)


    def _create_temp_directory(self):

        """

        Prepare a temporary directory to render the molecule images.

        Creates:
            tmp (directory): create a directory in the cwd.

        """

        from tempfile import gettempdir
        tmp = os.path.join(gettempdir(), '.{}'.format(hash(os.times())))
        os.makedirs(tmp)

        return tmp


    def _destroy_temp_directory(self, tmp):

        """

        Destroys the temporary directory as a part of cleanup

        """

        shutil.rmtree(tmp, ignore_errors=True)

    def _add_table_label(self, smiles):

        """

        Generate the table header - pretty simple for now and keeping with molecule 2D images and the SMILES.


        """

        overview_information = [[
            Paragraph('%s' % smiles, self.styles["Line_Label_Center"]),
        ]]

        overview_table = Table(overview_information, colWidths=(1.5 * inch))
        overview_table.setStyle(self.table_style_with_background)
        self.story.append(overview_table)

    def add_table(self, chemical_data):

        """

        Adds a row of the 2D image of a molecule and then the SMILES as one row.

        Arguments
            chemical_data (List): List of objects for the image and smiles [[image1, smiles1], [image2, smiles2]]

        """

        max_cols = 8
        col_widths = [
                0.85 * inch,
                0.85 * inch,
                0.85 * inch,
                0.85 * inch,
                0.85 * inch,
                0.85 * inch,
                0.85 * inch,
                0.85 * inch
        ]

        if len(chemical_data) < max_cols:


            row = [[]]

            # Images

            for i in range(0, len(chemical_data)):
                row[0].append(chemical_data[i][0])

            table = Table(row, colWidths=col_widths)
            table.setStyle(self.table_style_without_background)
            self.story.append(table)

            row = [[]]

            # SMILES

            for i in range(0, len(chemical_data)):
                row[0].append(Paragraph(chemical_data[i][1], self.styles["Line_Label_Center"]),)

            table = Table(row, colWidths=col_widths)
            table.setStyle(self.table_style_without_background)
            self.story.append(table)

            # Labels

            if self.labels:

                row = [[]]

                for i in range(0, len(chemical_data)):
                    row[0].append(Paragraph(self.labels[i], self.styles["Line_Label_Center"]),)

                table = Table(row, colWidths=col_widths)
                table.setStyle(self.table_style_without_background)
                self.story.append(table)

        else:

            for i in range(0, len(chemical_data), max_cols):

                data_left = len(chemical_data) - i

                if data_left < max_cols:

                    row = [[]]

                    # Images

                    for i in range(0, data_left):
                        row[0].append(chemical_data[data_left + i][0])

                        table = Table(row, colWidths=col_widths)
                        table.setStyle(self.table_style_without_background)
                        self.story.append(table)

                    row = [[]]

                    # SMILES

                    for i in range(0, data_left):
                        row[0].append(Paragraph(chemical_data[data_left + i][1], self.styles["Line_Label_Center"]),)

                        table = Table(row, colWidths=col_widths)
                        table.setStyle(self.table_style_without_background)
                        self.story.append(table)

                    # Labels

                    if self.labels:

                        row = [[]]

                        for i in range(0, data_left):
                            row[0].append(Paragraph(self.labels[data_left + i], self.styles["Line_Label_Center"]),)

                            table = Table(row, colWidths=col_widths)
                            table.setStyle(self.table_style_without_background)
                            self.story.append(table)
                else:

                    row = [[
                        chemical_data[i][0],
                        chemical_data[i + 1][0],
                        chemical_data[i + 2][0],
                        chemical_data[i + 3][0],
                        chemical_data[i + 4][0],
                        chemical_data[i + 5][0],
                        chemical_data[i + 6][0],
                        chemical_data[i + 7][0],

                    ]]

                    table = Table(row, colWidths=col_widths)
                    table.setStyle(self.table_style_without_background)
                    self.story.append(table)

                    row = [[
                        Paragraph(chemical_data[i][1], self.styles["Line_Label_Center"]),
                        Paragraph(chemical_data[i + 1][1], self.styles["Line_Label_Center"]),
                        Paragraph(chemical_data[i + 2][1], self.styles["Line_Label_Center"]),
                        Paragraph(chemical_data[i + 3][1], self.styles["Line_Label_Center"]),
                        Paragraph(chemical_data[i + 4][1], self.styles["Line_Label_Center"]),
                        Paragraph(chemical_data[i + 5][1], self.styles["Line_Label_Center"]),
                        Paragraph(chemical_data[i + 6][1], self.styles["Line_Label_Center"]),
                        Paragraph(chemical_data[i + 7][1], self.styles["Line_Label_Center"]),

                    ]]

                    table = Table(row, colWidths=col_widths)
                    table.setStyle(self.table_style_without_background)
                    self.story.append(table)

                    if self.labels:

                        row = [[
                            Paragraph(self.labels[i], self.styles["Line_Label_Center"]),
                            Paragraph(self.labels[i + 1], self.styles["Line_Label_Center"]),
                            Paragraph(self.labels[i + 2], self.styles["Line_Label_Center"]),
                            Paragraph(self.labels[i + 3], self.styles["Line_Label_Center"]),
                            Paragraph(self.labels[i + 4], self.styles["Line_Label_Center"]),
                            Paragraph(self.labels[i + 5], self.styles["Line_Label_Center"]),
                            Paragraph(self.labels[i + 6], self.styles["Line_Label_Center"]),
                            Paragraph(self.labels[i + 7], self.styles["Line_Label_Center"]),

                        ]]

                        table = Table(row, colWidths=col_widths)
                        table.setStyle(self.table_style_without_background)
                        self.story.append(table)


            self.add_spacer()

    @timeit
    def generate(self, smiles, labels=[], include_failed_smiles=False):


        """

        Build the story and generate the final pdf

        Arguments:
            smiles (List): List of smiles you would like to pass in
            labels (List): List of labels that might need to be added based on the user.
            include_failed_smiles (Bool): Whether the user wants to include failed smiles.

        """

        tmp = self._create_temp_directory()

        self.labels = labels

        try:
            self.smiles = smiles

            self.add_image(tmp, include_failed_smiles)

            # Build the initial PDF using Reportlab
            self.doc.build(self.story)

            # Read back in the PDF to add metadata using the PDF Writer
            # Currently in reportlab there isn't a way to support adding info on the pdf
            trailer = PdfReader(self.name)
            trailer.Info.smiles_list = self.smiles
            PdfWriter(self.name, trailer=trailer).write()

        finally:
            self._destroy_temp_directory(tmp)


# ------------ Indigo Renderer ------------------

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


