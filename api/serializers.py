from rest_framework import serializers
from django.contrib.auth.models import User
from core.models import Subsidiary, Subject, Level, Course, Package, Teacher, Room
from groups.models import Group, GroupCourse, Student
from schedule.models import SchedulePlan, ScheduledEvent, ScheduledEventCancellation, Event
from learning.models import (
    LearningMaterial, LearningMaterialNode, Curriculum, 
    CurriculumNode, CurriculumNodeMaterial, GroupCourseCurriculum
)
from rules.models import (
    WorkingPeriodRule, TeacherAvailabilityPeriod, TimeSlot, 
    RoomAvailabilityRule, ConflictType, Conflict
)


# Базовые сериализаторы для core моделей
class SubsidiarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subsidiary
        fields = '__all__'


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    subsidiary = SubsidiarySerializer(read_only=True)
    subsidiary_id = serializers.IntegerField(write_only=True)
    subject = SubjectSerializer(read_only=True)
    subject_id = serializers.IntegerField(write_only=True)
    level = LevelSerializer(read_only=True)
    level_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Course
        fields = '__all__'


class PackageSerializer(serializers.ModelSerializer):
    subsidiary = SubsidiarySerializer(read_only=True)
    subsidiary_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Package
        fields = '__all__'


class TeacherSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    subsidiaries = SubsidiarySerializer(many=True, read_only=True)
    subjects = SubjectSerializer(many=True, read_only=True)
    
    class Meta:
        model = Teacher
        fields = '__all__'


class RoomSerializer(serializers.ModelSerializer):
    subsidiary = SubsidiarySerializer(read_only=True)
    subsidiary_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Room
        fields = '__all__'


# Сериализаторы для groups моделей
class GroupSerializer(serializers.ModelSerializer):
    subsidiary = SubsidiarySerializer(read_only=True)
    subsidiary_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Group
        fields = '__all__'


class GroupCourseSerializer(serializers.ModelSerializer):
    group = GroupSerializer(read_only=True)
    group_id = serializers.IntegerField(write_only=True)
    course = CourseSerializer(read_only=True)
    course_id = serializers.IntegerField(write_only=True)
    package = PackageSerializer(read_only=True)
    package_id = serializers.IntegerField(write_only=True)
    teacher = TeacherSerializer(read_only=True)
    teacher_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = GroupCourse
        fields = '__all__'


class StudentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    groups = GroupSerializer(many=True, read_only=True)
    
    class Meta:
        model = Student
        fields = '__all__'


# Сериализаторы для schedule моделей
class SchedulePlanSerializer(serializers.ModelSerializer):
    subsidiary = SubsidiarySerializer(read_only=True)
    subsidiary_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = SchedulePlan
        fields = '__all__'


class ScheduledEventSerializer(serializers.ModelSerializer):
    plan = SchedulePlanSerializer(read_only=True)
    plan_id = serializers.IntegerField(write_only=True)
    group_course = GroupCourseSerializer(read_only=True)
    group_course_id = serializers.IntegerField(write_only=True)
    teacher = TeacherSerializer(read_only=True)
    teacher_id = serializers.IntegerField(write_only=True)
    room = RoomSerializer(read_only=True)
    room_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ScheduledEvent
        fields = '__all__'


class ScheduledEventCancellationSerializer(serializers.ModelSerializer):
    event = ScheduledEventSerializer(read_only=True)
    event_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ScheduledEventCancellation
        fields = '__all__'


class EventSerializer(serializers.ModelSerializer):
    subsidiary = SubsidiarySerializer(read_only=True)
    subsidiary_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Event
        fields = '__all__'


# Сериализаторы для learning моделей
class LearningMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningMaterial
        fields = '__all__'


class LearningMaterialNodeSerializer(serializers.ModelSerializer):
    material = LearningMaterialSerializer(read_only=True)
    material_id = serializers.IntegerField(write_only=True)
    parent = serializers.StringRelatedField(read_only=True)
    parent_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = LearningMaterialNode
        fields = '__all__'


class CurriculumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curriculum
        fields = '__all__'


class CurriculumNodeSerializer(serializers.ModelSerializer):
    curriculum = CurriculumSerializer(read_only=True)
    curriculum_id = serializers.IntegerField(write_only=True)
    parent = serializers.StringRelatedField(read_only=True)
    parent_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = CurriculumNode
        fields = '__all__'


class CurriculumNodeMaterialSerializer(serializers.ModelSerializer):
    curriculum_node = CurriculumNodeSerializer(read_only=True)
    curriculum_node_id = serializers.IntegerField(write_only=True)
    material_node = LearningMaterialNodeSerializer(read_only=True)
    material_node_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = CurriculumNodeMaterial
        fields = '__all__'


class GroupCourseCurriculumSerializer(serializers.ModelSerializer):
    group_course = GroupCourseSerializer(read_only=True)
    group_course_id = serializers.IntegerField(write_only=True)
    curriculum = CurriculumSerializer(read_only=True)
    curriculum_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = GroupCourseCurriculum
        fields = '__all__'


# Сериализаторы для rules моделей
class WorkingPeriodRuleSerializer(serializers.ModelSerializer):
    subsidiary = SubsidiarySerializer(read_only=True)
    subsidiary_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = WorkingPeriodRule
        fields = '__all__'


class TeacherAvailabilityPeriodSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer(read_only=True)
    teacher_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = TeacherAvailabilityPeriod
        fields = '__all__'


class TimeSlotSerializer(serializers.ModelSerializer):
    subsidiary = SubsidiarySerializer(read_only=True)
    subsidiary_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = TimeSlot
        fields = '__all__'


class RoomAvailabilityRuleSerializer(serializers.ModelSerializer):
    room = RoomSerializer(read_only=True)
    room_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = RoomAvailabilityRule
        fields = '__all__'


class ConflictTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConflictType
        fields = '__all__'


class ConflictSerializer(serializers.ModelSerializer):
    conflict_type = ConflictTypeSerializer(read_only=True)
    conflict_type_id = serializers.IntegerField(write_only=True)
    plan = SchedulePlanSerializer(read_only=True)
    plan_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Conflict
        fields = '__all__'


# Пользовательские сериализаторы
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']
        read_only_fields = ['id', 'is_staff']


# Сериализаторы для расширенных представлений
class ScheduleViewSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения расписания с полной информацией"""
    group_course = GroupCourseSerializer(read_only=True)
    teacher = TeacherSerializer(read_only=True)
    room = RoomSerializer(read_only=True)
    
    class Meta:
        model = ScheduledEvent
        fields = '__all__'


class TeacherScheduleSerializer(serializers.ModelSerializer):
    """Сериализатор для расписания преподавателя"""
    scheduled_events = ScheduleViewSerializer(many=True, read_only=True)
    
    class Meta:
        model = Teacher
        fields = ['id', 'user', 'phone', 'scheduled_events']


class GroupScheduleSerializer(serializers.ModelSerializer):
    """Сериализатор для расписания группы"""
    group_courses = GroupCourseSerializer(many=True, read_only=True)
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'subsidiary', 'group_courses']


class ConflictDetailSerializer(serializers.ModelSerializer):
    """Детализированный сериализатор конфликтов"""
    conflict_type = ConflictTypeSerializer(read_only=True)
    plan = SchedulePlanSerializer(read_only=True)
    
    class Meta:
        model = Conflict
        fields = '__all__' 