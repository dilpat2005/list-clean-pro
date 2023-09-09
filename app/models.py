# app/models.py

import psycopg2
from psycopg2 import sql
from app import db_params  # Import your db_params from __init__.py

class UserRole:
    def __init__(self, role_id, role_name, assign_task, complete_task, set_occupancy, set_room, manage_housekeepers, manage_assignments):
        self.role_id = role_id
        self.role_name = role_name
        self.assign_task = assign_task
        self.complete_task = complete_task
        self.set_occupancy = set_occupancy
        self.set_room = set_room
        self.manage_housekeepers = manage_housekeepers
        self.manage_assignments = manage_assignments

    @classmethod
    def create(cls, role_name, assign_task, complete_task, set_occupancy, set_room, manage_housekeepers, manage_assignments):
        try:
            connection = psycopg2.connect(**db_params)
            cursor = connection.cursor()

            insert_query = sql.SQL("INSERT INTO user_roles (role_name, assign_task, complete_task, set_occupancy, set_room, manage_housekeepers, manage_assignments) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING role_id;")
            cursor.execute(insert_query, (role_name, assign_task, complete_task, set_occupancy, set_room, manage_housekeepers, manage_assignments))
            new_role_id = cursor.fetchone()[0]
            connection.commit()

            cursor.close()
            connection.close()

            return cls(new_role_id, role_name, assign_task, complete_task, set_occupancy, set_room, manage_housekeepers, manage_assignments)
        except Exception as e:
            raise e

    @classmethod
    def get_by_id(cls, role_id):
        try:
            connection = psycopg2.connect(**db_params)
            cursor = connection.cursor()

            select_query = sql.SQL("SELECT * FROM user_roles WHERE role_id = %s;")
            cursor.execute(select_query, (role_id,))
            role_data = cursor.fetchone()

            cursor.close()
            connection.close()

            if role_data:
                role_id, role_name, assign_task, complete_task, set_occupancy, set_room, manage_housekeepers, manage_assignments = role_data
                return cls(role_id, role_name, assign_task, complete_task, set_occupancy, set_room, manage_housekeepers, manage_assignments)
            else:
                return None
        except Exception as e:
            raise e


class Assignment:
    def __init__(self, assignment_id, task_id, room_id, assigned_by, assigned_to, status, completion_date, notes, is_active):
        self.assignment_id = assignment_id
        self.task_id = task_id
        self.room_id = room_id
        self.assigned_by = assigned_by
        self.assigned_to = assigned_to
        self.status = status
        self.completion_date = completion_date
        self.notes = notes
        self.is_active = is_active

    @classmethod
    def create(cls, task_id, room_id, assigned_by, assigned_to, status, completion_date, notes):
        try:
            connection = psycopg2.connect(**db_params)
            cursor = connection.cursor()

            insert_query = sql.SQL("INSERT INTO assignments (task_id, room_id, assigned_by, assigned_to, status, completion_date, notes, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING assignment_id;")
            cursor.execute(insert_query, (task_id, room_id, assigned_by, assigned_to, status, completion_date, notes, True))
            new_assignment_id = cursor.fetchone()[0]
            connection.commit()

            cursor.close()
            connection.close()

            return cls(new_assignment_id, task_id, room_id, assigned_by, assigned_to, status, completion_date, notes, True)
        except Exception as e:
            raise e

    @classmethod
    def get_by_id(cls, assignment_id):
        try:
            connection = psycopg2.connect(**db_params)
            cursor = connection.cursor()

            select_query = sql.SQL("SELECT * FROM assignments WHERE assignment_id = %s;")
            cursor.execute(select_query, (assignment_id,))
            assignment_data = cursor.fetchone()

            cursor.close()
            connection.close()

            if assignment_data:
                assignment_id, task_id, room_id, assigned_by, assigned_to, status, completion_date, notes, is_active = assignment_data
                return cls(assignment_id, task_id, room_id, assigned_by, assigned_to, status, completion_date, notes, is_active)
            else:
                return None
        except Exception as e:
            raise e
