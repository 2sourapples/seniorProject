import flask
import psycopg2
import sys
#import datetime

def get_client_list(dbc, uid):
    with dbc, dbc.cursor() as cur:
        cur.execute('''
            SELECT user_id, display_name
            FROM pfs_user
            WHERE assigned_therapist = %s
              AND role = 'Client'
            ORDER BY display_name
        ''', (uid,))

        client_list = []
        for user_id, display_name in cur:
            client_list.append({'user_id': user_id,
                               'display_name': display_name})

        return client_list


def get_user_info(dbc, uid):
    with dbc,dbc.cursor() as cur:
        cur.execute('''
            SELECT Client.user_id, Client.user_name, Client.pw_hash, 
                   Client.display_name, Client.e_mail, 
                   Client.phone_number, Client.role, 
                   Client.assigned_therapist, Therapist.display_name
            FROM pfs_user AS Client
            JOIN pfs_user AS Therapist
               ON(Client.assigned_therapist=Therapist.user_id)
            WHERE Client.user_id = %s
            ''', (uid,))

        row = cur.fetchone()
        if row is None:
            return None
        (user_id, user_name, pw_hash, display_name, e_mail, 
         phone_number, role, assigned_therapist, therapist_name) = row

        user_info = {'user_id': user_id, 'user_name': user_name,
                     'pw_hash':pw_hash, 'display_name': display_name,
                     'e_mail':e_mail, 'phone_number':phone_number, 
                     'role': role, 'assigned_therapist': assigned_therapist,
                     'therapist_name': therapist_name}
        #print ('uid=', uid)
        #print ('user_info.display_name=', user_info.get(display_name))
        #print ('user_info.role=', user_info.get(role))
        return user_info


def get_therapists(dbc):
    with dbc, dbc.cursor() as cur:
        cur.execute('''
            SELECT user_id, display_name
            FROM pfs_user
            WHERE role LIKE('Therapist')
            ORDER BY display_name
        ''')
        therapists = []
        for user_id, display_name in cur:
            therapists.append({'user_id': user_id,
                               'display_name': display_name})
        return therapists


def update_user(dbc, uid, form):
    ntries = 1
    while ntries < 5:
        try:
            with dbc:
                with dbc.cursor() as cur:
                    #check to verify user exists, and abort if not
                    cur.execute('''
                      SELECT user_id FROM pfs_user
                      WHERE user_id = %s
                    ''', (uid,))
                    row = cur.fetchone()
                    if row is None:
                        flask.abort(403)
                    
                    user_name = form['user_name'].strip()
                    if not user_name:
                        user_name = None
                    display_name = form['display_name'].strip()
                    if not display_name:
                        display_name = None
                    e_mail = form['e_mail'].strip()
                    if not e_mail:
                        e_mail = None
                    phone_number = form['phone_number'].strip()
                    if not phone_number:
                        phone_number = None
                    role = form['role'].strip()
                    if not role:
                        role = None
                    assigned_therapist = form['assigned_therapist'].strip()
                    if not assigned_therapist:
                        assigned_therapist = None

                    cur.execute('''
                        UPDATE pfs_user
                        SET user_name = %s, display_name = %s,
                            e_mail = %s, phone_number = %s, 
                            role = %s, assigned_therapist = %s
                        WHERE user_id = %s
                    ''', (user_name, display_name, e_mail, phone_number,
                          role, assigned_therapist, uid))
                return
        except psycopg2.DatabaseError as dbe:
            print("commit error: {}".format(dbe), file=sys.stderr)
            dbc.rollback()
            ntries += 1

    flask.abort(500)

def get_client_surveys(dbc,cid):
    with dbc, dbc.cursor() as cur:
        cur.execute('''
            SELECT survey_id,question_list, client_comment,
                   therapist_comment, time_created, time_completed
            FROM survey
            WHERE client_id = %s
            ORDER BY time_created DESC
        ''', (cid,))
        surveys = []
        for (survey_id,question_list, client_comment,
             therapist_comment, time_created, time_completed) in cur:
            surveys.append({'survey_id': survey_id,
                            'question_list': question_list,
                            'client_comment': client_comment,
                            'therapist_comment': therapist_comment,
                            'time_created': time_created,
                            'time_completed': time_completed})

        return surveys

def get_survey(dbc,survey_id):
    with dbc, dbc.cursor() as cur:
        cur.execute('''
            SELECT survey_id, client_id, question_list, client_comment,
                   therapist_comment, time_created, time_completed
            FROM survey
            WHERE survey_id = %s
        ''', (survey_id,))

        row = cur.fetchone()
        if row is None:
            flask.abort(404)

        # unpack row
        (survey_id, client_id, question_list, client_comment,
         therapist_comment, time_created, time_completed) = row

        survey = {'survey_id': survey_id,
                  'client_id': client_id,
                  'question_list': question_list,
                  'client_comment': client_comment,
                  'therapist_comment': therapist_comment,
                  'time_created': time_created,
                  'time_completed': time_completed}

        #print ('survey_id=', survey_id)
        #print ('client_id=', client_id)
        #print ('question_list=', question_list)
        #print ('survey.question_list=', survey['question_list'])
        return survey

def get_questions_text(dbc,question_list):
    question_id_array = question_list.split('%')
    quid_array_length = len(question_id_array)
    question_id_list = ''
    for question_id in question_id_array:
        question_id_list = question_id_list + question_id
        quid_array_length = quid_array_length - 1
        if quid_array_length > 0 :
            question_id_list = question_id_list + ","    
    #print('question_id_list = ', question_id_list)

    #build query to get text for all question
    query ='''
        SELECT question_id, question_text
        FROM question
        WHERE question_id IN (
            '''
    query += question_id_list + ') '

    #print('query', query)

    with dbc, dbc.cursor() as cur:
        cur.execute(query)

        question_list_array = []
        for (question_id, question_text) in cur:
            question_list_array.append({'question_id': question_id,
                            'question_text': question_text})

        return question_list_array

def get_client_surveys2(dbc,cid):
    with dbc, dbc.cursor() as cur:
        cur.execute('''
            SELECT survey_id, client_comment,
                   therapist_comment, time_created, time_completed,
                   avg_score, phq9
            FROM survey2
            WHERE client_id = %s
            ORDER BY time_created DESC
        ''', (cid,))
        surveys2 = []
        for (survey_id, client_comment, therapist_comment,
             time_created, time_completed, avg_score, phq9) in cur:
            surveys2.append({'survey_id': survey_id,
                             'client_comment': client_comment,
                             'therapist_comment': therapist_comment,
                             'time_created': time_created,
                             'time_completed': time_completed,
                             'avg_score': avg_score,
                             'phq9': phq9})

        return surveys2


def get_survey2(dbc,survey_id):
    with dbc, dbc.cursor() as cur:
        cur.execute('''
            SELECT survey_id, client_id, client_comment,
                   therapist_comment, time_created, time_completed,
                   question1, q1.question_text,
                   question2, q2.question_text,
                   question3, q3.question_text,
                   question4, q4.question_text,
                   question5, q5.question_text,
                   question6, q6.question_text,
                   question7, q7.question_text,
                   question8, q8.question_text,
                   question9, q9.question_text,
                   question10, q10.question_text,
                   answer1, answer2, answer3, answer4, answer5,
                   answer6, answer7, answer8, answer9, answer10
            FROM survey2
            LEFT OUTER JOIN question AS q1 ON(survey2.question1=q1.question_id)
            LEFT OUTER JOIN question AS q2 ON(survey2.question2=q2.question_id)
            LEFT OUTER JOIN question AS q3 ON(survey2.question3=q3.question_id)
            LEFT OUTER JOIN question AS q4 ON(survey2.question4=q4.question_id)
            LEFT OUTER JOIN question AS q5 ON(survey2.question5=q5.question_id)
            LEFT OUTER JOIN question AS q6 ON(survey2.question6=q6.question_id)
            LEFT OUTER JOIN question AS q7 ON(survey2.question7=q7.question_id)
            LEFT OUTER JOIN question AS q8 ON(survey2.question8=q8.question_id)
            LEFT OUTER JOIN question AS q9 ON(survey2.question9=q9.question_id)
            LEFT OUTER JOIN question AS q10 ON(survey2.question10=q10.question_id)
            WHERE survey_id = %s
        ''', (survey_id,))

        row = cur.fetchone()
        if row is None:
            flask.abort(404)

        # unpack row
        (survey_id, client_id, client_comment,
         therapist_comment, time_created, time_completed,
         question1, q1_text,
         question2, q2_text,
         question3, q3_text,
         question4, q4_text,
         question5, q5_text,
         question6, q6_text,
         question7, q7_text,
         question8, q8_text,
         question9, q9_text,
         question10, q10_text,
         answer1, answer2, answer3, answer4, answer5,
         answer6, answer7, answer8, answer9, answer10) = row


        #change to dict to see if code can be shorter
        temp_array = [{'q_text': q1_text, 'a_val': answer1},
                      {'q_text': q2_text, 'a_val': answer2},
                      {'q_text': q3_text, 'a_val': answer3},
                      {'q_text': q4_text, 'a_val': answer4},
                      {'q_text': q5_text, 'a_val': answer5},
                      {'q_text': q6_text, 'a_val': answer6},
                      {'q_text': q7_text, 'a_val': answer7},
                      {'q_text': q8_text, 'a_val': answer8},
                      {'q_text': q9_text, 'a_val': answer9},
                      {'q_text': q10_text, 'a_val': answer10}]

        #remove any elemts that are None
        #question_text_array = filter(None, temp_array)
        #alternative method below works also
        #question_text_array = [x for x in temp_array if x is not None]

        #changed to version below (because now using list of dict items)
        question_text_array = [x for x in temp_array if x['q_text'] is not None]


        survey = {'survey_id': survey_id,
                  'client_id': client_id,
                  'client_comment': client_comment,
                  'therapist_comment': therapist_comment,
                  'time_created': time_created,
                  'time_completed': time_completed,
                  'question1':question1, 'q1_text':q1_text,
                  'question2':question2, 'q2_text':q2_text,
                  'question3':question3, 'q3_text':q3_text,
                  'question4':question4, 'q4_text':q4_text,
                  'question5':question5, 'q5_text':q5_text,
                  'question6':question6, 'q6_text':q6_text,
                  'question7':question7, 'q7_text':q7_text,
                  'question8':question8, 'q8_text':q8_text,
                  'question9':question9, 'q9_text':q9_text,
                  'question10':question10, 'q10_text':q10_text,
                  'question_text_array':question_text_array,
                  'answer1':answer1, 'answer2':answer2, 'answer3':answer3,
                  'answer4':answer4, 'answer5':answer5, 'answer6':answer6,
                  'answer7':answer7, 'answer8':answer8, 'answer9':answer9,
                  'answer10':answer10}

        #print ('survey_id=', survey_id)
        #print ('client_id=', client_id)
        #print ('question_list=', question_list)
        #print ('survey.question_list=', survey['question_list'])
        return survey


def save_answers(dbc, survey_id, form):
    ntries = 1
    while ntries < 5:
        try:
            with dbc:
                #print('save_answers - test point 1')
                #print('save_answers - survey_id = ', survey_id)
                with dbc.cursor() as cur:
                    #check to verify survey exists, and abort if not
                    cur.execute('''
                      SELECT survey_id FROM survey2
                      WHERE survey_id = %s
                    ''', (survey_id,))
                    row = cur.fetchone()
                    if row is None:
                        flask.abort(403)

                   
                    num_questions = form['num_questions']
                    #print('num_questions=', num_questions)

                    answer1 = form['answer1']
                    if not answer1:
                        answer1 = None
                    answer2 = None
                    answer3 = None
                    answer4 = None
                    answer5 = None
                    answer6 = None
                    answer7 = None
                    answer8 = None
                    answer9 = None
                    answer10 = None

                    answer2 = 'None'
                    if int(num_questions) > 1: 
                        answer2 = form['answer2']
                        if not answer2:
                            answer2 = 'None'
                    answer3 = 'None'
                    if int(num_questions) > 2: 
                        answer3 = form['answer3']
                        if not answer3:
                            answer3 = 'None'
                    answer4 = 'None'
                    if int(num_questions) > 3: 
                        answer4 = form['answer4']
                        if not answer4:
                            answer4 = 'None'
                    answer5 = 'None'
                    if int(num_questions) > 4: 
                        answer5 = form['answer5']
                        if not answer5:
                            answer5 = 'None'
                    answer6 = 'None'
                    if int(num_questions) > 5: 
                        answer6 = form['answer6']
                        if not answer6:
                            answer6 = 'None'
                    answer7 = 'None'
                    if int(num_questions) > 6: 
                        answer7 = form['answer7']
                        if not answer7:
                            answer7 = 'None'
                    answer8 = 'None'
                    if int(num_questions) > 7: 
                        answer8 = form['answer8']
                        if not answer8:
                            answer8 = 'None'
                    answer9 = 'None'
                    if int(num_questions) > 8: 
                        answer9 = form['answer9']
                        if not answer9:
                            answer9 = 'None'
                    answer10 = 'None'
                    if int(num_questions) > 9: 
                        answer10 = form['answer10']
                        if not answer10:
                            answer10 = 'None'
                    client_comment = form['client_comment'].strip()
                    if not client_comment:
                        client_comment = None

                    #print('save_answers - test point 4')
                    #print('save_answers - survey_id = ', survey_id)

                    update_needed = False
                    query ='''
                        UPDATE survey2
                        SET '''
                    if answer1 != 'None':
                        query += 'answer1 =' + answer1 + ','
                        update_needed = True
                    if answer2 != 'None':
                        query += 'answer2 =' + answer2 + ','
                        update_needed = True 
                    if answer3 != 'None':
                        query += 'answer3 =' + answer3 + ','
                        update_needed = True 
                    if answer4 != 'None':
                        query +=  'answer4 =' + answer4 + ','
                        update_needed = True 
                    if answer5 != 'None':
                        query += 'answer5 =' + answer5 + ','
                        update_needed = True 
                    if answer6 != 'None':
                        query += 'answer6 =' + answer6 + ','
                        update_needed = True 
                    if answer7 != 'None':
                        query += 'answer7 =' + answer7 + ','
                        update_needed = True 
                    if answer8 != 'None':
                        query += 'answer8 =' + answer8 + ','
                        update_needed = True 
                    if answer9 != 'None':
                        query += 'answer9 =' + answer9 + ','
                        update_needed = True 
                    if answer10 != 'None':
                        query += 'answer10 =' + answer10 + ','
                        update_needed = True
                    if client_comment != None:
                        query += 'client_comment =' + "'" + client_comment + "'"
                        update_needed = True
                        #print('print from if stmt')
                    else:
                        #this approach did not remove comment (only matter on second write)#remove last comma
                        #query = query[:-1]
                        #print('print from else stmt')
                        #this line added to blank out comment(probably do not need if editing survey not allowed)
                        query += 'client_comment =' + "''"
                    query += ' WHERE survey_id =' + str(survey_id)

                    #print('query = ', query)
                    if update_needed == True:
                        cur.execute(query)

                return
        except psycopg2.DatabaseError as dbe:
            print("commit error: {}".format(dbe), file=sys.stderr)
            dbc.rollback()
            ntries += 1

    flask.abort(500)


def update_avg_score(dbc, survey_id):
    ntries = 1
    while ntries < 5:
        try:
            with dbc:
                with dbc.cursor() as cur:
                    #check to verify survey exists, and abort if not
                    cur.execute('''
                        SELECT survey_id, answer1, answer2, answer3, answer4, answer5,
                               answer6, answer7, answer8, answer9, answer10
                        FROM survey2
                        WHERE survey_id = %s
                    ''', (survey_id,))

                    row = cur.fetchone()
                    if row is None:
                        flask.abort(404)

                    # unpack row
                    (survey_id, answer1, answer2, answer3, answer4, answer5,
                     answer6, answer7, answer8, answer9, answer10) = row
                    total_of_answers = 0
                    count_of_answers = 0

                    if answer1 != None:
                        total_of_answers += answer1
                        count_of_answers += 1
                    if answer2 != None:
                        total_of_answers += answer2
                        count_of_answers += 1
                    if answer3 != None:
                        total_of_answers += answer3
                        count_of_answers += 1
                    if answer4 != None:
                        total_of_answers += answer4
                        count_of_answers += 1
                    if answer5 != None:
                        total_of_answers += answer5
                        count_of_answers += 1
                    if answer6 != None:
                        total_of_answers += answer6
                        count_of_answers += 1
                    if answer7 != None:
                        total_of_answers += answer7
                        count_of_answers += 1
                    if answer8 != None:
                        total_of_answers += answer8
                        count_of_answers += 1
                    if answer9 != None:
                        total_of_answers += answer9
                        count_of_answers += 1
                    if answer10 != None:
                        total_of_answers += answer10
                        count_of_answers += 1

                    avg_score = None
                    if count_of_answers > 0:
                        avg_score = (float(total_of_answers)/float(count_of_answers))

                    cur.execute('''
                        UPDATE survey2
                        SET avg_score = %s
                        WHERE survey_id = %s
                    ''', (avg_score, survey_id))


                return
        except psycopg2.DatabaseError as dbe:
            print("commit error: {}".format(dbe), file=sys.stderr)
            dbc.rollback()
            ntries += 1

    flask.abort(500)


def get_templates(dbc, cid):
    with dbc, dbc.cursor() as cur:
        cur.execute('''
            SELECT template_id, phq9
            FROM template
            WHERE client_id = %s
        ''', (cid,))

        templates = []
        for (template_id, phq9) in cur:
            templates.append({'template_id':template_id, 'phq9':phq9})

        return templates


def get_template(dbc, template_id):
    with dbc, dbc.cursor() as cur:
        cur.execute('''
            SELECT template_id, therapist_id, client_id,
                   question_list, send_time1, send_time2,
                   send_time3, send_time4, send_time5
            FROM template
            WHERE template_id = %s
        ''', (template_id,))

        row = cur.fetchone()
        if row is None:
            flask.abort(404)

        # unpack row
        (template_id, therapist_id, client_id, question_list,
         send_time1, send_time2, send_time3, send_time4, send_time5) = row

        template = {'template_id': template_id,
                  'therapist_id': therapist_id,
                  'client_id': client_id,
                  'question_list': question_list,
                  'send_time1': send_time1, 'send_time2': send_time2,
                  'send_time3': send_time3, 'send_time4': send_time4,
                  'send_time5': send_time5}

        #print ('template_id=', template_id)
        #print ('client_id=', client_id)
        #print ('template.question_list=', template['question_list'])
        return template


def create_templates(dbc, therapist_id, client_id, form):

    Create_PHQ9 = 'n'
    Create_Custom = 'n'
    #print('Create_PHQ9=', Create_PHQ9)
    #print('Create_Custom=', Create_Custom)

    Create_PHQ9 = form['Create_PHQ9']
    Create_Custom = form['Create_Custom']

    #print('Create_PHQ9=', Create_PHQ9)
    #print('Create_Custom=', Create_Custom)


    #build query to get insert one or two templates
    query = ''
    if Create_PHQ9 == 'y':
        query +='''
            INSERT INTO template (therapist_id, client_id, question_list, phq9)
            VALUES (''' + str(therapist_id) + ', ' + str(client_id) + ', \'1%2%3%4%5%6%7%8%9\', TRUE);'

    if Create_Custom == 'y':
        query +='''
            INSERT INTO template (therapist_id, client_id, question_list, phq9)
            VALUES (''' + str(therapist_id) + ', ' + str(client_id) + ', \'\', FALSE);'

    #print('query=', query)

    ntries = 1
    while ntries < 5:
        try:
            with dbc:
                with dbc.cursor() as cur:
                    cur.execute(query)

                return
        except psycopg2.DatabaseError as dbe:
            print("commit error: {}".format(dbe), file=sys.stderr)
            dbc.rollback()
            ntries += 1

    flask.abort(500)


def get_client_surveys2_param(dbc,cid,start_date, end_date):
    #time_now = datetime.datetime.now()
    #time_2wks_ago = time_now - datetime.timedelta(days=14)
    #if start_date > end_date:
        #print('start date > end_date')
    #    start_date = 'default'
    #    end_date = 'default'
    #if start_date == 'default':
    #    start_date = time_2wks_ago
    #if end_date == 'default':
    #    end_date = time_now
    #print('time_now=', time_now)
    #print('time_2wks_ago=', time_2wks_ago)
    #print('start_date=', start_date)
    #print('end_date=', end_date)

    #build query to get text for all question
    query ='''
        SELECT survey_id, client_comment,
                   therapist_comment, time_created, time_completed,
                   avg_score, phq9
            FROM survey2
            WHERE client_id = ''' + cid
    #query +=  cid + ' '
    query +='''
            AND time_created::date >= \'''' + str(start_date) +  '\'::date'
    query +='''
            AND time_created::date <= \'''' + str(end_date) +  '\'::date'
    query +='''
            ORDER BY time_created DESC'''

    #print('query=', query)
        
    #with dbc, dbc.cursor() as cur:
    #    cur.execute('''
    #        SELECT survey_id, client_comment,
    #               therapist_comment, time_created, time_completed,
    #               avg_score, phq9
    #        FROM survey2
    #        WHERE client_id = %s
    #        ORDER BY time_created DESC
    #    ''', (cid,))

    with dbc, dbc.cursor() as cur:
        cur.execute(query)

        surveys2_param = []
        for (survey_id, client_comment, therapist_comment,
             time_created, time_completed, avg_score, phq9) in cur:
            surveys2_param.append({'survey_id': survey_id,
                             'client_comment': client_comment,
                             'therapist_comment': therapist_comment,
                             'time_created': time_created,
                             'time_completed': time_completed,
                             'avg_score': avg_score,
                             'phq9': phq9})

        return surveys2_param
