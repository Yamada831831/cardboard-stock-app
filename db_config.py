import psycopg2

def get_db_connection():
    return psycopg2.connect(
        "postgresql://NeonDB_owner:npg_Vo1YNCDy7AJB@ep-green-shape-a5kaurfc-pooler.us-east-2.aws.neon.tech/NeonDB?sslmode=require"
    )
