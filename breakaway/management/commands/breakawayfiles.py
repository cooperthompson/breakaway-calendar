import re
import os
import shlex
import urllib
import urllib2
import subprocess
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    args = '<pdf_file pdf_file ...>'
    help = 'Pull down the BreakAway PDF files and convert these to text files'

    def handle(self, *args, **options):
        pdf_files = self.get_pdf_files()

        if os.name == "nt":
            self.stderr.write("You probably don't want to run this on Windows...")
            return

        for pdf_filename in pdf_files:
            self.process_file(pdf_filename)

    @staticmethod
    def get_pdf_files():
        """
        This method finds all PDF files linked from http://breakawaysports.com/current-league.php
        and returns them as a list of URLs to the PDF documents for later processing
        @return: A list of pdf files (urls)
        """
        pdf_files = []
        response = urllib2.urlopen('http://breakawaysports.com/current-league.php')
        html = response.read()
        matches = re.findall(".*href=\"(.*\.pdf)\".*", html)

        for match in matches:
            pdf_files.append("http://breakawaysports.com%s" % match)

        return pdf_files

    def process_file(self, pdf_uri):
        """
        This method takes a URL of a PDF file, downloads it, and converts it
        into two different text files using the UNIX pdftotext utility.

        One text file is generated using the -layout option to maintain the original PDF's layout.
        This format is used for parsing game data.

        One text file is generated without the -layout option.  This format is used for parsing
        team data.

        @param pdf_uri: A URL to a PDF file to download
        """

        pdf_filename = os.path.join(settings.BASE_DIR, "import", os.path.basename(pdf_uri))
        urllib.urlretrieve(pdf_uri, pdf_filename)

        with open(pdf_filename, 'r') as pdf_file:
            self.convert_pdf_to_text(pdf_file, 0)  # non-layout version

        with open(pdf_filename, 'r') as pdf_file:
            self.convert_pdf_to_text(pdf_file, 1)  # layout version

        self.stdout.write('Successfully imported "%s"' % pdf_uri)

    def convert_pdf_to_text(self, pdf_file, layout):
        """
        @param pdf_file: open PDF file to convert
        @param layout: boolean indicator if the PDF should be parsed into a
            layout or non-layout text document
        @return: text version of the PDF
        """

        base, ext = os.path.splitext(os.path.basename(pdf_file.name))
        if layout:
            text_filename = os.path.join(settings.BASE_DIR, "import", "%s-layout.txt" % base)
        else:
            text_filename = os.path.join(settings.BASE_DIR, "import", "%s-plain.txt" % base)

        #self.stdout.write("Generating text file: %s." % text_filename)

        if layout:
            cmd = "pdftotext -layout '%s' '%s'" % (pdf_file.name, text_filename)
            proc = subprocess.Popen(shlex.split(cmd))
            out, err = proc.communicate()
        else:
            cmd = "pdftotext '%s' '%s'" % (pdf_file.name, text_filename)
            proc = subprocess.Popen(shlex.split(cmd))
            out, err = proc.communicate()

        if err:
            self.stdout.write("ERROR: %s" % err)

        return text_filename