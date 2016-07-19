import flask
from pfs import pfs_users, pfs_functions
from pfs.dbutil import db_connect
from contextlib import closing
import datetime

#import urllib
#import psycopg2
#import sys


app = flask.Flask(__name__)
app.config.from_pyfile('settings.py')


@app.route('/')
def hello_world():
    if 'auth_user' in flask.session:
        # we have a user
        with db_connect(app) as dbc:
            uid = flask.session['auth_user']
            user = pfs_users.get_user(dbc, uid)
            if user is None:
                app.logger.error('invalid user %d', uid)
                flask.abort(400)

            client_list = pfs_functions.get_client_list(dbc, uid)
            return flask.render_template('pfs_home.html', user=user,
                                         client_list=client_list)
    else:
        return flask.render_template('pfs_login.html')


@app.route('/login', methods=['POST'])
def login():
    username = flask.request.form['user']
    password = flask.request.form['passwd']
    display_name = flask.request.form['display_name']
    e_mail = flask.request.form['e_mail']
    phone_number = flask.request.form['phone_number']
    role = flask.request.form['role']
    if username is None or password is None:
        flask.abort(400)
    action = flask.request.form['action']
    if action == 'Log in':
        with closing(db_connect(app)) as dbc:
            uid = pfs_users.check_auth(dbc, username, password)
            #user_info = pfs_functions.get_user_info(dbc,uid)
            if uid is not None:
                flask.session['auth_user'] = uid
                #add temp client login
                with closing(db_connect(app)) as dbc:
                    user_info = pfs_functions.get_user_info(dbc,uid)
                    #role = user_info.role
                    #print ('uid=', uid)
                    #print ('user_info.displayname=', user_info.get(display_name))
                    if user_info.get(role) == 'Client':
                        return flask.redirect('/client_details/uid', code=303)
                    else:
                        return flask.redirect('/', code=303)

                #end temp client login
                #return flask.redirect('/', code=303)
            else:
                flask.abort(403)
    elif action == 'Create account':
        with closing(db_connect(app)) as dbc:
            uid = pfs_users.create_user(dbc, username, password, display_name,
                                        e_mail, phone_number, role)
            flask.session['auth_user'] = uid
            return flask.redirect('/', code=303)

@app.route('/logoff')
def logoff():
    if 'auth_user' in flask.session:
        # we have a user
        flask.session['auth_user'] = 0
        return flask.render_template('pfs_login.html')
    else:
        return flask.render_template('pfs_login.html')


@app.route('/user_profile', methods=['GET', 'POST'])
def user_profile():
    if 'auth_user' in flask.session:
        uid = flask.session['auth_user']
    else:
        flask.abort(403)

    if flask.request.method == 'GET':
        with closing(db_connect(app)) as dbc:
            user_info = pfs_functions.get_user_info(dbc,uid)
        return flask.render_template('pfs_user_profile.html', user_info=user_info)
    else:
        with closing(db_connect(app)) as dbc:
            pfs_functions.update_user(dbc, uid, form)
        return flask.redirect('/', code=303)


@app.route('/edit_user_profile', methods=['GET', 'POST'])
def edit_user_profile():
    if 'auth_user' in flask.session:
        uid = flask.session['auth_user']
    else:
        flask.abort(403)

    if flask.request.method == 'GET':
        with closing(db_connect(app)) as dbc:
            user_info = pfs_functions.get_user_info(dbc, uid)
            therapists = pfs_functions.get_therapists(dbc)
        return flask.render_template('edit_pfs_user_profile.html',
                                     user_info=user_info, therapists=therapists)

    else:
        with closing(db_connect(app)) as dbc:
            pfs_functions.update_user(dbc, uid, flask.request.form)
        return flask.redirect('/user_profile', code=303)


#no longer used - replaced by client_details_select
@app.route('/client_details/<int:cid>', methods=['GET', 'POST'])
def client_details(cid):
    if 'auth_user' in flask.session:
        uid = flask.session['auth_user']
    else:
        flask.abort(403)

    if flask.request.method == 'GET':
        with closing(db_connect(app)) as dbc:
            user_info = pfs_functions.get_user_info(dbc, cid)
            client_surveys = pfs_functions.get_client_surveys(dbc,cid)
            client_surveys2 = pfs_functions.get_client_surveys2(dbc,cid)
        return flask.render_template('client_details.html',
                                     user_info = user_info,
                                     client_surveys = client_surveys,
                                     client_surveys2 = client_surveys2)

    #I do not think the 'POST' method is used
    else:
        with closing(db_connect(app)) as dbc:
            user_info = pfs_functions.get_user_info(dbc, cid)
        return flask.redirect('/', code=303)


@app.route('/answer_survey/<int:survey_id>', methods=['GET', 'POST'])
def answer_survey(survey_id):
    if 'auth_user' in flask.session:
        uid = flask.session['auth_user']
    else:
        flask.abort(403)

    if flask.request.method == 'GET':
        with closing(db_connect(app)) as dbc:
            survey = pfs_functions.get_survey(dbc, survey_id)
            question_text_array = \
                pfs_functions.get_questions_text(dbc,survey['question_list'])
        return flask.render_template('answer_survey.html', survey=survey,
                                     question_text_array=question_text_array)

    else:
        with closing(db_connect(app)) as dbc:
            #pfs_functions.save_answer(dbc, bid, uid, flask.request.form)
            survey = pfs_functions.get_survey(dbc, survey_id)
            #test = survey.get(client_id)
        return flask.redirect('/client_details/' + str(survey.client_id),
                              code=303)

@app.route('/answer_survey2/<int:survey_id>', methods=['GET', 'POST'])
def answer_survey2(survey_id):
    if 'auth_user' in flask.session:
        uid = flask.session['auth_user']
    else:
        flask.abort(403)

    if flask.request.method == 'GET':
        with closing(db_connect(app)) as dbc:
            survey2 = pfs_functions.get_survey2(dbc, survey_id)
        return flask.render_template('answer_survey2.html', survey2=survey2)

    else:
        with closing(db_connect(app)) as dbc:
            #print('test point 1')
            pfs_functions.save_answers(dbc, survey_id, flask.request.form)
            pfs_functions.update_avg_score(dbc, survey_id)
            survey2 = pfs_functions.get_survey2(dbc, survey_id)
            #print('test point 5')
        return flask.render_template('answer_survey2.html', survey2=survey2)


@app.route('/create_templates/<int:client_id>', methods=['GET', 'POST'])
def create_templates(client_id):
    #print('flask.request.method=', flask.request.method)
    if 'auth_user' in flask.session:
        uid = flask.session['auth_user']
    else:
        flask.abort(403)
    #print('flask.request.method=', flask.request.method)
    if flask.request.method == 'GET':
        #print('Test Point1 - GET')
        with closing(db_connect(app)) as dbc:
            templates = pfs_functions.get_templates(dbc, client_id)
        return flask.render_template('create_templates.html',
                                      templates=templates,
                                      client_id=client_id)

    else:
        #print('Test Point1 - POST')
        with closing(db_connect(app)) as dbc:
            user_info = pfs_functions.get_user_info(dbc,client_id)
            #print('Test Point1.1')
            therapist_id = user_info['assigned_therapist']
            #print('Test Point1.2')
            pfs_functions.create_templates(dbc, therapist_id, client_id, flask.request.form)
            #print('Test Point2')
        return flask.redirect('/create_templates/' + str(client_id),
                              code=303)


@app.route('/view_edit_template/<int:template_id>', methods=['GET', 'POST'])
def view_edit_template(template_id):
    if 'auth_user' in flask.session:
        uid = flask.session['auth_user']
    else:
        flask.abort(403)

    if flask.request.method == 'GET':
        with closing(db_connect(app)) as dbc:
            template = pfs_functions.get_template(dbc, template_id)
            question_text_array = \
                pfs_functions.get_questions_text(dbc,template['question_list'])


        return flask.render_template('view_edit_template.html',
                                      template=template,
                                      question_text_array=question_text_array)

    else:
        #item below edited with temporary information
        with closing(db_connect(app)) as dbc:
            #pfs_functions.save_answers(dbc, survey_id, flask.request.form)
            #pfs_functions.update_avg_score(dbc, survey_id)
            survey2 = pfs_functions.get_survey2(dbc, template_id)
        return flask.render_template('answer_survey2.html', survey2=survey2)


#@app.route('/client_details_select/<int:cid>', methods=['GET', 'POST'])
#def client_details_select(cid):
@app.route('/client_details_select', methods=['GET', 'POST'])
def client_details_select():

    cid = flask.request.args['cid']
    start_date = flask.request.args['start_date']
    end_date = flask.request.args['end_date']
    #print('cid=',cid)
    #print('start_date=',start_date)
    #print('end_date=',end_date)
    time_now = datetime.datetime.now()
    time_2wks_ago = time_now - datetime.timedelta(days=14)
    if start_date > end_date:
        #print('start date > end_date')
        start_date = 'default'
        end_date = 'default'
    if start_date == 'default':
        start_date = time_2wks_ago
    if end_date == 'default':
        end_date = time_now
    #start_date = start_date.strftime('%Y-%m-%d')
    #start_date = start_date.strptime(date_string, format)
    #print('start_date=',start_date)
    #print('end_date=',end_date)
    #start_date = datetime.strptime(start_date, format)

    #start_date = start_date.date()

    all_args = flask.request.args

    if 'auth_user' in flask.session:
        uid = flask.session['auth_user']
    else:
        flask.abort(403)

    if flask.request.method == 'GET':
        with closing(db_connect(app)) as dbc:
            user_info = pfs_functions.get_user_info(dbc, cid)
            client_surveys = pfs_functions.get_client_surveys(dbc,cid)
            client_surveys2 = \
                pfs_functions.get_client_surveys2_param(dbc,cid,start_date, end_date)
            templates = pfs_functions.get_templates(dbc, cid)
        return flask.render_template('client_details_select.html',
                                     user_info = user_info,
                                     client_surveys = client_surveys,
                                     client_surveys2 = client_surveys2,
                                     start_date=start_date,end_date=end_date,
                                     templates=templates)
    #I do not think the 'POST' method is used
    else:
        with closing(db_connect(app)) as dbc:
            pfs_functions.get_user_info(dbc, cid, flask.request.form)
        return flask.redirect('/', code=303)


if __name__ == '__main__':
    app.run()
