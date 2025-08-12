from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal
import os
import csv
import argparse
import json

class Category:
    def __init__(self, name: str, created_at: datetime | None = None) -> None:
        self.__name: str = name
        self.__created_at: datetime | None = created_at

    @property
    def name(self) -> str:
        return self.__name

    @property
    def created_at(self) -> datetime | None:
        return self.__created_at

    @created_at.setter
    def created_at(self, created_at: datetime) -> None:
        assert isinstance(created_at, datetime)
        self.__created_at = created_at


class Transaction:
    def __init__(self, created_at: datetime, amount: Decimal, category: Category, notes: str):
        self.__created_at: datetime
        self.__amount: Decimal
        self.__category: Category
        self.__notes: str

        self.created_at = created_at
        self.amount = amount
        self.category = category
        self.notes = notes

    @property
    def created_at(self) -> datetime:
        return self.__created_at

    @created_at.setter
    def created_at(self, created_at: datetime) -> None:
        assert (isinstance(created_at, datetime))
        self.__created_at = created_at

    @property
    def amount(self) -> Decimal:
        return self.__amount

    @amount.setter
    def amount(self, amount: Decimal) -> None:
        assert (isinstance(amount, Decimal))
        self.__amount = amount

    @property
    def category(self) -> Category:
        return self.__category

    @category.setter
    def category(self, category: Category) -> None:
        assert (isinstance(category, Category))
        self.__category = category

    @property
    def notes(self) -> str:
        return self.__notes

    @notes.setter
    def notes(self, notes: str) -> None:
        assert (isinstance(notes, str))
        self.__notes = notes


class Transactions:
    def __init__(self) -> None:
        self.__transactions: list[Transaction] = list()

    @property
    def categories(self) -> set[Category]:
        return {
            t.category
            for t
            in self.__transactions
        }

    def add_transaction(self, transaction: Transaction) -> None:
        assert isinstance(transaction, Transaction)
        self.__transactions.append(transaction)

    def set_default_category_created_ats(self) -> None:
        category_earliest_transactions: dict[str, datetime] = dict()
        for transaction in self.__transactions:
            try:
                if transaction.created_at < category_earliest_transactions[transaction.category.name]:
                    category_earliest_transactions[transaction.category.name] = transaction.created_at
            except KeyError:
                category_earliest_transactions[transaction.category.name] = transaction.created_at

        for transaction in self.__transactions:
            transaction.category.created_at = category_earliest_transactions[transaction.category.name]

    def __repr__(self) -> str:
        self.set_default_category_created_ats()

        top_level: dict[str, list[dict]] = {
            "transactions": list(),
            "categories": list()
        }

        for category in self.categories:
            assert category.created_at is not None
            category_dict: dict[str, str] = {
                "name": category.name,
                "created_at": category.created_at.isoformat()
            }
            top_level["categories"].append(category_dict)

        for transaction in self.__transactions:
            transaction_dict: dict[str, str | int | dict | float] = {
                "category": [category_dict for category_dict in top_level["categories"] if transaction.category.name == category_dict["name"]][0],
                "description": transaction.notes,
                "amount": float(transaction.amount),
                "created_at": transaction.created_at.isoformat()
            }
            top_level["transactions"].append(transaction_dict)

        return json.dumps(top_level, indent=2).replace("+00:00", "Z")

    def to_json(self) -> str:
        return repr(self)


def parse_expense_log(file_path: str) -> Transactions:
    transactions: Transactions = Transactions()
    assert os.path.exists(file_path) and os.path.isfile(file_path)
    with open(file_path, "r") as file:
        csv_reader = csv.reader(file)
        for i, row in enumerate(csv_reader):
            if i == 0:
                continue
            try:
                day: str
                month: str
                year: str
                day, month, year = row[0].split("/")
                hour: str
                minute: str
                second: str = "00"
                hour, minute = row[1].split(":")
                transaction_datetime = datetime(
                    2000+int(year),
                    int(month),
                    int(day),
                    int(hour),
                    int(minute),
                    int(second),
                    tzinfo=ZoneInfo("America/Edmonton")
                ).astimezone(ZoneInfo("UTC"))
                negative_symbol: str
                amount_string: str
                negative_symbol, amount_string = row[2].split("$")
                is_negative: bool = (negative_symbol == "-")
                amount_string = amount_string.replace(",", "") # remove thousands marker
                negative_multiplier: int = -1 if is_negative else 1
                amount: Decimal = Decimal(amount_string) * negative_multiplier
                category_string: str = row[3]
                category: Category = Category(category_string)
                notes: str = row[4]
                transaction: Transaction = Transaction(transaction_datetime, amount, category, notes)
                transactions.add_transaction(transaction)
            except Exception as e:
                print(f"Exception when parsing CSV file: {e}\nSkipping bad row: {i}")
                continue # skip bad row

    return transactions


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--expense-log-path", required=True, type=str)
    args = parser.parse_args()
    expense_log_path: str = args.expense_log_path

    transactions: Transactions = parse_expense_log(expense_log_path)

    with open("./transactions.json", "w") as file:
        file.write(transactions.to_json())
        file.flush()

# FIX TIMEZONE WHEN IMPORTING
