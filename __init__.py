import copy
import csv
import json
import os
import re
from subprocess import check_output, Popen
from time import sleep
from mycroft import MycroftSkill, intent_file_handler
from mycroft.api import DeviceApi
from mycroft.configuration import Configuration
from mycroft.messagebus.message import Message
from mycroft.util.format import nice_duration
# from test.integrationtests.skills.skill_tester import
join = os.path.join

class SkillTesting(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.file_path_base = get_skills_dir()
        self.file_path_test = 'test/intent'
        self.file_path_reading_output = '/'.join([
            self.file_system.path,
            'reading-output'])
        if not os.path.isdir(self.file_path_reading_output):
            os.mkdir(self.file_path_reading_output)
        self.reset_data_vars()

    def initialize(self):
        self.update_settings()

    def update_settings(self):
        self.test_identifier = self.settings.get('test_identifier', '')
        for l in csv.reader([self.settings.get('phrases', '')],
                            skipinitialspace=True):
            self.input_utterances = l
        self.delay = int(self.settings.get('delay', '30'))

    @intent_file_handler('read.utterances.intent')
    def read_utterances(self, message):
        self.update_settings()
        num_tests = len(self.input_utterances)
        # TODO Currently a guess, modify once we have better data
        avg_response_time = 20
        estimated_length = nice_duration(num_tests * (
                                         self.delay + avg_response_time))
        self.speak_dialog('reading.started',
                          data={'num': num_tests,
                                'estimated_length': estimated_length})
        sleep(self.delay)
        # Add extra utterance to call final code
        # Why? Workaround as code in handler after phrase loop doesn't execute
        self.input_utterances.append(self.translate('trigger.reading.complete'))
        self.add_event('mycroft.skill.handler.start', self.detect_handler)
        self.add_event('speak', self.detect_response)
        for i, phrase in enumerate(self.input_utterances):
            phrase = phrase.strip().strip('"').strip()
            if i < len(self.input_utterances) - 1:
                # TODO would it be better to
                # catch the utterance from the messagebus
                self.reading_output.append([phrase])
            self.bus.emit(Message("recognizer_loop:utterance",
                                      {'utterances': [phrase],
                                      'lang': 'en-us'}))
            sleep(self.delay)

    def detect_handler(self, m):
        handler_message_data = json.loads(m.serialize())['data']
        self.log.debug(handler_message_data)
        if 'name' in handler_message_data.keys():
            name, intent = handler_message_data['name'].split('.')
            if name != 'SkillTesting':
                self.reading_output[len(self.reading_output)-1].extend(
                (name, intent))

    def detect_response(self, m):
        message_data = json.loads(m.serialize())['data']
        self.log.debug(message_data)
        if 'utterance' in message_data.keys():
            self.reading_output[len(self.reading_output)-1].append(
                (message_data['utterance']))

    @intent_file_handler('reading.complete.intent')
    def handle_reading_complete(self, message):
        sleep(self.delay)
        self.speak_dialog('reading.complete')
        # Save locally to potentially generate tests from
        # Remove unsupported characters from filename
        file_name = ''.join(
            x for x in self.test_identifier \
            if (x.isalnum() or x in "._-")) + '.csv'
        # TODO Actually track which output files are created and manage them
        self.output_file = '/'.join([self.file_path_reading_output, file_name])
        with open(self.output_file, 'w') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerows(self.reading_output)
        # Upload to Termbin
        upload_cmd = 'cat ' + self.output_file + ' | nc termbin.com 9999'
        url = check_output(upload_cmd, shell=True).decode().strip('\n\x00')
        # Email to User
        data = {
            'test_identifier': self.test_identifier,
            'url': url,
            'device_name': self.get_device_name(),
            'num_tests': len(self.reading_output) - 1
            }
        email = '\n'.join(self.translate_template('phrase.results.email', data))
        subject = self.translate('phrase.results.email.subject', data)
        # self.send_email(subject, email)
        # Reset variables and finish
        self.reset_data_vars()

    def reset_data_vars(self):
        self.reading_output = [['Utterance', 'Skill', 'IntentHandler', 'Response']]
        self.files_created = []

    def get_device_name(self):
        try:
            return DeviceApi().get()['name']
        except:
            return self.log.exception('API Error')
            return ':error:'

    @intent_file_handler('create.tests.intent')
    def handle_create_tests(self, message):
        # imported_csv = '/'.join([
        #     self.file_path_base,
        #     'skill-testing-skill.krisgesling',
        #     'tests_to_create.csv'])
        # self.create_tests(imported_csv)
        self.log.debug('Creating test files')
        with open(self.output_file) as csvfile:
            tests_to_create = csv.DictReader(csvfile)
            for test in tests_to_create:
                if test['Skill'] == '':
                    continue
                test_file_name = "".join(
                    x for x in test['Utterance'] \
                    if (x.isalnum() or x in "._-")) + 'intent.json'
                # TODO Fix - need to get Skill directory from Skillname
                # [self.file_path_base, test['Skill'], \
                test_file_path = '/'.join(
                    [self.file_path_base, 'mycroft-weather.mycroftai', \
                    self.file_path_test, test_file_name])
                self.files_created.append(test_file_path)
                with open(test_file_path, "w+") as test_file:
                    test_file.write(self.test_template(
                        test['Utterance'], test['IntentHandler']))
                    test_file.close()

    def test_template(self, utterance, intent_type):
        return '\n'.join(['{',
                          '    "utterance": "{utterance}",',
                          '    "intent_type": "{intent_type}"',
                          '}'])

    @intent_file_handler('run.tests.intent')
    def handle_run_tests(self, message):
        self.speak('running tests')
        os.system('mycroft-start skillstest')

    @intent_file_handler('remove.tests.intent')
    def handle_remove_tests(self, message):
        self.log.debug('Removing files')
        files_removed = []
        for f in self.files_created:
            if os.path.exists(f):
                os.remove(f)
            files_removed.append(f)

        if set(files_removed) == set(self.files_created):
            self.speak_dialog('all.files.removed')
            self.files_created = []
        else:
            self.speak_dialog('file.removal.failed')
            self.log.info('WARNING: Some files could not be removed')
            files_not_removed = set(self.files_created) - set(files_removed)
            for f in files_not_removed:
                self.log.info(f)

def get_skills_dir():
    return (
        os.path.expanduser(os.environ.get('SKILLS_DIR', '')) or
        os.path.expanduser(join(
            Configuration.get()['data_dir'],
            Configuration.get()['skills']['msm']['directory']
        ))
    )

def stop(self):
    pass

def create_skill():
    return SkillTesting()
