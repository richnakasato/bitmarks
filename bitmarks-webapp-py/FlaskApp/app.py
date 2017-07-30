# all code heavily derived from:
# https://code.tutsplus.com/series/creating-a-web-app-from-scratch-using-python-flask-and-mysql--cms-827
import sys
import uuid
import random
import requests
#import json		# using flask version

# crypto includes
from base64 import b64encode, b64decode
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from datetime import datetime

# web app includes
from flask import Flask, render_template, json, request, redirect, session, url_for
from flaskext.mysql import MySQL

# bitmarks api {{{
namespace = "edu.gatech.bitmarks"
resource = "resource:"+namespace
bitmarks_api = "http://localhost:3000/api/"
#bitmarks_api = "http://ec2-34-212-169-28.us-west-2.compute.amazonaws.com:3000/api/"
not_found = 404
class_key = "$class"

# learner api
learner_payload_keys = [class_key, "learnerId", "firstName", "lastName", "salt"]
learner_payload = dict.fromkeys(learner_payload_keys)
learner_class = "Learner"
learner_namespace_class = namespace+"."+learner_class
learner_payload[class_key] = learner_namespace_class
learner_resource = resource+"."+learner_class+"#"
learner_api = bitmarks_api+learner_class+"/"

# issuer api
issuer_payload_keys = [class_key, "issuerId", "name", "country", "url"]
issuer_payload = dict.fromkeys(issuer_payload_keys)
issuer_class = "Issuer"
issuer_namespace_class = namespace+"."+issuer_class
issuer_payload[class_key] = issuer_namespace_class
issuer_resource = resource+"."+issuer_class+"#"
issuer_api = bitmarks_api+issuer_class+"/"

# item api
item_payload_keys = [class_key, "itemId", "credential", "units", "comments",
                     "issuer"]
item_payload = dict.fromkeys(item_payload_keys)
item_class = "TranscriptItem"
item_namespace_class = namespace+"."+item_class
item_payload[class_key] = item_namespace_class
item_resource = resource+"."+item_class+"#"
item_api = bitmarks_api+item_class+"/"
item_filter = bitmarks_api+item_class+"?filter="

# transaction api
transcript_payload_keys = [class_key, "quantity", "itemJSON", "issuerJSON",
                           "learnerHash", "issuerTxHashSig"]
transcript_payload = dict.fromkeys(transcript_payload_keys)
transcript_class = "AcademicTransaction"
transcript_namespace_class = namespace+"."+transcript_class
transcript_payload[class_key] = transcript_namespace_class
transcript_resource = resource+"."+transcript_class+"#"
transcript_api = bitmarks_api+transcript_class+"/"

# system
transaction_api = bitmarks_api+"system/"+"transactions"
#/// }}}


# utility functions {{{
# https://stackoverflow.com/questions/379906/parse-string-to-float-or-int
def isFloat(val):
  try:
    float(val)
    return True
  except ValueError:
    return False
# // }}}


# bitmarks functions {{{
# returns a uuid string
def generateNewUuidStr():
  return str(uuid.uuid4())


# returns true if uuid found, false otherwise
def findByUuid(api_plus_string):
  req = requests.get(api_plus_string)
  if req.status_code == not_found:
    return False
  return True


# returns response obj of uuid
def getByUuid(api_plus_string):
  return requests.get(api_plus_string)


# returns true if uuid found, false otherwise
def findLearnerByUuid(learner_uuid):
  return findByUuid(learner_api+learner_uuid)


# returns true if uuid found, false otherwise
def findIssuerByUuid(issuer_uuid):
  return findByUuid(issuer_api+issuer_uuid)


# returns true if uuid found, false otherwise
def findItemByUuid(item_uuid):
  return findByUuid(item_api+item_uuid)


# ensures learner payload fields are populated
def fixLearner(u, f, l, s):
  if not u:
    u = generateNewUuidStr()
  if not f:
    f = "Jane"
  if not l:
    l = "Smith"
  if not s:
    s = '{0:04}'.format(random.randint(1,10000))
  return u, f, l, s


# ensures issuer payload fields are populated
def fixIssuer(u, n, c, r):
  if not u:
    u = generateNewUuidStr()
  if not n:
    n = "University College"
  if not c:
    c = "USA"
  if not r:
    r = 'www.university-college.edu'
  return u, n, c, r


# ensures item payload fields are populated
def fixItem(u, n, i, c):
  if not u:
    u = uuid.uuid4()
  if not n:
    n = "Introduction to College 101"
  if not i:
    i = "GPA"
  if not c:
    c = "No comments."
  return u, n, i, c


# ensures transaction payload fields are populated
def fixTransaction(q):
  if not q or not isFloat(q):
    q = "0";
  else:
    q = q.rstrip('.0')
  return q


# returns json object for item id
def getItemResponseObj(item_id):
  item_string = item_api+item_id
  r = requests.get(item_string)
  return r


# returns json object for issuer id
def getIssuerResponseObj(issuer_id):
  issuer_string = issuer_api+issuer_id
  r = requests.get(issuer_string)
  return r


# returns json object for learner id
def getLearnerResponseObj(learner_id):
  learner_string = learner_api+learner_id
  r = requests.get(learner_string)
  return r


# returns json objects for all transactions
def getTransactionResponseObjs():
  r = requests.get(transaction_api)
  return r


# returns json string for item id
def getItemJson(item_id):
  r = getItemResponseObj(item_id)
  item_json = json.dumps(r.json())
  return item_json


# returns json string for issuer id
def getIssuerJson(issuer_id):
  r = getIssuerResponseObj(issuer_id)
  issuer_json = json.dumps(r.json())
  return issuer_json


# build item string from item response
def getItemStringFromRespObj(r):
  part_1 = r.json()[class_key]
  part_2 = r.json()['credential']
  part_3 = r.json()['units']
  item_string = part_1 + " " + part_2 + " " + part_3
  return item_string


# build issuer string from item response
def getIssuerStringFromRespObj(r):
  part_1 = r.json()[class_key]
  part_2 = r.json()['name']
  part_3 = r.json()['country']
  part_4 = r.json()['url']
  issuer_string = part_1 + " " + part_2 + " " + part_3 + " " + part_4
  return issuer_string


# get item string from item address
def getItemString(item_id):
  res = getItemResponseObj(item_id)
  return getItemStringFromRespObj(res)


# get issuer string from issuer address
def getIssuerString(issuer_id):
  res = getIssuerResponseObj(issuer_id)
  return getIssuerStringFromRespObj(res)


# build learner hash from learner response
def getLearnerHashFromRespObj(r):
  hash_1 = r.json()['firstName']
  hash_2 = r.json()['lastName']
  hash_3 = str(r.json()['salt'])
  learner_string_to_hash = hash_1 + " " + hash_2 + " " + hash_3
  learner_hash = SHA256.new(learner_string_to_hash).hexdigest()
  return learner_hash


# build learner name from learner response
def getLearnerNameFromRespObj(r):
  first_name = r.json()['firstName']
  last_name = r.json()['lastName']
  learner_name = first_name + " " + last_name
  return learner_name


# get learner hash from learner address
def getLearnerHash(learner_id):
  res = getLearnerResponseObj(learner_id)
  return getLearnerHashFromRespObj(res)


# get learner name from learner address
def getLearnerName(learner_id):
  res = getLearnerResponseObj(learner_id)
  return getLearnerNameFromRespObj(res)


# hydrates learner payload
def hydrateLearnerPayload(uuid, first, last, salt):
  uuid, first, last, salt = fixLearner(uuid, first, last, salt)
  learner_payload['learnerId'] = uuid
  learner_payload['firstName'] = first
  learner_payload['lastName']  = last
  learner_payload['salt']      = salt
  return learner_payload


# hydrates issuer payload
def hydrateIssuerPayload(uuid, name, country, url):
    uuid, name, country, url = fixIssuer(uuid, name, country, url)
    issuer_payload['issuerId']  = uuid
    issuer_payload['name']      = name
    issuer_payload['country']   = country
    issuer_payload['url']       = url
    return issuer_payload


# hydrates item payloads
def hydrateItemPayload(uuid, name, unit, comment, issuer):
    uuid, name, unit, comment = fixItem(uuid, name, unit, comment)
    item_payload['itemId']      = uuid
    item_payload['credential']  = name
    item_payload['units']       = unit
    item_payload['comments']    = comment
    item_payload['issuer']      = issuer_resource+issuer
    return item_payload


#helper function to hydrate transaction payload - PRE SIGNATURE
def hydrateTransactionPayloadPreSig(quantity, item, issuer, learner):
    quantity = fixTransaction(quantity)
    transcript_payload['quantity']         = quantity
    transcript_payload['itemJSON']         = item
    transcript_payload['issuerJSON']       = issuer
    transcript_payload['learnerHash']      = learner
    transcript_payload['issuerTxHashSig']  = ""
    return transcript_payload


# returns learner response object of uuid
def getLearnerByUuid(learner_uuid):
  return getByUuid(learner_api+learner_uuid)


# returns issuer response object of uuid
def getIssuerByUuid(issuer_uuid):
  return getByUuid(issuer_api+issuer_uuid)


# returns item response object of uuid
def getItemByUuid(item_uuid):
  return getByUuid(item_api+item_uuid)


# returns item response object of all items
def getAllItems():
  sys.stderr.write(str(item_api[:-1])+'\n')
  return getByUuid(item_api)


# returns filtered item response object of uuid
def getFilteredItemsByUuid(issuer_uuid):
  issuer = {'issuer': issuer_resource+issuer_uuid}
  issuer = json.dumps(issuer)
  return getByUuid(item_filter+issuer)


# builds the string we sign and/or verify from tx obj
def buildSignOrVerifyStringFromTxObj(tx_obj):
  string_out = str(tx_obj[class_key]) + " " + \
               str(tx_obj['quantity']) + " " + \
               str(tx_obj['itemJSON']) + " " + \
               str(tx_obj['issuerJSON']) + " " + \
               str(tx_obj['learnerHash'])
  return string_out


# get issuer tx hash sig from tx obj
def getIssuerTxHashSigFromTxObj(tx_obj):
  string_out = str(tx_obj['issuerTxHashSig'])
  return string_out


# verify a string with a public key
def isVerifyStringWithRsa(message, public, signature):
    #key = RSA.importKey(open(public, "r").read())
    key = RSA.importKey(public)
    verifier = PKCS1_v1_5.new(key)
    #digest = SHA256.new(message)
    if verifier.verify(message, signature):
        return True
    return False
#/// }}}


# flask functions{{{
# flask and sql
app = Flask(__name__)
mysql = MySQL()

# mysql configurations
app.config['MYSQL_DATABASE_USER'] = 'bitmarks'
app.config['MYSQL_DATABASE_PASSWORD'] = 'bitmarks_password'
app.config['MYSQL_DATABASE_DB'] = 'bitMarks'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

# error messages
db_err = 'Debugging here!'
ua_err = 'Please sign in!'
dp_err = 'Uuid already exists!'
is_err = 'Issuer address does not exist!'

@app.route("/")
def main():
  return render_template('index.html')


@app.route('/showSignUp')
def showSignUp():
  return render_template('signup.html')


@app.route('/signUp', methods=['POST','GET'])
def signUp():
  try:
    _name = request.form['inputName']
    _email = request.form['inputEmail']
    _password = request.form['inputPassword']
    _usertype = request.form['inputType']

    if _name and _email and _password and _usertype:
      conn = mysql.connect()
      cursor = conn.cursor()
      #_hashed_password = generate_password_hash(_password)
      cursor.callproc('sp_createUser',(_name,_email,_password,_usertype))
      data = cursor.fetchall()

      if len(data) is 0:
        conn.commit()
        return json.dumps({'message':'User created successfully!'})
      else:
        return json.dumps({'error':str(data[0])})
    else:
      return json.dumps({'html':'<span>Enter the required fields!</span>'})

  except Exception as e:
    return json.dumps({'error':str(e)})

  finally:
    cursor.close()
    conn.close()


@app.route('/showSignIn')
def showSignIn():
  return render_template('signin.html')


@app.route('/validateLogin', methods=['POST'])
def validateLogin():
  err_str = 'Wrong email address of password!'
  try:
    _username = request.form['inputEmail']
    _password = request.form['inputPassword']

    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.callproc('sp_validateLogin',(_username,))
    data = cursor.fetchall()

    if len(data) > 0:
      if _password == str(data[0][3]):
        session['user'] = data[0][0]
        usertype = str(data[0][4])
        if usertype == 'Learner':
          return redirect('/learnerHome')
        elif usertype == 'Issuer':
          return redirect('/issuerHome')
        else:
          return redirect('/supportHome')
      else:
        return render_template('error.html', error=err_str)
    else:
      return render_template('error.html', error=err_str)

  except Exception as e:
    return render_template('error.html', error=str(e))

  finally:
    cursor.close()
    conn.close()


@app.route('/learnerHome')
def learnerHome():
  if session.get('user'):
    return render_template('learnerhome.html')
  else:
    return render_template('learnererror.html', error=ua_err)


@app.route('/issuerHome')
def issuerHome():
  if session.get('user'):
    return render_template('issuerhome.html')
  else:
    return render_template('issuererror.html', error=ua_err)


@app.route('/supportHome')
def supportHome():
  if session.get('user'):
    req = getTransactionResponseObjs()
    unverified_tx_list = json.loads(req.text)
    return render_template('supporthome.html', utx=unverified_tx_list)
  else:
    return render_template('supporterror.html', error=ua_err)


@app.route('/logout')
def logout():
  session.pop('user',None)
  return redirect('/')


@app.route('/showAddLearner')
def showAddLearner():
  return render_template('addlearner.html')


@app.route('/addLearner', methods=['POST'])
def addLearner():
  try:
    if session.get('user'):
      _user = session.get('user')

      _firstname = request.form['inputFirstName']
      _lastname = request.form['inputLastName']
      _saltvalue = request.form['inputSaltValue']
      _newuuid = generateNewUuidStr()

      conn = mysql.connect()
      cursor = conn.cursor()
      cursor.callproc('sp_addLearner',(_newuuid, _user))
      data = cursor.fetchall()

      if not findLearnerByUuid(_newuuid) and len(data) is 0:
        this_payload = hydrateLearnerPayload( _newuuid,
                                              _firstname,
                                              _lastname,
                                              _saltvalue )
        req = requests.post(learner_api, data=this_payload)
        conn.commit()
        return redirect('/learnerHome')
      else:
        return render_template('learnererror.html', error=dp_err)
    else:
      return render_template('learnererror.html', error=ua_err)

  except Exception as e:
    return render_template('learnererror.html', error=str(e))

  finally:
    cursor.close()
    conn.close()


@app.route('/getLearnerAddrs')
def getLearnerAddrs():
  try:
    if session.get('user'):
      _user = session.get('user')

      conn = mysql.connect()
      cursor = conn.cursor()
      cursor.callproc('sp_getLearnerAddrByUser',(_user,))
      addrs = cursor.fetchall()

      learner_addrs_dict = []
      for addr in addrs:
        learner_addr_entry = {'Id':addr[0],
                              'Address':addr[1],
                              'User Id':addr[2]}
        learner_addrs_dict.append(learner_addr_entry)
      return json.dumps(learner_addrs_dict)
    else:
      return render_template('learnererror.html', error=ua_err)

  except Exception as e:
    return render_template('learnererror.html', error=str(e))

  finally:
    cursor.close()
    conn.close()


@app.route('/getLearnerAddrDetails', methods=['POST'])
def getLearnerAddrDetails():
  try:
    if session.get('user'):
      _user = session.get('user')
      _addr = request.form['address']
      details = getLearnerByUuid(_addr).json()
      return json.dumps(details)
    else:
      return render_template('learnererror.html', error=ua_err)

  except Exception as e:
    return render_template('learnererror.html', error=str(e))


@app.route('/showAddIssuer')
def showAddIssuer():
  return render_template('addissuer.html')


@app.route('/addIssuer', methods=['POST'])
def addIssuer():
  try:
    if session.get('user'):
      _user = session.get('user')

      _name = request.form['inputIssuerName']
      _country = request.form['inputIssuerCountry']
      _url = request.form['inputIssuerUrl']
      _newuuid = generateNewUuidStr()

      conn = mysql.connect()
      cursor = conn.cursor()
      cursor.callproc('sp_addIssuer',(_newuuid, _user))
      data = cursor.fetchall()

      if not findLearnerByUuid(_newuuid) and len(data) is 0:
        this_payload = hydrateIssuerPayload( _newuuid,
                                             _name,
                                             _country,
                                             _url )
        req = requests.post(issuer_api, data=this_payload)
        conn.commit()
        return redirect('/issuerHome')
      else:
        return render_template('issuererror.html', error=dp_err)
    else:
      return render_template('issuererror.html', error=ua_err)

  except Exception as e:
    return render_template('issuererror.html', error=str(e))

  finally:
    cursor.close()
    conn.close()


@app.route('/getIssuerAddrs')
def getIssuerAddrs():
  try:
    if session.get('user'):
      _user = session.get('user')

      conn = mysql.connect()
      cursor = conn.cursor()
      cursor.callproc('sp_getIssuerAddrByUser',(_user,))
      addrs = cursor.fetchall()

      issuer_addrs_dict = []
      for addr in addrs:
        issuer_addr_entry = {'Id':addr[0],
                             'Address':addr[1],
                             'User Id':addr[2]}
        issuer_addrs_dict.append(issuer_addr_entry)
      return json.dumps(issuer_addrs_dict)
    else:
      return render_template('issuererror.html', error=ua_err)

  except Exception as e:
    return render_template('issuererror.html', error=str(e))

  finally:
    cursor.close()
    conn.close()


@app.route('/getIssuerAddrDetails', methods=['POST'])
def getIssuerAddrDetails():
  try:
    if session.get('user'):
      _user = session.get('user')
      _addr = request.form['address']
      details = getIssuerByUuid(_addr).json()
      return json.dumps(details)
    else:
      return render_template('issuererror.html', error=ua_err)

  except Exception as e:
    return render_template('issuererror.html', error=str(e))


@app.route('/getIssuerAddrCourses', methods=['POST'])
def getIssuerAddrCourses():
  try:
    if session.get('user'):
      _user = session.get('user')
      _addr = request.form['address']
      courses = getAllItems().json()
      issuer_courses_dict = []
      for course in courses:
        if _addr in course['issuer']:
          issuer_courses_entry = {'id':course['itemId'],
                                  'name':course['credential'],
                                  'comment':course['comments']}
          issuer_courses_dict.append(issuer_courses_entry)
      return json.dumps(issuer_courses_dict)
    else:
      return render_template('issuererror.html', error=ua_err)

  except Exception as e:
    return render_template('issuererror.html', error=str(e))


@app.route('/showAddItem')
def showAddItem():
  return render_template('additem.html')


@app.route('/addItem', methods=['POST'])
def addItem():
  try:
    if session.get('user'):
      _user = session.get('user')
      _name = request.form['inputItemName']
      _units = request.form['inputUnitsName']
      _comments = request.form['inputComments']
      _address = request.form['inputIssuerAddress']
      _newuuid = generateNewUuidStr()

      if not findItemByUuid(_newuuid):
        if findIssuerByUuid(_address):
          this_payload = hydrateItemPayload( _newuuid,
                                             _name,
                                             _units,
                                             _comments,
                                             _address )
          req = requests.post(item_api, data=this_payload)
          return redirect('/issuerHome')
        else:
          return render_template('issuererror.html', error=is_err)
      else:
        return render_template('issuererror.html', error=dp_err)
    else:
      return render_template('issuererror.html', error=ua_err)

  except Exception as e:
    return render_template('issuererror.html', error=str(e))


@app.route('/showAddTransaction')
def showAddTransaction():
  return render_template('addtransaction.html')


@app.route('/addTransaction', methods=['POST'])
def addTransaction():
  try:
    if session.get('user'):
      _user = session.get('user')
      _issr_addr = request.form['inputIssuerAddress']
      _cred_addr = request.form['inputCredentialAddress']
      _lrnr_addr = request.form['inputLearnerAddress']
      _quantity = request.form['inputQuantity']
      _newuuid = generateNewUuidStr()

      if not findIssuerByUuid(_issr_addr):
        return render_template('issuererror.html', error=is_err)
      if not findItemByUuid(_cred_addr):
        return render_template('issuererror.html', error=is_err)
      if not findLearnerByUuid(_lrnr_addr):
        return render_template('issuererror.html', error=is_err)

      _item_json = getItemString(_cred_addr)
      _issuer_json = getIssuerString(_issr_addr)
      _learner_hash = getLearnerHash(_lrnr_addr)
      this_payload = hydrateTransactionPayloadPreSig( _quantity,
                                                      _item_json,
                                                      _issuer_json,
                                                      _learner_hash )
      session['payload'] = this_payload
      return redirect('/showSignTransaction')
    else:
      return render_template('issuererror.html', error=ua_err)

  except Exception as e:
    return render_template('issuererror.html', error=str(e))


@app.route('/showSignTransaction')
def showSignTransaction():
  this_payload = session['payload']
  string_to_sign = buildSignOrVerifyStringFromTxObj(this_payload)
  return render_template('signtransaction.html', sts=string_to_sign)


@app.route('/signTransaction', methods=['POST'])
def signTransaction():
  try:
    if session.get('user'):
      _user = session.get('user')
      _signed_text = request.form['inputSignedTransaction']
      this_payload = session['payload']
      this_payload['issuerTxHashSig'] = _signed_text
      r = requests.post(transcript_api, data=this_payload)
      session['payload'] = None
      return redirect('/issuerHome')
    else:
      return render_template('issuererror.html', error=ua_err)

  except Exception as e:
    return render_template('issuererror.html', error=str(e))


@app.route('/showViewLearner')
def showViewLearner():
  return render_template('viewlearner.html')


@app.route('/viewLearner', methods=['POST'])
def viewLearner():
  try:
    if session.get('user'):
      _user = session.get('user')
      _learner_addr = request.form['inputLearnerAddress']
      session['learner'] = _learner_addr
      _learner_hash = getLearnerHash(_learner_addr)
      _learner_name = getLearnerName(_learner_addr)
      req = getTransactionResponseObjs()
      complete_tx_list = json.loads(req.text)
      this_learner_tx_list = []
      for tx in complete_tx_list:
        if tx['learnerHash'] == _learner_hash:
          this_learner_tx_list.append(tx)
      session['transactions'] = this_learner_tx_list
      session['learner_name'] = _learner_name
      return redirect('/showVerifyTransaction')
    else:
      return render_template('learnererror.html', error=ua_err)

  except Exception as e:
    return render_template('learnererror.html', error=str(e))


@app.route('/showVerifyTransaction')
def showVerifyTransaction():
  _tx_list = session['transactions']
  _learner_name = session['learner_name']
  session['learner'] = None
  session['transactions'] = None
  session['learner_name'] = None
  return render_template('verifytransaction.html', tx=_tx_list, ln=_learner_name)


if __name__ == "__main__":
  app.secret_key = 'why would I tell you my secret key?'
  app.run()
# // }}}
