from dataclasses import dataclass
from typing import Set

from serious import JsonModel


@dataclass(frozen=True)
class Student:
    id: int = 0
    name: str = "student"


@dataclass(frozen=True)
class Professor:
    id: int
    name: str


@dataclass(frozen=True)
class Course:
    id: int
    name: str
    professor: Professor
    students: Set[Student]


class TestEncoder:

    def setup_class(self):
        self.s1 = Student(1, 'student')
        self.p = Professor(1, 'professor')
        self.c = Course(1, 'course', self.p, {self.s1})

    def test_student(self):
        model = JsonModel(Student)
        assert model.dump(self.s1) == '{"id": 1, "name": "student"}'

    def test_professor(self):
        model = JsonModel(Professor)
        assert model.dump(self.p) == '{"id": 1, "name": "professor"}'

    def test_course(self):
        model = JsonModel(Course)
        assert model.dump(self.c) == '{"id": 1, ' \
                                      '"name": "course", ' \
                                      '"professor": {"id": 1, "name": "professor"}, ' \
                                      '"students": [{"id": 1, "name": "student"}]}'

    def test_students_missing(self):
        s1_anon = Student(1, 'student')
        s2_anon = Student(2, 'student')
        one = [s1_anon, s2_anon]
        two = [s2_anon, s1_anon]
        actual = JsonModel(Student, allow_missing=True).load_many('[{"id": 1}, {"id": 2}]')
        assert actual == one or actual == two
