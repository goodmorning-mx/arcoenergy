from datetime import date, datetime, timezone
from decimal import Decimal
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from alembic.migration import MigrationContext
from alembic.operations import Operations

from app.models import AccountingAccount, AccountingEntry, AccountingLine, Base, HistoryCard, HistoryCardReview
from app.product_api import AccountingEntryInput, AccountingLineInput, accounting_statements


def test_accounting_entry_requires_balanced_debits_and_credits():
    valid = AccountingEntryInput(description="Cobro de anticipo", lines=[
        AccountingLineInput(account_id="cash", debit=Decimal("150.00")),
        AccountingLineInput(account_id="income", credit=Decimal("150.00")),
    ])
    assert valid.lines[0].debit == valid.lines[1].credit
    with pytest.raises(ValidationError):
        AccountingEntryInput(description="Descuadrado", lines=[
            AccountingLineInput(account_id="cash", debit=Decimal("150.00")),
            AccountingLineInput(account_id="income", credit=Decimal("149.00")),
        ])
    with pytest.raises(ValidationError):
        AccountingLineInput(account_id="cash", debit=Decimal("1.00"), credit=Decimal("1.00"))


def test_statements_derive_from_financial_journal_without_changing_operations():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        assets = AccountingAccount(code="1000", name="Activo", account_type="asset", is_group=True)
        cash_group = AccountingAccount(code="1110", name="Caja y bancos", account_type="asset", is_group=True, parent=assets)
        cash = AccountingAccount(code="1111", name="Santander", account_type="asset", parent=cash_group, cash_flow_activity="exclude")
        other_cash = AccountingAccount(code="1112", name="Banco Azteca", account_type="asset", parent=cash_group, cash_flow_activity="exclude")
        income_group = AccountingAccount(code="4000", name="Ingresos", account_type="income", is_group=True)
        income = AccountingAccount(code="4100", name="Ventas", account_type="income", parent=income_group, cash_flow_activity="operating")
        expense_group = AccountingAccount(code="6000", name="Gastos de operación", account_type="expense", is_group=True)
        expense = AccountingAccount(code="6001", name="Viáticos", account_type="expense", parent=expense_group, cash_flow_activity="operating")
        equity_group = AccountingAccount(code="3000", name="Patrimonio", account_type="equity", is_group=True)
        equity = AccountingAccount(code="3001", name="Apertura", account_type="equity", parent=equity_group)
        db.add_all([assets, cash_group, cash, other_cash, income_group, income, expense_group, expense, equity_group, equity])
        db.flush()

        def entry(folio, day, description, pairs):
            row = AccountingEntry(folio=folio, occurred_on=day, description=description, created_at=datetime.now(timezone.utc))
            row.lines = [AccountingLine(account=account, debit=debit, credit=credit) for account, debit, credit in pairs]
            db.add(row)
            return row

        opening = entry("ASI-0", date(2026, 11, 1), "Saldo inicial", [(cash, 1000, 0), (equity, 0, 1000)])
        opening.source_type = "financial_account_opening"
        entry("ASI-1", date(2026, 11, 2), "Venta recibida", [(cash, 100, 0), (income, 0, 100)])
        entry("ASI-2", date(2026, 11, 3), "Pago de viáticos", [(expense, 20, 0), (cash, 0, 20)])
        entry("ASI-3", date(2026, 11, 4), "Transferencia entre bancos", [(other_cash, 10, 0), (cash, 0, 10)])
        db.commit()

        report = accounting_statements(date(2026, 11, 1), date(2026, 11, 30), db=db)
        assert report["balance_sheet"]["assets"] == Decimal("1080.00")
        assert report["balance_sheet"]["retained_result"] == Decimal("80.00")
        assert report["balance_sheet"]["assets"] == report["balance_sheet"]["liabilities_and_equity"]
        assert report["income_statement"]["income"] == Decimal("100.00")
        assert report["income_statement"]["operating_expenses"] == Decimal("20.00")
        assert report["income_statement"]["period_result"] == Decimal("80.00")
        assert report["cash_flow"]["opening_cash"] == Decimal("1000.00")
        assert report["cash_flow"]["closing_cash"] == Decimal("1080.00")
        assert report["cash_flow"]["activities"]["operating"]["inflows"] == Decimal("100.00")
        assert report["cash_flow"]["activities"]["operating"]["outflows"] == Decimal("20.00")
        assert report["cash_flow"]["net_change"] == Decimal("80.00")


def test_financial_migration_seeds_chart_and_records_source_cards():
    migration_path = Path(__file__).parents[1] / "alembic" / "versions" / "202611240162_accounting_ledger_statements.py"
    spec = spec_from_file_location("accounting_ledger_migration", migration_path)
    migration = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE ae_customers (id VARCHAR(36) PRIMARY KEY, name VARCHAR(180) NOT NULL)"))
        connection.execute(text("CREATE TABLE ae_financial_accounts (id VARCHAR(36) PRIMARY KEY, name VARCHAR(120) NOT NULL, active BOOLEAN NOT NULL, opening_balance NUMERIC(14,2) NOT NULL, opening_balance_date DATE NOT NULL)"))
        connection.execute(text("CREATE TABLE ae_projects (id VARCHAR(36) PRIMARY KEY)"))
        connection.execute(text("INSERT INTO ae_customers (id,name) VALUES ('cust-1','Rosa Martínez')"))
        connection.execute(text("INSERT INTO ae_financial_accounts (id,name,active,opening_balance,opening_balance_date) VALUES ('bank-1','Santander',true,1000.00,'2026-11-01')"))
        HistoryCard.__table__.create(connection)
        HistoryCardReview.__table__.create(connection)
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()
        assert len(inspect(connection).get_table_names()) >= 7
        assert connection.execute(text("SELECT COUNT(*) FROM ae_accounting_accounts")).scalar_one() == 19
        assert connection.execute(text("SELECT COUNT(*) FROM ae_accounting_accounts WHERE linked_customer_id='cust-1' AND name='Rosa Martínez'")).scalar_one() == 1
        assert connection.execute(text("SELECT COUNT(*) FROM ae_accounting_accounts WHERE linked_financial_account_id='bank-1' AND name='Santander'")).scalar_one() == 1
        assert connection.execute(text("SELECT COUNT(*) FROM ae_accounting_entries WHERE source_type='financial_account_opening'")).scalar_one() == 1
        assert connection.execute(text("SELECT COUNT(*) FROM ae_accounting_lines")).scalar_one() == 2
        assert connection.execute(text("SELECT COUNT(*) FROM ae_history_cards WHERE story_id IN ('US-47','US-48','US-49')")).scalar_one() == 3
        assert connection.execute(text("SELECT COUNT(*) FROM ae_history_card_reviews WHERE story_id IN ('US-47','US-48','US-49') AND finished=false")).scalar_one() == 3


def test_financial_migration_handles_tables_precreated_by_initial_domain_revision():
    migration_path = Path(__file__).parents[1] / "alembic" / "versions" / "202611240162_accounting_ledger_statements.py"
    spec = spec_from_file_location("accounting_ledger_precreated_migration", migration_path)
    migration = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE ae_customers (id VARCHAR(36) PRIMARY KEY, name VARCHAR(180) NOT NULL)"))
        connection.execute(text("CREATE TABLE ae_financial_accounts (id VARCHAR(36) PRIMARY KEY, name VARCHAR(120) NOT NULL, active BOOLEAN NOT NULL, opening_balance NUMERIC(14,2) NOT NULL, opening_balance_date DATE NOT NULL)"))
        connection.execute(text("CREATE TABLE ae_projects (id VARCHAR(36) PRIMARY KEY)"))
        HistoryCard.__table__.create(connection)
        HistoryCardReview.__table__.create(connection)
        Base.metadata.create_all(connection, tables=[
            AccountingAccount.__table__, AccountingEntry.__table__, AccountingLine.__table__,
        ])
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()
        assert connection.execute(text("SELECT COUNT(*) FROM ae_accounting_accounts WHERE code='1000'")).scalar_one() == 1
        assert connection.execute(text("SELECT COUNT(*) FROM ae_history_cards WHERE story_id IN ('US-47','US-48','US-49')")).scalar_one() == 3
