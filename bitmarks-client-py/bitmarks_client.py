import sys
import uuid
import requests

# bitmark connection definitions
namespace = "edu.gatech.bitmarks"
resource = "resource:"+namespace
bitmarks_api = "http://localhost:3000/api/"
not_found = 404

# bitmark model definitions
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


def issuerMode():
    print "Creating new school..."
    schoolId = uuid.uuid4()
    print "Using guid(address): ", schoolId
    # three modes for a school: 1) create school, 2) create class, 3) transact
    # 1) create school...
    # to create, we need a guid, firstname(entered), lastname(entered), salt

    # 2) create class...
    # to create, we need a guid, firstname(entered), lastname(entered), salt

    # 3) transact...
    # to create, we need a guid, firstname(entered), lastname(entered), salt


# helper function to create a new student based on user input
def createLearner():
    print "Creating new student..."
    i = uuid.uuid4()
    print "Using guid(address): ", i
    f = raw_input("Please enter a first name for new student: ")
    l = raw_input("Please enter a last name for new student: ")
    s = "asdf"
    # ensure salt is 4 *digits*
    while len(s) != 4 or not s.isdigit():
        s = raw_input("Please enter a 4 digit hash salt value: ")
    print "\n"
    return i, f, l, s


# helper function to locate a student based on the string of the student guid
def findLearner(learnerId):
    locate_this_learner = learner_api+learnerId
    r = requests.get(locate_this_learner)
    if r.status_code == not_found:
        return False
    return True


# handles learner mode functions for the client application
def learnerMode():
    # two modes for a student: 1) create, 2) search
    # 1) create...
    # to create, we need a guid, firstname(entered), lastname(entered), salt
    sid, first, last, salt = createLearner()
    print "Creating new student with: ", first, last, salt
    # check if this guid is in the database
    studentId_string = str(sid)
    # no student id found, go ahead and add
    if not findLearner(studentId_string):
        print "Not found!  Okay to add..."
        learner_payload["learnerId"] = sid
        learner_payload["firstName"] = first
        learner_payload["lastName"]  = last
        learner_payload["salt"]      = salt
        r = requests.post(learner_api, data=learner_payload)
        print "Added new student, RECORD THESE VALUES: ", sid, salt
    else:
        print "Found!  Cannot add new user!  Exiting!"
        exit()
    # 2) search...
    #TODO

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

