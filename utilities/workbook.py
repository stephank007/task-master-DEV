from xlsxwriter.format import Format
from xlsxwriter.worksheet import Worksheet
import pandas as pd

class WorkbookFormats:
    def __init__(self):
        self._wb = None
        self._align_left = {
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'left',
            'indent': 1
        }
        self._align_date = {
            'num_format': 'dd/mm/yyyy',
            'valign': 'vcenter',
            'align': 'center'
        }
        self._align_center = {
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'center'
        }
        self._align_rtl = {
            'text_wrap': True,
            'align': 'right',
            'valign': 'vcenter',
            'reading_order': 2,
            'indent': 1
        }
        self._align_percent = {
            'align': 'center',
            'valign': 'vcenter',
            'num_format': 10
        }
        self._align_header = {
            'font_name': 'Arial',
            'font_size': 12,
            'bold': True,
            'align': 'center',
            'bg_color': '#C6EFCE',
            'font_color': '#006100'
        }

    def set_writer(self, file_name: str) -> pd.ExcelWriter:
        writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
        self._wb = writer.book
        self._wb.set_size(2048, 1280)
        return writer

    def align_left(self) -> Format:
        wb = self._wb
        return wb.add_format(self._align_left)

    def align_date(self) -> Format:
        wb = self._wb
        return wb.add_format(self._align_date)

    def align_center(self) -> Format:
        wb = self._wb
        return wb.add_format(self._align_center)

    def align_rtl(self) -> Format:
        wb = self._wb
        return wb.add_format(self._align_rtl)

    def align_percent(self) -> Format:
        wb = self._wb
        return wb.add_format(self._align_percent)

    def align_header(self) -> Format:
        wb = self._wb
        return wb.add_format(self._align_header)

    def format_header(self, ws: Worksheet, dff: pd.DataFrame) -> dict:
        c_dict = {}
        if isinstance(dff.columns, pd.MultiIndex):
            # print('multi-index columns')
            for col_num, value in enumerate(dff.columns.values):
                # print('{}-{}: {}'.format(value[0], value[1], col_num + 1))
                c_dict.update({'{}-{}'.format(value[0], value[1]): col_num + 1})
                ws.write(1, col_num + 1, value[1], self.align_header())
        else:
            # print('NOT multi-index columns')
            for col_num, value in enumerate(dff.columns.values):
                c_dict.update({value: col_num + 1})
                # print('{:12}: {}'.format(value, col_num + 1))
                ws.write(0, col_num + 1, value, self.align_header())
        return c_dict

    @staticmethod
    def auto_freeze(ws: Worksheet, dff: pd.DataFrame) -> None:
        if isinstance(dff.columns, pd.MultiIndex):
            ws.autofilter(1, 1, dff.shape[0], dff.shape[1])
            ws.freeze_panes(1, 1)
        else:
            ws.autofilter(0, 0, dff.shape[0], dff.shape[1])
            ws.freeze_panes(1, 0)


"""
    date_formats = [
        'dd/mm/yyyy',
        'mm/dd/yy',
        'dd m yy',
        'd mm yy',
        'd mmm yy',
        'd mmmm yy',
        'd mmmm yyy',
        'd mmmm yyyy',
        'dd/mm/yy hh:mm',
        'dd/mm/yy hh:mm:ss',
        'dd/mm/yy hh:mm:ss.000',
        'hh:mm',
        'hh:mm:ss',
        'hh:mm:ss.000',
    ]
"""
