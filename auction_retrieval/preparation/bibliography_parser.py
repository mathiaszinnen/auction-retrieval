import pikepdf
import json
from pdfminer.high_level import extract_text
import requests
import re
from tqdm import tqdm

class BibliographyParser:
    DEFAULT_BIBLIOGRAPHIES = [
        ("bibliographies/Baehr_German_Sales_1930_1945_2013.pdf", (50, 824)),
        ("bibliographies/Bommert_Brand_German_sales_1901_1929_2019.pdf", (50, 824))
    ]

    def __init__(self, output_dir, lit_pdfs=None, page_ranges=None):
        """
        If no lit_pdfs or page_ranges are provided, 
        use the default bibliographies included in the repository.
        """
        if lit_pdfs is None or page_ranges is None:
            self.lit_pdfs, self.page_ranges = zip(*self.DEFAULT_BIBLIOGRAPHIES)
        else:
            self.lit_pdfs = lit_pdfs
            self.page_ranges = page_ranges

        self.output_dir = output_dir
        self.catalogues = []
        self.current_entry = {}

    @staticmethod
    def _is_header(line):
        return bool(re.search(r'<[^>]+', line))

    @staticmethod
    def _has_link(line):
        return 'http://' in line or 'https://' in line

    @staticmethod
    def _has_type(line):
        return 'Lose' in line and '; ' in line

    @staticmethod
    def _sanitize_kw(kw):
        return kw.strip().replace('\xa0', '').replace(',', '')

    @classmethod
    def _get_types(cls, line):
        kws_raw = line.split('; ')[1].split(', ')
        return [cls._sanitize_kw(kw) for kw in kws_raw] if kws_raw else []

    @staticmethod
    def _get_link(line):
        if 'https://' in line:
            return 'https://' + line.split('https://')[-1]
        if 'http://' in line:
            return 'http://' + line.split('http://')[-1]
        return None

    @staticmethod
    def _get_fn(uri):
        try:
            response = requests.get(uri)
            response.raise_for_status()
            return response.url.split('/')[-1]
        except requests.RequestException:
            return ''

    @staticmethod
    def _extract_location(line):
        location = line.split('<')[1].split('>')[0].strip()
        return (location.replace(' ', '')
                        .replace('imBreisgau', '')
                        .replace('a.M.', ' am Main')
                        .replace('\xa0a.\xa0M.', ' am Main')
                        .replace('amMain', ' am Main'))

    @staticmethod
    def _extract_date(line):
        dates = re.findall(r'[12]\d{3}', line)
        return int(dates[0]) if len(dates) == 1 else -1

    @classmethod
    def _has_year(cls, text):
        return cls._extract_date(text) != -1

    @classmethod
    def _start_entry(cls, title):
        return {
            'title': title,
            'text_lines': [],
            'location': cls._extract_location(title),
            'year': cls._extract_date(title),
            'types': []
        }

    @staticmethod
    def _is_valid_entry(entry):
        return 'title' in entry

    def _save_entry(self, entry):
        if self._is_valid_entry(entry):
            self.catalogues.append(entry)

    def _fill_entry(self, entry, text):
        if not self._is_valid_entry(entry):
            return entry

        entry['text_lines'].append(text)

        if self._has_link(text):
            link = self._get_link(text)
            if link:
                entry['uri'] = link
                entry['fn'] = self._get_fn(link)

        if self._has_type(text):
            entry['types'] = self._get_types(text)

        if entry['year'] == '' and self._has_year(text):
            entry['year'] = self._extract_date(text)

        return entry

    def _dump_catalogues(self):
        output_path = self.output_dir / "catalogues_dict.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.catalogues, f, ensure_ascii=False, indent=4)

    def parse_pdf_batchwise(self, pdf_path, start_page, end_page):
        text = extract_text(
            pdf_path,
            page_numbers=list(range(start_page, end_page)),
            laparams=None  # Use default layout params
        )

        lines = text.splitlines()
        for line in tqdm(lines):
            if self._is_header(line):
                self._save_entry(self.current_entry)
                self.current_entry = self._start_entry(line)
            else:
                self.current_entry = self._fill_entry(self.current_entry, line)

        self._save_entry(self.current_entry)

    def parse(self, dump=True):
        print('Parsing bibliography files...')

        for pdf_path, page_range in zip(self.lit_pdfs, self.page_ranges):
            start_page, end_page = page_range

            with pikepdf.open(pdf_path) as pdf:
                num_pages = len(pdf.pages)
                assert end_page <= num_pages, f"Requested end_page {end_page} exceeds total pages {num_pages}"

            self.parse_pdf_batchwise(pdf_path, start_page, end_page)

        if dump:
            self._dump_catalogues()

        return self.catalogues
