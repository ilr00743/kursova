from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404
from django.views import View
from django.views.generic import TemplateView, FormView
from django.views.generic.edit import FormMixin, ProcessFormView
from django.core.exceptions import FieldError, ObjectDoesNotExist
from django.db import IntegrityError, transaction, DataError
from django.core.paginator import Paginator
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import *
from .permissions import *
from .forms import *

class BaseView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        unread = MailboxReceived.objects.filter(
            recipient__user=self.request.user,
            read=False
        )
        context['unread'] = len(unread)
        try:
            context['username'] = self.request.session['user']
        except KeyError:
            context['username'] = None
        return context


class HomepageView(FormView):
    template_name = 'yourgrades/homepage.html'
    form_class = LoginForm

    def get(self, request, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data())

    def get_success_url(self):
        user_permission = list(self.request.user.get_all_permissions())[0]
        if user_permission == 'yourgrades.student':
            return reverse('yourgrades:student_parent')
        elif user_permission == 'yourgrades.parent':
            return reverse('yourgrades:student_parent')
        elif user_permission == 'yourgrades.teacher':
            return reverse('yourgrades:teacher')
        elif user_permission == 'yourgrades.manager':
            return reverse('yourgrades:manager')
        else:
            raise ValueError("Unknown permission")

    def form_valid(self, form):
        try:
            User.objects.get(username=form.cleaned_data['username'])
        except User.DoesNotExist:
            # User doesnt exist
            return render(
                self.request, 'yourgrades/homepage.html',
                {'form': form, 'user_no_exist': True}
            )
        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )
        if user is not None:
            login(self.request, user)
        else:
            # Wrong password
            return render(
                self.request,
                'yourgrades/homepage.html',
                {'form': form, 'wrong_password': True}
            )
        self.request.session['user'] = f'{self.request.user.first_name} ' \
                                       f'{self.request.user.last_name}'
        return super().form_valid(form)


class LogOutView(View):
    def get(self, request):
        if request.user.is_authenticated:
            logout(request)
            request.session['user'] = None
        return HttpResponseRedirect(reverse('yourgrades:homepage'))


class FirstLoginView(LoginRequiredMixin, UserPassesTestMixin, ProcessFormView,
                     FormMixin, BaseView):
    template_name = 'yourgrades/firstlogin.html'
    form_class = FirstLoginForm
    permission = {
        'yourgrades.student': Student,
        'yourgrades.parent': Parent,
        'yourgrades.teacher': Teacher
    }

    def test_func(self):
        test = False
        if self.request.user.has_perm('yourgrades.student') \
                or self.request.user.has_perm('yourgrades.parent') \
                or self.request.user.has_perm('yourgrades.teacher'):
            test = True
        return test

    def get_success_url(self):
        user_permission = list(self.request.user.get_all_permissions())[0]
        if user_permission == 'yourgrades.student':
            self.request.session['user'] = get_object_or_404(
                Student,
                user=self.request.user
            ).__str__()
            return reverse('yourgrades:student_parent')
        elif user_permission == 'yourgrades.parent':
            self.request.session['user'] = get_object_or_404(
                Parent,
                user=self.request.user
            ).__str__()
            return reverse('yourgrades:student_parent')
        elif user_permission == 'yourgrades.teacher':
            self.request.session['user'] = get_object_or_404(
                Teacher,
                user=self.request.user
            ).__str__()
            return reverse('yourgrades:teacher')
        elif user_permission == 'yourgrades.manager':
            self.request.session['user'] = self.request.user.username
            return reverse('yourgrades:manager')
        else:
            raise ValueError("Unknown permission")

    def get_initial(self):
        initial = super().get_initial()
        username = self.request.user.username
        initial['username'] = username
        return initial

    def form_valid(self, form):
        user = self.request.user
        with transaction.atomic():
            if form.cleaned_data['username'] != user.username:
                try:
                    user.username = form.cleaned_data['username']
                    user.save()
                except IntegrityError:
                    return render(
                        self.request,
                        'yourgrades/firstlogin.html',
                        {'form': form, 'user_taken': True, }
                    )
            if form.cleaned_data['password'] == \
                    form.cleaned_data['password_confirm']:
                try:
                    user.set_password(form.cleaned_data['password'])
                    user.save()
                    login(self.request, user)
                except IntegrityError:
                    raise Http404('Password problem.')
            else:
                return render(
                    self.request,
                    'yourgrades/firstlogin.html',
                    {'form': form, 'pass_no_confirm': True, }
                )
            user_permission = list(self.request.user.get_all_permissions())[0]
            person = get_object_or_404(
                self.permission[user_permission],
                user=user
            )
            person.first_login = False
            person.save()
        return super().form_valid(form)


class ManagerPanelView(LoginRequiredMixin, UserPassesTestMixin, BaseView):
    template_name = 'yourgrades/manager.html'
    inactive_school_classes = None
    inactive_teachers = None

    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def post(self, request, **kwargs):
        try:
            if request.POST['inactive_class'] == 'on':
                self.inactive_school_classes = \
                    SchoolClass.objects.filter(active=False).order_by('-year')
            else:
                self.inactive_school_classes = None
            return super(ManagerPanelView, self).render_to_response(
                self.get_context_data(**kwargs)
            )
        except KeyError:
            try:
                if request.POST['inactive_teachers'] == 'on':
                    self.inactive_teachers = \
                        Teacher.objects.filter(active=False).order_by('name')
                else:
                    self.inactive_teachers = None
                return super(ManagerPanelView, self).render_to_response(
                    self.get_context_data(**kwargs)
                )
            except KeyError:
                return HttpResponseRedirect(
                    self.request.META.get('HTTP_REFERER')
                )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classes'] = SchoolClass.objects.filter(
            active=True
        ).order_by('name')
        context['ia_classes'] = self.inactive_school_classes

        students = {}
        for my_class in context['classes']:
            all_students = Student.objects.filter(school_class=my_class)
            students[my_class] = all_students
        context['students'] = students

        context['teachers'] = Teacher.objects.filter(
            active=True
        ).order_by('name')
        context['ia_teachers'] = self.inactive_teachers
        return context


class CreateSchoolClassView(LoginRequiredMixin, UserPassesTestMixin,
                            ProcessFormView, FormMixin, BaseView):
    template_name = 'yourgrades/managercreateschoolclass.html'
    form_class = SchoolClassForm

    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def get_success_url(self):
        return reverse('yourgrades:manager')

    def form_valid(self, form):
        # Method is called only when data is valid
        current_class = form.save(commit=False)
        current_class.unique_code = f'{form["name"].value()}' \
                                    f'{form["year"].value()}'
        current_class.save()
        return super().form_valid(form)


class EditSchoolClassView(LoginRequiredMixin, UserPassesTestMixin,
                          ProcessFormView, FormMixin, BaseView):
    template_name = 'yourgrades/managereditschoolclass.html'
    form_class = CreateStudentForm

    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['students'] = Student.objects.filter(
            school_class__unique_code=self.kwargs['class_unique_code']
        ).order_by('surname')
        school_class = get_object_or_404(
            SchoolClass,
            unique_code=self.kwargs['class_unique_code']
        )
        context['current_class'] = school_class
        context['subjects'] = Subject.objects.filter(school_class=school_class)
        return context

    def get_success_url(self):
        return reverse(
            'yourgrades:edit_school_class',
            kwargs={'class_unique_code': self.kwargs['class_unique_code']}
        )

    def create_gradebook_user(self, form, person):
        valid = {'student', 'parent1', 'parent2', 'teacher'}
        if person not in valid:
            raise ValueError(f'person parameter must be one of {valid}.')

        if person == 'student':
            prefix = '123'
            permission_codename = 'student'
            name = 'name'
            surname = 'surname'
        elif person == 'parent1':
            prefix = '345'
            permission_codename = 'parent'
            name = 'first_parent_name'
            surname = 'first_parent_surname'
        elif person == 'parent2':
            prefix = '345'
            permission_codename = 'parent'
            name = 'second_parent_name'
            surname = 'second_parent_surname'

        username = form.cleaned_data[name] + form.cleaned_data[surname]
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                password=username + prefix
            )
        else:
            numbering = 2
            while True:
                new_username = f'{username}{numbering}'
                if not User.objects.filter(username=new_username).exists():
                    user = User.objects.create_user(
                        username=new_username,
                        password=f'{new_username}{prefix}'
                    )
                    break
                else:
                    numbering += 1
        # Add permission
        content_type = ContentType.objects.get_for_model(RightsSupport)
        permission = Permission.objects.get(
            content_type=content_type,
            codename=permission_codename
        )
        user.user_permissions.add(permission)
        user.first_name = form.cleaned_data[name]
        user.last_name = form.cleaned_data[surname]
        return user

    def form_valid(self, form, **kwargs):
        with transaction.atomic():
            user = self.create_gradebook_user(form, 'student')
            user.save()
            school_class = get_object_or_404(
                SchoolClass,
                unique_code=self.kwargs['class_unique_code']
            )
            student = Student(
                user=user,
                name=form.cleaned_data['name'],
                surname=form.cleaned_data['surname'],
                birthday=form.cleaned_data['birthday'],
                school_class=school_class,
            )
            student.save()
            user = self.create_gradebook_user(form, 'parent1')
            user.save()
            parent1 = Parent(
                user=user,
                name=form.cleaned_data['first_parent_name'],
                surname=form.cleaned_data['first_parent_surname'],
                student=student
            )
            parent1.save()
            if not form.cleaned_data['second_parent_name'] or not \
                    form.cleaned_data['second_parent_surname']:
                return super().form_valid(form)
            else:
                user = self.create_gradebook_user(form, 'parent2')
                user.save()
                parent2 = Parent(
                    user=user,
                    name=form.cleaned_data['second_parent_name'],
                    surname=form.cleaned_data['second_parent_surname'],
                    student=student
                )
                parent2.save()
                return super().form_valid(form)


class DeactivationSchoolClassView(LoginRequiredMixin, UserPassesTestMixin,
                                  View):
    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def post(self, request, **kwargs):
        current_class = get_object_or_404(
            SchoolClass,
            unique_code=kwargs['class_unique_code']
        )
        current_class.active = False
        current_class.save()
        return HttpResponseRedirect(
            reverse(
                'yourgrades:edit_school_class',
                kwargs={'class_unique_code': kwargs['class_unique_code']}
            )
        )


class DeactivationTeacherView(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def get(self, request, **kwargs):
        teacher = get_object_or_404(
            Teacher,
            user__id=kwargs['teacher_user_id']
        )
        teacher.active = False
        teacher.save()
        return HttpResponseRedirect(reverse('yourgrades:manager'))


class ActivationSchoolClassView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def post(self, request, **kwargs):
        current_class = get_object_or_404(
            SchoolClass,
            unique_code=kwargs['class_unique_code']
        )
        current_class.active = True
        current_class.save()
        return HttpResponseRedirect(
            reverse(
                'yourgrades:edit_school_class',
                kwargs={'class_unique_code': kwargs['class_unique_code']}
            )
        )


class ActivationTeacherView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def get(self, request, **kwargs):
        teacher = get_object_or_404(
            Teacher,
            user__id=kwargs['teacher_user_id']
        )
        teacher.active = True
        teacher.save()
        return HttpResponseRedirect(reverse('yourgrades:manager'))


class DeleteStudentView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def get(self, request, **kwargs):
        student = get_object_or_404(Student, user__id=kwargs['user_id'])
        parents = get_list_or_404(Parent, student=student)
        class_unique_code = student.school_class.unique_code

        parent_user = parents[0].user
        parent_user.delete()
        try:
            parent_user = parents[1].user
            parent_user.delete()
        except IndexError:
            pass
        student_user = student.user
        student_user.delete()

        return HttpResponseRedirect(
            reverse(
                'yourgrades:edit_school_class',
                kwargs={'class_unique_code': class_unique_code}
            )
        )


class AddTeacherView(LoginRequiredMixin, UserPassesTestMixin, ProcessFormView,
                     FormMixin, BaseView):
    template_name = 'yourgrades/manageraddteacher.html'
    form_class = CreateTeacherForm

    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def get_success_url(self):
        return reverse('yourgrades:manager')

    def form_valid(self, form):
        # Method is called only when data is valid
        username = form.cleaned_data['name'] + form.cleaned_data['surname']
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                password=f'{username}234'
            )
            content_type = ContentType.objects.get_for_model(RightsSupport)
            permission = Permission.objects.get(
                content_type=content_type,
                codename='teacher'
            )
            user.user_permissions.add(permission)
        else:
            numbering = 2
            while True:
                new_username = username + str(numbering)
                if not User.objects.filter(username=new_username).exists():
                    user = User.objects.create_user(
                        username=new_username,
                        password=f'{new_username}123'
                    )
                    content_type = ContentType.objects.get_for_model(
                        RightsSupport
                    )
                    permission = Permission.objects.get(
                        content_type=content_type,
                        codename='teacher'
                    )
                    user.user_permissions.add(permission)
                    break
                else:
                    numbering += 1
        user.first_name = form.cleaned_data['name']
        user.last_name = form.cleaned_data['surname']
        with transaction.atomic():
            user.save()
            teacher = Teacher(
                user=user,
                name=form.cleaned_data['name'],
                surname=form.cleaned_data['surname'],
            )
            teacher.save()
        return super().form_valid(form)


class AddSubjectView(LoginRequiredMixin, UserPassesTestMixin, ProcessFormView,
                     FormMixin, BaseView):
    template_name = 'yourgrades/manageraddsubject.html'
    form_class = CreateSubjectForm

    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def get_success_url(self):
        return reverse(
            'yourgrades:edit_school_class', 
            kwargs={'class_unique_code': self.kwargs['class_unique_code']}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['class_unique_code'] = self.kwargs['class_unique_code']
            return context
        except KeyError:
            raise Http404("There was a problem getting the class code.")

    def form_valid(self, form):
        with transaction.atomic():
            try:
                subject = Subject(
                    name=form.cleaned_data['name'],
                    unique_code=f'{form.cleaned_data["shortcut"]}'
                                f'{self.kwargs["class_unique_code"]}',
                    school_class=SchoolClass.objects.get(
                        unique_code=self.kwargs['class_unique_code']
                    )
                )
                subject.save()
            except IntegrityError:
                context = self.get_context_data()
                context['form'] = form
                context['shortcut_error'] = True
                return render(
                    self.request,
                    'yourgrades/manageraddsubject.html',
                    context
                )
            try:
                subject_teachers = SubjectTeachers(subject=subject)
                subject_teachers.save()
                for teacher in form.cleaned_data['teachers']:
                    subject_teachers.teacher.add(teacher)
                    subject_teachers.save()
            except IntegrityError:
                raise Http404("There was a problem with submitting form data.")
        return super().form_valid(form)


class ManagerSubjectView(LoginRequiredMixin, UserPassesTestMixin,
                         ProcessFormView, FormMixin, BaseView):
    template_name = 'yourgrades/managersubjectpanel.html'
    form_class = AddSubjectDateForm

    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def get_success_url(self):
        return reverse(
            'yourgrades:subject_view',
            kwargs={
                'class_unique_code': self.kwargs['class_unique_code'],
                'subject_unique_code': self.kwargs['subject_unique_code']
            }
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subject = get_object_or_404(
            Subject,
            unique_code=self.kwargs['subject_unique_code']
        )
        school_class = get_object_or_404(
            SchoolClass,
            unique_code=self.kwargs['class_unique_code']
        )
        context['subject'] = subject
        context['class'] = school_class
        subject_dates = SubjectDate.objects.filter(subject=subject)
        dates = [[False for days in range(1, 7)] for lessons in range(1, 9)]
        for subject_date in subject_dates:
            iteration = -1
            for day in ['Mo', 'Tu', 'We', 'Th', 'Fr', 'St']:
                iteration += 1
                if subject_date.day == day:
                    break
            dates[subject_date.lesson_number - 1][iteration] = True
        context['dates'] = dates

        try:
            subject_teachers = SubjectTeachers.objects.get(subject=subject)
            context['teachers'] = subject_teachers.teacher.all()
        except SubjectTeachers.DoesNotExist:
            context['teachers'] = None
        grades = Grades.objects.filter(
            subject=subject,
            manager_mode=False
        ).order_by('date')
        manager_grades = Grades.objects.filter(
            subject=subject,
            manager_mode=True
        ).order_by('date')
        manager_canceled_grades = CanceledGrades.objects.filter(
            subject=subject
        ).order_by('date')
        paginator_grades = Paginator(grades, 10)
        paginator_manager_grades = Paginator(manager_grades, 10)
        paginator_manager_canceled_grades = Paginator(
            manager_canceled_grades,
            10
        )
        context['grades'] = paginator_grades.get_page(
            self.request.GET.get('page1')
        )
        context['manager_grades'] = paginator_manager_grades.get_page(
            self.request.GET.get('page2')
        )
        context['manager_canceled_grades'] = \
            paginator_manager_canceled_grades.get_page(
                self.request.GET.get('page3')
            )
        if 'exist' in self.kwargs:
            context['exist'] = self.kwargs['exist']
        return context

    def form_valid(self, form):
        try:
            SubjectDate.objects.get(
                day=form.cleaned_data['day'],
                lesson_number=form.cleaned_data['lesson_number'],
                subject__unique_code=self.kwargs['subject_unique_code']
            )
            return self.render_to_response(
                self.get_context_data(form=form, exist=True)
            )
        except SubjectDate.DoesNotExist:
            with transaction.atomic():
                subject_date = form.save(commit=False)
                subject = get_object_or_404(
                    Subject,
                    unique_code=self.kwargs['subject_unique_code']
                )
                subject_date.subject = subject
                subject_date.save()
        return super().form_valid(form)


class DeleteSubjectDateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def get(self, request, **kwargs):
        days = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'St']
        day = days[kwargs['day'] - 1]
        lesson = kwargs['lesson']
        date = get_object_or_404(SubjectDate, lesson_number=lesson, day=day)
        date.delete()
        return HttpResponseRedirect(
            reverse(
                'yourgrades:subject_view',
                kwargs={
                    'class_unique_code': kwargs['class_unique_code'],
                    'subject_unique_code': kwargs['subject_unique_code'],
                }
            )
        )


class TimetableView(LoginRequiredMixin, UserPassesTestMixin, BaseView):
    template_name = 'yourgrades/timetable.html'

    def test_func(self):
        test = False
        if self.request.user.has_perm('yourgrades.student') or \
                self.request.user.has_perm('yourgrades.parent') or \
                self.request.user.has_perm('yourgrades.teacher'):
            test = True
        return test

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['person'] = self.kwargs['person']
        if self.kwargs['person'] == 'student':
            try:
                student = Student.objects.get(user=self.request.user)
            except Student.DoesNotExist:
                student = get_list_or_404(
                    Parent,
                    user=self.request.user
                )[0].student
            subjects = Subject.objects.filter(
                school_class=student.school_class
            )

        elif self.kwargs['person'] == 'teacher':
            teacher = get_object_or_404(Teacher, user=self.request.user)
            subject_teacher = SubjectTeachers.objects.filter(
                teacher=teacher,
                subject__school_class__active=True
            )
            subjects = [subject.subject for subject in subject_teacher]

        all_subject_dates = {}
        for subject in subjects:
            all_subject_dates[subject] = SubjectDate.objects.filter(
                subject=subject,
            )
        dates = [[False for days in range(1, 7)] for lessons in range(1, 9)]

        for subject_dates in all_subject_dates.values():
            for subject_date in subject_dates:
                iteration = -1
                for day in ['Mo', 'Tu', 'We', 'Th', 'Fr', 'St']:
                    iteration += 1
                    if subject_date.day == day:
                        break
                dates[subject_date.lesson_number - 1][iteration] = \
                    subject_date.subject
        context['dates'] = dates

        return context


class ManagerStudentView(LoginRequiredMixin, UserPassesTestMixin,
                         ProcessFormView, FormMixin, BaseView):
    template_name = 'yourgrades/managerstudent.html'
    form_class = AddGradeForm

    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def get_success_url(self):
        return reverse(
            'yourgrades:manager_student',
            kwargs={'user_id': self.kwargs['user_id']}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = get_object_or_404(
            Student,
            user__id=self.kwargs['user_id']
        )
        context['student'] = student
        parents = Parent.objects.filter(student=student)

        parents_active = {}
        for parent in parents:
            if parent.first_login is True:
                parents_active[parent] = parent.user.username
            else:
                parents_active[parent] = None

        context['parents_active'] = parents_active
        subjects = Subject.objects.filter(
            school_class=student.school_class
        )

        subject_grades = {}
        for subject in subjects:
            subject_grades[subject] = Grades.objects.filter(
                subject=subject,
                student=student
            )
        context['subject_grades'] = subject_grades
        context['invalid'] = self.get_second_form()

        try:
            context['del'] = self.kwargs['del']
        except KeyError:
            context['del'] = None

        return context

    def get_second_form(self):
        if self.request.method == 'POST':
            try:
                return tuple(
                    (
                        AddGradeForm(self.request.POST),
                        self.request.POST.get('subject')
                    )
                )
            except KeyError:
                return None
        else:
            return None

    def form_invalid(self, form):
        if 'del_grade' in self.request.POST:
            grade = get_object_or_404(
                Grades,
                id=self.request.POST.get('del_grade')
            )
            canceled_grade = CanceledGrades(
                grade=grade.grade,
                date=grade.date,
                subject=grade.subject,
                student=grade.student
            )
            canceled_grade.save()
            with transaction.atomic():
                message = Message(
                    subject='Оцінку відмінено',
                    text=f'Твою оцінку ({grade.grade}) з предмету {grade.subject.name} '
                         f'було відмінено.'
                )
                message.save()
                sender = Sender(user=self.request.user, message=message)
                sender.save()
                recipient = Recipient(user=grade.student.user, message=message)
                recipient.save()
                mailbox_received = MailboxReceived(
                    sender=sender,
                    recipient=recipient,
                    message=message
                )
                mailbox_received.save()
            grade.delete()
            self.kwargs['del'] = True
        form = AddGradeForm()
        return super().form_invalid(form)

    def form_valid(self, form):
        subject = get_object_or_404(
            Subject,
            unique_code=self.request.POST.get('subject')
        )
        student = get_object_or_404(Student, user__id=self.kwargs['user_id'])
        try:
            grade = form.save(commit=False)
            grade.student = student
            grade.subject = subject
            grade.manager_mode = True
            grade.save()
        except FieldError:
            raise Http404(
                "There was a problem with grade saving. Try again later"
            )
        try:
            message = Message(
                subject='Нова оцінка',
                text=f'Введена нова оцінка з предмету {subject.name}. '
                     f'Твоя оцінка {grade.grade}.',
            )
            with transaction.atomic():
                message.save()
                sender = Sender(user=self.request.user, message=message)
                sender.save()
                recipient = Recipient(user=student.user, message=message)
                recipient.save()
                mailbox_received = MailboxReceived(
                    sender=sender,
                    recipient=recipient,
                    message=message
                )
                mailbox_received.save()
        except FieldError:
            raise Http404(
                "There was a problem sending messages about new grade"
            )
        return super().form_valid(form)


class ManagerGradesHistoryView(LoginRequiredMixin, UserPassesTestMixin,
                               BaseView):
    template_name = 'yourgrades/managerhistory.html'

    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grades = Grades.objects.filter(manager_mode=True)
        canceled_grades = CanceledGrades.objects.all()

        paginator_grades = Paginator(grades, 10)
        paginator_canceled_grades = Paginator(canceled_grades, 10)
        context['grades'] = paginator_grades.get_page(
            self.request.GET.get('page1')
        )
        context['canceled_grades'] = paginator_canceled_grades.get_page(
            self.request.GET.get('page2')
        )
        return context


class DeleteSubjectView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def get(self, request, **kwargs):
        subject = get_object_or_404(
            Subject, unique_code=self.kwargs['subject_unique_code']
        )
        subject.delete()
        return HttpResponseRedirect(
            reverse(
                'yourgrades:edit_school_class',
                kwargs={'class_unique_code': self.kwargs['class_unique_code']}
            )
        )


class DeleteSubjectTeacherView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def get(self, request, **kwargs):
        teacher = Teacher.objects.get(user__id=self.kwargs['teacher_user_id'])
        subject = get_object_or_404(
            Subject,
            unique_code=self.kwargs['subject_unique_code']
        )
        subject_teacher = get_object_or_404(
            SubjectTeachers,
            subject=subject,
            teacher=teacher
        )
        subject_teacher.teacher.remove(teacher)
        return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))


class ManagerDeleteTeacherView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def get(self, request, **kwargs):
        teacher = Teacher.objects.get(user__id=self.kwargs['teacher_user_id'])
        teacher_user = teacher.user
        teacher_user.delete()
        return HttpResponseRedirect(reverse('yourgrades:manager'))


class ManagerResetUserView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def get(self, request, **kwargs):
        user = get_object_or_404(User, id=self.kwargs['user_id'])
        username = user.first_name + user.last_name
        try:
            existing_user = User.objects.get(username=username)
            if existing_user.id == user.id:
                user.set_password(username + str(self.kwargs['prefix']))
            else:
                numbering = 2
                while True:
                    new_username = username + str(numbering)
                    if not User.objects.filter(username=new_username).exists():
                        user.username = new_username
                        user.set_password(
                            new_username + str(self.kwargs['prefix'])
                        )
                        break
                    numbering += 1
        except User.DoesNotExist:
            user.username = username
            user.set_password(username + str(self.kwargs['prefix']))
        with transaction.atomic():
            user.save()
            if self.kwargs['prefix'] == 123:
                student = get_object_or_404(Student, user=user)
                student.first_login = True
                student.save()
            elif self.kwargs['prefix'] == 234:
                teacher = get_object_or_404(Teacher, user=user)
                teacher.first_login = True
                teacher.save()
            elif self.kwargs['prefix'] == 345:
                parent = get_object_or_404(Parent, user=user)
                parent.first_login = True
                parent.save()
        return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))


class ManagerTeacherEditView(LoginRequiredMixin, UserPassesTestMixin,
                             ProcessFormView, FormMixin, BaseView):
    template_name = 'yourgrades/managereditteacher.html'
    form_class = CreateTeacherForm

    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def get_success_url(self):
        return reverse('yourgrades:manager_teacher', kwargs={
            'teacher_user_id': self.kwargs['teacher'].user.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['teacher'] = self.kwargs['teacher']
        return context

    def get_initial(self):
        teacher = get_object_or_404(
            Teacher,
            user__id=self.kwargs['user_id']
        )
        self.kwargs['teacher'] = teacher
        initial = {'name': teacher.name, 'surname':teacher.surname}
        return initial

    def form_valid(self, form):
        teacher = self.kwargs['teacher']
        teacher.name = form.cleaned_data['name']
        teacher.surname = form.cleaned_data['surname']
        with transaction.atomic():
            teacher.save()
            teacher.user.first_name = teacher.name
            teacher.user.last_name = teacher.surname
            teacher.user.save()
        return super().form_valid(form)


class ManagerStudentEditView(LoginRequiredMixin, UserPassesTestMixin,
                             ProcessFormView, FormMixin, BaseView):
    template_name = 'yourgrades/managereditstudent.html'
    form_class = CreateStudentForm

    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = self.kwargs['student']
        return context

    def get_initial(self):
        student = get_object_or_404(
            Student,
            user__id=self.kwargs['user_id']
        )
        self.kwargs['student'] = student
        parents = Parent.objects.filter(student=student).order_by('user__id')
        self.kwargs['parents'] = parents
        initial = {
            'name': student.name,
            'surname': student.surname,
            'birthday': student.birthday,
            'first_parent_name': parents[0].name,
            'first_parent_surname': parents[0].surname
        }
        try:
            initial['second_parent_name'] = parents[1].name
            initial['second_parent_surname'] = parents[1].surname
        except IndexError:
            pass
        return initial

    def get_success_url(self):
        return reverse(
            'yourgrades:manager_student',
            kwargs={'user_id': self.kwargs['student'].user.id}
        )

    def form_valid(self, form):
        student = self.kwargs['student']
        parents = self.kwargs['parents']

        student.name = form.cleaned_data['name']
        student.surname = form.cleaned_data['surname']
        student.birthday = form.cleaned_data['birthday']
        with transaction.atomic():
            student.save()
            student.user.first_name = student.name
            student.user.last_name = student.surname

            parents[0].name = form.cleaned_data['first_parent_name']
            parents[0].surname = form.cleaned_data['first_parent_surname']
            parents[0].save()
            parents[0].user.first_name = parents[0].name
            parents[0].user.last_name = parents[0].surname
            parents[0].user.save()
            try:
                parents[1].name = form.cleaned_data['second_parent_name']
                parents[1].surname = form.cleaned_data['second_parent_surname']
                parents[1].save()
                parents[1].user.first_name = parents[1].name
                parents[1].user.last_name = parents[1].surname
                parents[1].user.save()
            except IndexError:
                pass
        return super().form_valid(form)


class AddSubjectTeacherView(LoginRequiredMixin, UserPassesTestMixin,
                            ProcessFormView, FormMixin, BaseView):
    template_name = 'yourgrades/manageraddsubjectteacher.html'
    form_class = AddSubjectTeacherForm

    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def get_success_url(self):
        return reverse(
                'yourgrades:subject_view',
                kwargs={
                    'class_unique_code': self.kwargs['class_unique_code'],
                    'subject_unique_code': self.kwargs['subject_unique_code'],
                }
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class'] = get_object_or_404(
            SchoolClass,
            unique_code=self.kwargs['class_unique_code']
        )
        context['subject'] = get_object_or_404(
            Subject,
            unique_code=self.kwargs['subject_unique_code']
        )
        return context

    def form_valid(self, form):
        # Method is called only when data is valid
        subject = get_object_or_404(
            Subject,
            unique_code=self.kwargs['subject_unique_code']
        )
        with transaction.atomic():
            try:
                subject_teachers = SubjectTeachers.objects.get(subject=subject)
            except SubjectTeachers.DoesNotExist:
                subject_teachers = SubjectTeachers(subject=subject)
                subject_teachers.save()
            for teacher in form.cleaned_data['teachers']:
                subject_teachers.teacher.add(teacher)
                subject_teachers.save()
        return super().form_valid(form)


class ManagerTeacherView(LoginRequiredMixin, UserPassesTestMixin, BaseView):
    template_name = 'yourgrades/managerteacher.html'

    def test_func(self):
        return self.request.user.has_perm('yourgrades.manager')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = get_object_or_404(
            Teacher,
            user__id=kwargs['teacher_user_id']
        )
        subject_teacher = SubjectTeachers.objects.filter(teacher=teacher)
        subjects = [subject.subject for subject in subject_teacher]
        context['subjects'] = subjects
        context['teacher'] = teacher
        return context


class TeacherPanelView(LoginRequiredMixin, UserPassesTestMixin, BaseView):
    template_name = 'yourgrades/teacher.html'

    def test_func(self):
        return self.request.user.has_perm('yourgrades.teacher')

    def get(self, request, *args, **kwargs):
        teacher = get_object_or_404(Teacher, user=self.request.user)
        if teacher.first_login is True:
            return HttpResponseRedirect(reverse('yourgrades:first_login'))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = get_object_or_404(Teacher, user=self.request.user)
        try:
            subject_teacher = SubjectTeachers.objects.filter(teacher=teacher)
            subjects = [subject.subject for subject in subject_teacher]
            context['subjects'] = subjects
            school_classes = [
                subject.subject.school_class for subject in subject_teacher
            ]
            school_classes = list(dict.fromkeys(school_classes))
            context['school_classes'] = school_classes
        except SubjectTeachers.DoesNotExist:
            context['nosubjects'] = True

        return context


class TeacherSubjectView(LoginRequiredMixin, UserPassesTestMixin,
                         ProcessFormView, FormMixin, BaseView):
    template_name = 'yourgrades/teachersubject.html'
    form_class = AddGradeForm

    def test_func(self):
        return self.request.user.has_perm('yourgrades.teacher')

    def get_success_url(self):
        return reverse('yourgrades:teacher_subject', kwargs={
            'subject_unique_code': self.kwargs['subject_unique_code']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subject = get_object_or_404(
            Subject,
            unique_code=self.kwargs['subject_unique_code']
        )
        context['subject'] = subject
        students = Student.objects.filter(
            school_class=subject.school_class
        ).order_by('surname')
        context['students'] = [
            (student, Grades.objects.filter(subject=subject, student=student))
            for student in students
        ]
        context['form2'] = self.get_second_form()[0]
        context['invalid_student'] = self.get_second_form()[1]
        grades = Grades.objects.filter(
            subject=subject,
            manager_mode=False
        ).order_by('date')
        manager_grades = Grades.objects.filter(
            subject=subject,
            manager_mode=True
        ).order_by('date')
        manager_canceled_grades = CanceledGrades.objects.filter(
            subject=subject,
        ).order_by('date')
        paginator_grades = Paginator(grades, 10)
        paginator_manager_grades = Paginator(manager_grades, 10)
        paginator_manager_canceled_grades = Paginator(
            manager_canceled_grades,
            10
        )
        context['grades'] = paginator_grades.get_page(
            self.request.GET.get('page1')
        )
        context['manager_grades'] = paginator_manager_grades.get_page(
            self.request.GET.get('page2')
        )
        context['manager_canceled_grades'] = \
            paginator_manager_canceled_grades.get_page(
                self.request.GET.get('page3')
            )
        return context

    def get_second_form(self):
        if self.request.method == 'POST':
            current_form = AddGradeForm(self.request.POST)
            if not current_form.is_valid():
                try:
                    student = get_object_or_404(
                        Student,
                        user__id=self.request.POST.get('student')
                    )
                    return current_form, student
                except KeyError:
                    return None, None
        return None, None

    def form_invalid(self, form):
        form = AddGradeForm()
        return self.render_to_response(
            self.get_context_data(form=form, wrong=True)
        )

    def form_valid(self, form):
        # Method is called only when data is valid
        subject = get_object_or_404(
            Subject,
            unique_code=self.kwargs['subject_unique_code']
        )
        student = get_object_or_404(
            Student,
            user__id=self.request.POST.get('student')
        )
        try:
            grade = form.save(commit=False)
            grade.student = student
            grade.subject = subject
            grade.save()
        except FieldError:
            raise Http404(
                "There was a problem with grade saving. Try again later"
            )
        message = Message(
            subject='Нова оцінка',
            text=f'Ти отримав нову оцінку з предмету {subject.name}. '
                 f'Твоя оцінка: {grade.grade}.'
        )
        with transaction.atomic():
            try:
                message.save()
            except (DataError, TypeError):
                raise Http404('Text or subject too long or wrong datatype')
            sender = Sender(user=self.request.user, message=message)
            sender.save()
            recipient = Recipient(user=student.user, message=message)
            recipient.save()
            try:
                mailbox_received = MailboxReceived(
                    sender=sender,
                    recipient=recipient,
                    message=message
                )
                mailbox_received.save()
            except FieldError:
                raise Http404(
                    "There was a problem sending messages about new grade"
                )
        return super().form_valid(form)


class CreateMessageView(LoginRequiredMixin, UserPassesTestMixin,
                        ProcessFormView, FormMixin, BaseView):
    """
    Passes messages between users. The view uses 2 variables

    *prefix - specifies the type of recipient:
    1 - school class
    2 - all parents of class students
    3 - all subject teachers
    4 - single student
    5 - parents of student
    6 - manager
    7 - single teacher

    *code - represents:
        class.unique_code for 1,2 prefixes,
        user.id for 4,5,7 prefixes (for prefix 5- student.user.id not parents!)
        None for manager (sends to all managers), subject unique_code for
        prefix 3
    """
    template_name = 'yourgrades/message.html'
    form_class = MessageForm

    def test_func(self):
        test = False
        if self.request.user.has_perm('yourgrades.student') or \
                self.request.user.has_perm('yourgrades.parent') or \
                self.request.user.has_perm('yourgrades.teacher') or \
                self.request.user.has_perm('yourgrades.manager'):
            test = True
        return test

    def get_success_url(self):
        user_permission = list(self.request.user.get_all_permissions())[0]
        if user_permission == 'yourgrades.student':
            return reverse('yourgrades:student_parent')
        elif user_permission == 'yourgrades.parent':
            return reverse('yourgrades:student_parent')
        elif user_permission == 'yourgrades.teacher':
            return reverse('yourgrades:teacher')
        elif user_permission == 'yourgrades.manager':
            return reverse('yourgrades:manager')
        else:
            raise ValueError("Unknown permission")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.kwargs['prefix'] == 1:
            context['recipient'] = get_object_or_404(
                SchoolClass,
                unique_code=self.kwargs['code']
            )
            context['recipient_type'] = 1
        elif self.kwargs['prefix'] == 2:
            context['recipient'] = get_object_or_404(
                SchoolClass,
                unique_code=self.kwargs['code'],
            )
            context['recipient_type'] = 2
        elif self.kwargs['prefix'] == 3:
            subject = get_object_or_404(
                Subject,
                unique_code=self.kwargs['code'],
            )
            context['recipient'] = get_object_or_404(
                SubjectTeachers,
                subject=subject,
            )
            context['recipient_type'] = 3
        elif self.kwargs['prefix'] == 4:
            context['recipient'] = get_object_or_404(
                Student,
                user__id=self.kwargs['code'],
            )
            context['recipient_type'] = 4
        elif self.kwargs['prefix'] == 5:
            context['recipient'] = get_object_or_404(
                Student,
                user__id=self.kwargs['code'],
            )
            context['recipient_type'] = 5
        elif self.kwargs['prefix'] == 6:
            context['recipient_type'] = 6
        elif self.kwargs['prefix'] == 7:
            context['recipient'] = get_object_or_404(
                Teacher,
                user__id=self.kwargs['code'],
            )
            context['recipient_type'] = 7
        return context

    def form_valid(self, form):
        # Message and sender models are save the same way for all types
        # of users
        with transaction.atomic():
            message = form.save()
            sender = Sender(user=self.request.user, message=message)
            sender.save()
            # Recipient and MailboxReceived models depend on the type of
            # target user
            if self.kwargs['prefix'] in {1, 2}:
                school_class = get_object_or_404(
                    SchoolClass,
                    unique_code=self.kwargs['code']
                )
                recipient_name = school_class.name
                if self.kwargs['prefix'] == 2:
                    recipient_name += ' parents'
                students = Student.objects.filter(school_class=school_class)
                if not students:
                    return self.render_to_response(
                        self.get_context_data(
                            form=form,
                            no_students=True,
                            back=True
                        )
                    )
                if not students:
                    raise Http404("Wrong class unique_code")
                for student in students:
                    if self.kwargs['prefix'] == 1:
                        recipient = Recipient(
                            user=student.user,
                            message=message
                        )
                        recipient.save()
                        mailbox_received = MailboxReceived(
                            sender=sender,
                            recipient=recipient,
                            message=message
                        )
                        mailbox_received.save()
                    else:
                        parents = Parent.objects.filter(student=student)
                        for parent in parents:
                            recipient = Recipient(
                                user=parent.user,
                                message=message
                            )
                            recipient.save()
                            mailbox_received = MailboxReceived(
                                sender=sender,
                                recipient=recipient,
                                message=message
                            )
                            mailbox_received.save()
            elif self.kwargs['prefix'] == 3:
                subject = get_object_or_404(
                    Subject,
                    unique_code=self.kwargs['code']
                )
                recipient_name = f'{subject.name} teachers'
                subject_teachers = get_object_or_404(
                    SubjectTeachers,
                    subject=subject
                )
                teachers = subject_teachers.teacher.all()
                for teacher in teachers:
                    recipient = Recipient(user=teacher.user, message=message)
                    recipient.save()
                    mailbox_received = MailboxReceived(
                        sender=sender,
                        recipient=recipient,
                        message=message
                    )
                    mailbox_received.save()
            elif self.kwargs['prefix'] == 4:
                student = get_object_or_404(
                    Student,
                    user__id=self.kwargs['code']
                )
                recipient_name = student.__str__()
                recipient = Recipient(user=student.user, message=message)
                recipient.save()
                mailbox_received = MailboxReceived(
                    sender=sender,
                    recipient=recipient,
                    message=message
                )
                mailbox_received.save()
            elif self.kwargs['prefix'] == 5:
                student = get_object_or_404(
                    Student,
                    user__id=self.kwargs['code']
                )
                recipient_name = f'{student.__str__()} parents'
                parents = Parent.objects.filter(student=student)
                for parent in parents:
                    recipient = Recipient(user=parent.user, message=message)
                    recipient.save()
                    mailbox_received = MailboxReceived(
                        sender=sender,
                        recipient=recipient,
                        message=message
                    )
                    mailbox_received.save()
            elif self.kwargs['prefix'] == 6:
                permission = Permission.objects.get(codename='manager')
                managers = User.objects.filter(user_permissions=permission)
                recipient_name = 'Managers'
                for manager in managers:
                    recipient = Recipient(user=manager, message=message)
                    recipient.save()
                    mailbox_received = MailboxReceived(
                        sender=sender,
                        recipient=recipient,
                        message=message
                    )
                    mailbox_received.save()
            elif self.kwargs['prefix'] == 7:
                teacher = get_object_or_404(
                    Teacher,
                    user__id=self.kwargs['code']
                )
                recipient_name = teacher.__str__()
                recipient = Recipient(user=teacher.user, message=message)
                recipient.save()
                mailbox_received = MailboxReceived(
                    sender=sender,
                    recipient=recipient,
                    message=message
                )
                mailbox_received.save()
            # Same for all type of senders
            mailbox_sent = MailboxSent(
                sender=sender,
                recipient=recipient_name,
                message=message
            )
            mailbox_sent.save()
        return super().form_valid(form)


class MailboxView(LoginRequiredMixin, UserPassesTestMixin, BaseView):
    template_name = 'yourgrades/mailbox.html'

    def test_func(self):
        test = False
        if self.request.user.has_perm('yourgrades.student') or\
                self.request.user.has_perm('yourgrades.parent') or\
                self.request.user.has_perm('yourgrades.teacher') or\
                self.request.user.has_perm('yourgrades.manager'):
            test = True
        return test

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sent = MailboxSent.objects.filter(
            sender__user=self.request.user
        ).order_by('-id')
        received = MailboxReceived.objects.filter(
            recipient__user=self.request.user
        ).order_by('-id')
        paginator_sent = Paginator(sent, 15)
        paginator_received = Paginator(received, 15)
        context['received'] = paginator_received.get_page(
            self.request.GET.get('page2')
        )
        context['sent'] = paginator_sent.get_page(
            self.request.GET.get('page1')
        )
        try:
            context['user_type'] = list(
                self.request.user.get_all_permissions()
            )[0]
        except IndexError:
            raise Http404("User not recognized.")
        return context


class MailTextView(LoginRequiredMixin, UserPassesTestMixin, BaseView):
    template_name = 'yourgrades/mailtext.html'

    def test_func(self):
        test = False
        if self.request.user.has_perm('yourgrades.student') or\
                self.request.user.has_perm('yourgrades.parent') or\
                self.request.user.has_perm('yourgrades.teacher') or\
                self.request.user.has_perm('yourgrades.manager'):
            test = True
        return test

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.kwargs['mailbox_type'] == 1:
            mailbox = get_object_or_404(
                MailboxReceived,
                id=self.kwargs['mailbox_id']
            )
            context['mailbox'] = mailbox
            mailbox.read = True
            mailbox.save()
        elif self.kwargs['mailbox_type'] == 2:
            mailbox = get_object_or_404(
                MailboxSent,
                id=self.kwargs['mailbox_id']
            )
            context['mailbox'] = mailbox
        return context


class StudentParentView(LoginRequiredMixin, UserPassesTestMixin, BaseView):
    template_name = 'yourgrades/studentparent.html'

    def test_func(self):
        test = False
        if self.request.user.has_perm('yourgrades.student') or \
                self.request.user.has_perm('yourgrades.parent'):
            test = True
        return test

    def get(self, request, *args, **kwargs):
        try:
            person = Student.objects.get(user=self.request.user)
        except ObjectDoesNotExist:
            person = get_object_or_404(Parent, user=self.request.user)
        if person.first_login is True:
            return HttpResponseRedirect(reverse('yourgrades:first_login'))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            permission = list(self.request.user.get_all_permissions())[0]
        except IndexError:
            raise Http404("User not recognized.")

        if permission == 'yourgrades.student':
            student = get_object_or_404(Student, user=self.request.user)
            context['person'] = student
        elif permission == 'yourgrades.parent':
            parent = get_object_or_404(Parent, user=self.request.user)
            student = parent.student
            context['person'] = parent

        subjects = Subject.objects.filter(school_class=student.school_class)
        subjects_grades = {}
        for subject in subjects:
            subjects_grades[subject] = Grades.objects.filter(
                subject=subject,
                student=student
            )
        context['subjects_grades'] = subjects_grades

        return context
