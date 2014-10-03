from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from mongoengine import NULLIFY, PULL


'''
Grade book models
'''
class GradeBook(db.EmbeddedDocument):
  categories = db.ListField(db.EmbeddedDocumentField('GBCategory'))

  def getCategoryByName(self, name):
    for c in self.categories:
      if c.name == name:
        return c
    return None

  def cleanup(self):
    for c in self.categories:
      c.cleanup()

class GBCategory(db.EmbeddedDocument):
  name = db.StringField(required=True)
  entries = db.ListField(db.ReferenceField('GBEntry'))

  def __init__(self, name, **data):
    super(GBCategory, self).__init__(**data)
    self.name = name

  def cleanup(self):
    for e in self.entries:
      e.cleanup()
      e.delete()

class GBEntry(db.Document):
  name = db.StringField(required=True)
  columns = db.ListField(db.ReferenceField('GBColumn'))

  def __init__(self, name, **data):
    super(GBEntry, self).__init__(**data)
    self.name = name

  def cleanup(self):
    for c in self.columns:
      c.cleanup()
      c.delete()

class GBColumn(db.Document):
  name = db.StringField()
  maxScore = db.DecimalField(default=0)

  #Map usernames to grade entries
  scores = db.MapField(db.ReferenceField('GBGrade'))


  def __init__(self, name, **data):
    super(GBColumn, self).__init__(**data)
    self.name = name

  def cleanup(self):
    # for k in self.scores:
    #   s = self.scores[k]
    #   self.scores[k] = None
    #   s.delete()
    pass

class GBGrade(db.Document):
  #Map score name (eg. GrutorScore or TestScore) to scores
  scores = db.MapField(db.DecimalField())


'''
Course and submission models
'''

class Submission(db.EmbeddedDocument):
  submissionTime = db.DateTimeField(required=True)
  isLate = db.BooleanField(default=False)
  filePath = db.StringField(required=True)
  grade = db.ReferenceField('GBGrade')

  def cleanup(self):
    try:
      self.grade.delete()
    except:
      pass

class StudentSubmissionList(db.EmbeddedDocument):
  submissions = db.ListField(db.EmbeddedDocumentField('Submission'))
  partners = db.ListField(db.ReferenceField('User'))

  def cleanup(self):
    for s in self.submissions:
      s.cleanup()
    self.submissions = []

class Problem(db.Document):
  name = db.StringField()
  gradeColumn = db.ReferenceField('GBColumn', reverse_delete_rule=NULLIFY)
  duedate = db.DateTimeField()
  rubric = db.MapField(db.DecimalField())

  #Map usernames to submission lists
  studentSubmissions = db.MapField(db.EmbeddedDocumentField('StudentSubmissionList'))

  def __init__(self, name, **data):
    super(Problem, self).__init__(**data)
    self.name = name

  def cleanup(self):
    if self.gradeColumn != None:
      self.gradeColumn.cleanup()
    for k in self.studentSubmissions:
      self.studentSubmissions[k].cleanup()

  def totalPoints(self):
    total = 0
    for k in self.rubric:
      total += self.rubric[k]
    return total

  def getSubmissionStatus(self, user):
    '''Returns a status number and if the assignemnt is late'''
    if user.username in self.studentSubmissions:
      return (1, False)
    else:
      return (0, False)

class AssignmentGroup(db.Document):
  name = db.StringField(required=True)
  gradeEntry = db.ReferenceField('GBEntry', reverse_delete_rule=NULLIFY)
  problems = db.ListField(db.ReferenceField('Problem', reverse_delete_rule=PULL))

  def __init__(self, name, **data):
    super(AssignmentGroup, self).__init__(**data)
    self.name = name

  def cleanup(self):
    if self.gradeEntry != None:
      self.gradeEntry.cleanup()
    for p in self.problems:
      p.cleanup()
      p.delete()

class Course(db.Document):
  #Identification information
  name = db.StringField(required=True)
  semester = db.StringField(required=True)

  #Information for grading and submission
  gradeBook = db.EmbeddedDocumentField('GradeBook')
  assignments = db.ListField(db.ReferenceField('AssignmentGroup', reverse_delete_rule=PULL))

  #Is this course still being taught at this time
  isActive = db.BooleanField(default=True)

  def cleanup(self):
    self.gradeBook.cleanup()

    for a in self.assignments:
      a.cleanup()
      a.delete()

'''
User model(s)
'''
class User(db.Document):
  #General user information
  firstName = db.StringField()
  lastName = db.StringField()
  username = db.StringField(required=True)
  email = db.EmailField()
  passHash = db.StringField(max_length=512)

  #What courses are they teaching/in
  courseStudent    = db.ListField(db.ReferenceField('Course', reverse_delete_rule=PULL))
  courseGrutor     = db.ListField(db.ReferenceField('Course', reverse_delete_rule=PULL))
  courseInstructor = db.ListField(db.ReferenceField('Course', reverse_delete_rule=PULL))

  #Is this user an admin
  isAdmin = db.BooleanField(default=False)

  def is_authenticated(self):
    return True

  def is_active(self):
    return True

  def is_anonymous(self):
    return False

  def get_id(self):
    return unicode(self.id)

  def setPassword(self, pw):
    self.passHash = generate_password_hash(pw)

  def checkPassword(self, pw):
    return check_password_hash(self.passHash, pw)

  def gradingCourses(self):
    out = self.courseGrutor + self.courseInstructor
    out = list(set(out))
    return out
