from flask import Flask
from sqlite3 import dbapi2 as sqlite3
from functools import wraps
from flask import Flask, request, session, url_for, redirect, \
render_template, abort, g, flash, _app_ctx_stack
import os, subprocess
import urllib.request
from werkzeug import check_password_hash, generate_password_hash

app = Flask("OTS-POC")
app.config.from_object(__name__)
if not os.path.exists("./data"):
    os.makedirs("./data")
# if not os.path.isfile('poc.db'):
#     init_db()

app.config.update(dict(
        DATABASE=os.path.join(app.root_path, 'poc.db'),
        DEBUG=True,
        SECRET_KEY=b'_5#y2L"F4Q8z\n\xec]/',
        USERNAME='admin',
        PASSWORD='3'
))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def get_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

@app.cli.command('initdb')
def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    print('Initialized the database.')

def query_db(query, args=(), one=False):
    """Queries the database and returns a list of dictionaries."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv

@app.route("/", methods=['GET', 'POST'])
@login_required
def home():
    return render_template('home.html', items=all_items())

@login_required
def check_ots_server():
    try:
        return (urllib.request.urlopen("http://localhost:14788").getcode() == 200)
    except:
        return False

@login_required
def stamp(file_path):
    # ots --wait --verbose stamp -c http://localhost:14788 -m 1 FILE
    if check_ots_server():
        procedure = subprocess.Popen("ots --verbose stamp -c http://localhost:14788 -m 1 " + file_path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out, err) = procedure.communicate()
        return out.decode()
    else:
        raise Exception("Unable to connect to calendar server.")

@login_required
def verify_ots(ots_file_path):
    if check_ots_server():
        procedure = subprocess.Popen("ots --btc-regtest -l http://127.0.0.1:14788 verify " + ots_file_path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out, err) = procedure.communicate()
        return out.decode()
    else:
        raise Exception("Unable to connect to calendar server.")

@login_required
def upgrade_ots(ots_file_path):
    # ots --btc-regtest -l http://127.0.0.1:14788 upgrade FILE.ots 
    if check_ots_server():
        procedure = subprocess.Popen("ots --btc-regtest -l http://127.0.0.1:14788 upgrade " + ots_file_path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out, err) = procedure.communicate()
        return out.decode()
    else:
        raise Exception("Unable to connect to calendar server.")

@login_required
def info_ots(ots_file_path):
    # ots --btc-regtest -l http://127.0.0.1:14788 info FILE.ots
    if check_ots_server():
        procedure = subprocess.Popen("ots --btc-regtest -l http://127.0.0.1:14788 info " + ots_file_path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out, err) = procedure.communicate()
        return out.decode()
    else:
        raise Exception("Unable to connect to calendar server.")

@login_required
def mine_bitcoin():
    '''
    import subprocess
    test = subprocess.Popen(["ping","-W","2","-c", "1", "192.168.1.70"], stdout=subprocess.subprocess.PIPE)
    output = test.communicate()[0]
    '''
    procedure = subprocess.Popen("bitcoin-cli -datadir=/root/miner generate 3", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out, err) = procedure.communicate()
    return out.decode()

@login_required
@app.route('/item/create', methods=['GET', 'POST'])
def create_item():
    error = None
    row_data = None
    if request.method == 'POST':
        if not request.form['name']:
            error = 'You have to enter a name.'
        elif not request.form['type']:
            error = 'You have to enter a type.'
        elif not request.form['data']:
            error = 'You have to enter a data.'
        else:
            db = get_db()
            if request.form['type'] == "pure": # New root item
                row_data = db.execute('''insert into item (
                          name, owner, data, verified, derived, timestamped) values (?, ?, ?, 0, 0, 0)''',
                          [request.form['name'], g.user["uuid"], request.form['data']])
            elif request.form['type'] == "derived": # Create by combine
                if not request.form['link']:
                    error = 'You have to enter a link for combined item.'
                else:
                    row_data = db.execute('''insert into item (
                      name, owner, data, linked_item, verified, derived, timestamped) values (?, ?, ?, ?, 0, 1, 0)''',
                      [request.form['name'], g.user["uuid"], request.form['data'], request.form['link']])
            if not error:
                try:
                    db.commit()
                    lastrowid = row_data.lastrowid
                    item_row = query_db('''select * from item where rowid = ?''', [lastrowid], True)
                    try:
                        transaction(item_row["item_id"], request.form['data'], "Create Item")
                    except Exception as e:
                        flash(str(e.args[0]) + "\n" + "Transaction time stamping not started.")
                    finally:
                        flash('Successfully Created')
                        return redirect(url_for('home'))
                except Exception as e:
                    return render_template('create_item.html', error=e.args[0])
        return render_template('create_item.html', error=error)

    return render_template('create_item.html', error=error)

@login_required
def transaction(item_id, data, txn_type):
    db = get_db()
    txn_row = query_db('''select * from txn order by txn_id desc limit 1''', one=True)
    if not txn_row:
        txn_row = {}
        txn_row["txn_id"] = 0
    row_data = db.execute('''insert into txn (
      ts_start, ts_complete, prev_tx, item_id, type, data_file_path, ots_file_path) values (0, 0, ?, ?, ?, ?, ?)''',
      [txn_row["txn_id"], item_id, txn_type, '', ''])
    db.commit()
    lastrowid = row_data.lastrowid
    txn_row = query_db('''select * from txn where rowid = ?''', [lastrowid], one=True)

    db.execute('''update item set
          stamp_txn_id = ?
          where item_id = ?''',
          [txn_row["txn_id"], item_id])
    db.commit()

    data_file_path = "./data/" + str(txn_row["txn_id"])
    data_file = open(data_file_path, "w")
    data_file.write(data)
    data_file.close()

    try:
        stamp(data_file_path)
        db.execute('''update txn set
          ts_start = 1 ,
          data_file_path = ? ,
          ots_file_path = ?
          where txn_id = ?''',
          [data_file_path, data_file_path + ".ots" , txn_row["txn_id"]])
        db.commit()
        db.execute('''update item set
              timestamped = 1
              where item_id = ?''',
              [item_id])
        db.commit()
    except Exception as e:
        raise Exception(e)

@app.route('/transactions', methods=['GET'])
@login_required
def all_transaction():
    txns = query_db('''select * from txn''')
    return render_template('txns.html', txns=txns)

@app.route('/txn/verify', methods=['GET'])
@login_required
def verify_upgrade_transaction():
    txn_row = query_db('''select * from txn where txn_id = ?''', [request.args["txn_id"]], one=True)
    try:
        verify_result = verify_ots(txn_row["ots_file_path"])
        if 'Success! Bitcoin attests data existed' in verify_result:
            upgrade_result = upgrade_ots(txn_row["ots_file_path"])
            db = get_db()
            db.execute('''update txn set
              ts_complete = 1
              where txn_id = ?''',
              [txn_row["txn_id"]])
            db.commit()
            db.execute('''update item set
                  timestamped = 1
                  where item_id = ?''',
                  [txn_row["item_id"]])
            db.commit()
            flash(upgrade_result)
    except Exception as e:
        flash(str(e.args[0]))

    return redirect(url_for('transaction_detail', txn_id=[request.args["txn_id"]]))

@app.route('/txn/stamp', methods=['GET'])
@login_required
def stamp_transaction():
    try:
        data_file_path = "./data/" + str([request.args["txn_id"]])
        stamp_result = stamp(data_file_path)
        db = get_db()
        db.execute('''update txn set
          ts_start = 1 ,
          data_file_path = ? ,
          ots_file_path = ?
          where txn_id = ?''',
          [data_file_path, data_file_path + ".ots" , [request.args["txn_id"]]])
        db.commit()
        flash(stamp_result)
    except Exception as e:
        flash(str(e.args[0]))

    return redirect(url_for('transaction_detail', txn_id=[request.args["txn_id"]]))

@login_required
def transaction_timestamp_info(txn_id):
    txn_row = query_db('''select * from txn where txn_id = ?''', [tnx_id], one=True)
    try:
        timpstamp_info = verify_ots(txn_row["ots_file_path"])
        return timpstamp_info.split('\n')[1]
    except Exception as e:
        print(e.args) 

@app.route('/txn/details', methods=['GET'])
@login_required
def transaction_detail():
    txn_row = query_db('''select * from txn where txn_id = ?''', [request.args["txn_id"]], one=True)
    try:
        transaction_info = info_ots(txn_row["ots_file_path"])
        timpstamp_info = verify_ots(txn_row["ots_file_path"])
        # return transaction_info
        return render_template('txn_details.html', txn=txn_row, ots_info=transaction_info, ts_info=timpstamp_info.split('\n')[1])
    except Exception as e:
        return render_template('txn_details.html', txn=txn_row, ots_info=e.args[0], ts_info="")

@login_required
def all_items():
    return query_db('''select * from item''')

@app.route('/item/details', methods=['GET'])
@login_required
def item_detail():
    item = query_db('''select * from item where item_id = ?''', [request.args["item_id"]], one=True)
    return render_template('item_details.html', item=item)

@login_required
def item_chain(item_id):
    return query_db('''select * from txn where item_id = ?''', [item_id])

@app.route('/item/verify', methods=['GET'])
@login_required
def verify_item():
    try:
        db = get_db()
        db.execute('''update item set 
                    verified = 1 , 
                    verified_by = ?
                    where item_id = ?''', [g.user["uuid"], request.args["item_id"]])
        db.commit()
        flash("Successfully Verified.")
    except Exception as e:
        flash(str(e.args[0]))

    return redirect(url_for('item_detail', item_id=request.args["item_id"]))

@app.route('/item/edit', methods=['GET', "POST"])
@login_required
def edit_item():
    if request.method == 'POST':
        try:
            item = query_db('''select * from item where item_id = ?''', [request.form["item_id"]], one=True)
            db = get_db()
            db.execute('''update item set
                        data = ?
                        where item_id = ?''', [request.form["data"], request.form["item_id"]])
            db.commit()

            data_file_path = "./data/" + str(item["stamp_txn_id"])
            data_file = open(data_file_path, "w")
            data_file.write(request.form["data"])
            data_file.close()

            flash("Successfully Updated.")
            return redirect(url_for('item_detail', item_id=request.args["item_id"]))
        except Exception as e:
            flash(str(e.args[0]))

    item = query_db('''select * from item where item_id = ?''', [request.args["item_id"]], one=True)
    return render_template('edit_item.html', item=item)

@login_required
def verify_user():
    pass

@login_required
def owner_transfer():
    pass

@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = query_db('select * from user where user_id = ?',
                            [session['user_id']], one=True)

def get_user_id(uuid):
    """Convenience method to look up the id for a uuid."""
    rv = query_db('select user_id from user where uuid = ?',
                  [uuid], one=True)
    return rv[0] if rv else None

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Logs the user in."""
    if g.user:
        return redirect(url_for('home'))
    error = None
    if request.method == 'POST':
        user = query_db('''select * from user where
            uuid = ?''', [request.form['uuid']], one=True)
        if user is None:
            error = 'Invalid uuid'
        elif not check_password_hash(user['pw_hash'],
                                     request.form['password']):
            error = 'Invalid password'
        else:
            flash('You were logged in')
            session['user_id'] = user['user_id']
            return redirect(url_for('home'))
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registers the user."""
    if g.user:
        return redirect(url_for('home'))
    error = None
    if request.method == 'POST':
        if not request.form['uuid']:
            print(1)
            error = 'You have to enter a uuid'
        elif not request.form['email'] or \
                '@' not in request.form['email']:
            print(2)
            error = 'You have to enter a valid email address'
        elif not request.form['password']:
            print(3)
            error = 'You have to enter a password'
        elif request.form['password'] != request.form['password2']:
            print(4)
            error = 'The two passwords do not match'
        elif get_user_id(request.form['uuid']) is not None:
            print(5)
            error = 'The uuid is already exists'
        else:
            print(6)
            db = get_db()
            db.execute('''insert into user (
              uuid, email, pw_hash, type, verified) values (?, ?, ?, ?, 0)''',
              [request.form['uuid'], request.form['email'],
               generate_password_hash(request.form['password']), request.form['type']])
            db.commit()
            print(7)
            flash('You were successfully registered and can login now')
            return redirect(url_for('login'))
    return render_template('register.html', error=error)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/logout')
@login_required
def logout():
    """Logs the user out."""
    flash('You were logged out')
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)