# Project Structure
## Api:
```
    /:
        GET: All projects
        POST: Create project
    /pk/:
        GET: Retrieve project("pk")
        PUT or PATCH: partial or full update project
    /upload:
        POST: upload model("mdl") or spread sheet("xlsx") related to the project
    /simulations/pk:
        GET:
            - : Get simulations of project("pk")
            - id : Get simulation("all data") of project("pk")
            - id, var :
                var in variables : Get data variable of project("pk")
                var not in variables : Get list variables of project("pk")
            - option : 
                generate : Generate new simulation of project("pk")
```
## dependency:
You need to install [vensim](https://vensim.com/download/)

also some python dependency
```
    django: $> pip3 install Django
    rest_framework: $> pip3 install djangorestframework
    background_task: $> pip3 install django-background-tasks
    django-cors-headers: $> pip3 install django-cors-headers
    numpy: $> pip3 install numpy
    pandas: $> pip3 install pandas
 ```
## setup:
```
    $> python manage.py makemigrations coreapi
    $> python manage.py migrate
```
## Run:
```
    $> python manage.py runserver
    #the project support tasks queue you should run 
    $> python manage.py process_tasks
```
