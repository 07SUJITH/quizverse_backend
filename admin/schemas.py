import uuid

from ninja import Schema, ModelSchema
from typing import List, Union

from admin.models import *


class NameSchema(Schema):
    name: str


class InstitutionLink(Schema):
    link_id: List[str]

class FacultyCourseLinkSchema(Schema):
    course_id: str
    faculty_id: str

class FacultyOutSchema(ModelSchema):
    id: Union[str, uuid.UUID]

    class Meta:
        model = Faculty
        fields = "__all__"

class StudentOutSchema(ModelSchema):
    id: Union[str, uuid.UUID]

    class Meta:
        model = Student
        fields = "__all__"

class UserMembershipIDSchema(Schema):
    member_id: str
    user_id: str
    department_ids: List[str]


class GiveRolesMembershipSchema(Schema):
    user_membership_id: List[UserMembershipIDSchema]
    class_or_semester: Union[int, None]


class GiveRolesSchema(Schema):
    entity_id: str = None
    user_ids: List[str]


class InstitutionInSchema(ModelSchema):
    education_system_id: str

    class Meta:
        model = Institution
        exclude = ["id", "created_at", "updated_at", "education_system"]


class InstitutionOutSchema(ModelSchema):
    id: Union[str, uuid.UUID]

    class Meta:
        model = Institution
        fields = "__all__"


class EducationSystemOutSchema(ModelSchema):
    id: Union[str, uuid.UUID]

    class Meta:
        model = EducationSystem
        fields = "__all__"


class CommunityInSchema(ModelSchema):

    class Meta:
        model = Community
        exclude = ["id", "created_at", "updated_at"]


class CommunityOutSchema(ModelSchema):
    id: Union[str, uuid.UUID]

    class Meta:
        model = Community
        fields = "__all__"


class DepartmentOutSchema(ModelSchema):
    id: Union[str, uuid.UUID]

    class Meta:
        model = Department
        fields = "__all__"


class CourseInSchema(ModelSchema):
    department_id: str
    education_system_id: str

    class Meta:
        model = Course
        exclude = ["id", "created_at", "updated_at", "education_system"]


class CourseOutSchema(ModelSchema):
    id: Union[str, uuid.UUID]
    handled_by_faculty: List[dict] = None
    class Meta:
        model = Course
        fields = "__all__"


class ModuleInSchema(ModelSchema):
    course_id: str

    class Meta:
        model = Module
        exclude = ["id", "created_at", "updated_at"]


class ModuleOutSchema(ModelSchema):
    id: Union[str, uuid.UUID]

    class Meta:
        model = Module
        fields = "__all__"
