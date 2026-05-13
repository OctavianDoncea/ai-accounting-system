from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import datetime

class Session(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    base_currency = Column(String(3), default='USD')

    chart_of_accounts = relationship('ChartOfAccount', back_populates='session')
    transactions = relationship('Transaction', back_populates='session')
    invoices = relationship('Invoice', back_populates='session')
    bank_statement_imports = relationship('BankStatementImport', back_populates='session')

class ChartOfAccount(Base):
    __tablename__ = 'chart_of_accounts'
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(Enum('Asset', 'Liability', 'Equity', 'Revenue', 'Expense', name='account_type'), nullable=False)

    session = relationship('Session', back_populates='chart_of_accounts')
    debit_entries = relationship('JournalEntry', foreign_keys='JournalEntry.debit_account_id', back_populates='debit_account')
    credit_entries = relationship('JournalEntry', foreign_keys='JournalEntry.credit_account_id', back_populates='credit_account')

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    description = Column(String(500), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='USD')
    debit_account_id = Column(Integer, ForeignKey('chart_of_accounts.id'))
    credit_account_id = Column(Integer, ForeignKey('chart_of_accounts.id'))
    source = Column(Enum('BANK_STATEMENT', 'INVOICE', 'MANUAL', name='transaction_source'))
    status = Column(String(20), default='unposted')

    session = relationship('Session', back_populates='transactions')
    debit_account = relationship('ChartOfAccount', foreign_keys=[debit_account_id])
    credit_account = relationship('ChartOfAccount', foreign_keys=[credit_account_id])
    journal_entries = relationship('JournalEntry', back_populates='transaction')

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    vendor = Column(String(255))
    invoice_date = Column(DateTime)
    due_date = Column(DateTime)
    total = Column(Float)
    currency = Column(String(3), default="USD")
    raw_text = Column(Text)
    line_items = Column(JSON)

    session = relationship("Session", back_populates="invoices")

class BankStatementImport(Base):
    __tablename__ = 'bank_statement_imports'
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    file_name = Column(String(255))
    processed_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    session = relationship('Session', back_populates='bank_statement_imports')

class JournalEntry(Base):
    __tablename__ = 'jounral_entries'
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'))
    debit_account_id = Column(Integer, ForeignKey('chart_of_accounts.id'))
    credit_account_id = Column(Integer, ForeignKey('chart_of_accounts.id'))
    debit_amount = Column(Float, default=0)
    credit_amount = Column(Float, default=0)
    entry_date = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    transaction = relationship('Transaction', back_populates='jounral_entries')
    debit_account = relationship('ChartOfAccount', foreign_keys=[debit_account_id])
    credit_account = relationship('ChartOfAccount', foreign_keys=[credit_account_id])