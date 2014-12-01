import re
from subprocess import Popen, PIPE
from os import environ
from datetime import datetime
import re

import itertools, json

PLUGIN_NAME = "Python"

PYTHON_TEST_REGEX=r"^.*?def (.*?)\(self\):$"

def testFileParser(filename):
  '''
  Takes a python pyunit test file and attempts to extract all the tests.
  It may accidentally grab other helper functions you define because it is
  using a simple regex search.
  '''
  with open(filename) as f:
    contents = f.read()

  testRegex = re.compile(PYTHON_TEST_REGEX, re.M)

  testNames = []

  for test in testRegex.findall(contents):
    if test != "setUp" and test != "tearDown":
      testNames.append(test)

  return testNames

def runTests(cmdPrefix, testFile, timeLimit):
  startTime = datetime.now()
  testProc = Popen(cmdPrefix + ['python', testFile], \
                    stdout=PIPE, stderr=PIPE, env=environ)

  timeoutReached = False
  while testProc.poll() is None:
    currentTime = datetime.now()
    delta = currentTime - startTime
    if delta.total_seconds() > timeLimit:
      testProc.kill()
      timeoutReached = True
      break


  #Check for a timeout
  if timeoutReached:
    summary = {}
    summary['totalTests'] = 0
    summary['failedTests'] = 0
    summary['timeout'] = timeoutReached
    summary['died'] = False
    summary['generalError'] = ""

    return summary, {}

  testOut, testError = testProc.communicate()

  #Parse the results
  testSummarySearch = re.search("Ran ([0-9]+) tests in", testError)

  #If we don't find the test summary the tests died so we report that
  if not testSummarySearch:
    summary = {}
    summary['totalTests'] = 0
    summary['failedTests'] = 0
    summary['timeout'] = timeoutReached
    summary['died'] = True
    summary['generalError'] = testError

    return summary, {}

  # Get the list of failed tests

  failedSections = testError.split('='*70)

  splitList = []
  for section in failedSections:
    splitList.append(section.split('-'*70))

  #flatten the lists
  sections = list(itertools.chain.from_iterable(splitList))

  #Create the summary
  summary = {}
  summary['totalTests'] = int(testSummarySearch.group(1))

  failedSections = sections[1:-1]
  summary['failedTests'] = len(failedSections)/2
  summary['died'] = False
  summary['timeout'] = False

  #Extract the messages from the failed tests
  failedTests = {}
  for i in range(0, len(failedSections), 2):
    header = failedSections[i]
    headerParts = header.split()
    tname = headerParts[1]

    pyunitmsg = failedSections[i+1]

    failedTests[tname] = {'hint': pyunitmsg}

  return summary, failedTests

# def runTests(cmdPrefix, testFile, timeLimit):
#   startTime = datetime.now()
#   testProc = Popen(cmdPrefix + ['python', testFile], stdout=PIPE, stderr=PIPE, env=environ)
#
#   timeoutReached = False
#   while testProc.poll() is None:
#     currentTime = datetime.now()
#     delta = currentTime - startTime
#     if delta.total_seconds() > timeLimit:
#       testProc.kill()
#       timeoutReached = True
#       break
#
#   return timeoutReached, testProc.stdout.read(), testProc.stderr.read()

def testResultParser(output, error):
  failedSections = error.split('='*70)

  splitList = []
  for section in failedSections:
    splitList.append(section.split('-'*70))

  #Flatten the list
  sections = list(itertools.chain.from_iterable(splitList))

  #Check how many tests were run based on the summary
  summarySection = sections[-1]
  summaryWords = summarySection.split()

  summary = {}
  summary['total'] = int(summaryWords[1])

  failedSections = sections[1:-1]
  summary['failed'] = int(len(failedSections)/2)
  summary['died'] = False

  failedTests = {}

  #Extract the messages for the failed tests
  for i in range(0, len(failedSections), 2):
    header = failedSections[i]
    headerParts = header.split()
    tname = headerParts[1]

    pyunitmsg = failedSections[i+1]

    failedTests[tname] = {'hint': pyunitmsg}

  return summary, failedTests
