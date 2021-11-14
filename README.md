# Gradebook
##### Live: [http://gradebook.pythonanywhere.com/yourgrades](http://gradebook.pythonanywhere.com/yourgrades)
##
# Running the application 
#### To start the app, follow the steps below.
###### 1. Clone repo:
    git clone https://github.com/MarcelDrugi/GradeBook
###### 2. Go to project main directory:
    cd GradeBook
###### 3. Create virtual environment:
    virtualenv venv 
###### 4. Activate venv:
    source venv/bin/activate
###### 5. Install requirements:
    pip3 install -r  requirements.txt
###### 6. Create database for the project. <br>You can use any SQL management system, but you need to install it into venv.<br> From requirements.txt you have already installed mySQL. If you want to use it: 
    mysql -u [your_username] -p
###### 7a. Create  <span style="color:black">.env</span> file in <span style="color:black">/rate/backend/rate/rate</span> (the directory that contains <span style="color:black">settings.py</span> file).<br>
###### 7b. To the <span style="color:black">.env</span>  file enter settings of the database you created and some secret key. <br> For mySQL the file should looks like:
    SECRET_KEY=your_secret_key
    ENGINE=django.db.backends.mysql
    DATABASE_NAME=name_of_created_databas
    DATABASE_USER=username
    DATABASE_PASSWORD=password
###### 8. Go to the project main directory(<span style="color:black">/rate/backend/rate</span>) and make the migration
    python3 managey makemigrations
    python3 managey migrate
###### 9. Create superuser
    python3 manage.py createsuperuser
###### 10. Run the server:
    python3 manage.py runserver
###### 11. Login as superuser, create a school-manager account and assign it the permission:
    yourgrades|rights support|Global manager rights
###### 12. After logging in as a manager through the home page, you will be able to create student / parent / teacher accounts, create classes, manage them and use other functionalities to build a gradebook
#####
##### The app should be launched at:

    http://127.0.0.1:8000/yourgrades
##### You can also use the live version with a set of users.
    http://gradebook.pythonanywhere.com/yourgrades

## 
# App description
### Gradebook works with 4 user types.
1) Manager (e. g. school head)
2) Student
3) Parent
4) Teacher

### The manager account allows:

- create classes and accounts for students, parents and teachers,
- activate / deactivate / delete classes / teachers,
- create subjects for individual classes, connect selected teachers to them,
- set lesson dates for individual subjects,
- send messages to individual students / teachers / parents and to entire classes,
- edit users' personal data and reset login details,
- view the history of teacher grades,
- enter / delete grades in administrative mode.

### Teacher's account allows:
- enter grades in the subjects taught,
- send messages to students / parents or entire classes and to the manager
- download your class schedule,
- view the history of entered ratings,

### The student / parent account allows:
- review the grades received,
- download the current timetable,
- exchange messages with subject teachers and the manager.

