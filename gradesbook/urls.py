from django.urls import path
from . import views

app_name = 'gradesbook'

urlpatterns = [
    path('', views.HomepageView.as_view(), name='homepage'),
    path('/manager', views.ManagerPanelView.as_view(), name='manager'),
    path('/manager/creaateschoolclass', views.CreateSchoolClassView.as_view(),
         name='create_school_class'),
    path('/manager/editschoolclass/<str:class_unique_code>',
         views.EditSchoolClassView.as_view(), name='edit_school_class'),
    path('/manager/delstudent/<int:user_id>',
         views.DeleteStudentView.as_view(), name='del_student'),
    path('/manager/deactivationschoolclass/<str:class_unique_code>',
         views.DeactivationSchoolClassView.as_view(),
         name='deactivation_school_class'),
    path('/manager/activationschoolclass/<str:class_unique_code>',
         views.ActivationSchoolClassView.as_view(),
         name='activation_school_class'),
    path('/manager/deactivationteacher/<str:teacher_user_id>',
         views.DeactivationTeacherView.as_view(),
         name='deactivation_teacher'),
    path('/manager/activationteacher/<str:teacher_user_id>',
         views.ActivationTeacherView.as_view(),
         name='activation_teacher'),
    path('/manager/addteacher', views.AddTeacherView.as_view(),
         name='add_teacher'),
    path('/manager/editschoolclass/<str:class_unique_code>/addsubject',
         views.AddSubjectView.as_view(), name='add_subject'),
    path('/manager/editstudent/<int:user_id>',
         views.ManagerStudentEditView.as_view(), name='manager_student_edit'),
    path('/manageresetusesr/<int:prefix>/<int:user_id>',
         views.ManagerResetUserView.as_view(), name='manager_reset_user'),
    path('/manager/editschoolclass/<str:class_unique_code>/'
         '<str:subject_unique_code>', views.ManagerSubjectView.as_view(),
         name='subject_view'),
    path('/manager/deldate/<str:class_unique_code>/<str:subject_unique_code>'
         '/<int:day>/<int:lesson>', views.DeleteSubjectDateView.as_view(),
         name='delete_date'),
    path('/manager/delsubject/<str:class_unique_code>/'
         '<str:subject_unique_code>', views.DeleteSubjectView.as_view(),
         name='del_subject'),
    path('/delsubjectteacher/<str:class_unique_code>/' +
         '<str:subject_unique_code>/<int:teacher_user_id>',
         views.DeleteSubjectTeacherView.as_view(), name='del_subject_teacher'),
    path('/addnewsubjectteacher/<str:class_unique_code>/' +
         '<str:subject_unique_code>',
         views.AddSubjectTeacherView.as_view(), name='add_subject_teacher'),
    path('/manager/teacher/<str:teacher_user_id>',
         views.ManagerTeacherView.as_view(), name='manager_teacher'),
    path('/manager/editteacher/<int:user_id>',
         views.ManagerTeacherEditView.as_view(), name='manager_teacher_edit'),
    path('/manager/delteacher/<str:teacher_user_id>',
         views.ManagerDeleteTeacherView.as_view(), name='manager_del_teacher'),
    path('/teacher', views.TeacherPanelView.as_view(), name='teacher'),
    path('/teachersubject/<str:subject_unique_code>',
         views.TeacherSubjectView.as_view(), name='teacher_subject'),
    path('/timetable/<str:person>', views.TimetableView.as_view(),
         name='timetable'),
    path('/mailbox', views.MailboxView.as_view(), name='mailbox'),
    path('/mailtext/<int:mailbox_id>/<int:mailbox_type>',
         views.MailTextView.as_view(), name='mail_text'),
    path('/studentparent', views.StudentParentView.as_view(),
         name='student_parent'),
    path('/firstlogin', views.FirstLoginView.as_view(), name='first_login'),
    path('/logout', views.LogOutView.as_view(), name='logout'),
    path('/createmessage/<int:prefix>/<str:code>',
         views.CreateMessageView.as_view(), name='create_message'),
    path('/manager/student/<int:user_id>', views.ManagerStudentView.as_view(),
         name='manager_student'),
]
