import sys
import uuid
import requests
import json
import random
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

# bitmark connection definitions // {{{
namespace = "edu.gatech.bitmarks"
resource = "resource:"+namespace
#bitmarks_api = "http://localhost:3000/api/"
bitmarks_api = "http://ec2-34-212-169-28.us-west-2.compute.amazonaws.com:3000/api/"
not_found = 404
# // }}}

# bitmark model definitions // {{{
class_key = "$class"

## TRANSCRIPT TRANSACTION
transcript_payload_keys = [class_key, "quantity", "item", "issuer", "learner",
                           "itemJSON", "issuerJSON", "learnerHash",
                           "issuerTxHashSig", "transactionId", "timestamp"]
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

# user client definitions
client_modes = ["  (i)ssuer", "  (l)earner", "  (s)upport"]
client_shortcuts = ["i", "l", "s"]
# // }}}

################################################################################
# CRYPTO FUNCTIONS // {{{
################################################################################
# derived from https://gist.github.com/lkdocs/6519378
def generateRsaKeypair(bits=2048):
    new_key = RSA.generate(bits, e=65537)
    public_key = new_key.publickey().exportKey("PEM")
    private_key = new_key.exportKey("PEM")
    return private_key, public_key


# derived from https://www.dlitz.net/software/pycrypto/api/current/Crypto.PublicKey.RSA-module.html 
def writeRsaKeysToFile(filename):
    private_key, public_key = generateRsaKeypair()
    f_private = open(filename+"_PRIVATE.pem", 'w')
    f_private.write(private_key)
    f_public = open(filename+"_public.pem", 'w')
    f_public.write(public_key)
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
# HYDRATE PAYLOAD FUNCTIONS // {{{
################################################################################
# helper function to hydrate issuer payloads
def hydrateIssuerPayload(sid, name, country, url):
    sid, name, country, url = fixIssuer(sid, name, country, url)
    issuer_payload["issuerId"]  = sid
    issuer_payload["name"]      = name
    issuer_payload["country"]   = country
    issuer_payload["url"]       = url
    return issuer_payload


# helper function to hydrate learner payloads
def hydrateLearnerPayload(sid, first, last, salt):
    sid, first, last, salt = fixLearner(sid, first, last, salt)
    learner_payload["learnerId"] = sid
    learner_payload["firstName"] = first
    learner_payload["lastName"]  = last
    learner_payload["salt"]      = salt
    return learner_payload


# helper function to hydrate item payloads
def hydrateItemPayload(sid, name, unit, comment, issuer):
    sid, name, unit, comment = fixItem(sid, name, unit, comment)
    item_payload["itemId"]      = sid
    item_payload["credential"]  = name
    item_payload["units"]       = unit
    item_payload["comments"]    = comment
    item_payload["issuer"]      = issuer_resource+issuer
    return item_payload
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
            print "Added new record item!"

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
            print "start"
            # first, get json for item
            item_string = item_api+item
            r = requests.get(item_string)
            item_json = json.dumps(r.json())
            # second, get json for issuer
            issuer_string = issuer_api+issuer
            r = requests.get(issuer_string)
            issuer_json = json.dumps(r.json())
            # third, get hash for learner...
            # - first, build learner string to has
            learner_string = learner_api+learner
            r = requests.get(learner_string)
            hash_1 = r.json()['firstName']
            hash_2 = r.json()['lastName']
            hash_3 = str(r.json()['salt'])
            learner_string_to_hash = hash_1 + " " + hash_2 + " " + hash_3
            learner_hash = SHA256.new(learner_string_to_hash).hexdigest()
            print "done"


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
    else:
        print "Found! Cannot add new user! Exiting!"
        exit()
    # 2) search...
    #TODO


# handles learner mode functions for the client application
def supportMode():
    print "entered support mode"
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

    writeRsaKeysToFile('test')

    exit()
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
