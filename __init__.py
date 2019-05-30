import copy
import csv
import json
import os
from subprocess import check_output
from time import sleep
from mycroft import MycroftSkill, intent_file_handler
from mycroft.api import DeviceApi
from mycroft.configuration import Configuration
from mycroft.messagebus.message import Message
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
        self.test_identifier = self.settings.get('test_identifier', '')
        self.phrase_delimeter = self.settings.get('phrase_delimeter', ',')
        self.text_delimeter = self.settings.get('text_delimeter', '"')
        self.input_utterances = self.settings.get(
            'phrases',
            'what is my ip, who made you'
            ).split(self.phrase_delimeter)
        self.delay = int(self.settings.get('delay', '30'))

    def reset_data_vars(self):
        self.reading_output = [['Phrase', 'SkillName', 'IntentHandler']]
        self.files_created = []

    def detect_handler(self, m):
        handler_message_data = json.loads(m.serialize())['data']
        self.log.debug(handler_message_data)
        if 'name' in handler_message_data.keys():
            name, intent = handler_message_data['name'].split('.')
            if name != 'SkillTesting':
                self.reading_output[len(self.reading_output)-1].extend(
                                                                (name, intent))

    @intent_file_handler('read.utterances.intent')
    def read_utterances(self, message):
        # Add extra utterance to call final code
        # Why? Workaround as code in handler after phrase loop doesn't execute
        self.input_utterances.append(self.translate('trigger.reading.complete'))
        self.add_event('mycroft.skill.handler.start', self.detect_handler)
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

    @intent_file_handler('reading.complete.intent')
    def handle_reading_complete(self, message):
        self.log.debug('Finished reading. Building output...')
        # Save locally to potentially generate tests from
        # Remove unsupported characters from filename
        file_name = ''.join(
            x for x in self.test_identifier \
            if (x.isalnum() or x in "._-")) + '.csv'
        output_file = '/'.join([self.file_path_reading_output, file_name])
        with open(output_file, 'w') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerows(self.reading_output)
        # Upload to Termbin
        upload_cmd = 'cat ' + output_file + ' | nc termbin.com 9999'
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
        self.send_email(subject, email)
        # Reset variables and finish
        self.reset_data_vars()
        self.speak_dialog('reading.complete')

    @intent_file_handler('create.tests.intent')
    def handle_testing_skill(self, message):
        imported_csv = '/'.join([
            self.file_path_base,
            'skill-testing-skill.krisgesling',
            'tests_to_create.csv'])
        self.create_tests(imported_csv)
        sleep(5)
        # Run the tests?
        self.remove_created_tests(self.files_created)

    def create_tests(self, imported_csv):
        self.log.debug('Creating test files')
        with open(imported_csv) as csvfile:
            tests_to_create = csv.DictReader(csvfile)
            for test in tests_to_create:
                test_file_name = "".join(
                    x for x in test['utterance'] \
                    if (x.isalnum() or x in "._-")) + 'intent.json'
                test_file_path = '/'.join(
                    [self.file_path_base, test['skill'], \
                     self.file_path_test, test_file_name])
                self.files_created.append(test_file_path)
                with open(test_file_path, "w+") as test_file:
                    test_file.write(self.test_template(
                        test['utterance'], test['expected_dialog']))
                    test_file.close()

    def get_device_name(self):
        try:
            return DeviceApi().get()['name']
        except:
            return self.log.exception('API Error')
            return ':error:'

    def remove_created_tests(self, file_list):
        self.log.debug('Removing files')
        files_removed = []
        for f in file_list:
            if os.path.exists(f):
                os.remove(f)
            files_removed.append(f)

        if set(files_removed) == set(file_list):
            self.log.info('All Files removed')
            # TODO should I be reseting files_removed and/or files_created
        else:
            self.log.info('WARNING: Some files could not be removed')
            files_not_removed = set(file_list) - set(files_removed)
            for f in files_not_removed:
                self.log.info(f)

    def test_template(self, utterance, expected_dialog):
        return '\n'.join([
            '{',
            '    "utterance": "{utterance}",',
            '    "expected_dialog": "{expected_dialog}"',
            '}'
            ])

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
