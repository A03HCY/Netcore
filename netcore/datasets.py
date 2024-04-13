import sqlite3
import uuid
import datetime
import ast

class MEMLimit:
    def __init__(self) -> None:
        self.__soft_limit = self.__hard_limit = 1024 * 1024 *10
    
    @property
    def soft(self) -> int:
        return self.__soft_limit
    
    @property
    def hard(self) -> int:
        return self.__hard_limit

MEM = MEMLimit()

def init():
    global _ds
    _ds = {}

def set(key, value): _ds[key] = value

def get(key, df=None): return _ds.get(key, df)

def items(): return _ds.items()

def keys(): return _ds.keys()

def pop(key): return _ds.pop(key)

def clear(): _ds.clear()

def setdefault(key): return _ds.setdefault(key)

def setlist(keys):
    for i in keys: _ds.setdefault(i)


class RowIterator:
    def __init__(self, curs, table, query:str=None):
        self.table_name = table
        self.curs = curs
        self.query = query
        if not query: self.query = f"SELECT * FROM {self.table_name}"

    def __enter__(self):
        self.curs.execute(self.query)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __iter__(self):
        return self

    def __next__(self):
        row = self.curs.fetchone()
        if row is not None:
            return row
        else:
            raise StopIteration

class Database:
    def __init__(self, path):
        self.path = path
        self.__enter__()
    
    def __enter__(self):
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.curs = self.conn.cursor()
        return self.curs

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.curs:
            self.curs.close()
    
    @property
    def current_time(self) -> int:
        return int(datetime.datetime.now().timestamp())
    
    @property
    def new_uuid(self) -> str:
        return str(uuid.uuid4())

    def execute_query(self, query):
        self.curs.execute(query)
        self.conn.commit()

    def check_columns_exist(self, table, columns):
        query = f"PRAGMA table_info({table})"
        self.curs.execute(query)
        table_columns = [column[1] for column in self.curs.fetchall()]

        for column in columns:
            if column not in table_columns:
                return False

        return True

    def create_table(self, table_name, fields, key=None, unique=None):
        create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ("
        field_definitions = []

        for field, data_type in fields.items():
            if isinstance(data_type, type):
                if data_type == int:
                    data_type = 'INTEGER'
                elif data_type == str:
                    data_type = 'TEXT'
                elif data_type == float:
                    data_type = 'REAL'
            field_definition = f"{field} {data_type}"
            
            if key and field == key:
                field_definition += " PRIMARY KEY"
            
            if unique and (isinstance(unique, str) and field == unique or isinstance(unique, list) and field in unique):
                field_definition += " UNIQUE"
            
            field_definitions.append(field_definition)

        create_table_query += ", ".join(field_definitions)
        create_table_query += ")"
        self.execute_query(create_table_query)
    
    def get_table_rows(self, table:str):
        query = f"SELECT COUNT(*) FROM {table}"
        self.curs.execute(query)
        result = self.curs.fetchone()[0]
        return result
    
    def iter_table_rows(self, table:str) -> RowIterator:
        return RowIterator(self.curs, table)
    
    def get_all_rows(self, table:str):
        query = f"SELECT * FROM {table}"
        self.curs.execute(query)
        result = self.curs.fetchall()
        return result
    
    def get_all_rows_one_by_one(self, table:str, func):
        query = f"SELECT * FROM {table}"
        self.curs.execute(query)
        row = self.curs.fetchone()
        while row is not None:
            func(row)
            row = self.curs.fetchone()

    def get_table_columns(self, table):
        query = f"PRAGMA table_info({table})"
        self.curs.execute(query)
        table_columns = [column[1] for column in self.curs.fetchall()]
        return table_columns
    
    def get_column_type(self, table, column):
        query = f"PRAGMA table_info({table})"
        self.curs.execute(query)
        table_info = self.curs.fetchall()
        for info in table_info:
            if info[1] == column:
                column_type = info[2]
                if column_type == "INTEGER":
                    return int
                elif column_type == "REAL":
                    return float
                elif column_type == "TEXT":
                    return str
                else:
                    return None
        return None
    
    def validate_data_types(self, table, data) -> bool:
        table_columns = self.get_table_columns(table)
        for column, value in zip(table_columns, data):
            column_type = self.get_column_type(table, column)
            if not isinstance(value, column_type):
                print(value, column_type)
                return False
        return True
    
    def insert_data(self, table, data) -> bool:
        columns = self.get_table_columns(table)
        if isinstance(data, dict):
            if not self.check_columns_exist(table, data.keys()):
                print("Invalid columns. Aborting insertion.")
                return False
            data = tuple([data[i] for i in columns])
        elif isinstance(data, tuple):
            if len(columns) != len(data):
                print("Invalid number of values. Aborting insertion.")
                return False
        else:
            print("Invalid data forms. Aborting insertion.")
            return False
        
        if not self.validate_data_types(table, data):
            print("Invalid data types. Aborting insertion.")
            return False

        placeholders = ", ".join(["?"] * len(data))
        query = f"INSERT INTO {table} VALUES ({placeholders})"
        self.curs.execute(query, data)
        self.conn.commit()
        return True
    
    def convert(self, table, data) -> list:
        columns = self.get_table_columns(table)
        result = []
        for i in data:
            result.append(dict(zip(columns, i)))
        return result


    def select_data(self, table, conditions, iter:bool=False) -> list:
        if not self.check_columns_exist(table, conditions.keys()):
            print("Invalid columns. Aborting selection.")
            return []

        conditions_query = " AND ".join([f"{column} = ?" for column in conditions.keys()])
        query = f"SELECT * FROM {table} WHERE {conditions_query}"
        if iter: return RowIterator(self.curs, table, query=query)
        self.curs.execute(query, tuple(conditions.values()))
        result = self.curs.fetchall()
        return self.convert(table, result)
    
    def select_numble(self, table:str, key:str, start:int, end:int, iter:bool=False) -> list:
        columns = self.get_table_columns(table)

        if not key in columns:
            print("Invalid columns. Aborting selection.")
            return []
        
        if not self.get_column_type(table, key) in [int, float]:
            print("Invalid type. Aborting selection.")
            return []
        
        query = f"SELECT * FROM {table} WHERE {key} > {start} AND {key} < {end}"
        if iter: return RowIterator(self.curs, table, query=query)
        self.curs.execute(query)
        result = self.curs.fetchall()
        return self.convert(table, result)


    def delete_data(self, table, conditions) -> None:
        if not self.check_columns_exist(table, conditions.keys()):
            print("Invalid columns. Aborting deletion.")
            return

        conditions_query = " AND ".join([f"{column} = ?" for column in conditions.keys()])
        query = f"DELETE FROM {table} WHERE {conditions_query}"
        self.curs.execute(query, tuple(conditions.values()))
        self.conn.commit()

    def build_set_string(self, data) -> str:
        set_values = ", ".join([f"{column} = ?" for column in data.keys()])
        return set_values

    def build_condition_string(self, condition) -> str:
        condition_string = " AND ".join([f"{column} = ?" for column in condition.keys()])
        return condition_string

    def update_data(self, table, data, condition, only=True) -> bool:
        if not self.check_columns_exist(table, data.keys()):
            print("Invalid columns. Aborting update.")
            return False

        where_condition = self.build_condition_string(condition)
        query = f"UPDATE {table} SET {self.build_set_string(data)} WHERE {where_condition}"
        values = tuple(data.values()) + tuple(condition.values())
        self.curs.execute(query, values)
        rows_affected = self.curs.rowcount

        if only and rows_affected != 1:
            print("More than one row affected. Aborting update.")
            self.conn.rollback()
            return False
        else:
            self.conn.commit()
            return True
    
    def close(self):
        self.curs.close()
        self.conn.close()


class Dictionary:
    def __init__(self, db: Database, table: str) -> None:
        self.db = db
        self.table = table
        self.fields = {'key': str, 'value': str, 'type': str}
        self.db.create_table(self.table, self.fields)
    
    def identify(self, value):
        val_type = 'non'
        if type(value)  == int:
            value = str(value)
            val_type = 'int'
        if type(value) in [dict, list, tuple]:
            value = str(value)
            val_type = 'ast'
        if type(value) == str: val_type = 'str'
        return value, val_type

    def __setitem__(self, key: str, value) -> None:
        self.set(key, value)

    def __getitem__(self, key: str) -> str:
        result = self.get(key)
        if result:
            return result
        raise KeyError(key)

    def __delitem__(self, key: str) -> None:
        self.db.delete_data(self.table, {'key': key})

    def set(self, key: str, value) -> None:
        if not type(key) == str:
            return
        value, val_type = self.identify(value)
        result = self.db.select_data(self.table, {'key': key})
        if result:
            self.db.update_data(self.table, {'value': value, 'type': val_type}, {'key': key})
        else:
            self.db.insert_data(self.table, {'key': key, 'value': value, 'type': val_type})

    def get(self, key: str) -> str:
        if not type(key) == str:
            return
        result = self.db.select_data(self.table, {'key': key})
        if result:
            value =  result[0]['value']
            val_type = result[0]['type']
            if val_type == 'int':
                return int(value)
            if val_type == 'ast':
                return ast.literal_eval(value)
            return value
        return None

    def delete(self, key: str) -> None:
        if not type(key) == str:
            return
        self.db.delete_data(self.table, {'key': key})