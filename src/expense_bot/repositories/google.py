"""Google Sheets-backed storage."""
import logging
from datetime import date
from enum import Enum, auto
from functools import cache
from typing import Iterable

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from ..model import EARN, SPEND, Category, ExpenseItem
from ..repository import Repository
from ..secrets import secrets

logger = logging.getLogger()


class Scope(Enum):
    """Authorization scopes for Google Sheets API."""

    READ = "https://www.googleapis.com/auth/spreadsheets.readonly"
    WRITE = "https://www.googleapis.com/auth/spreadsheets"


class Input(Enum):
    """Parsing option for data entered into Google Sheets."""

    RAW = auto()
    USER_ENTERED = auto()

    def __str__(self) -> str:
        return self.name


class Render(Enum):
    """Rendering options for getting values from Google Sheets."""

    FORMULA = auto()
    FORMATTED_VALUE = auto()
    UNFORMATTED_VALUE = auto()

    def __str__(self) -> str:
        return self.name


class GoogleSheets(Repository):
    """Google Sheets-backed repository."""

    def __init__(
        self,
        spreadsheet_id: str = "1Jn-zYIl3pmJBmj8ki2YY9QovfNMCzLXaqxmy7N9ZEoY",
        template_sheet: str = "TEMPLATE",
        formula_cell_range: str = "Notes!D2:D2",
    ):
        try:
            creds_dict = secrets["g-service-acct"]
        except Exception as exc:
            raise ValueError("Credentials were not provided") from exc

        self.creds = Credentials.from_service_account_info(creds_dict)

        self._sheet_id = spreadsheet_id
        self._template_sheet = template_sheet
        self._formula_cell = formula_cell_range

    @staticmethod
    @cache
    def _sheet_service_with_scope(creds: Credentials, scope: Scope):
        logger.info(
            "Configuring sheet service with scope '%s'...", scope.name
        )
        service = build(
            "sheets", "v4", credentials=creds.with_scopes([scope.value])
        )
        return service.spreadsheets()  # pylint: disable=E1101

    @property
    def _sheet(self):
        return self._sheet_service_with_scope(self.creds, Scope.READ)

    @property
    def _mutable_sheet(self):
        return self._sheet_service_with_scope(self.creds, Scope.WRITE)

    @staticmethod
    def _to_internal(items: list[ExpenseItem]) -> list[str]:
        if not items:
            raise ValueError("Items list is empty!")

        vals = [str(p.amt) for p in items]
        vals.extend("" for _ in range(len(items), 4))

        descr = ", ".join(p.vnd for p in items)
        vals.append(descr)
        return vals

    @staticmethod
    def _from_internal(vals: list[str], cat: Category) -> list[ExpenseItem]:
        descr = vals[-1].split(", ") if vals[-1] else []
        amts = [float(p) for p in vals[:-1] if p]

        assert len(amts) == len(descr), "Descriptions don't match amounts!"
        return [ExpenseItem(amt, vnd, cat) for amt, vnd in zip(amts, descr)]

    def _get_cells(
        self, page: str, row: int, *, render: Render
    ) -> list[ExpenseItem]:
        result = (
            self._sheet.values()
            .get(
                spreadsheetId=self._sheet_id,
                range=f"{page}!D{row}:H{row}",
                valueRenderOption=str(render),
            )
            .execute()
        )

        vals = result.get("values") or [["" for _ in range(5)]]
        return self._from_internal(vals[0], EARN if row == 3 else SPEND)

    def get_all(self, *, dt: date) -> Iterable[ExpenseItem]:
        page = dt.strftime("%m/%y")
        row = dt.day + 4

        assert self._sheet_exists(page), f"Sheet '{page}' does not exist!"
        return self._get_cells(page, row, render=Render.UNFORMATTED_VALUE)

    @staticmethod
    def _gen_dates(dt: date):
        for day in range(1, 32):
            try:
                yield dt.replace(day=day).strftime("%m/%d/%Y")
            except ValueError:
                break

    def add(self, item: ExpenseItem, /, *, dt: date):
        assert dt >= date(2019, 1, 1), "Date is too far in the past!"

        page = dt.strftime("%m/%y")
        row = dt.day + 4 if item.cat is SPEND else 3

        if not self._sheet_exists(page):
            self._create_new_sheet(page, row_names=self._gen_dates(dt))

        items = list(
            self._get_cells(page, row, render=Render.UNFORMATTED_VALUE)
        )
        if item.cat is SPEND:
            msg = f"No room to add more purchases for {dt}!"
        else:
            msg = f"No room to add more earnings for {dt.strftime('%m/%Y')}!"
        assert len(items) < 4, msg

        items.append(item)
        (
            self._mutable_sheet.values()
            .update(
                spreadsheetId=self._sheet_id,
                range=f"{page}!D{row}:H{row}",
                body={"values": [self._to_internal(items)]},
                valueInputOption=str(Input.USER_ENTERED),
            )
            .execute()
        )

    def _get_sheet_id_by_title(self, title: str) -> int:
        items = self._sheet.get(spreadsheetId=self._sheet_id).execute()
        for item in items["sheets"]:
            if item["properties"]["title"] == title:
                return item["properties"]["sheetId"]

        raise ValueError(f"Sheet with title '{title}' not found!")

    def _sheet_exists(self, page: str) -> bool:
        try:
            _ = self._get_sheet_id_by_title(page)
            return True
        except ValueError:
            return False

    def _create_new_sheet(self, page: str, row_names: Iterable[str]):
        assert not self._sheet_exists(page), f"Sheet '{page}' already exists!"

        logger.info("Creating a new sheet from the template...")
        template_id = self._get_sheet_id_by_title(self._template_sheet)

        copy_response = (
            self._mutable_sheet.sheets()
            .copyTo(
                spreadsheetId=self._sheet_id,
                sheetId=template_id,
                body={"destination_spreadsheet_id": self._sheet_id},
            )
            .execute()
        )

        auto_title = copy_response["title"]
        new_sheet_id = copy_response["sheetId"]

        logger.info(
            "Created new sheet (id=%s, title='%s'})", new_sheet_id, auto_title
        )

        logger.info(
            "Renaming created sheet to '%s' and moving it to the front...",
            page,
        )
        self._mutable_sheet.batchUpdate(
            spreadsheetId=self._sheet_id,
            body={
                "requests": {
                    "updateSheetProperties": {
                        "fields": "index, title",
                        "properties": {
                            "sheetId": new_sheet_id,
                            "index": 1,
                            "title": page,
                        },
                    },
                },
            },
        ).execute()

        logger.info("Clearing cells in range 'D3:H35'...")
        self._mutable_sheet.values().clear(
            spreadsheetId=self._sheet_id,
            range=f"{page}!D3:H35",
        ).execute()

        logger.info("Updating the date column...")
        vals = [[name] for name in row_names]

        self._mutable_sheet.values().update(
            spreadsheetId=self._sheet_id,
            range=f"{page}!B5:B{4+len(vals)}",
            body={"values": vals},
            valueInputOption=str(Input.USER_ENTERED),
        ).execute()

        if len(vals) < 31:
            diff = 31 - len(vals)

            logger.info("Removing the last %s rows in the sheet...", diff)
            self._mutable_sheet.values().clear(
                spreadsheetId=self._sheet_id,
                range=f"{page}!B{36-diff}:C35",
            ).execute()

        logger.info("Fetching the formula for the total balance...")
        formula = (
            self._sheet.values()
            .get(
                spreadsheetId=self._sheet_id,
                range=self._formula_cell,
                valueRenderOption=str(Render.FORMULA),
            )
            .execute()
        )["values"][0][0]

        if page not in formula:
            logger.info("Updating the formula for the total balance...")

            formula += f"-'{page}'!A1"

            self._mutable_sheet.values().update(
                spreadsheetId=self._sheet_id,
                range=self._formula_cell,
                body={"values": [[formula]]},
                valueInputOption=str(Input.USER_ENTERED),
            ).execute()
