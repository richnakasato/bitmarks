import sys
import uuid
import requests
import json
import random
from base64 import b64encode, b64decode
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from datetime import datetime

left = None
right = None

# bitmark connection definitions // {{{
namespace = "edu.gatech.bitmarks"
resource = "resource:"+namespace
#bitmarks_api = "http://localhost:3000/api/"
bitmarks_api = "http://ec2-54-213-28-177.us-west-2.compute.amazonaws.com:3000/api/"
not_found = 404
# // }}}

# bitmark model definitions // {{{
class_key = "$class"

## TRANSCRIPT TRANSACTION
transcript_payload_keys = [class_key, "quantity", "itemJSON", "issuerJSON",
                           "learnerHash", "issuerTxHashSig"]
transcript_payload = dict.fromkeys(transcript_payload_keys)
transcript_class = "AcademicTransaction"
transcript_namespace_class = namespace+"."+transcript_class
transcript_payload[class_key] = transcript_namespace_class
transcript_resource = resource+"."+transcript_class+"#"
transcript_api = bitmarks_api+transcript_class+"/"

## ISSUERS
issuer_payload_keys = [class_key, "issuerId", "name", "country", "url"]
issuer_payload = dict.fromkeys(issuer_payload_keys)
issuer_class = "Issuer"
issuer_namespace_class = namespace+"."+issuer_class
issuer_payload[class_key] = issuer_namespace_class
issuer_resource = resource+"."+issuer_class+"#"
issuer_api = bitmarks_api+issuer_class+"/"

## LEARNERS
learner_payload_keys = [class_key, "learnerId", "firstName", "lastName", "salt"]
learner_payload = dict.fromkeys(learner_payload_keys)
learner_class = "Learner"
learner_namespace_class = namespace+"."+learner_class
learner_payload[class_key] = learner_namespace_class
learner_resource = resource+"."+learner_class+"#"
learner_api = bitmarks_api+learner_class+"/"

## TRANSCRIPT LINE ITEMS (CREDENTIALS)
item_payload_keys = [class_key, "itemId", "credential", "units", "comments",
                     "issuer"]
item_payload = dict.fromkeys(item_payload_keys)
item_class = "TranscriptItem"
item_namespace_class = namespace+"."+item_class
item_payload[class_key] = item_namespace_class
item_resource = resource+"."+item_class+"#"
item_api = bitmarks_api+item_class+"/"

## SYSTEM
transaction_api =bitmarks_api+"system/"+"transactions/"

# user client definitions
client_modes = ["  (i)ssuer", "  (l)earner", "  (s)upport"]
client_shortcuts = ["i", "l", "s"]
# // }}}

################################################################################
# CRYPTO FUNCTIONS // {{{
################################################################################
# helper function to generate new RSA private/public keypair
# derived from https://gist.github.com/lkdocs/6519378
def generateRsaKeypair(bits=2048):
    new_key = RSA.generate(bits, e=65537)
    public_key = new_key.publickey().exportKey("PEM")
    private_key = new_key.exportKey("PEM")
    return private_key, public_key


# helper function to write RSA keypairs to files
# derived from https://www.dlitz.net/software/pycrypto/api/current/Crypto.PublicKey.RSA-module.html
def writeRsaKeysToFile(filename):
    private_key, public_key = generateRsaKeypair()
    f_private = open(filename+"_PRIVATE.pem", 'w')
    f_private.write(private_key)
    f_public = open(filename+"_public.pem", 'w')
    f_public.write(public_key)


# both signStringWithRsa and isVerifyStringWithRsa derived from:
# https://www.dlitz.net/software/pycrypto/api/current/Crypto.Signature.PKCS1_v1_5-module.html
# helper function to sign hash of string (presumably JSON transaction string)
def signStringWithRsa(message, private):
    key = RSA.importKey(open(private, "r").read())
    signer = PKCS1_v1_5.new(key)
    digest = SHA256.new(message)
    signature = signer.sign(digest)
    return signature


# helper function to verify hash of string with public key and signature
def isVerifyStringWithRsa(message, public, signature):
    key = RSA.importKey(open(public, "r").read())
    verifier = PKCS1_v1_5.new(key)
    digest = SHA256.new(message)
    if verifier.verify(digest, signature):
        return True
    else:
        return False


# helper function to build string of payload values in KNOWN order for signing
def buildStringToSignFromPayload(payload):
    payload_dict = json.loads(payload)
    output = str(payload_dict[class_key]) + " " + \
             str(payload_dict['quantity']) + " " + \
             str(payload_dict['itemJSON']).replace("\\","") + " " + \
             str(payload_dict['issuerJSON']).replace("\\","") + " " + \
             str(payload_dict['learnerHash'])
    return output


# helper function to build string of payload values from json response
def buildStringToSignFromResponse(response):
    payload = json.dumps(response.json(), ensure_ascii=False)
    return buildStringToSignFromPayload(payload)


# helper function to get signature from payload
def getStringSignatureFromPayload(payload):
    payload_dict = json.loads(payload)
    signature = str(payload_dict['issuerTxHashSig'])
    return signature


#helper function to get signature from json response
def getStringSignatureFromResponse(response):
    payload = json.dumps(response.json(), ensure_ascii=False)
    return getStringSignatureFromPayload(payload)


# helper function to build learner hash from learner response
def getLearnerHashFromRespObj(r):
    hash_1 = r.json()['firstName']
    hash_2 = r.json()['lastName']
    hash_3 = str(r.json()['salt'])
    learner_string_to_hash = hash_1 + " " + hash_2 + " " + hash_3
    learner_hash = SHA256.new(learner_string_to_hash).hexdigest()
    return learner_hash


# generates set of RSA keypairs for testing
def generateKeyPairs():
    #legit_college = "universityCollege"
    #writeRsaKeysToFile(legit_college)
    #other_legit_college = "collegeUniversity"
    #writeRsaKeysToFile(other_legit_college)
    for_profit_university = "internationalInstitute"
    writeRsaKeysToFile(for_profit_university)
    #fake_university = "georgeTech"
    #writeRsaKeysToFile(fake_university)
# // }}}


################################################################################
# FIND FUNCTIONS // {{{
################################################################################
# helper function to find via api
def findApi(search_string):
    r = requests.get(search_string)
    if r.status_code == not_found:
        return False
    return True


# helper function to locate an issuer based on the guid string
def findIssuer(issuerId):
    locate_this_issuer = issuer_api+issuerId
    return findApi(locate_this_issuer)


# helper function to locate a learner based on the guid string
def findLearner(learnerId):
    locate_this_learner = learner_api+learnerId
    return findApi(locate_this_learner)


# helper function to locate a item based on the guid string
def findItem(itemId):
    locate_this_item = item_api+itemId
    return findApi(locate_this_item)


# helper function locate a transaction based on the guid string
def findTransaction(transcriptId):
    locate_this_transaction = transcript_api+transcriptId
    return findApi(locate_this_transaction)
# // }}}


################################################################################
# CREATE FUNCTIONS // {{{
################################################################################
# helper function to create a new issuer based on user input
def createIssuer():
    print "Creating new school..."
    i = uuid.uuid4()
    print "Using guid(address): ", i
    n = raw_input("Please enter a name for the school: ")
    c = raw_input("Please enter the country where the school is located: ")
    u = raw_input("Please enter a url for the school: ")
    print "\n"
    return i, n, c, u


# helper function to create a new learner based on user input
def createLearner():
    print "Creating new student..."
    i = uuid.uuid4()
    print "Using guid(address): ", i
    f = raw_input("Please enter a first name for the student: ")
    l = raw_input("Please enter a last name for the student: ")
    s = "asdf"
    # ensure salt is 4 *digits*
    while len(s) != 4 or not s.isdigit():
        s = raw_input("Please enter a 4 digit hash salt value: ")
    print "\n"
    return i, f, l, s


# helper function to create a new item based on user input
def createItem():
    print "Creating new learning record item..."
    i = uuid.uuid4()
    print "Using guid(id): ", i
    n = raw_input("Please enter a name for the learning record item: ")
    u = raw_input("Please enter the units used for measurement: ")
    c = raw_input("Please enter any applicable comments: ")
    print "\n"
    return i, n, u, c


# helper function to create a new transaction based on user input
def createTransaction():
    print "Creating new transaction..."
    q = raw_input("Please the quantity of learning record units: ")
    print "\n"
    return q
# // }}}


################################################################################
# FIXING FUNCTIONS // {{{
################################################################################
# helper function to ensure issuer fields are populated
def fixIssuer(i, n, c, u):
    if not i:
        i = uuid.uuid4()
    if not n:
        n = "default school name"
    if not c:
        c = "default school country"
    if not u:
        u = "default school url"
    return i, n, c, u


# helper function to ensure learner fields are populated
def fixLearner(i, f, l, s):
    if not i:
        i = uuid.uuid4()
    if not f:
        f = "default first name"
    if not l:
        l = "default last name"
    if not s:
        s = '{0:04}'.format(random.randint(1,10000))
    return i, f, l, s


# helper function to ensure item fields are populated
def fixItem(i, n, u, c):
    if not i:
        i = uuid.uuid4()
    if not n:
        n = "default record name"
    if not u:
        u = "default units"
    if not c:
        c = "no comments"
    return i, n, u, c


# helper function to ensure transaction fields are populated
def fixTransaction(q):
    if not q:
        q = "0";
    return q
# // }}}


################################################################################
# JSON/OBJ FUNCTIONS // {{{
################################################################################
# helper function to retrieve json for item id
def getItemJson(item_id):
    item_string = item_api+item_id
    r = requests.get(item_string)
    item_json = json.dumps(r.json())
    return item_json


# helper function to retrieve json for issuer id
def getIssuerJson(issuer_id):
    issuer_string = issuer_api+issuer_id
    r = requests.get(issuer_string)
    issuer_json = json.dumps(r.json())
    return issuer_json


# helper function to retrieve response obj for learner
def getLearnerResponseObj(learner_id):
    learner_string = learner_api+learner_id
    r = requests.get(learner_string)
    return r
# // }}}


################################################################################
# HYDRATE PAYLOAD FUNCTIONS // {{{
################################################################################
# helper function to hydrate issuer payloads
def hydrateIssuerPayload(sid, name, country, url):
    sid, name, country, url = fixIssuer(sid, name, country, url)
    issuer_payload['issuerId']  = sid
    issuer_payload['name']      = name
    issuer_payload['country']   = country
    issuer_payload['url']       = url
    return issuer_payload


# helper function to hydrate learner payloads
def hydrateLearnerPayload(sid, first, last, salt):
    sid, first, last, salt = fixLearner(sid, first, last, salt)
    learner_payload['learnerId'] = sid
    learner_payload['firstName'] = first
    learner_payload['lastName']  = last
    learner_payload['salt']      = salt
    return learner_payload


# helper function to hydrate item payloads
def hydrateItemPayload(sid, name, unit, comment, issuer):
    sid, name, unit, comment = fixItem(sid, name, unit, comment)
    item_payload['itemId']      = sid
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
# // }}}


################################################################################
# CLIENT MODE HELPER FUNCTIONS // {{{
################################################################################
# handles learner mode functions for the client application
def issuerMode():
    # three modes for a school: 1) create school, 2) create class, 3) transact
    sel = raw_input("Please enter a mode - create (s)chool, (c)lass, or (t)ransaction: ")
    print "\n"
    # 1) school...
    if sel[0] == "s":
        # 1) create school...
        sid, name, country, url = createIssuer()
        print "Creating new school with: ", name, country, url
        # check if this guid is in the database
        id_string = str(sid)
        if not findIssuer(id_string):
            print "Not found!  Okay to add..."
            this_payload = hydrateIssuerPayload(sid, name, country, url)
            r = requests.post(issuer_api, data=this_payload)
            print "Added new school, RECORD THIS VALUE: ", sid
            exit()
        else:
            print "Found! Cannot add new school! Exiting!"
            exit()

    # other options require a valid issuer address
    issuer = raw_input("Please enter a valid issuer address: ")
    print "\n"
    found_issuer = False
    if findIssuer(issuer):
        print "Valid issuer!"
        found_issuer = True
    else:
        print "INVALID issuer! Cannot create record without valid issuer"
        exit()

    # 2) class...
    if sel[0] == "c" and found_issuer:
        # 2) create class...
        sid, name, unit, comment = createItem()
        print "Creating new learning record with: ", name, unit, comment
        # check if this guid is in the database
        id_string = str(sid)
        if not findItem(id_string):
            print "Not found!  Okay to add..."
            this_payload = hydrateItemPayload(sid, name, unit, comment,
                                              issuer)
            r = requests.post(item_api, data=this_payload)
            print "Added new record item, RECORD THIS VALUES: ", sid

    # 3) transact...
    elif sel[0] == "t" and found_issuer:
        # we'll want to filter for this later...
        item = raw_input("Please enter a valid item id: ")
        print "\n"
        found_item = False
        if findItem(item):
            print "Valid item!"
            found_item = True
        else:
            print "INVALID item! Cannot create record without valid item"
            exit()
        learner = raw_input("Please enter a valid learner address: ")
        print "\n"
        found_learner = False
        if findLearner(learner):
            print "Valid learner!"
            found_learner = True
        else:
            print "INVALID learner! Cannot create record without valid learner"
            exit()
        valid_quantity = False
        if found_item and found_learner:
            quantity = createTransaction()
            if isFloat(quantity):
                print "Creating new transaction with: ", quantity
                valid_quantity = True
            else:
                print "INVALID quantity! Cannot create transaction without valid quantity"
                exit()

        # we have enough to do a transaction here...
        if valid_quantity:
            item_json = getItemJson(item)
            issuer_json = getIssuerJson(issuer)
            learner_hash = getLearnerHashFromRespObj(getLearnerResponseObj(
                learner))
            this_payload = hydrateTransactionPayloadPreSig(quantity,
                                                           item_json,
                                                           issuer_json,
                                                           learner_hash)
            # sign transaction
            this_payload_json = json.dumps(this_payload)
            string_to_sign = buildStringToSignFromPayload(this_payload_json)

            # get keypair private name
            print "Keypair names have the form 'name'_PRIVATE.pem and 'name'_public.pem..."
            keypair_name = raw_input("Please enter a keypair 'name' to sign: ")
            private_keypair_name = keypair_name + "_PRIVATE.pem"
            signature = signStringWithRsa(string_to_sign,
                                          private_keypair_name)
            this_payload['issuerTxHashSig'] = b64encode(signature)
            payload_json = json.dumps(this_payload)
            r = requests.post(transcript_api, data=this_payload)
            print "Added new transcript transaction!"
            exit()


# handles learner mode functions for the client application
def learnerMode():
    # two modes for a student: 1) create, 2) search
    # 1) create...
    # to create, we need a guid, firstname(entered), lastname(entered), salt
    sid, first, last, salt = createLearner()
    print "\nCreating new student with: ", first, last, salt
    # check if this guid is in the database
    id_string = str(sid)
    # no student id found, go ahead and add
    if not findLearner(id_string):
        print "Not found!  Okay to add..."
        this_payload = hydrateLearnerPayload(sid, first, last, salt)
        r = requests.post(learner_api, data=this_payload)
        print "Added new student, RECORD THESE VALUES: ", sid, salt
        exit()
    else:
        print "Found! Cannot add new user! Exiting!"
        exit()
    # 2) search...
    #TODO


# handles learner mode functions for the client application
def supportMode():
    # N modes for a support: 1) check , 2) search
    # 1) check...
    # to check, we need a guid
    #t_id = raw_input("Please enter a valid transaction id: ")
    #t_string = transaction_api+t_id
    #r = requests.get(t_string)
    #message = buildStringToSignFromResponse(r)
    #signature = getStringSignatureFromResponse(r)
    #sig = b64decode(signature)
    #if isVerifyStringWithRsa(message, 'test_public.pem', sig):
    #    print "This transaction has a valid signature!"
    #    #exit()
    #else:
    #    print "This transaction has an INVALID signature!"
    #    #exit()
    # 2) search...
    l_id = raw_input("Please enter a valid learner address: ")
    # get keypair public name
    print "Keypair names have the form 'name'_PRIVATE.pem and 'name'_public.pem..."
    keypair_name = raw_input("Please enter a keypair 'name' to verify: ")
    public_keypair_name = keypair_name + "_public.pem"
    l_hash = getLearnerHashFromRespObj(getLearnerResponseObj(l_id))
    r = requests.get(transaction_api)
    complete_transaction_list = json.loads(r.text)
    learner_transaction_list = []
    for transaction in complete_transaction_list:
        if transaction['learnerHash'] == l_hash:
            learner_transaction_list.append(transaction)
    # only print valid transactions
    for transaction in learner_transaction_list:
        t_id = transaction['transactionId']
        print "Verifying " + str(t_id) + "... "
        t_string = transaction_api+t_id
        r = requests.get(t_string)
        message = buildStringToSignFromResponse(r)
        signature = getStringSignatureFromResponse(r)
        sig = b64decode(signature)
        if isVerifyStringWithRsa(message, public_keypair_name, sig):
            print "Valid transcript item(s):\n"
            print message
            print "--------------------\n"
        else:
            print "INVALID signature!\n"
    exit()
# // }}}


################################################################################
# MISC HELPER FUNCTIONS // {{{
################################################################################
# checks if a string is a float (for transaction quanities)
# grabbed from https://stackoverflow.com/questions/354038/how-do-i-check-if-a-string-is-a-number-float-in-python
def isFloat(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


# gets user input
def getUserModeSelect():
    # select client modes
    print "Possible client modes:"
    for mode in client_modes:
        print mode
    sel_client_mode = raw_input("Enter a client mode: ")
    if sel_client_mode[0] not in client_shortcuts:
        return None
    else:
        return sel_client_mode[0]
# // }}}


################################################################################
# MAIN APPLICATION // {{{
################################################################################
# client application main()
def main():
    user_selection = getUserModeSelect()
    print "\n"
    # execute appropriate subcall
    if user_selection == client_shortcuts[0]:
        issuerMode()
    elif user_selection == client_shortcuts[1]:
        learnerMode()
    elif user_selection == client_shortcuts[2]:
        supportMode()
    else:
        print "INVALID mode... exiting!"
        exit()

if __name__ == "__main__":
    main()
# // }}}
