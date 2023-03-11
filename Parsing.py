import bs4.element
import requests
from bs4 import BeautifulSoup
import typing
import pdf2image
import pandas
import os
import datetime
import PIL


class CustomTypes:
    Tag = typing.NewType("HtmlTag", bs4.element.Tag)


class ScheduleDataBase:
    """Class for control and manage schedules

    Data of schedules contain in .csv file in format:
    (<year> | <month> | <day> | <class>)
    """

    CSV_PATH = "scheduleData/"
    """Path to directory with csv file"""

    DATA_PATH = "scheduleData/Data/"
    """path of directory, where contain data"""

    CSV_NAME = "scheduleData.csv"
    """Name of scv file"""

    COLUMNS = ["year", "data", "class"]
    """Cols of .csv data frame"""

    dataFrame: pandas.DataFrame = None

    def __init__(self):
        self._init_data_frame()

    def __del__(self):
        """If class deleted it method save data frame"""
        self.dataFrame.to_csv(f"{self.CSV_PATH}{self.CSV_NAME}", index=False)

    def _create_data_frame(self) -> pandas.DataFrame:
        """
        :return: New empty data frame
        """
        dataFrame = pandas.DataFrame(columns=self.COLUMNS)

        return dataFrame

    def _init_data_frame(self) -> None:
        """Create or load data frame if it exists"""

        # if csv exists
        fullPath = f"{self.CSV_PATH}{self.CSV_NAME}"
        if os.path.exists(fullPath):
            self.dataFrame = pandas.read_csv(fullPath)
        else:
            self.dataFrame = self._create_data_frame()


class ParseSchedule:
    POPPLER_PATH = "poppler-23.01.0\\Library\\bin"
    """Path for pdf2image lib"""

    DPI = 400
    """Image quality"""

    CUT_INFO = {
        "11.1": [0, (286, 370, 1314, 2923)],
        "11.2": [0],
        "10.1": [0],
        "10.2": [0],
        "9.1": [1],
        "9.2": [1],
        "9.3": [1],
        "9.4": [1],
        "9.5.1": [2],
        "9.5.2": [2],
        "9.6.1": [2],
        "9.6.2": [2],
        "8.1": [3],
        "8.2": [3],
        "8.3": [3],
        "8.4": [3],
        "8.5": [3],
        "7.1": [4],
        "7.2": [4],
        "7.3": [4],
        "6.1": [5],
        "6.2": [5],
        "6.3": [5],
        "5.1": [6],
        "5.2": [6],
        "5.3": [6],
        "5.4": [6],
    }
    """
    Info for cut schedule image
    schoolClass : [page_num, (x0, y0, x1, y1)]
    """

    class Parse:
        """Parsing logic"""

        MONTHS = [
            "сентября",
            "октября",
            "декабря",
            "февраля",
            "марта",
            "апреля",
            "мая",
            "июня",
            "июля",
            "августа",
            "января",
            "ноября",
        ]
        """list of literal names of months"""

        URL = "https://school.kco27.ru/raspisanie-urokov-i-konsultacij/"
        """Url that contain schedule"""

        ELEMENT_DETECTOR = ("a", {"target": "_blank"})
        """Args for detect a schedule like element \n
        (<tag>, {<attribute1> : <value1> ... <attributeN> : <valueN>})
        """

        SCHEDULE_EXTENSION = "pdf"

        @classmethod
        def _check_tag(cls, tag: CustomTypes.Tag) -> bool:
            """
            Use to check a tag for a schedule
            :param tag: html tag
            :return: True if tag is schedule  else False
            """

            def check_name(name: str) -> bool:
                """
                :return: True if name is correct else False
                """

                if len(data := name.split()) != 2:
                    return False

                date, month = data
                if date.isnumeric() and month in cls.MONTHS:
                    return True
                return False

            if len(tmp := tag["href"].split("/")[-1].split(".")) != 2:
                return False

            # getting filename and extension by parse url
            filename, extension = tmp

            return extension == cls.SCHEDULE_EXTENSION and check_name(filename)

        @classmethod
        def _get_filename_from_url(cls, url: str) -> str:
            """
            :param url: str
            :return: filename without extension from url
            """

            try:
                return url.split("/")[-1].split(".")[0]
            except IndexError:
                return ""

        @classmethod
        def _get_urls(cls) -> list:
            """
            :return: list of schedule urls
            """

            page = requests.get(cls.URL)
            soup = BeautifulSoup(page.text, "html.parser")

            list_of_tags = list(soup.find_all(cls.ELEMENT_DETECTOR[0], **cls.ELEMENT_DETECTOR[1]))

            return list(tag["href"] for tag in filter(cls._check_tag, list_of_tags))

        @classmethod
        def get_all_filenames(cls) -> list:
            """
            :return: list of all string filenames of schedules without extension on website
            """
            urls = cls._get_urls()

            names = [cls._get_filename_from_url(url) for url in urls]

            return names

        @classmethod
        def get_pdf_bytes(cls) -> dict:
            """
            :return: dict of (filename : bytes)
            """

            returned_dict = {}

            for link in cls._get_urls():
                response = requests.get(link)

                filename = cls._get_filename_from_url(link)
                data = response.content
                returned_dict[filename] = data

            return returned_dict

    @classmethod
    def get_images(cls) -> dict:
        """
        :return: dict of (date : list[Image])
        """
        returned_dict = {}

        for date, pdfBytes in cls.Parse.get_pdf_bytes().items():
            pdfImages = pdf2image.convert_from_bytes(pdfBytes, dpi=cls.DPI, poppler_path=cls.POPPLER_PATH)

            returned_dict[date] = pdfImages

        return returned_dict

    @classmethod
    def cut(cls):

        # returned_list = []
        #
        # for img_list in cls.get_images().values():
        #     returned_list.append(img_list[0].crop(cls.CUT_INFO["11.1"]))
        for img_list in cls.get_images().values():
            img_list[2].crop(cls.CUT_INFO["11.1"][1]).show()


def main():
    # ScheduleDataBase()
    ParseSchedule.cut()


if __name__ == '__main__':
    main()
