from sqlite3 import OperationalError
from typing import Any

from sqlalchemy.dialects import sqlite
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.engine.row import Row
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import Column, MetaData, Table
from sqlalchemy.sql.expression import select
from sqlalchemy.types import String

from pas.assistant.run import AssistantRun
from pas.storage.base import AssistantStorage
from pas.utils.dttm import current_datetime
from pas.utils.log import logger


class SqlAssistantStorage(AssistantStorage):
    def __init__(
        self,
        table_name: str,
        db_url: str | None = None,
        db_file: str | None = None,
        db_engine: Engine | None = None,
    ):
        """
        This class provides assistant storage using a sqlite database.

        The following order is used to determine the database connection:
            1. Use the db_engine if provided
            2. Use the db_url
            3. Use the db_file
            4. Create a new in-memory database

        :param table_name: The name of the table to store assistant runs.
        :param db_url: The database URL to connect to.
        :param db_file: The database file to connect to.
        :param db_engine: The database engine to use.
        """
        _engine: Engine | None = db_engine
        if _engine is None and db_url is not None:
            _engine = create_engine(db_url)
        elif _engine is None and db_file is not None:
            engine_db_file = f"sqlite:///{db_file}"
            logger.debug(f"{engine_db_file=}")
            _engine = create_engine(engine_db_file)
        else:
            _engine = create_engine("sqlite://")

        if _engine is None:
            raise ValueError("Must provide either db_url, db_file or db_engine")

        # Database attributes
        self.table_name: str = table_name
        self.db_url: str | None = db_url
        self.db_engine: Engine = _engine
        self.metadata: MetaData = MetaData()

        # Database session
        self.Session: sessionmaker[Session] = sessionmaker(bind=self.db_engine)

        # Database table for storage
        self.table: Table = self.get_table()

    def get_table(self) -> Table:
        return Table(
            self.table_name,
            self.metadata,
            # Database ID/Primary key for this run
            Column("run_id", String, primary_key=True),
            # Assistant name
            Column("name", String),
            # Run name
            Column("run_name", String),
            # ID of the user participating in this run
            Column("user_id", String),
            # -*- LLM data (name, model, etc.)
            Column("llm", sqlite.JSON),
            # -*- Assistant memory
            Column("memory", sqlite.JSON),
            # Metadata associated with this assistant
            Column("assistant_data", sqlite.JSON),
            # Metadata associated with this run
            Column("run_data", sqlite.JSON),
            # Metadata associated the user participating in this run
            Column("user_data", sqlite.JSON),
            # Metadata associated with the assistant tasks
            Column("task_data", sqlite.JSON),
            # The timestamp of when this run was created.
            Column("created_at", sqlite.DATETIME, default=current_datetime()),
            # The timestamp of when this run was last updated.
            Column("updated_at", sqlite.DATETIME, onupdate=current_datetime()),
            extend_existing=True,
            sqlite_autoincrement=True,
        )

    def table_exists(self) -> bool:
        logger.debug(f"Checking if table exists: {self.table.name}")
        try:
            return inspect(self.db_engine).has_table(self.table.name)
        except Exception as e:
            logger.error(e)
            return False

    def create(self) -> None:
        if not self.table_exists():
            logger.debug(f"Creating table: {self.table.name}")
            self.table.create(self.db_engine)

    def _read(self, session: Session, run_id: str) -> Row[Any] | None:
        stmt = select(self.table).where(self.table.c.run_id == run_id)
        try:
            return session.execute(stmt).first()
        except OperationalError:
            # Create table if it does not exist
            self.create()
        except Exception as e:
            logger.warning(e)
        return None

    def read(self, run_id: str) -> AssistantRun | None:
        with self.Session() as sess:
            existing_row: Row[Any] | None = self._read(session=sess, run_id=run_id)
            return (
                AssistantRun.model_validate(existing_row)
                if existing_row is not None
                else None
            )

    def get_all_run_ids(self, user_id: str | None = None) -> list[str]:
        run_ids: list[str] = []
        try:
            with self.Session() as sess:
                # get all run_ids for this user
                stmt = select(self.table)
                if user_id is not None:
                    stmt = stmt.where(self.table.c.user_id == user_id)
                # order by created_at desc
                stmt = stmt.order_by(self.table.c.created_at.desc())
                # execute query
                rows = sess.execute(stmt).fetchall()
                for row in rows:
                    if row is not None and row.run_id is not None:
                        run_ids.append(row.run_id)
        except OperationalError:
            logger.debug(f"Table does not exist: {self.table.name}")
        return run_ids

    def get_all_runs(self, user_id: str | None = None) -> list[AssistantRun]:
        conversations: list[AssistantRun] = []
        try:
            with self.Session() as sess:
                # get all runs for this user
                stmt = select(self.table)
                if user_id is not None:
                    stmt = stmt.where(self.table.c.user_id == user_id)
                # order by created_at desc
                stmt = stmt.order_by(self.table.c.created_at.desc())
                # execute query
                rows = sess.execute(stmt).fetchall()
                for row in rows:
                    if row.run_id is not None:
                        conversations.append(AssistantRun.model_validate(row))
        except OperationalError:
            logger.debug(f"Table does not exist: {self.table.name}")
        return conversations

    def upsert(self, row: AssistantRun) -> AssistantRun | None:
        """
        Create a new assistant run if it does not exist, otherwise update the existing conversation.
        """
        with self.Session() as sess:
            # Create an insert statement
            stmt = sqlite.insert(self.table).values(
                run_id=row.run_id,
                name=row.name,
                run_name=row.run_name,
                user_id=row.user_id,
                llm=row.llm,
                memory=row.memory,
                assistant_data=row.assistant_data,
                run_data=row.run_data,
                user_data=row.user_data,
                task_data=row.task_data,
            )

            # Define the upsert if the run_id already exists
            # See: https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#insert-on-conflict-upsert
            stmt = stmt.on_conflict_do_update(
                index_elements=["run_id"],
                set_=dict(
                    name=row.name,
                    run_name=row.run_name,
                    user_id=row.user_id,
                    llm=row.llm,
                    memory=row.memory,
                    assistant_data=row.assistant_data,
                    run_data=row.run_data,
                    user_data=row.user_data,
                    task_data=row.task_data,
                ),  # The updated value for each column
            )

            try:
                sess.execute(stmt)
                sess.commit()  # Make sure to commit the changes to the database
                return self.read(run_id=row.run_id)
            except OperationalError as oe:
                logger.debug(f"OperationalError occurred: {oe}")
                self.create()  # This will only create the table if it doesn't exist
                try:
                    sess.execute(stmt)
                    sess.commit()
                    return self.read(run_id=row.run_id)
                except Exception as e:
                    logger.warning(f"Error during upsert: {e}")
                    sess.rollback()  # Rollback the session in case of any error
            except Exception as e:
                logger.warning(f"Error during upsert: {e}")
                sess.rollback()
        return None

    def delete(self) -> None:
        if self.table_exists():
            logger.debug(f"Deleting table: {self.table_name}")
            self.table.drop(self.db_engine)
