import sys
import uuid
import requests

# bitmark connection definitions
namespace = "edu.gatech.bitmarks"
resource = "resource:"+namespace
bitmarks_api = "http://localhost:3000/api/"

# bitmark model definitions
## TRANSCRIPT TRANSACTION
transcript_payload_keys = ["$class", "quantity", "item", "issuer", "learner",
                           "itemJSON", "issuerJSON", "learnerHash",
                           "issuerTxHashSig", "transactionId", "timestamp"]
transcript_payload = dict.fromkeys(transcript_payload_keys)
transcript_class = "AcademicTransaction"
transcript_namespace_class = namespace+"."+transcript_class
transcript_resource = resource+"."+transcript_class+"#"
transcript_api = bitmarks_api+transcript_class+"/"

## ISSUERS
issuer_payload_keys = ["$class", "issuerId", "name", "country", "url"]
issuer_payload = dict.fromkeys(issuer_payload_keys)
issuer_class = "Issuer"
issuer_namespace_class = namespace+"."+issuer_class
issuer_resource = resource+"."+issuer_class+"#"
issuer_api = bitmarks_api+issuer_class+"/"

## LEARNERS
learner_payload_keys = ["$class", "learnerId", "firstName", "lastName", "salt"]
learner_payload = dict.fromkeys(learner_payload_keys)
learner_class = "Learner"
learner_namespace_class = namespace+"."+learner_class
learner_resource = resource+"."+learner_class+"#"
learner_api = bitmarks_api+learner_class+"/"

## TRANSCRIPT LINE ITEMS (CREDENTIALS)
item_payload_keys = ["$class", "itemId", "credential", "units", "comments",
                     "issuer"]
item_payload = dict.fromkeys(item_payload_keys)
item_class = "TranscriptItem"
item_namespace_class = namespace+"."+item_class
item_resource = resource+"."+item_class+"#"
item_api = bitmarks_api+item_class+"/"

# user client definitions 
client_modes = ["  (i)ssuer", "  (l)earner", "  (s)upport"]
client_shortcuts = ["i", "l", "s"]


def issuerMode():
    print "entered issuer mode"


def learnerMode():
    print "entered learner mode"


def supportMode():
    print "entered support mode"


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

# client application main()
def main():
    user_selection = getUserModeSelect()
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

# select client modes
client_modes = ["  (i)ssuer", "  (l)earner", "  (s)upport"]
client_shortcuts = ["i", "l", "s"]
print "Possible client modes:"
for mode in client_modes:
    print mode
sel_client_mode = raw_input("Enter a client mode: ")
if sel_client_mode[0] not in client_shortcuts:
    print "INVALID mode... exiting!"
    exit()

# execute appropriate subcall
if sel_client_mode[0] == client_shortcuts[0]:
    issuerMode()
elif sel_client_mode[0] == client_shortcuts[1]:
    learnerMode()
elif sel_client_mode[0] == client_shortcuts[2]:
    supportMode()
else:
    print "Should not see this!"
    exit()

# work with clients mode selected
if sel_client_mode == client_modes[0]:
    print 'create school mode...'
    schoolId = uuid.uuid4()
    print 'using guid(address): ', schoolId
elif sel_client_mode == client_modes[1]:
    print 'create student mode...'
    studentId = uuid.uuid4()
    print 'using guid(address): ', studentId
    # two modes for a student: create, search
    # mode 1) create:
    # to create, we need a guid, firstname(entered), lastname(entered), salt
    fName = raw_input('Please enter a first name for new student: ')
    lName = raw_input('Please enter a last name for new student: ')
    salt = 'asdf'
    while len(salt) != 4 or not salt.isdigit():
        salt = raw_input('Please enter a 4 digit hash salt value: ')
    print 'creating new student with: ', fName, lName, salt
    # check if this guid is in the database
    check_user = bitmarks_url + str(studentId)
    print 'checking for user: ', check_user
    r = requests.get(check_user)
    # no student id found, go ahead and add
    if r.status_code == 404:
        print 'not found!  okay to add...'
        payload = {'$class'     : learner_class,
                   'learnerId'  : studentId,
                   'firstName'  : fName,
                   'lastName'   : lName,
                   'salt'       : salt}
        r = requests.post(bitmarks_url, data=payload)
        print 'added new student, RECORD THESE VALUES: ', studentId, salt
    else:
        print 'found!  cannot add new user'
elif sel_client_mode == client_modes[2]:
    print 'interviewer mode...'

