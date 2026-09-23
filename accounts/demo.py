"""
Demo accounts created by `manage.py seed_demo` and shown on the login page when
SHOW_DEMO_CREDENTIALS is enabled. Kept in one place so the seed and the login
page can never disagree.
"""

DEMO_PASSWORD = "demo1234"

DEMO_ACCOUNTS = [
    {"username": "staff", "role": "staff", "first_name": "LVAEP", "last_name": "Staff"},
    {"username": "tutor.maria", "role": "tutor", "first_name": "Maria", "last_name": "Alvarez"},
    {"username": "tutor.james", "role": "tutor", "first_name": "James", "last_name": "Okafor"},
    {"username": "student.ana", "role": "student", "first_name": "Ana", "last_name": "Pereira"},
    {"username": "student.wei", "role": "student", "first_name": "Wei", "last_name": "Chen"},
    {"username": "student.samuel", "role": "student", "first_name": "Samuel", "last_name": "Diallo"},
    {"username": "student.fatima", "role": "student", "first_name": "Fatima", "last_name": "Rahman"},
]
