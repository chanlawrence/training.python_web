#!/usr/bin/env python
from flask import Flask
from contextlib import closing
from flask import g
from flask import render_template
from flask import abort
from flask import request
from flask import url_for
from flask import redirect
from flask import session
from flask import flash

import sqlite3

app = Flask(__name__)
app.config.from_pyfile('microblog.cfg')

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db: 
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_database_connection():
    db = getattr(g, 'db', None) #getattr is the same as bob.get('key', None)
    if db is None:
        g.db = db = connect_db()
    return db

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def write_entry(title, text):
    con = get_database_connection()
    con.execute('insert into entries (title, text) values (?, ?)',
                 [title, text])
    con.commit()

def get_all_entries():
    con = get_database_connection()
    cur = con.execute('SELECT title, text FROM entries ORDER BY id DESC')
    return [dict(title=row[0], text=row[1]) for row in cur.fetchall()] #this is a list comprehension. Iterating through each row, then builds a dictionary.

@app.route('/')
def show_entries():
    entries = get_all_entries()
    return render_template('show_entries.html', entries=entries)

@app.route('/add', methods=['POST'])
def add_entry():
    try:
        write_entry(request.form['title'], request.form['text'])
    except sqlite3.Error:
        #abort(500)
        flash('Entry caused an error')
    flash('New entry posted')
    return redirect(url_for('show_entries'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

if __name__ == '__main__':
    app.run(debug=True)