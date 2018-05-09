#!/usr/bin/env python3
# Author: William Henning <whenning@google.com>

import re
import os
import sys
import platform
from collections import defaultdict

# parse_test_results.py overview
#
# usage:
#    python parse_test_results.py
#
# This script parses the validation layers tests and reports the number of
# passes, failures, unexpected errors, and tests that were skipped on every
# device.

skip_prefix = "TEST_SKIPPED: "

class OutputStats(object):
  def __init__(self):
    self.current_profile = ""
    self.current_test = ""
    self.test_results = defaultdict(defaultdict)

  def match(self, line):
    self.new_profile_match(line)
    self.test_suite_end_match(line)
    self.start_test_match(line)
    self.skip_test_match(line)
    self.pass_test_match(line)
    self.fail_test_match(line)
    self.unexpected_error_match(line)

  def print_summary(self):
    passed_tests = 0
    skipped_tests = 0
    failed_tests = 0
    for test_name, results in self.test_results.items():
      skipped_profiles = 0
      passed_profiles = 0
      failed_profiles = 0
      for profile, result in results.items():
        if result == "pass":
          passed_profiles += 1
        if result == "fail":
          failed_profiles += 1
        if result == "skip":
          skipped_profiles += 1
      if failed_profiles != 0:
        print("TEST FAILED:", test_name)
        failed_tests += 1
      elif skipped_profiles == len(results):
        print("TEST NEVER RAN:", test_name)
        skipped_tests += 1
      else:
        passed_tests += 1
    num_tests = len(self.test_results)
    print("PASSED: ", passed_tests, "/", num_tests, " tests")
    if skipped_tests != 0:
      print("NEVER RAN: ", skipped_tests, "/", num_tests, " tests")
    if failed_tests != 0:
      print("FAILED: ", failed_tests, "/", num_tests, "tests")

  def new_profile_match(self, line):
    if re.search(r'Testing with profile .*/(.*)', line) != None:
      self.current_profile = re.search(r'Testing with profile .*/(.*)', line).group(1)

  def test_suite_end_match(self, line):
    if re.search(r'\[-*\]', line) != None:
      self.test_case = ""

  def start_test_match(self, line):
    if re.search(r'\[ RUN\s*\]', line) != None:
      test = re.search(r'] (.*)', line).group(1)
      self.start_test(test)

  def skip_test_match(self, line):
    if re.search(r'TEST_SKIPPED', line) != None:
      self.test_results[self.current_test][self.current_profile] = "skip"

  def pass_test_match(self, line):
    if re.search(r'\[\s*OK \]', line) != None:
      self.pass_test()

  def fail_test_match(self, line):
    if re.search(r'\[\s*FAILED\s*\]', line) != None and self.current_test != "":
      self.fail_test()

  def unexpected_error_match(self, line):
    pass

  def start_test(self, test_name):
    assert self.current_test == ""
    self.current_test = test_name

  def pass_test(self):
    if self.test_results.get(self.current_test, {}).get(self.current_profile, "") != "skip":
        self.test_results[self.current_test][self.current_profile] = "pass"
    self.current_test = ""

  def fail_test(self):
    self.test_results[self.current_test][self.current_profile] = "fail"
    self.current_test = ""

  def skip_test(self):
    self.test_results[self.current_test][self.current_profile] = "skip"
    current_test = ""

  def unexpected_error(self):
    pass

def main():
  stats = OutputStats()
  for line in sys.stdin:
    stats.match(line)
  stats.print_summary()

if __name__ == '__main__':
  main()
