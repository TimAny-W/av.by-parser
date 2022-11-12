import os
import sys
import time

from bs4 import BeautifulSoup
import asyncio
import aiohttp
import ssl
import certifi
import pandas as pd
from PyQt5 import QtWidgets

from Ui import Ui_MainWindow

items = []
years = []
cashed = []
urls = []


class UI(QtWidgets.QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.init_UI()

    def init_UI(self):
        self.ui.pushButton.clicked.connect(self._start_parser)

    def _start_parser(self):
        pages = int(self.ui.spinBox.text())

        self.ui.label_3.setText('Ищем обьявления на av.by...')
        self.ui.label_3.repaint()

        Parser(pages)

        all_info = list(zip(items, years, cashed, urls))

        self.ui.label_3.setText(f"Получено {len(all_info)} обьявлений")
        self.ui.label_3.repaint()




class Parser:
    def __init__(self, pages):
        self.pages = pages

        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
        }
        asyncio.get_event_loop().run_until_complete(self._run())

    async def _get_page_info(self, session, page):
        if page == 1:
            url = "https://cars.av.by/filter"
        else:
            url = f'https://cars.av.by/filter?page={page}'

        async with session.get(url=url) as response:
            try:
                html_source = await response.text()

                page_info = BeautifulSoup(html_source, 'html.parser')

                await self._select_info_from_page(page_info)
            except Exception as ex:
                print(f'[ERROR] {repr(ex)}')

    async def _select_info_from_page(self, page_info):
        car_names = page_info.find_all('a', class_='listing-item__link')
        for name in car_names:
            items.append(name.text)
            urls.append(f'https://cars.av.by{name["href"]}')

        items_cashes = page_info.find_all('div', class_='listing-item__priceusd')
        for cash in items_cashes:
            cashed.append(cash.text)

        years_list = page_info.find_all('div', class_='listing-item__params')
        for year in years_list:
            years.append(year.text)

    async def _load_site_info(self):
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        conn = aiohttp.TCPConnector(ssl=ssl_context)

        async with aiohttp.ClientSession(connector=conn, headers=self.headers) as session:
            tasks = []
            for page in range(1, self.pages):
                task = asyncio.create_task(self._get_page_info(session=session, page=page))
                tasks.append(task)
            await asyncio.gather(*tasks)

    async def _save_to_excel(self):
        data_frame = pd.DataFrame({"Марка": items,
                                   "Год": years,
                                   "Цена": cashed,
                                   "Ссылка": urls,
                                   })
        path = r'./info'
        if not os.path.exists(path):
            os.mkdir(r'./info')
        data_frame.to_excel(r'./info/av_by_info.xlsx')

    async def _run(self):
        await self._load_site_info()
        all_info = zip(items, years, cashed, urls)

        await self._save_to_excel()



if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    application = UI()
    application.show()

    sys.exit(app.exec_())

