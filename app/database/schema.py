
from app.database.connection import get_connection


CREATE_DOCUMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    source TEXT NOT NULL,
    department TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    effective_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


CREATE_CHUNKS_TABLE = """
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    text TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    source TEXT NOT NULL,
    extraction_method TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_chunks_document
        FOREIGN KEY (document_id)
        REFERENCES documents(document_id)
        ON DELETE CASCADE
);
"""


CREATE_CHUNKS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_chunks_document_id
ON chunks(document_id);
"""


CREATE_DEPARTMENT_INDEX = """
CREATE INDEX IF NOT EXISTS idx_documents_department_status
ON documents(department, status);
"""


# --------------------------------------------------
# Authorization tables
# --------------------------------------------------

CREATE_APP_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS app_users (
    user_id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


CREATE_USER_ROLES_TABLE = """
CREATE TABLE IF NOT EXISTS user_roles (
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_user_roles
        PRIMARY KEY (user_id, role),

    CONSTRAINT fk_user_roles_user
        FOREIGN KEY (user_id)
        REFERENCES app_users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_user_roles_role
        CHECK (role IN ('employee', 'manager', 'admin'))
);
"""


CREATE_USER_DEPARTMENT_ACCESS_TABLE = """
CREATE TABLE IF NOT EXISTS user_department_access (
    user_id TEXT NOT NULL,
    department TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_user_department_access
        PRIMARY KEY (user_id, department),

    CONSTRAINT fk_user_department_access_user
        FOREIGN KEY (user_id)
        REFERENCES app_users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_user_department_access_department
        CHECK (LENGTH(TRIM(department)) > 0)
);
"""


CREATE_USER_DEPARTMENT_INDEX = """
CREATE INDEX IF NOT EXISTS idx_user_department_access_department
ON user_department_access(department);
"""


def create_schema() -> None:
    """Create or update the database schema safely."""

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

            # Existing RAG tables: preserve current behavior and data.
            cursor.execute(CREATE_DOCUMENTS_TABLE)

            cursor.execute("""
                ALTER TABLE documents
                ADD COLUMN IF NOT EXISTS department TEXT,
                ADD COLUMN IF NOT EXISTS status TEXT
                    NOT NULL DEFAULT 'active',
                ADD COLUMN IF NOT EXISTS effective_date DATE;
            """)

            cursor.execute(CREATE_CHUNKS_TABLE)
            cursor.execute(CREATE_CHUNKS_INDEX)
            cursor.execute(CREATE_DEPARTMENT_INDEX)

            # New authorization tables.
            cursor.execute(CREATE_APP_USERS_TABLE)
            cursor.execute("""
    ALTER TABLE app_users
    ADD COLUMN IF NOT EXISTS password_hash TEXT;
""")
            cursor.execute(CREATE_USER_ROLES_TABLE)
            cursor.execute(CREATE_USER_DEPARTMENT_ACCESS_TABLE)
            cursor.execute(CREATE_USER_DEPARTMENT_INDEX)

        connection.commit()

    finally:
        connection.close()
