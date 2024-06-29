from base.databasecommon import DatabaseConnection


def BEGIN_TRANSACTION():
    if DatabaseConnection.inst().isInTransaction():
        raise Exception( "BEGIN_TRANSACTION() kann nicht aufgerufen werden, wenn eine Transaktion aktiv ist." )
    DatabaseConnection.inst().begin_transaction()

def COMMIT_TRANSACTION():
    DatabaseConnection.inst().commit_transaction()

def ROLLBACK_TRANSACTION():
    DatabaseConnection.inst().rollback_transaction()

def TRANSACTION_RUNNING() -> bool:
    return DatabaseConnection.inst().isInTransaction()