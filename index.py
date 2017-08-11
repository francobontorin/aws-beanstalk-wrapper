#!/usr/bin/python
import boto3
import json
import time
import os
import flask
from jinja2 import Environment
from jinja2.loaders import FileSystemLoader
from flask import Flask, render_template, flash, request, url_for, redirect
from wtforms import TextField, TextAreaField, validators, StringField, SubmitField
from wtforms.validators import InputRequired, Email, Length, AnyOf
from flask_wtf import FlaskForm
from werkzeug import secure_filename

##############
# GLOBAL VARS
##############

beanstalk = boto3.client('elasticbeanstalk')
s3 = boto3.client('s3')
bucket = 'chc-beanstalk-apps'
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'
# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = 'uploads/'
# These are the extension that are acceped to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['zip'])
app_platforms = {"Java":"64bit Amazon Linux 2017.03 v2.5.2 running Java 8", "Node.js":"64bit Amazon Linux 2017.03 v4.2.0 running Node.js", "PHP":"64bit Amazon Linux 2017.03 v2.4.2 running PHP 5.5", "Python":"64bit Amazon Linux 2017.03 v2.4.2 running Python 2.7"}

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

class MyForm(FlaskForm):
    app_name = TextField('Name:', validators=[validators.required()])
    description = TextField('Description:', validators=[validators.required()])
    app_version = TextField('App Version', validators=[validators.required()])
    platform = TextField('Platform', validators=[validators.required()])

@app.route('/', methods=['GET', 'POST'])
def homepage():
    try:
        form = MyForm(request.form)

        if request.method == 'POST':
            app_name=request.form['app_name']
            description=request.form['description']
            app_version=request.form['app_version']
            platform=request.form['platform']
            file = request.files['file']
            # Check if the file is one of the allowed types/extensions
            if file and allowed_file(file.filename):
                # Make the filename safe, remove unsupported chars
                filename = secure_filename(file.filename)
                # Move the file form the temporal folder to
                # the upload folder we setup
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                if form.validate():
                    return redirect(url_for('submit', app_name=app_name, description=description, app_version=app_version, platform=platform, file=filename, method='POST'))
                else:
                    flash('Error: All the form fields are required ' + str(form.errors))
            else:
                flash('Error: File Format not supported')

        return render_template("main.html", form=form)

    except Exception as e:
        return (str(e))

@app.route('/submit/', methods=['GET', 'POST'])
def submit():
    app_name = request.args['app_name']
    description = request.args['description']
    app_version = request.args['app_version']
    platform = request.args['platform']
    file = request.args['file']
    if request.method == 'POST':
        return redirect(url_for('deploy', app_name=app_name, description=description, app_version=app_version, platform=platform, file=file, method='POST'))
    else:
        return render_template("submit.html", app_name=app_name, description=description, app_version=app_version, platform=platform, file=file, method='POST')


@app.route('/deploy/', methods=['GET', 'POST'])
def deploy():

    app_name = request.args['app_name']
    description = request.args['description']
    app_version = request.args['app_version']
    platform = app_platforms[request.args['platform']]
    zip_file = request.args['file']
 
    if request.method == 'GET':
        try:
            # Upload bundle code to S3          
            s3_upload = s3.upload_file('uploads/'+zip_file, bucket, zip_file)
            
            #Create App
            create_app = beanstalk.create_application_version(ApplicationName=app_name, VersionLabel=app_version, SourceBundle={'S3Bucket': bucket, 'S3Key': zip_file}, AutoCreateApplication=True, Process=True)
            time.sleep(5)

            #Create Environment
            create_env = beanstalk.create_environment(ApplicationName=app_name, VersionLabel=app_version, EnvironmentName=app_name, SolutionStackName=platform)

            def inner():
                env_status = beanstalk.describe_environments(ApplicationName=app_name)['Environments'][0]['Status']
                while 'Ready' not in env_status:
                    env_status = beanstalk.describe_environments(ApplicationName=app_name)['Environments'][0]['Status']
                    env_logs = json.dumps(beanstalk.describe_events(ApplicationName=app_name)['Events'][0], indent=4, sort_keys=True, default=str)
                    yield '%s<br/>\n' % env_logs
                    time.sleep(30)
                env_details = json.dumps(beanstalk.describe_environments(ApplicationName=app_name)['Environments'][0], indent=4, sort_keys=True, default=str)
                yield '<strong>Application has been deployed<br><br>Details:<br><br>%s<br/></strong>\n' % env_details
            env = Environment(loader=FileSystemLoader('templates'))
            tmpl = env.get_template('deploy.html')
            return flask.Response(tmpl.generate(result=inner()))

        except Exception as e:
            flash('Error: ' + str(e))
        
    return render_template("deploy.html")

if __name__ == "__main__":
    app.run(debug=True)
